import hashlib
import re
from io import BytesIO

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from pypdf import PdfReader

from gestion_casos.models import (
    DocumentoInstitucional,
    ReglaInstitucional,
    VersionReglamento,
)
from gestion_casos.reglamento_2026 import (
    DISPOSICIONES_REGLAMENTO_2026,
    PDF_SHA256_REGLAMENTO_2026,
    VERSION_FUENTE_REGLAMENTO_2026,
)


def _normalizar_cita(texto):
    return re.sub(r'\s+', ' ', texto).strip()


def _clave_cita(texto):
    return re.sub(r'\s+', '', texto).casefold()


class Command(BaseCommand):
    help = (
        'Agrega disposiciones verificadas del Reglamento Interno 2026 como reglas '
        'pendientes; no modifica propuestas existentes.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--version-id', type=int, required=True)

    @staticmethod
    def _hash_origen(disposicion):
        return hashlib.sha256(
            (
                f'{PDF_SHA256_REGLAMENTO_2026}\0'
                f'{disposicion["clave"]}\0'
                f'{disposicion["evidencia_textual"]}'
            ).encode('utf-8')
        ).hexdigest()

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            version = (
                VersionReglamento.objects.select_for_update()
                .select_related('documento')
                .get(pk=options['version_id'])
            )
        except VersionReglamento.DoesNotExist as error:
            raise CommandError('No existe esa versión de reglamento.') from error

        documento = version.documento
        if documento.tipo_documento != 'Reglamento':
            raise CommandError('La versión no pertenece a un reglamento.')
        if documento.estado_procesamiento != DocumentoInstitucional.EstadoProcesamiento.COMPLETADO:
            raise CommandError('El documento no está procesado correctamente.')
        if documento.checksum_sha256 != PDF_SHA256_REGLAMENTO_2026:
            raise CommandError(
                'El checksum del documento no corresponde al PDF oficial verificado; '
                'no se agregaron disposiciones.'
            )
        try:
            with documento.archivo.open('rb') as archivo:
                contenido_pdf = archivo.read()
            lector = PdfReader(BytesIO(contenido_pdf), strict=False)
            paginas_pdf = [pagina.extract_text() or '' for pagina in lector.pages]
        except Exception as error:
            raise CommandError(
                'No se pudo volver a verificar la paginación del PDF almacenado.'
            ) from error
        if hashlib.sha256(contenido_pdf).hexdigest() != PDF_SHA256_REGLAMENTO_2026:
            raise CommandError(
                'El archivo almacenado no coincide con el checksum oficial.'
            )

        texto_documento = _normalizar_cita(documento.texto_extraido)
        if (
            'REGLAMENTO INTERNO' not in texto_documento.upper()
            or 'VERSIÓN 2026' not in texto_documento.upper()
        ):
            raise CommandError(
                'El texto extraído no confirma el nombre y la versión del reglamento.'
            )
        citas_ausentes = []
        for regla in DISPOSICIONES_REGLAMENTO_2026:
            pagina_pdf = regla['pagina_pdf']
            pagina_fin = regla.get('pagina_pdf_hasta', pagina_pdf)
            if (
                regla['version_fuente'] != VERSION_FUENTE_REGLAMENTO_2026
                or regla['tipo_medida'] == ReglaInstitucional.TipoMedida.NO_CLASIFICADA
                or pagina_pdf > len(paginas_pdf)
                or pagina_fin > len(paginas_pdf)
            ):
                citas_ausentes.append(regla['clave'])
                continue
            texto_pagina = paginas_pdf[pagina_pdf - 1]
            primeras_lineas = [
                linea.strip()
                for linea in texto_pagina.splitlines()
                if linea.strip()
            ][:2]
            texto_pagina_fin = paginas_pdf[pagina_fin - 1]
            primeras_lineas_fin = [
                linea.strip()
                for linea in texto_pagina_fin.splitlines()
                if linea.strip()
            ][:2]
            if (
                str(regla['pagina_impresa']) not in primeras_lineas
                or str(regla.get('pagina_impresa_hasta', regla['pagina_impresa']))
                not in primeras_lineas_fin
                or _clave_cita(regla['evidencia_textual'])
                not in _clave_cita(texto_pagina)
            ):
                citas_ausentes.append(regla['clave'])
        if citas_ausentes:
            raise CommandError(
                'No se verificaron todas las citas en el documento procesado; '
                'no se agregó ninguna regla: ' + ', '.join(citas_ausentes)
            )

        hashes = {
            disposicion['clave']: self._hash_origen(disposicion)
            for disposicion in DISPOSICIONES_REGLAMENTO_2026
        }
        reglas_verificadas = list(
            ReglaInstitucional.objects.filter(
                version__documento=documento,
                hash_origen__in=hashes.values(),
            ).select_related('version')
        )
        versiones_existentes = {
            regla.version_id: regla.version for regla in reglas_verificadas
        }
        if len(versiones_existentes) > 1:
            raise CommandError(
                'Las disposiciones ya existen en varias versiones; no se modificó ninguna.'
            )

        if versiones_existentes:
            version_destino = next(iter(versiones_existentes.values()))
        else:
            version_destino = version
            if version.reglas.exists():
                ultimo_numero = (
                    VersionReglamento.objects.filter(documento=documento)
                    .order_by('-numero')
                    .values_list('numero', flat=True)
                    .first()
                    or 0
                )
                version_destino = VersionReglamento.objects.create(
                    documento=documento,
                    numero=ultimo_numero + 1,
                    creada_por=version.creada_por,
                )

        hashes_existentes = {regla.hash_origen for regla in reglas_verificadas}
        faltan_reglas = set(hashes.values()) - hashes_existentes
        if (
            version_destino.estado != VersionReglamento.Estado.BORRADOR
            and faltan_reglas
        ):
            raise CommandError(
                'La versión que contiene las disposiciones ya no es borrador; '
                'no se modificó.'
            )

        creadas = 0
        omitidas_por_duplicado = 0
        citas_existentes = {
            _normalizar_cita(texto).casefold()
            for texto in version_destino.reglas.values_list('evidencia_textual', flat=True)
        }
        for disposicion in DISPOSICIONES_REGLAMENTO_2026:
            cita_normalizada = _normalizar_cita(
                disposicion['evidencia_textual']
            ).casefold()
            if cita_normalizada in citas_existentes:
                omitidas_por_duplicado += 1
                continue
            datos = {
                key: value
                for key, value in disposicion.items()
                if key not in {'clave'}
            }
            datos.update({
                'version': version_destino,
                'activador': ReglaInstitucional.Activador.MANUAL,
                'solo_presentacion': True,
                'estado': ReglaInstitucional.Estado.PENDIENTE,
                'titulo_fuente': 'Título XVIII',
                'referencia_origen': (
                    f'Título XVIII · p. {disposicion["pagina_impresa"]} '
                    f'(PDF {disposicion["pagina_pdf"]})'
                ),
                'hash_origen': hashes[disposicion['clave']],
            })
            regla, creada = ReglaInstitucional.objects.get_or_create(
                version=version_destino,
                hash_origen=datos['hash_origen'],
                defaults=datos,
            )
            if not creada and (
                regla.evidencia_textual != datos['evidencia_textual']
                or regla.titulo != datos['titulo']
                or regla.seccion_fuente != datos['seccion_fuente']
            ):
                raise CommandError(
                    f'La clave de origen {disposicion["clave"]} ya existe con '
                    'contenido diferente; no se sobrescribió.'
                )
            creadas += int(creada)
            citas_existentes.add(cita_normalizada)

        self.stdout.write(
            self.style.SUCCESS(
                f'Se agregaron {creadas} disposiciones pendientes de revisión; '
                f'{omitidas_por_duplicado} citas ya existían en la versión destino y se dejaron '
                f'intactas. Versión destino: {version_destino.pk}; las coincidencias '
                'idempotentes se conservaron sin cambios.'
            )
        )
