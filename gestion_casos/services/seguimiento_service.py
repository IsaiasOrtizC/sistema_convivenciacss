"""Lógica del seguimiento de casos: arma las filas que se muestran en el panel."""

from ..models import AccionSeguimiento, Caso, Involucran, SeguimientoCaso
from ..trazabilidad import trazar
from .caso_service import identificador_estudiante


@trazar('SERVICE', 'SeguimientoService', 'armando el seguimiento de casos')
def obtener_filas_seguimiento(filtro_estado=''):
    if filtro_estado not in ('', *SeguimientoCaso.Estado.values):
        filtro_estado = ''
    casos = list(
        Caso.objects.select_related('lugar')
        .prefetch_related('estudiantes')
        .order_by('-caso_fecha', '-caso_id')[:100]
    )
    caso_ids = [caso.caso_id for caso in casos]
    estudiante_ids = {
        estudiante.estudiante_id
        for caso in casos
        for estudiante in caso.estudiantes.all()
    }
    seguimientos = SeguimientoCaso.objects.filter(
        caso_id__in=caso_ids,
        estudiante_id__in=estudiante_ids,
    ).prefetch_related('acciones', 'historial')
    seguimiento_por_clave = {
        (item.caso_id, item.estudiante_id): item for item in seguimientos
    }
    categorias = {}
    for relacion in Involucran.objects.filter(caso_id__in=caso_ids).values(
        'caso_id', 'estudiante_id', 'tipo_falta'
    ):
        categorias.setdefault((relacion['caso_id'], relacion['estudiante_id']), set()).add(
            relacion['tipo_falta']
        )

    filas = []
    for caso in casos:
        estudiantes = list(caso.estudiantes.all())
        if not estudiantes:
            estudiantes = [None]
        for estudiante in estudiantes:
            seguimiento = (
                seguimiento_por_clave.get((caso.caso_id, estudiante.estudiante_id))
                if estudiante else None
            )
            estado = seguimiento.estado if seguimiento else SeguimientoCaso.Estado.ABIERTO
            if filtro_estado and estado != filtro_estado:
                continue
            acciones = list(seguimiento.acciones.all()) if seguimiento else []
            filas.append({
                'caso': caso,
                'estudiante_id': (
                    identificador_estudiante(estudiante) if estudiante else 'Sin estudiante asociado'
                ),
                'estudiante_pk': estudiante.estudiante_id if estudiante else None,
                'categoria': ', '.join(sorted(categorias.get(
                    (caso.caso_id, estudiante.estudiante_id), set()
                ))) if estudiante else '',
                'seguimiento': seguimiento,
                'estado': estado,
                'estado_label': (
                    seguimiento.get_estado_display() if seguimiento else 'En seguimiento'
                ),
                'acciones': acciones,
                'avance': (
                    round(
                        sum(a.estado == AccionSeguimiento.Estado.COMPLETADA for a in acciones)
                        * 100 / len(acciones)
                    ) if acciones else None
                ),
            })
    return filas
