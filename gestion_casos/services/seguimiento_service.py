"""Lógica del seguimiento de casos: arma las filas que se muestran en el panel."""

from ..models import AccionSeguimiento, Caso, Involucran, SeguimientoCaso
from ..trazabilidad import trazar
from .caso_service import identificador_estudiante


@trazar('SERVICE', 'SeguimientoService', 'armando el seguimiento de casos')
def obtener_filas_seguimiento(filtro_estado='', cursos_ids=None):
    """Construye las filas de seguimiento de casos.

    Si se pasa `cursos_ids` (por ejemplo, para un Profesor Jefe), filtra
    directamente en la base de datos los casos y estudiantes de esos cursos.
    """
    if filtro_estado not in ('', *SeguimientoCaso.Estado.values):
        filtro_estado = ''

    casos_qs = Caso.objects.select_related('lugar').prefetch_related('estudiantes__curso')
    if cursos_ids is not None:
        cursos_lista = list(cursos_ids)
        if not cursos_lista:
            return []
        casos_qs = casos_qs.filter(estudiantes__curso_id__in=cursos_lista).distinct()

    casos = list(casos_qs.order_by('-caso_fecha', '-caso_id')[:100])
    if not casos:
        return []

    caso_ids = [caso.caso_id for caso in casos]
    cursos_permitidos = set(cursos_ids) if cursos_ids is not None else None

    estudiante_ids = set()
    for caso in casos:
        for estudiante in caso.estudiantes.all():
            if cursos_permitidos is None or estudiante.curso_id in cursos_permitidos:
                estudiante_ids.add(estudiante.estudiante_id)

    seguimiento_por_clave = {}
    if estudiante_ids:
        seguimientos = (
            SeguimientoCaso.objects
            .filter(
                caso_id__in=caso_ids,
                estudiante_id__in=estudiante_ids,
            )
            .prefetch_related('acciones', 'historial')
        )
        seguimiento_por_clave = {
            (item.caso_id, item.estudiante_id): item
            for item in seguimientos
        }

    categorias = {}
    for relacion in Involucran.objects.filter(caso_id__in=caso_ids).values(
        'caso_id', 'estudiante_id', 'tipo_falta'
    ):
        categorias.setdefault(
            (relacion['caso_id'], relacion['estudiante_id']),
            set(),
        ).add(relacion['tipo_falta'])

    filas = []
    for caso in casos:
        estudiantes = list(caso.estudiantes.all())
        if cursos_permitidos is not None:
            estudiantes = [
                est for est in estudiantes
                if est.curso_id in cursos_permitidos
            ]
        elif not estudiantes:
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
            completadas = sum(
                1 for a in acciones
                if a.estado == AccionSeguimiento.Estado.COMPLETADA
            )
            avance = round((completadas * 100) / len(acciones)) if acciones else None

            filas.append({
                'caso': caso,
                'caso_id': caso.caso_id,
                'estudiante_id': (
                    identificador_estudiante(estudiante)
                    if estudiante else 'Sin estudiante asociado'
                ),
                'estudiante_pk': estudiante.estudiante_id if estudiante else None,
                'categoria': (
                    ', '.join(sorted(categorias.get(
                        (caso.caso_id, estudiante.estudiante_id), set()
                    )))
                    if estudiante else ''
                ),
                'seguimiento': seguimiento,
                'estado': estado,
                'estado_label': (
                    seguimiento.get_estado_display()
                    if seguimiento else 'En seguimiento'
                ),
                'acciones': acciones,
                'avance': avance,
            })

    return filas