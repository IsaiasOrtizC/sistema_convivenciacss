"""Disposiciones seleccionadas manualmente del Reglamento Interno 2026."""

from .models import ReglaInstitucional

PDF_SHA256_REGLAMENTO_2026 = (
    '9e3e308b4471c66d9880124f88c337150572cad508789792b2cae660965cfaf8'
)

REFERENCIAS_TITULOS_2026 = {
    'IX': {
        'titulo': 'RELACIÓN ENTRE LA FAMILIA Y EL ESTABLECIMIENTO',
        'pagina_impresa': 32,
        'pagina_pdf': 33,
    },
    'XVIII': {
        'titulo': 'DE LAS FALTAS, DEBIDO PROCESO, MEDIDAS PEDAGÓGICAS, REPARATORIAS Y SANCIONES',
        'pagina_impresa': 48,
        'pagina_pdf': 49,
        'ultima_pagina_impresa': 57,
        'ultima_pagina_pdf': 58,
    },
    'pagina_impresa_34': {
        'titulo': 'USO DEL UNIFORME Y LA PRESENTACIÓN PERSONAL DE LOS ALUMNOS',
        'pagina_pdf': 35,
        'no_corresponde_a_titulo': 'IX',
    },
}

DISPOSICIONES_REGLAMENTO_2026 = (
    {
        'clave': 'clasificacion-leve',
        'titulo': 'Clasificación de falta leve',
        'categoria_falta': 'Leve',
        'conducta_condicion': (
            'Criterio: acción de responsabilidad individual que quebranta normas del '
            'establecimiento y no afecta a otros miembros de la comunidad educativa. '
            'Conductas enumeradas: molestar a compañeros provocando indisciplina grupal; '
            'no acatar la entrada a clases a la hora correspondiente; salir de clases sin '
            'autorización; usar accesorios no permitidos; usar equipos electrónicos durante '
            'la clase salvo autorización circunstancial; lanzar intencionalmente papeles o '
            'basura de manera reiterada; llamar la atención de trabajadores con gritos o '
            'silbidos; interrumpir clases sin motivo justificado o perturbar su tranquilidad; '
            'no guardar compostura en actos cívicos; usar apodos que menoscaben; no traer la '
            'agenda o arrancarle páginas de manera reiterada; ingerir alimentos o bebidas '
            '(excepto agua) durante clases u otras actividades; vender o comercializar artículos '
            'sin autorización; usar inadecuadamente o incompletamente el uniforme salvo '
            'autorización; no asistir a reforzamientos o apoyos; no contribuir a un clima '
            'propicio para el aprendizaje; ingresar atrasado a clase o actividad; no devolver '
            'objetos encontrados en el establecimiento.'
        ),
        'evidencia_textual': (
            'Acciones de responsabilidad individual que quebrantan normativas del '
            'establecimiento y que no afectan a otros miembros de la comunidad educativa.'
        ),
        'pagina_impresa': 48,
        'pagina_pdf': 49,
        'pagina_impresa_hasta': 52,
        'pagina_pdf_hasta': 53,
        'seccion_fuente': (
            'XVIII, definición a) y 3.A, FALTA LEVE; conductas enumeradas, '
            'páginas impresas 51-52 (PDF 52-53)'
        ),
        'estado_cantidad': ReglaInstitucional.EstadoCantidad.NO_APLICA,
    },
    {
        'clave': 'clasificacion-grave',
        'titulo': 'Clasificación de falta grave',
        'categoria_falta': 'Grave',
        'conducta_condicion': (
            'Criterio: acción individual o colectiva que quebranta normas internas, afecta '
            'a otros miembros de la comunidad educativa y/o deteriora intencionalmente '
            'infraestructura o materiales. Conductas enumeradas: dañar o hacer mal uso '
            'intencional de bienes del Colegio; amenazar, desafiar, provocar, ridiculizar o '
            'descalificar a miembros de la comunidad; emplear lenguaje ofensivo, provocativo '
            'o indecoroso; portar o exhibir elementos cortantes no solicitados que sean '
            'peligrosos; fumar dentro del Colegio o fuera de él portando uniforme; abandonar '
            'el Colegio sin autorización o ausentarse de clases estando dentro; incumplir '
            'compromisos que condicionen permanencia o seguridad; rayar bienes del Colegio, '
            'funcionarios o compañeros; dañar o ensuciar deliberadamente dependencias, '
            'edificio o mobiliario.'
        ),
        'evidencia_textual': (
            'Acciones individuales o colectivas que quebrantan normativas internas del '
            'establecimiento, que afecten a otros miembros de la comunidad educativa y/o '
            'deterioren intencionalmente la infraestructura o materiales del establecimiento.'
        ),
        'pagina_impresa': 48,
        'pagina_pdf': 49,
        'pagina_impresa_hasta': 53,
        'pagina_pdf_hasta': 54,
        'seccion_fuente': (
            'XVIII, definición b) y 3.B, FALTA GRAVE; conductas enumeradas, '
            'páginas impresas 52-53 (PDF 53-54)'
        ),
        'estado_cantidad': ReglaInstitucional.EstadoCantidad.NO_APLICA,
    },
    {
        'clave': 'clasificacion-gravisima',
        'titulo': 'Clasificación de falta gravísima',
        'categoria_falta': 'Gravísima',
        'conducta_condicion': (
            'Criterio: acción individual o colectiva que quebranta normas internas y afecta '
            'directamente la integridad de miembros de la comunidad escolar, o constituye '
            'delito. Conductas enumeradas: cometer hechos constitutivos de delito; sustraer '
            'objetos (robo o hurto); agredir física o escritamente a integrantes de la '
            'comunidad; responder groseramente o usar lenguaje irrespetuoso/gestual hacia '
            'docentes o asistentes; amedrentar, amenazar, chantajear, intimidar, hostigar, '
            'acosar o burlarse; discriminar por las circunstancias enumeradas en el Reglamento; '
            'asistir en estado de intemperancia o manifiesta ingesta de drogas; adulterar, '
            'falsificar, destruir o apoderarse de documentos del establecimiento o usarlos '
            'sin autorización; realizar actos descritos como delitos informáticos o difundir '
            'maltrato por medios cibernéticos; participar en actos pendencieros o agresiones '
            'por identidad u otras circunstancias enumeradas; pertenecer o dirigir grupos '
            'involucrados en actividades reñidas con la moral o que promuevan discriminación; '
            'realizar acoso o ataques de connotación sexual; portar o tener armas descritas '
            'en el Reglamento; traer, reproducir o tramitar material pornográfico; microtráfico, '
            'posesión, tenencia, introducción, comercialización o consumo de drogas bajo la '
            'tuición del Colegio; quemar, destruir o destrozar bienes del establecimiento, '
            'funcionarios o compañeros.'
        ),
        'evidencia_textual': (
            'Acciones individuales o colectivas que quebranten normativas internas del '
            'establecimiento y afectan directamente la integridad de otros miembros de la '
            'comunidad escolar. También aquellas acciones que constituyan delito.'
        ),
        'pagina_impresa': 48,
        'pagina_pdf': 49,
        'pagina_impresa_hasta': 54,
        'pagina_pdf_hasta': 55,
        'seccion_fuente': (
            'XVIII, definición c) y 3.C, FALTA GRAVÍSIMA; conductas enumeradas, '
            'páginas impresas 53-54 (PDF 54-55)'
        ),
        'estado_cantidad': ReglaInstitucional.EstadoCantidad.NO_APLICA,
    },
    {
        'clave': 'leve-anotacion-negativa',
        'titulo': 'Medida inicial para falta leve',
        'categoria_falta': 'Leve',
        'conducta_condicion': 'Falta clasificada como leve conforme al Título XVIII.',
        'evidencia_textual': (
            'SANCIÓN A LA FALTA LEVE: Anotación negativa asentada en el libro de clases, '
            'la cual deberá ser aplicada por el Profesor Jefe, de Asignatura, Inspectoría o Dirección.'
        ),
        'medida_asociada': (
            'Anotación negativa asentada en el libro de clases. Aplicación a cargo de '
            'Profesor Jefe, Profesor de Asignatura, Inspectoría o Dirección.'
        ),
        'pagina_impresa': 52,
        'pagina_pdf': 53,
        'seccion_fuente': 'XVIII, 3.A, SANCIÓN A LA FALTA LEVE',
        'estado_cantidad': ReglaInstitucional.EstadoCantidad.NO_APLICA,
    },
    {
        'clave': 'leve-tres-anotaciones',
        'titulo': 'Tres anotaciones negativas por faltas leves',
        'categoria_falta': 'Leve',
        'conducta_condicion': (
            'Acumulación de anotaciones negativas asociadas a faltas de disciplina leve.'
        ),
        'unidad_umbral': ReglaInstitucional.UnidadUmbral.ANOTACIONES,
        'cantidad_minima': 3,
        'estado_cantidad': ReglaInstitucional.EstadoCantidad.DEFINIDA,
        'medida_asociada': (
            'Conversación del Profesor Jefe con el alumno; registrar la entrevista '
            'y firma en el formato respectivo.'
        ),
        'evidencia_textual': (
            '3 anotaciones: Conversación del Profesor Jefe con el Alumno, quedando '
            'registro y firma de la entrevista en formato respectivo, el cual se '
            'encuentra al interior de la carpeta de entrevistas.'
        ),
        'pagina_impresa': 52,
        'pagina_pdf': 53,
        'seccion_fuente': 'XVIII, 3.A, acumulación de faltas de disciplina leve',
    },
    {
        'clave': 'leve-cinco-anotaciones',
        'titulo': 'Cinco anotaciones negativas por faltas leves',
        'categoria_falta': 'Leve',
        'conducta_condicion': (
            'Acumulación de anotaciones negativas asociadas a faltas de disciplina leve.'
        ),
        'unidad_umbral': ReglaInstitucional.UnidadUmbral.ANOTACIONES,
        'cantidad_minima': 5,
        'estado_cantidad': ReglaInstitucional.EstadoCantidad.DEFINIDA,
        'medida_asociada': (
            'Citación del Profesor Jefe al apoderado en presencia del alumno; '
            'registrar la firma del apoderado en la hoja de vida y los compromisos '
            'del alumno en la carpeta de entrevistas.'
        ),
        'evidencia_textual': (
            '5 anotaciones: Citación del Profesor Jefe al Apoderado en presencia del alumno. '
            'El objetivo de la reunión será poner en conocimiento las anotaciones al apoderado, '
            'registrando su firma en la hoja de vida. Los compromisos del alumno en relación '
            'con el cambio de comportamiento, deberá consignarse en la carpeta de entrevistas.'
        ),
        'pagina_impresa': 52,
        'pagina_pdf': 53,
        'seccion_fuente': 'XVIII, 3.A, acumulación de faltas de disciplina leve',
    },
    {
        'clave': 'grave-suspension',
        'titulo': 'Suspensión por falta grave',
        'categoria_falta': 'Grave',
        'conducta_condicion': (
            'Falta grave, después del debido proceso. La sanción debe ser proporcional '
            'a la edad y gravedad; la graduación considera reiteración, edad y comportamiento general.'
        ),
        'medida_asociada': 'Suspensión temporal de clases.',
        'duracion_minima_dias': 2,
        'duracion_maxima_dias': 3,
        'unidad_duracion': ReglaInstitucional.UnidadDuracion.DIAS,
        'estado_cantidad': ReglaInstitucional.EstadoCantidad.NO_ESPECIFICADA,
        'condiciones': (
            'Cumplir el debido proceso; la sanción es proporcional a la edad de desarrollo '
            'del alumno y al grado de la falta. La graduación considera reiteración, edad y '
            'comportamiento general. Para faltas graves, el proceso no puede superar 10 días '
            'desde el inicio de la investigación; la apelación de esta sanción tiene un plazo '
            'de tres días hábiles desde su notificación.'
        ),
        'evidencia_textual': (
            'Suspensión temporal de clases por dos o tres días.'
        ),
        'pagina_impresa': 53,
        'pagina_pdf': 54,
        'seccion_fuente': 'XVIII, C) PROCEDIMIENTO Y SANCIÓN A FALTA GRAVE',
    },
    {
        'clave': 'gravisima-separacion-preventiva',
        'titulo': 'Separación preventiva ante riesgo de seguridad',
        'categoria_falta': 'Gravísima',
        'conducta_condicion': (
            'Riesgo para la seguridad de los estudiantes involucrados antes de finalizar '
            'el debido proceso y determinar responsabilidades.'
        ),
        'medida_asociada': (
            'Separación preventiva de los estudiantes como medida inmediata de resguardo; '
            'se adopta antes de determinar responsabilidades.'
        ),
        'duracion_minima_dias': 3,
        'duracion_maxima_dias': 5,
        'unidad_duracion': ReglaInstitucional.UnidadDuracion.DIAS,
        'estado_cantidad': ReglaInstitucional.EstadoCantidad.NO_APLICA,
        'condiciones': (
            'Debe existir riesgo para la seguridad de los estudiantes involucrados; '
            'se aplica antes de concluir el debido proceso, para evitar nuevos conflictos '
            'y proteger a los estudiantes. La redacción impresa dice “se adaptará”; el '
            'personal autorizado debe confirmar la interpretación antes de aprobar.'
        ),
        'evidencia_textual': (
            'En aquellos casos en los que se encuentre en riesgo la seguridad de los estudiantes '
            'involucrados y antes de finalizar el debido proceso y determinar responsabilidades '
            'y con ello sanciones disciplinarias y con el objetivo de evitar nuevos conflictos y '
            'principalmente con el objetivo de proteger a los estudiantes involucrados, se adaptará '
            'de forma inmediata como medida de resguardo la separación preventiva de los estudiantes de 3 a 5 días.'
        ),
        'pagina_impresa': 54,
        'pagina_pdf': 55,
        'seccion_fuente': 'XVIII, C) PROCEDIMIENTO Y SANCIÓN A FALTA GRAVÍSIMA',
        'excepciones': (
            'La redacción impresa dice “se adaptará”; el personal autorizado debe validar '
            'la interpretación de esta medida antes de aprobarla.'
        ),
    },
    {
        'clave': 'gravisima-suspension',
        'titulo': 'Suspensión por falta gravísima',
        'categoria_falta': 'Gravísima',
        'conducta_condicion': (
            'Falta gravísima, luego del debido proceso; la sanción se elige según el caso.'
        ),
        'medida_asociada': 'Suspensión de clases.',
        'duracion_minima_dias': 3,
        'duracion_maxima_dias': 5,
        'unidad_duracion': ReglaInstitucional.UnidadDuracion.DIAS,
        'estado_cantidad': ReglaInstitucional.EstadoCantidad.NO_ESPECIFICADA,
        'condiciones': (
            'Cumplir el debido proceso. El plazo de cinco días puede prorrogarse por '
            'cinco días adicionales cuando la gravedad de la falta ponga en riesgo la '
            'seguridad de los integrantes de la comunidad escolar. Para faltas gravísimas, '
            'el proceso no puede superar 15 días desde el inicio de la investigación; la '
            'apelación general tiene un plazo de tres días hábiles. Cancelación de matrícula '
            'y expulsión tienen un plazo de reconsideración de quince días hábiles.'
        ),
        'evidencia_textual': (
            'Suspensión de clases de tres y hasta cinco días. El plazo de cinco días podrá '
            'prorrogarse por cinco días adicionales, cuando la gravedad de la falta ponga en '
            'riesgo la seguridad de los integrantes de la comunidad escolar.'
        ),
        'pagina_impresa': 55,
        'pagina_pdf': 56,
        'seccion_fuente': 'XVIII, C) Sanción ante la Falta Gravísima',
        'excepciones': (
            'Prórroga de cinco días adicionales solo cuando la gravedad de la falta ponga '
            'en riesgo la seguridad de integrantes de la comunidad escolar.'
        ),
    },
    {
        'clave': 'suspension-limite-general',
        'titulo': 'Límite general de suspensión',
        'conducta_condicion': (
            'Regla general sobre duración máxima de suspensión temporal de clases.'
        ),
        'medida_asociada': 'Suspensión temporal de clases.',
        'duracion_maxima_dias': 5,
        'unidad_duracion': ReglaInstitucional.UnidadDuracion.DIAS_HABILES,
        'estado_cantidad': ReglaInstitucional.EstadoCantidad.NO_APLICA,
        'evidencia_textual': (
            'la suspensión no puede aplicarse por periodos que superen los cinco días hábiles, '
            'sin perjuicio que de manera excepcional se pueda prorrogar una vez por igual periodo'
        ),
        'pagina_impresa': 50,
        'pagina_pdf': 51,
        'seccion_fuente': 'XVIII, 1.3.b, Suspensión temporal de clases',
        'excepciones': (
            'El reglamento permite, de manera excepcional, una prórroga única por igual '
            'periodo. La relación entre este límite general y la regla específica para faltas '
            'gravísimas requiere revisión humana.'
        ),
    },
    {
        'clave': 'condicionalidad-reiteracion',
        'titulo': 'Condicionalidad por faltas reiteradas',
        'conducta_condicion': (
            'Faltas reiteradas durante un semestre con comportamiento persistente y sin '
            'cambios pese a las estrategias institucionales.'
        ),
        'estado_cantidad': ReglaInstitucional.EstadoCantidad.NO_ESPECIFICADA,
        'medida_asociada': 'Condicionalidad de matrícula.',
        'condiciones': (
            'La aplicación es decisión exclusiva del Director y requiere debido proceso; '
            'el reglamento indica que debe revisarse al final de cada semestre. El proceso '
            'para faltas leves no puede superar tres días hábiles desde su inicio.'
        ),
        'evidencia_textual': (
            'Alumno que cometa faltas reiteradas durante el periodo de un Semestre: '
            'Entendiéndose como un comportamiento persistente sin evidenciar cambios en el alumno, '
            'a pesar de las estrategias abordadas por las entidades pertinentes dentro de nuestra Institución'
        ),
        'pagina_impresa': 55,
        'pagina_pdf': 56,
        'seccion_fuente': 'XVIII, 3.1.a, SITUACIONES QUE AMERITAN LA CONDICIONALIDAD DE MATRÍCULA',
        'excepciones': (
            'No se define cuántas faltas o anotaciones constituyen “reiteradas”; no convertir '
            'el término en un umbral numérico.'
        ),
    },
    {
        'clave': 'cancelacion-matricula-riesgo',
        'titulo': 'Cancelación de matrícula por riesgo a la integridad',
        'conducta_condicion': (
            'Conducta que, justificadamente, se considere que pone en riesgo la integridad '
            'física y/o psíquica de un miembro de la comunidad educativa.'
        ),
        'estado_cantidad': ReglaInstitucional.EstadoCantidad.NO_ESPECIFICADA,
        'medida_asociada': 'Cancelación de matrícula para el año escolar siguiente.',
        'condiciones': (
            'Requiere debido proceso. La decisión corresponde al Director, con notificación '
            'escrita y posibilidad de reconsideración dentro de quince días hábiles, previa '
            'consulta al Consejo de Profesores.'
        ),
        'evidencia_textual': (
            'Dicha Sanción sólo se podrá aplicar, tras haber cumplido con un debido proceso '
            'de acuerdo con lo descrito en el presente Manual y en casos que justificadamente se '
            'considere que la conducta realizada por el estudiante pone en riesgo la integridad '
            'física y/o psíquica de algún miembro de la comunidad educativa.'
        ),
        'pagina_impresa': 50,
        'pagina_pdf': 51,
        'seccion_fuente': 'XVIII, 1.3.d, Cancelación de Matrícula',
        'excepciones': (
            'No se indica un mínimo de faltas, anotaciones ni reincidencias; la medida no se '
            'deduce automáticamente del número de eventos.'
        ),
    },
    {
        'clave': 'expulsion-riesgo',
        'titulo': 'Expulsión por riesgo a la integridad',
        'conducta_condicion': (
            'Conducta que, justificadamente, se considere que pone en riesgo la integridad '
            'física y/o psíquica de un miembro de la comunidad educativa.'
        ),
        'estado_cantidad': ReglaInstitucional.EstadoCantidad.NO_ESPECIFICADA,
        'medida_asociada': 'Expulsión; cancelación inmediata de la matrícula.',
        'condiciones': (
            'Requiere debido proceso. La decisión corresponde al Director, con notificación '
            'escrita y posibilidad de reconsideración dentro de quince días hábiles, previa '
            'consulta al Consejo de Profesores.'
        ),
        'evidencia_textual': (
            'Esta sanción sólo será aplicada tras haber cumplido los pasos del debido proceso '
            'descritos en este manual y en casos que justificadamente se considere que esté en '
            'riesgo la integridad física y/o psíquica de algún miembro de la comunidad educativa.'
        ),
        'pagina_impresa': 51,
        'pagina_pdf': 52,
        'seccion_fuente': 'XVIII, 1.3.e, Expulsión',
        'excepciones': (
            'No se indica un mínimo de faltas, anotaciones ni reincidencias; la medida no se '
            'deduce automáticamente del número de eventos.'
        ),
    },
)

VERSION_FUENTE_REGLAMENTO_2026 = 'Reglamento Interno 2026'
_TIPOS_MEDIDA_REGLAMENTO_2026 = {
    'clasificacion-leve': ReglaInstitucional.TipoMedida.CLASIFICACION,
    'clasificacion-grave': ReglaInstitucional.TipoMedida.CLASIFICACION,
    'clasificacion-gravisima': ReglaInstitucional.TipoMedida.CLASIFICACION,
    'leve-anotacion-negativa': ReglaInstitucional.TipoMedida.SANCION_DISCIPLINARIA,
    'leve-tres-anotaciones': ReglaInstitucional.TipoMedida.SANCION_DISCIPLINARIA,
    'leve-cinco-anotaciones': ReglaInstitucional.TipoMedida.SANCION_DISCIPLINARIA,
    'grave-suspension': ReglaInstitucional.TipoMedida.SANCION_DISCIPLINARIA,
    'gravisima-separacion-preventiva': ReglaInstitucional.TipoMedida.PREVENTIVA,
    'gravisima-suspension': ReglaInstitucional.TipoMedida.SANCION_DISCIPLINARIA,
    'suspension-limite-general': ReglaInstitucional.TipoMedida.SANCION_DISCIPLINARIA,
    'condicionalidad-reiteracion': ReglaInstitucional.TipoMedida.SANCION_DISCIPLINARIA,
    'cancelacion-matricula-riesgo': ReglaInstitucional.TipoMedida.SANCION_DISCIPLINARIA,
    'expulsion-riesgo': ReglaInstitucional.TipoMedida.SANCION_DISCIPLINARIA,
}
DISPOSICIONES_REGLAMENTO_2026 = tuple(
    {
        **disposicion,
        'tipo_medida': _TIPOS_MEDIDA_REGLAMENTO_2026[disposicion['clave']],
        'version_fuente': VERSION_FUENTE_REGLAMENTO_2026,
    }
    for disposicion in DISPOSICIONES_REGLAMENTO_2026
)
