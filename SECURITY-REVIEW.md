# Revisión de seguridad

**Fecha:** 2026-11-05

**Alcance:** revisión estática enfocada en autorización y exposición de datos
sensibles de convivencia escolar. No se realizaron cambios de código como parte
de esta revisión.

## Hallazgos

### HIGH — Exposición entre cursos en casos con estudiantes de varios cursos

**Confianza:** 9/10

El acceso de Profesor Jefe a un caso se concede si al menos un estudiante
involucrado pertenece a su curso. Después de esa comprobación, el detalle del
caso devuelve los datos de todos los estudiantes involucrados, incluidos
estudiantes de otros cursos. La misma validación permite exportar el caso. En el
historial de curso, los casos se filtran por curso, pero la lista de participantes
se obtiene sin restringirla al curso del profesor.

Esto puede exponer nombres, cursos y clasificaciones de convivencia de
estudiantes ajenos al curso asignado al profesor.

**Ubicaciones revisadas:**

- `gestion_casos/api.py`, líneas 453, 463, 475 y 494
- `gestion_casos/migration_api.py`, líneas 217 y 228
- `gestion_casos/services/caso_service.py`, líneas 196, 213 y 224

**Recomendación:** aplicar el alcance del curso también a los participantes
devueltos, al detalle y a los archivos exportados. Para casos compartidos,
denegar el acceso del Profesor Jefe o generar una vista/exportación que oculte
los estudiantes de otros cursos. Añadir pruebas que cubran casos con estudiantes
de cursos diferentes y verifiquen que no se filtran sus datos por detalle,
historial ni exportaciones.

## Resultado

Se identificó un hallazgo HIGH que requiere corrección antes de considerar
completo el aislamiento de datos entre cursos. Esta revisión estática no
certifica la ausencia de otras vulnerabilidades ni sustituye pruebas de
penetración, revisión de configuración de despliegue o auditoría de permisos en
producción.
