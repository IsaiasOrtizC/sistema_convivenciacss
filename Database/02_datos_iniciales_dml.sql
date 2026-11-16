--
-- PostgreSQL database dump
--

\restrict ihP8hHzXfbbLZmnQ7BswkFJKNAnGUUikzNRqA8FfS58Zrqb2x1GaOwiiZ4UNZlm

-- Dumped from database version 17.6
-- Dumped by pg_dump version 18.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: lugar; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.lugar (lugar_id, lugar_nombre, lugar_descripcion) VALUES (1, 'Patio central', 'Espacio abierto principal del establecimiento');
INSERT INTO public.lugar (lugar_id, lugar_nombre, lugar_descripcion) VALUES (2, 'Sala 10', 'Sala de clases primer piso ala norte');
INSERT INTO public.lugar (lugar_id, lugar_nombre, lugar_descripcion) VALUES (3, 'Baños 2° piso', 'Baños del segundo piso');
INSERT INTO public.lugar (lugar_id, lugar_nombre, lugar_descripcion) VALUES (4, 'Gimnasio', 'Recinto deportivo techado');
INSERT INTO public.lugar (lugar_id, lugar_nombre, lugar_descripcion) VALUES (5, 'Comedor', 'Espacio de alimentación');


--
-- Data for Name: rol; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.rol (rol_id, rol_nombre, rol_descripcion) VALUES (1, 'Administrador', 'Acceso total al sistema');
INSERT INTO public.rol (rol_id, rol_nombre, rol_descripcion) VALUES (2, 'Inspector', 'Registro y seguimiento de casos');
INSERT INTO public.rol (rol_id, rol_nombre, rol_descripcion) VALUES (3, 'Profesor Jefe', 'Visualiza casos de su curso');
INSERT INTO public.rol (rol_id, rol_nombre, rol_descripcion) VALUES (4, 'PConvivencia', 'Gestión del plan de convivencia');


--
-- Data for Name: usuario; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.usuario (usuario_id, usuario_nombre, usuario_apaterno, usuario_amaterno, usuario_correo, rol_id, usuario_contrasena, usuario_ultimo_acceso, usuario_primer_ingreso, usuario_activo, usuario_intentos_fallidos, usuario_bloqueado) VALUES (13, 'Jorge', 'Contreras', 'Espinoza', 'jorge.contreras@colegio.cl', 3, 'Profesor01', NULL, true, true, 0, false);
INSERT INTO public.usuario (usuario_id, usuario_nombre, usuario_apaterno, usuario_amaterno, usuario_correo, rol_id, usuario_contrasena, usuario_ultimo_acceso, usuario_primer_ingreso, usuario_activo, usuario_intentos_fallidos, usuario_bloqueado) VALUES (15, 'Sebastián', 'Navarro', 'Orellana', 'sebastian.navarro@colegio.cl', 2, 'Inspector02', '2026-06-14 22:54:20.738839+00', true, true, 0, false);
INSERT INTO public.usuario (usuario_id, usuario_nombre, usuario_apaterno, usuario_amaterno, usuario_correo, rol_id, usuario_contrasena, usuario_ultimo_acceso, usuario_primer_ingreso, usuario_activo, usuario_intentos_fallidos, usuario_bloqueado) VALUES (18, 'Maria', 'Soto', 'Peralta', 'maria.sotoperalta@colegio.cl', 2, 'temporal2', NULL, true, true, 0, false);
INSERT INTO public.usuario (usuario_id, usuario_nombre, usuario_apaterno, usuario_amaterno, usuario_correo, rol_id, usuario_contrasena, usuario_ultimo_acceso, usuario_primer_ingreso, usuario_activo, usuario_intentos_fallidos, usuario_bloqueado) VALUES (12, 'Pamela', 'Ibáñez', 'Salinas', 'pamela.ibanez@colegio.cl', 2, 'Inspector01', '2026-06-15 00:34:52.348762+00', true, true, 0, false);
INSERT INTO public.usuario (usuario_id, usuario_nombre, usuario_apaterno, usuario_amaterno, usuario_correo, rol_id, usuario_contrasena, usuario_ultimo_acceso, usuario_primer_ingreso, usuario_activo, usuario_intentos_fallidos, usuario_bloqueado) VALUES (21, 'Isaias', 'Abel', 'Ortiz', 'i.ortizcastro@uandresbello.edu', 1, '1234', NULL, true, true, 0, false);
INSERT INTO public.usuario (usuario_id, usuario_nombre, usuario_apaterno, usuario_amaterno, usuario_correo, rol_id, usuario_contrasena, usuario_ultimo_acceso, usuario_primer_ingreso, usuario_activo, usuario_intentos_fallidos, usuario_bloqueado) VALUES (22, 'Sheldon', 'Cooper', 'L', 'sheldon@gmail.com', 3, '1234', '2026-09-11 10:07:50.605907+00', true, true, 0, false);
INSERT INTO public.usuario (usuario_id, usuario_nombre, usuario_apaterno, usuario_amaterno, usuario_correo, rol_id, usuario_contrasena, usuario_ultimo_acceso, usuario_primer_ingreso, usuario_activo, usuario_intentos_fallidos, usuario_bloqueado) VALUES (34, 'Pedro', 'González', 'Pérez', 'prueba@colegio.com', 3, 'pbkdf2_sha256$1000000$yG7rkGsPkKN5CL4e5aYtBP$erZTZ29qyyXVBg0LgTvUfFZq37qosbrFVcet3zAt5yc=', NULL, false, true, 0, false);
INSERT INTO public.usuario (usuario_id, usuario_nombre, usuario_apaterno, usuario_amaterno, usuario_correo, rol_id, usuario_contrasena, usuario_ultimo_acceso, usuario_primer_ingreso, usuario_activo, usuario_intentos_fallidos, usuario_bloqueado) VALUES (19, 'Isaías', 'Ortiz', 'Castro', 'i.ortizcastro@icloud.com', 1, 'pbkdf2_sha256$1000000$BLACuN5UFG2IZza3bBQh6R$OuPAqpR0qlp+UZ9wA0qpBg/2/VNkhrQjLLwkO8aSPnk=', '2026-11-14 03:25:05.205391+00', false, true, 0, false);
INSERT INTO public.usuario (usuario_id, usuario_nombre, usuario_apaterno, usuario_amaterno, usuario_correo, rol_id, usuario_contrasena, usuario_ultimo_acceso, usuario_primer_ingreso, usuario_activo, usuario_intentos_fallidos, usuario_bloqueado) VALUES (28, 'Osvaldo', 'Caraccioli', 'Cisterna', 'oocaraccioli@gmail.com', 2, 'pbkdf2_sha256$1000000$eXMOVr3sy3lTb8UGKrVed1$DVjz7auc9R7kCpSc/7kM4f/15nZaenJho+S+bLC9LxA=', '2026-11-16 00:59:45.763978+00', false, true, 0, false);
INSERT INTO public.usuario (usuario_id, usuario_nombre, usuario_apaterno, usuario_amaterno, usuario_correo, rol_id, usuario_contrasena, usuario_ultimo_acceso, usuario_primer_ingreso, usuario_activo, usuario_intentos_fallidos, usuario_bloqueado) VALUES (26, 'Juan', 'Pérez', 'González', 'juan@gmail.com', 1, 'pbkdf2_sha256$1000000$byu0c7UbO6ehYhhTiBxFcz$yGAXUkc7fyr0r6dPku7wLvmgKx6lM4A1PaRBnVBbSgg=', '2026-09-30 12:37:25.356762+00', false, true, 0, false);
INSERT INTO public.usuario (usuario_id, usuario_nombre, usuario_apaterno, usuario_amaterno, usuario_correo, rol_id, usuario_contrasena, usuario_ultimo_acceso, usuario_primer_ingreso, usuario_activo, usuario_intentos_fallidos, usuario_bloqueado) VALUES (16, 'Rodrigo', 'Flores', 'Prueba1', 'rodrgo.jr2003@gmail.com', 4, 'pbkdf2_sha256$1000000$9qxJlRnOEXIr2gadWUdZUX$M55/ZstmoSTLhRgOAtUe1JaICcZIm4wTQfOYNqFFDUg=', '2026-06-15 00:36:05.878411+00', true, true, 1, false);
INSERT INTO public.usuario (usuario_id, usuario_nombre, usuario_apaterno, usuario_amaterno, usuario_correo, rol_id, usuario_contrasena, usuario_ultimo_acceso, usuario_primer_ingreso, usuario_activo, usuario_intentos_fallidos, usuario_bloqueado) VALUES (17, 'Carlos', 'Frias', 'Peralta', 'carlos.friasperalta@colegio.cl', 1, 'temporal2', NULL, true, true, 0, false);
INSERT INTO public.usuario (usuario_id, usuario_nombre, usuario_apaterno, usuario_amaterno, usuario_correo, rol_id, usuario_contrasena, usuario_ultimo_acceso, usuario_primer_ingreso, usuario_activo, usuario_intentos_fallidos, usuario_bloqueado) VALUES (25, 'Osvaldo', 'Caraccioli', 'Cisterna', 'o.caracciolicisterna@uandresbello.edu', 1, 'pbkdf2_sha256$1000000$gUCHy0hv5Xh7h3JRcoAwc3$kmLSF45ln2APYN1oriy0ekYtQlWQdUv0SGlnFSaa4BY=', '2026-11-16 01:59:01.019944+00', false, true, 0, false);
INSERT INTO public.usuario (usuario_id, usuario_nombre, usuario_apaterno, usuario_amaterno, usuario_correo, rol_id, usuario_contrasena, usuario_ultimo_acceso, usuario_primer_ingreso, usuario_activo, usuario_intentos_fallidos, usuario_bloqueado) VALUES (38, 'Felipe', 'Trujillo', 'Lopez', 'felipe.trujillo@sansebastianmelipilla.cl', 1, 'pbkdf2_sha256$1000000$2KXaKHPV7jq3Ms5pVn8044$e5k1a91O0Xub9A18G1um/+5p8+siHsaw/gwu4pbKD9g=', '2026-11-15 12:51:46.072227+00', false, true, 1, false);
INSERT INTO public.usuario (usuario_id, usuario_nombre, usuario_apaterno, usuario_amaterno, usuario_correo, rol_id, usuario_contrasena, usuario_ultimo_acceso, usuario_primer_ingreso, usuario_activo, usuario_intentos_fallidos, usuario_bloqueado) VALUES (37, 'Isaias', 'Ortiz', 'Inspector', 'isa@gmail.com', 2, 'pbkdf2_sha256$1000000$KzY2He9G60nNb8MOfAPXsI$23vYDW39KmlGxde2SYS+pKK3hbbrke2BJRr/Ld6CuPI=', '2026-10-14 16:45:34.063568+00', false, true, 0, false);
INSERT INTO public.usuario (usuario_id, usuario_nombre, usuario_apaterno, usuario_amaterno, usuario_correo, rol_id, usuario_contrasena, usuario_ultimo_acceso, usuario_primer_ingreso, usuario_activo, usuario_intentos_fallidos, usuario_bloqueado) VALUES (14, 'Daniela', 'Vergara', 'Palma', 'daniela.vergara@colegio.cl', 4, 'Convivencia1', NULL, true, true, 1, false);
INSERT INTO public.usuario (usuario_id, usuario_nombre, usuario_apaterno, usuario_amaterno, usuario_correo, rol_id, usuario_contrasena, usuario_ultimo_acceso, usuario_primer_ingreso, usuario_activo, usuario_intentos_fallidos, usuario_bloqueado) VALUES (11, 'Rodrigo', 'Flores', 'Admin', 'rodrgo.flores2003@gmail.com', 1, '12345', '2026-09-01 05:29:36.159967+00', true, true, 2, false);
INSERT INTO public.usuario (usuario_id, usuario_nombre, usuario_apaterno, usuario_amaterno, usuario_correo, rol_id, usuario_contrasena, usuario_ultimo_acceso, usuario_primer_ingreso, usuario_activo, usuario_intentos_fallidos, usuario_bloqueado) VALUES (23, 'Matias', 'Ibarra', '', 'matstreaming0752@gmail.com', 1, 'pbkdf2_sha256$1000000$RKpHsPZC5C3eG5GSVQMUw0$H2KVLdf/QhG/+GKw2xsnjUDychMbD638tgex68jOTa8=', '2026-11-15 07:40:21.890916+00', false, true, 0, false);
INSERT INTO public.usuario (usuario_id, usuario_nombre, usuario_apaterno, usuario_amaterno, usuario_correo, rol_id, usuario_contrasena, usuario_ultimo_acceso, usuario_primer_ingreso, usuario_activo, usuario_intentos_fallidos, usuario_bloqueado) VALUES (39, 'Benjamin', 'Orellana', 'Orellana', 'minicarlosganador@gmail.com', 2, 'pbkdf2_sha256$1000000$t7ls3HKwliTxbF9K3F0RYF$E37vm9I2uPHoFKlUzOee7H5jIpuxTjozsB+FqHtyhUM=', NULL, true, true, 0, false);
INSERT INTO public.usuario (usuario_id, usuario_nombre, usuario_apaterno, usuario_amaterno, usuario_correo, rol_id, usuario_contrasena, usuario_ultimo_acceso, usuario_primer_ingreso, usuario_activo, usuario_intentos_fallidos, usuario_bloqueado) VALUES (36, 'Pedro', 'González', 'Pérez', 'prueba.profesorjefe@colegio.com', 3, 'pbkdf2_sha256$1000000$46oZHAyF3TTyRMB3R7djK2$/8tdMcUN70C4tp4ubZPZ7rDykpNUSsyZAseiGZ5wdT4=', '2026-11-16 00:49:07.865188+00', false, true, 0, false);


--
-- Data for Name: caso; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (4, '2026-06-12', '[Alumno es sorprendido fumando] - alumno es sorprendido fumando en el comedor', NULL, 11, 5, '2026-09-01 05:31:59.505778+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (5, '2026-06-12', '[Alumno responde de forma violenta en el patio] - alumno responde de forma violenta durante el recreo', NULL, 11, 1, '2026-09-01 05:31:59.505778+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (6, '2026-06-12', '[Alumno raya pared] - alumno es sorprendido rayando paredes de baño', NULL, 11, 3, '2026-09-01 05:31:59.505778+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (7, '2026-06-12', '[caso prueba 5] - caso de prueba, caso de prueba, caso de prueba', NULL, 11, 5, '2026-09-01 05:31:59.505778+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (9, '2026-06-12', '[Alumno agrede a su compañero] - El alumno le da una cachetada mientras jugaban ', NULL, 11, 5, '2026-09-01 05:31:59.505778+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (22, '2026-06-14', '[caso de prueba 19] - caso de prueba 19 ahora comedor', NULL, 11, 5, '2026-09-01 05:31:59.505778+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (23, '2026-06-14', '[caso prueba 20] - Caso prueba 20 para video', NULL, 11, 4, '2026-09-01 05:31:59.505778+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (25, '2026-06-14', '[Caso prueba notificaciones] - caso prueba notificacion', NULL, 11, 2, '2026-09-01 05:31:59.505778+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (26, '2026-06-14', '[caso prueba 22] - caso prueba acciones', NULL, 12, 5, '2026-09-01 05:31:59.505778+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (30, '2026-09-24', '[Agresion Verbal al Docente] - La estudiante se coloca de pie en medio de la clase y le dice al profesor "Yo no necesito esta clase porque yo soy ficha, manejo cualquier monea si quiero le pago el sueldo"', NULL, 23, 2, '2026-09-24 20:27:48.541081+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (31, '2026-09-30', '[Copia] - fdfdf', NULL, 23, 2, '2026-09-30 12:41:46.781769+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (33, '2026-06-15', '[alumno se salta la clase ] - estudiante es sorprendida saltandose la clase de educacion fisica para comer un combo de pollo KFC ', NULL, 23, 4, '2026-10-03 20:39:16.030226+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (36, '2026-10-03', '[caso patio central ] - alumno golpea  a su compañero tras perder en un partido de ping-pong ', NULL, 23, 1, '2026-10-03 20:52:58.612939+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (37, '2026-10-03', '[retraso ] - estudiante llega tarde a clases de forma reiterada  ', NULL, 23, 2, '2026-10-03 20:53:55.40853+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (38, '2026-10-03', '[falta de respeto  ] - alumno se queda dormido en clase  ', NULL, 23, 2, '2026-10-03 20:54:49.056551+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (39, '2026-10-03', '[caso10] - as', NULL, 23, 3, '2026-10-03 20:57:26.364288+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (40, '2026-10-03', '[caso 11 ] - as', NULL, 23, 5, '2026-10-03 20:58:19.535227+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (41, '2026-10-03', '[caso11 ] - as', NULL, 23, 4, '2026-10-03 20:58:54.009103+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (42, '2026-10-03', '[caso 13 ] - as', NULL, 23, 1, '2026-10-03 21:00:09.718719+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (43, '2026-10-03', '[caso 67] - as', NULL, 23, 1, '2026-10-03 21:00:59.358998+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (28, '2026-09-01', '[Batalla de aura] - comportamiento inapropiado ', NULL, 19, 1, '2026-09-01 20:45:10.489117+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (34, '2026-10-03', '[alumno insulta a su compañera] - alumno le dice a su compañera deja de comer tanto o terminaras como su compañero Vicente', NULL, 23, 5, '2026-10-03 20:49:04.627598+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (44, '2026-10-03', '[caso 69] - estudiante ', NULL, 23, 3, '2026-10-03 21:02:10.218542+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (45, '2026-10-04', '[caso prueba 20] - s', NULL, 23, 3, '2026-10-04 04:03:19.585658+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (46, '2026-10-04', '[caso 21 ] - as', NULL, 23, 5, '2026-10-04 04:04:03.201164+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (47, '2026-10-04', '[caso prueba  22] - mj', NULL, 23, 4, '2026-10-04 04:05:13.753609+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (49, '2026-10-04', '[caso 24 ] - as', NULL, 23, 4, '2026-10-04 04:06:52.460616+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (50, '2026-10-04', '[caso 25 ] - qw', NULL, 23, 1, '2026-10-04 04:07:27.065358+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (51, '2026-10-04', '[caso 26] - as', NULL, 23, 3, '2026-10-04 04:08:13.953229+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (52, '2026-10-04', '[caso 27] - a', NULL, 23, 2, '2026-10-04 04:09:06.844685+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (53, '2026-10-04', '[caso 28] - ty', NULL, 23, 3, '2026-10-04 04:09:45.11613+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (54, '2026-10-04', '[caso 29] - as', NULL, 23, 1, '2026-10-04 04:10:33.962456+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (55, '2026-10-04', '[caso 30] - a', NULL, 23, 3, '2026-10-04 04:11:17.890976+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (56, '2026-10-04', '[caso 31] - s', NULL, 23, 3, '2026-10-04 04:12:07.043006+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (48, '2026-10-04', '[caso 23] - as', NULL, 23, 1, '2026-10-04 04:05:53.922265+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (57, '2026-10-04', '[caso 32e] - e', NULL, 23, 3, '2026-10-04 05:02:46.490567+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (35, '2026-10-03', '[caso prueba  8] - alumno amenaza que  hara una cumeada en el baño', NULL, 23, 5, '2026-10-03 20:51:28.192786+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (59, '0033-04-03', '[judas vende a jesus] - matias traciona a jesus por unas monedas de plata', '', 36, 1, '2026-10-13 21:01:19.38319+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (58, '2026-10-05', '[Caso Isa] - asdadasassdfdfrgtyokujxc', NULL, 19, 3, '2026-10-05 15:55:59.556174+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (60, '2026-10-14', '[caso prueba isa12] - vxcf', NULL, 19, 3, '2026-10-14 16:42:16.375314+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (61, '2026-10-14', '[caso inspector] - casisuns', NULL, 37, 5, '2026-10-14 16:46:27.716754+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (62, '2026-10-15', '[Caso Controladores] - lol', NULL, 19, 5, '2026-10-15 15:04:25.888345+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (63, '2026-10-16', '[Caso Contoladores + Consola] - lala', NULL, 19, 1, '2026-10-16 12:12:48.21236+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (64, '2026-10-16', '[caso terminal1 ] - loooo', NULL, 19, 5, '2026-10-16 19:05:17.543171+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (70, '2026-10-27', '[CASO GRAVE] - mmmmm', NULL, 19, 5, '2026-10-28 01:02:04.688863+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (71, '2026-10-27', '[CASO GRAVISIMO] - LOLOLOLO', NULL, 19, 4, '2026-10-28 01:06:50.982204+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (72, '2026-10-27', '[Caso correo] - aaa', NULL, 19, 3, '2026-10-28 01:11:48.08201+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (73, '2026-10-27', '[Caso gravisimo correo] - gggg', NULL, 19, 2, '2026-10-28 01:15:53.069386+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (74, '2026-11-02', '[Pelea en los baños] - Alumno toquetea a su compañero en el baño por la espalda', NULL, 23, 3, '2026-11-07 00:49:32.829457+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (75, '2026-11-12', '[pelea] - a', NULL, 28, 3, '2026-11-14 03:02:44.043378+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (76, '2026-11-06', '[l] - ,', NULL, 28, 3, '2026-11-14 03:04:30.486135+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (77, '2026-11-08', '[insulta a su profesor] - insulta a su profesor en clase y le dice pelao ctm', '', 36, 2, '2026-11-14 03:25:41.01951+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (78, '2026-11-13', '[pelea 1] - 1', NULL, 25, 3, '2026-11-14 20:14:49.419724+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (79, '2026-11-13', '[pelea 2] - 2', NULL, 25, 3, '2026-11-14 20:20:49.369503+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (80, '2026-11-14', '[pelea 3] - 3', NULL, 25, 3, '2026-11-14 20:24:03.279473+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (81, '2026-11-14', '[pelea 4] - q', NULL, 25, 3, '2026-11-14 20:31:05.838917+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (82, '2026-11-12', '[pelea 5] - 1', NULL, 25, 3, '2026-11-14 20:31:35.354229+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (84, '2026-11-14', '[pelea 6] - 1', NULL, 25, 4, '2026-11-14 20:34:40.89267+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (85, '2026-11-14', '[pelea 7] - 2', NULL, 25, 4, '2026-11-14 20:35:28.236391+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (86, '2026-11-14', '[pelea 9] - 2', NULL, 25, 1, '2026-11-14 20:36:53.954033+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (87, '2026-11-14', '[pelea 10] - 3', NULL, 25, 4, '2026-11-14 20:37:25.420689+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (88, '2026-11-14', '[pelea 11] - le pega a su compañero Matias Urria y dice soy el rey del mundo', NULL, 25, 3, '2026-11-14 20:39:14.014206+00');
INSERT INTO public.caso (caso_id, caso_fecha, caso_descripcion, evidencia, usuario_id, lugar_id, caso_creado_en) VALUES (65, '2026-10-19', '[Pelea inter cursos] - Matias', 'media/evidencias/invincible-mark-in-new-suit-custom-cursor_1_qnmv1u', 19, 1, '2026-10-19 22:42:28.798825+00');


--
-- Data for Name: curso; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.curso (curso_id, curso_grado, curso_letra) VALUES (1, '1° Medio', 'A');
INSERT INTO public.curso (curso_id, curso_grado, curso_letra) VALUES (2, '1° Medio', 'B');
INSERT INTO public.curso (curso_id, curso_grado, curso_letra) VALUES (3, '2° Medio', 'A');
INSERT INTO public.curso (curso_id, curso_grado, curso_letra) VALUES (4, '3° Medio', 'B');
INSERT INTO public.curso (curso_id, curso_grado, curso_letra) VALUES (6, '2° Medio', 'B');
INSERT INTO public.curso (curso_id, curso_grado, curso_letra) VALUES (7, '3° Medio', 'A');
INSERT INTO public.curso (curso_id, curso_grado, curso_letra) VALUES (8, '4° Medio', 'A');
INSERT INTO public.curso (curso_id, curso_grado, curso_letra) VALUES (9, '4° Medio', 'B');


--
-- Data for Name: documento_institucional; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.documento_institucional (documento_id, tipo_documento, titulo, archivo, fecha_subida, usuario_id, checksum_sha256, error_procesamiento, estado_procesamiento, numero_paginas, texto_extraido) VALUES (8, 'Protocolo', 'Reglamento', 'media/documentos_institucionales/REGLAMENTO_INTERNO__actualización_2026_1_oh9k5y.pdf', '2026-11-16 01:17:03.89637+00', 25, 'e5e34818cef0f583866bcfc28c3f841d62692f002201b09750ac2861e3ccc3fd', 'No se encontró Tesseract. Instala el ejecutable del sistema y configura TESSERACT_CMD si no está en PATH.', 'error', NULL, '');


--
-- Data for Name: estudiante; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (4, 'Sofía', 'Martínez', 'Reyes', 2, NULL, NULL, NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (5, 'Benjamín', 'López', 'Vargas', 2, NULL, NULL, NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (7, 'Matías', 'Sánchez', 'Cuevas', 4, NULL, NULL, NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (8, 'Rodrigo', 'Flores', 'Flores', 4, NULL, NULL, NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (11, 'vicente', 'vera', 'Flores', 3, NULL, NULL, NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (13, 'Rodrigo', 'Vasquez', 'Vasquez', 2, NULL, NULL, NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (15, 'Matias', 'Urria', 'Vera', 2, NULL, NULL, NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (28, 'Guillermo', 'Vasquez', 'Rodriguez', 4, NULL, NULL, NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (33, 'Alejandro', 'Torres', 'Mendoza', 1, NULL, NULL, NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (34, 'Sofia', 'Villarroel', 'Castro', 2, NULL, NULL, NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (36, 'Vicente', 'Villarroel', 'Pino', 2, 12, 'VV121MB', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (38, 'Mauricio', 'Navarrete', 'Alarcón', 2, 1, 'MN011MB', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (39, 'Joaquín', 'Mancilla', 'Ibaceta', 3, 1, 'JM012MA', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (40, 'Florencia', 'Delgado', 'Zapata', 4, 1, 'FD013MB', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (43, 'Loreto', 'Wagner', 'Pinto', 3, 2, 'LW022MA', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (44, 'Osvaldo', 'Parra', 'Espinoza', 4, 2, 'OP023MB', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (45, 'Belén', 'Godoy', 'Bustos', 1, 3, 'BG031MA', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (47, 'Daniela', 'Yévenes', 'Gallardo', 3, 3, 'DY032MA', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (48, 'Ignacia', 'Figueroa', 'Ulloa', 4, 3, 'IF033MB', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (49, 'Valeria', 'Torres', 'Saavedra', 1, 4, 'VT041MA', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (50, 'Ulises', 'Herrera', 'Yañez', 6, 1, 'UH012MB', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (51, 'Tamara', 'Zambrano', 'Leiva', 7, 1, 'TZ013MA', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (52, 'Esteban', 'Jara', 'Fuentealba', 8, 1, 'EJ014MA', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (53, 'Kevin', 'Ximénez', 'Quintana', 9, 1, 'KX014MB', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (54, 'Sebastián', 'Valdivia', 'Donoso', 6, 2, 'SV022MB', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (55, 'Agustín', 'Riquelme', 'Rebolledo', 7, 2, 'AR023MA', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (57, 'Nayareth', 'Urbina', 'Huerta', 9, 2, 'NU024MB', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (58, 'Zaira', 'Lagos', 'Toledo', 6, 3, 'ZL032MB', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (59, 'Gaspar', 'Olivares', 'Mella', 7, 3, 'GO033MA', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (75, 'Rosa  Alejandra', 'Melano', 'Jara', 3, 9, 'RM092MA', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (61, 'Cristian', 'Inostroza', 'Jofré', 9, 3, 'CI034MB', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (6, 'Isabella', 'Pérez', 'Núñez', 3, 1, 'IP012MA', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (30, 'Agustin', 'Flores', 'Martinez', 1, 5, 'AF051MA', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (3, 'Diego', 'Flores', 'Medina', 1, 7, 'DF071MA', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (9, 'Rodrigo', 'Flores', 'Galdames', 1, 8, 'RF081MA', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (1, 'Tomás', 'González', 'Silva', 1, 9, 'TG091MA', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (2, 'Camila', 'Ramírez', 'Torres', 1, 10, 'CR101MA', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (32, 'Fernando', 'Soto', 'Maulen', 1, 11, 'FS111MA', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (64, 'Matías Andrés', 'Rojas', 'Pérez', 1, NULL, NULL, NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (65, 'Sofía Ignacia', 'Muñoz', 'Contreras', 1, NULL, NULL, NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (66, 'Benjamín Felipe', 'Soto', 'Vargas', 1, NULL, NULL, NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (67, 'Valentina Josefa', 'González', 'Sepúlveda', 1, NULL, NULL, NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (69, 'Camila Fernanda', 'Silva', 'Araya', 1, NULL, NULL, NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (70, 'Joaquín Ignacio', 'Paredes', 'Fuentes', 1, NULL, NULL, NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (71, 'Martina Antonia', 'Torres', 'Navarro', 1, NULL, NULL, NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (72, 'Vicente Sebastián', 'Herrera', 'Espinoza', 1, NULL, NULL, NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (73, 'Florencia Daniela', 'Ramírez', 'Bravo', 1, NULL, NULL, NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (74, 'rodrigo', 'segundo', 'est', 1, 16, 'RS161MA', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (35, 'Carlos', 'Benitez', 'Morales', 4, 5, 'CB053MB', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (42, 'Willy', 'Quiroz', 'Wenzel', 2, 2, 'WQ021MB', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (46, 'Yerko', 'Escobar', 'Cea', 2, 3, 'YE031MB', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (10, 'Rodrigo', 'Flores', 'Flores', 2, NULL, NULL, NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (12, 'Vicente', 'Flores', 'Flores', 4, 15, NULL, NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (76, 'Agustin', 'Alvarado', 'rojas', 8, 15, NULL, NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (29, 'Constanza', 'Flores', 'Farias', 1, 6, 'CF061MA', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (68, 'Diego Alejandro', 'Castillo', 'Morales', 1, 6, NULL, NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (37, 'Rocío', 'Cortés', 'Xamenaa', 1, 1, 'RC011MA', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (63, 'Agustin', 'Alvarado', 'rojas', 7, 15, 'AA153MA', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (41, 'Paulina', 'Sepúlveda', 'Orellana', 1, 2, 'PS021MA', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (56, 'Ximena', 'Bahamondez', 'Novoa', 8, 2, 'XB024MA', NULL, true);
INSERT INTO public.estudiante (estudiante_id, estudiante_nombre, estudiante_apaterno, estudiante_amaterno, curso_id, estudiante_numero_lista, estudiante_identificador, estudiante_correo, estudiante_activo) VALUES (60, 'Antonia', 'Aguilar', 'Vergara', 8, 2, 'AA034MA', NULL, true);


--
-- Data for Name: version_reglamento; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: regla_institucional; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: notificacion; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #18 [prueba de notificacion prueba 15] asociado al alumno Alumno15 pApellido15 en la zona: Sala 10.', '2026-06-13 20:31:12.949302+00', true, '🚨', 11, 1, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #19 [caso prueba 16 (edicion)] asociado al alumno Alumno16 pApellido16 en la zona: Baños 2° piso.', '2026-06-13 21:09:53.784975+00', true, '🚨', 12, 2, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #20 [caso prueba 17 historial usuarios] asociado al alumno A17 AP17 en la zona: Comedor.', '2026-06-13 22:16:15.285747+00', true, '🚨', 11, 3, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #21 [caso prueba 18] asociado al alumno Alumno18 aPaterno18 en la zona: Gimnasio.', '2026-06-14 22:56:06.622316+00', true, '🚨', 11, 4, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #22 [caso de prueba 19] asociado al alumno Guillermo Vasquez en la zona: Gimnasio.', '2026-06-14 23:08:29.841647+00', true, '🚨', 11, 5, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #23 [caso prueba 20] asociado al alumno Agustin Flores en la zona: Sala 10.', '2026-06-14 23:25:43.904061+00', true, '🚨', 11, 6, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #24 [Caso prueba 21] asociado al alumno APrueba21 APaterno21 en la zona: Sala 10.', '2026-06-14 23:37:45.62162+00', true, '🚨', 11, 7, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #25 [Caso prueba notificaciones] asociado al alumno Alejandro Torres en la zona: Sala 10.', '2026-06-14 23:54:13.820764+00', true, '🚨', 11, 8, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #26 [caso prueba 22] asociado al alumno Sofia Villarroel en la zona: Comedor.', '2026-06-14 23:57:50.539432+00', false, '🚨', 12, 9, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #27 [Caso prueba 24] asociado al alumno Carlos Benitez en la zona: Baños 2° piso.', '2026-06-15 00:22:18.763009+00', true, '🚨', 11, 10, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #28 [Batalla de aura] asociado a: Rodrigo Flores en la zona: Patio central.', '2026-09-01 20:45:10.495265+00', true, '🚨', 19, 11, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #29 [Agresion Verbal al Docente] asociado a: Antonia Aguilar en la zona: Comedor.', '2026-09-24 20:27:43.082949+00', true, '🚨', 23, 12, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #30 [Agresion Verbal al Docente] asociado a: Antonia Aguilar en la zona: Sala 10.', '2026-09-24 20:27:49.636232+00', true, '🚨', 23, 13, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #31 [Copia] asociado a: Antonia Aguilar en la zona: Sala 10.', '2026-09-30 12:41:47.702908+00', true, '🚨', 23, 14, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #32 [prueba de ingles ] asociado a: Carlos Benitez en la zona: Baños 2° piso.', '2026-10-03 19:51:55.110463+00', true, '🚨', 23, 15, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #33 [alumno se salta la clase ] asociado a: Antonia Aguilar en la zona: Gimnasio.', '2026-10-03 20:39:17.032996+00', true, '🚨', 23, 16, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #34 [alumno insulta a su compañera  ] asociado a: Willy Quiroz en la zona: Comedor.', '2026-10-03 20:49:05.446325+00', true, '🚨', 23, 17, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #35 [caso prueba  8] asociado a: Rodrigo Flores en la zona: Baños 2° piso.', '2026-10-03 20:51:29.01222+00', true, '🚨', 23, 18, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #36 [caso patio central ] asociado a: Yerko Escobar en la zona: Patio central.', '2026-10-03 20:52:59.40701+00', true, '🚨', 23, 19, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #37 [retraso ] asociado a: Rodrigo Flores en la zona: Sala 10.', '2026-10-03 20:53:56.263569+00', true, '🚨', 23, 20, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #38 [falta de respeto  ] asociado a: Rodrigo Flores en la zona: Sala 10.', '2026-10-03 20:54:49.9218+00', true, '🚨', 23, 21, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #39 [caso10] asociado a: Yerko Escobar en la zona: Baños 2° piso.', '2026-10-03 20:57:27.208537+00', true, '🚨', 23, 22, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #40 [caso 11 ] asociado a: Yerko Escobar en la zona: Comedor.', '2026-10-03 20:58:20.354613+00', true, '🚨', 23, 23, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #41 [caso11 ] asociado a: Yerko Escobar en la zona: Gimnasio.', '2026-10-03 20:58:54.863886+00', true, '🚨', 23, 24, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #42 [caso 13 ] asociado a: Benjamín López en la zona: Patio central.', '2026-10-03 21:00:10.537299+00', true, '🚨', 23, 25, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #43 [caso 67] asociado a: Yerko Escobar en la zona: Patio central.', '2026-10-03 21:01:00.201626+00', true, '🚨', 23, 26, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #44 [caso 69 ] asociado a: Rodrigo Flores en la zona: Baños 2° piso.', '2026-10-03 21:02:11.062558+00', true, '🚨', 23, 27, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Prueba de notificación', 'Esta es una notificación de prueba para verificar que el estado de lectura funciona correctamente.', '2026-10-04 01:54:23.830074+00', true, '🔔', 23, 28, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Segunda prueba', 'Esta notificación debe permanecer sin leer hasta que se pulse.', '2026-10-04 01:58:17.937739+00', true, '🔔', 23, 29, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso modificado', 'El caso #44 fue modificado por Osvaldo Caraccioli.', '2026-10-04 03:06:13.898714+00', true, '✏️', 23, 30, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio B supera los 10 casos de convivencia esta semana. Actualmente registra 12 casos.', '2026-10-04 04:03:21.447399+00', false, '⚠️', 14, 31, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio B supera los 10 casos de convivencia esta semana. Actualmente registra 12 casos.', '2026-10-04 04:03:21.833788+00', false, '⚠️', 15, 32, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio B supera los 10 casos de convivencia esta semana. Actualmente registra 12 casos.', '2026-10-04 04:03:22.369491+00', false, '⚠️', 18, 33, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio B supera los 10 casos de convivencia esta semana. Actualmente registra 12 casos.', '2026-10-04 04:03:22.779033+00', false, '⚠️', 12, 34, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio B supera los 10 casos de convivencia esta semana. Actualmente registra 12 casos.', '2026-10-04 04:03:23.140916+00', false, '⚠️', 16, 35, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio B supera los 10 casos de convivencia esta semana. Actualmente registra 12 casos.', '2026-10-04 04:03:23.597894+00', false, '⚠️', 21, 36, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio B supera los 10 casos de convivencia esta semana. Actualmente registra 12 casos.', '2026-10-04 04:03:24.009994+00', false, '⚠️', 26, 37, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio B supera los 10 casos de convivencia esta semana. Actualmente registra 12 casos.', '2026-10-04 04:03:24.827563+00', false, '⚠️', 17, 39, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio B supera los 10 casos de convivencia esta semana. Actualmente registra 12 casos.', '2026-10-04 04:03:25.212833+00', false, '⚠️', 28, 40, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio B supera los 10 casos de convivencia esta semana. Actualmente registra 12 casos.', '2026-10-04 04:03:25.623678+00', false, '⚠️', 25, 41, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio B supera los 10 casos de convivencia esta semana. Actualmente registra 12 casos.', '2026-10-04 04:03:25.985911+00', false, '⚠️', 23, 42, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio B supera los 10 casos de convivencia esta semana. Actualmente registra 12 casos.', '2026-10-04 04:03:26.434215+00', false, '⚠️', 11, 43, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #45 [caso prueba 20] asociado a: Yerko Escobar en la zona: Baños 2° piso.', '2026-10-04 04:03:27.080024+00', false, '🚨', 23, 45, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #46 [caso 21 ] asociado a: Yerko Escobar en la zona: Comedor.', '2026-10-04 04:04:07.707743+00', false, '🚨', 23, 46, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #47 [caso prueba  22] asociado a: Yerko Escobar en la zona: Gimnasio.', '2026-10-04 04:05:18.259975+00', false, '🚨', 23, 47, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #48 [caso 23 ] asociado a: Yerko Escobar en la zona: Gimnasio.', '2026-10-04 04:05:58.402101+00', false, '🚨', 23, 48, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #49 [caso 24 ] asociado a: Yerko Escobar en la zona: Gimnasio.', '2026-10-04 04:06:56.9664+00', false, '🚨', 23, 49, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #50 [caso 25 ] asociado a: Yerko Escobar en la zona: Patio central.', '2026-10-04 04:07:31.55906+00', false, '🚨', 23, 50, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #51 [caso 26] asociado a: Yerko Escobar en la zona: Baños 2° piso.', '2026-10-04 04:08:18.46214+00', false, '🚨', 23, 51, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #52 [caso 27] asociado a: Yerko Escobar en la zona: Sala 10.', '2026-10-04 04:09:11.316122+00', false, '🚨', 23, 52, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #53 [caso 28] asociado a: Yerko Escobar en la zona: Baños 2° piso.', '2026-10-04 04:09:49.698708+00', false, '🚨', 23, 53, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #54 [caso 29] asociado a: Yerko Escobar en la zona: Patio central.', '2026-10-04 04:10:38.468492+00', false, '🚨', 23, 54, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #55 [caso 30] asociado a: Yerko Escobar en la zona: Baños 2° piso.', '2026-10-04 04:11:22.396356+00', false, '🚨', 23, 55, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #56 [caso 31] asociado a: Yerko Escobar en la zona: Baños 2° piso.', '2026-10-04 04:12:11.677814+00', false, '🚨', 23, 56, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio B supera los 10 casos de convivencia esta semana. Actualmente registra 24 casos.', '2026-10-04 05:02:50.974406+00', false, '⚠️', 36, 57, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #57 [caso 32] asociado a: Yerko Escobar en la zona: Baños 2° piso.', '2026-10-04 05:02:51.229306+00', false, '🚨', 23, 58, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio B supera los 10 casos de convivencia esta semana. Actualmente registra 12 casos.', '2026-10-04 04:03:24.41768+00', true, '⚠️', 19, 38, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso modificado', 'El caso #48 fue modificado por Osvaldo Caraccioli.', '2026-10-05 15:54:00.976516+00', false, '✏️', 23, 59, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nueva Bitácora Registrada', 'Se ha creado el caso #58 [Caso Isa] asociado a: Agustin Alvarado en la zona: Baños 2° piso.', '2026-10-05 15:56:00.776981+00', false, '🚨', 19, 62, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso modificado', 'El caso #58 fue modificado por Matias Ibarra.', '2026-10-05 16:18:06.256236+00', false, '✏️', 19, 63, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso modificado', 'El caso #58 fue modificado por Matias Ibarra.', '2026-10-11 22:22:10.971791+00', false, '✏️', 19, 64, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso modificado', 'El caso #57 fue modificado por Isaias Ortiz.', '2026-10-05 15:55:15.523281+00', true, '✏️', 23, 60, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso modificado', 'El caso #35 fue modificado por Osvaldo Caraccioli.', '2026-10-05 15:55:26.6854+00', true, '✏️', 23, 61, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #59 para Estudiante #15 en la zona Patio central.', '2026-10-13 21:01:22.427906+00', false, '🚨', 36, 65, 59, 'espera', NULL, 'caso_creado:59:usuario:36', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #59', 'Se registró el caso #59 como Gravísima en Patio central. Revisa sus antecedentes.', '2026-10-13 21:01:23.547965+00', false, '🚨', 11, 66, 59, 'espera', NULL, 'caso_gravisimo:59:admin:11', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #59', 'Se registró el caso #59 como Gravísima en Patio central. Revisa sus antecedentes.', '2026-10-13 21:01:24.470588+00', false, '🚨', 17, 67, 59, 'espera', NULL, 'caso_gravisimo:59:admin:17', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #59', 'Se registró el caso #59 como Gravísima en Patio central. Revisa sus antecedentes.', '2026-10-13 21:01:25.390068+00', false, '🚨', 19, 68, 59, 'espera', NULL, 'caso_gravisimo:59:admin:19', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #59', 'Se registró el caso #59 como Gravísima en Patio central. Revisa sus antecedentes.', '2026-10-13 21:01:26.312183+00', false, '🚨', 21, 69, 59, 'espera', NULL, 'caso_gravisimo:59:admin:21', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #59', 'Se registró el caso #59 como Gravísima en Patio central. Revisa sus antecedentes.', '2026-10-13 21:01:27.238016+00', false, '🚨', 23, 70, 59, 'espera', NULL, 'caso_gravisimo:59:admin:23', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #59', 'Se registró el caso #59 como Gravísima en Patio central. Revisa sus antecedentes.', '2026-10-13 21:01:28.163833+00', false, '🚨', 25, 71, 59, 'espera', NULL, 'caso_gravisimo:59:admin:25', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #59', 'Se registró el caso #59 como Gravísima en Patio central. Revisa sus antecedentes.', '2026-10-13 21:01:29.089204+00', false, '🚨', 26, 72, 59, 'espera', NULL, 'caso_gravisimo:59:admin:26', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #60 para AA034MA en la zona Baños 2° piso.', '2026-10-14 16:42:20.047464+00', false, '🚨', 19, 73, 60, 'espera', NULL, 'caso_creado:60:usuario:19', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #61 para AA153MA en la zona Comedor.', '2026-10-14 16:46:30.818837+00', false, '🚨', 37, 74, 61, 'espera', NULL, 'caso_creado:61:usuario:37', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #62 para FD013MB en la zona Comedor.', '2026-10-15 15:04:29.384023+00', false, '🚨', 19, 75, 62, 'espera', NULL, 'caso_creado:62:usuario:19', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #63 para AA153MA en la zona Patio central.', '2026-10-16 12:12:51.360943+00', false, '🚨', 19, 76, 63, 'espera', NULL, 'caso_creado:63:usuario:19', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #64 para AA153MA en la zona Comedor.', '2026-10-16 19:05:23.069066+00', false, '🚨', 19, 77, 64, 'espera', NULL, 'caso_creado:64:usuario:19', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #65 para AA034MA, AA153MA, PS021MA en la zona Patio central.', '2026-10-19 22:42:36.144214+00', false, '🚨', 19, 78, 65, 'espera', NULL, 'caso_creado:65:usuario:19', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #70 para IF033MB en la zona Comedor.', '2026-10-28 01:02:08.067709+00', false, '🚨', 19, 103, 70, 'espera', NULL, 'caso_creado:70:usuario:19', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #70', 'Se registró el caso #70 como Gravísima en Comedor. Revisa sus antecedentes.', '2026-10-28 01:02:09.330384+00', false, '🚨', 11, 104, 70, 'espera', NULL, 'caso_gravisimo:70:admin:11', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #70', 'Se registró el caso #70 como Gravísima en Comedor. Revisa sus antecedentes.', '2026-10-28 01:02:10.37047+00', false, '🚨', 17, 105, 70, 'espera', NULL, 'caso_gravisimo:70:admin:17', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #70', 'Se registró el caso #70 como Gravísima en Comedor. Revisa sus antecedentes.', '2026-10-28 01:02:11.411576+00', false, '🚨', 19, 106, 70, 'espera', NULL, 'caso_gravisimo:70:admin:19', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #70', 'Se registró el caso #70 como Gravísima en Comedor. Revisa sus antecedentes.', '2026-10-28 01:02:12.436375+00', false, '🚨', 21, 107, 70, 'espera', NULL, 'caso_gravisimo:70:admin:21', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #70', 'Se registró el caso #70 como Gravísima en Comedor. Revisa sus antecedentes.', '2026-10-28 01:02:13.472465+00', false, '🚨', 23, 108, 70, 'espera', NULL, 'caso_gravisimo:70:admin:23', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #70', 'Se registró el caso #70 como Gravísima en Comedor. Revisa sus antecedentes.', '2026-10-28 01:02:14.52933+00', false, '🚨', 25, 109, 70, 'espera', NULL, 'caso_gravisimo:70:admin:25', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #70', 'Se registró el caso #70 como Gravísima en Comedor. Revisa sus antecedentes.', '2026-10-28 01:02:15.578999+00', false, '🚨', 26, 110, 70, 'espera', NULL, 'caso_gravisimo:70:admin:26', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #71 para Estudiante #68 en la zona Gimnasio.', '2026-10-28 01:06:54.328765+00', false, '🚨', 19, 111, 71, 'espera', NULL, 'caso_creado:71:usuario:19', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #71', 'Se registró el caso #71 como Gravísima en Gimnasio. Revisa sus antecedentes.', '2026-10-28 01:06:55.577178+00', false, '🚨', 11, 112, 71, 'espera', NULL, 'caso_gravisimo:71:admin:11', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #71', 'Se registró el caso #71 como Gravísima en Gimnasio. Revisa sus antecedentes.', '2026-10-28 01:06:56.624029+00', false, '🚨', 17, 113, 71, 'espera', NULL, 'caso_gravisimo:71:admin:17', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #71', 'Se registró el caso #71 como Gravísima en Gimnasio. Revisa sus antecedentes.', '2026-10-28 01:06:57.66022+00', false, '🚨', 19, 114, 71, 'espera', NULL, 'caso_gravisimo:71:admin:19', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #71', 'Se registró el caso #71 como Gravísima en Gimnasio. Revisa sus antecedentes.', '2026-10-28 01:06:58.695486+00', false, '🚨', 21, 115, 71, 'espera', NULL, 'caso_gravisimo:71:admin:21', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #71', 'Se registró el caso #71 como Gravísima en Gimnasio. Revisa sus antecedentes.', '2026-10-28 01:06:59.736484+00', false, '🚨', 23, 116, 71, 'espera', NULL, 'caso_gravisimo:71:admin:23', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #71', 'Se registró el caso #71 como Gravísima en Gimnasio. Revisa sus antecedentes.', '2026-10-28 01:07:00.773861+00', false, '🚨', 25, 117, 71, 'espera', NULL, 'caso_gravisimo:71:admin:25', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #71', 'Se registró el caso #71 como Gravísima en Gimnasio. Revisa sus antecedentes.', '2026-10-28 01:07:01.822561+00', false, '🚨', 26, 118, 71, 'espera', NULL, 'caso_gravisimo:71:admin:26', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #72 para CF061MA en la zona Baños 2° piso.', '2026-10-28 01:11:51.422567+00', false, '🚨', 19, 119, 72, 'espera', NULL, 'caso_creado:72:usuario:19', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #72', 'Se registró el caso #72 como Gravísima en Baños 2° piso. Revisa sus antecedentes.', '2026-10-28 01:11:52.686767+00', false, '🚨', 11, 120, 72, 'espera', NULL, 'caso_gravisimo:72:admin:11', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #72', 'Se registró el caso #72 como Gravísima en Baños 2° piso. Revisa sus antecedentes.', '2026-10-28 01:11:53.722649+00', false, '🚨', 17, 121, 72, 'espera', NULL, 'caso_gravisimo:72:admin:17', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #72', 'Se registró el caso #72 como Gravísima en Baños 2° piso. Revisa sus antecedentes.', '2026-10-28 01:11:54.760765+00', false, '🚨', 19, 122, 72, 'espera', NULL, 'caso_gravisimo:72:admin:19', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #72', 'Se registró el caso #72 como Gravísima en Baños 2° piso. Revisa sus antecedentes.', '2026-10-28 01:11:55.79934+00', false, '🚨', 21, 123, 72, 'espera', NULL, 'caso_gravisimo:72:admin:21', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #72', 'Se registró el caso #72 como Gravísima en Baños 2° piso. Revisa sus antecedentes.', '2026-10-28 01:11:56.837541+00', false, '🚨', 23, 124, 72, 'espera', NULL, 'caso_gravisimo:72:admin:23', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #72', 'Se registró el caso #72 como Gravísima en Baños 2° piso. Revisa sus antecedentes.', '2026-10-28 01:11:57.877013+00', false, '🚨', 25, 125, 72, 'espera', NULL, 'caso_gravisimo:72:admin:25', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #72', 'Se registró el caso #72 como Gravísima en Baños 2° piso. Revisa sus antecedentes.', '2026-10-28 01:11:58.919757+00', false, '🚨', 26, 126, 72, 'espera', NULL, 'caso_gravisimo:72:admin:26', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #73 para EJ014MA en la zona Sala 10.', '2026-10-28 01:15:56.329089+00', false, '🚨', 19, 127, 73, 'espera', NULL, 'caso_creado:73:usuario:19', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #73', 'Se registró el caso #73 como Gravísima en Sala 10. Revisa sus antecedentes.', '2026-10-28 01:15:57.550496+00', false, '🚨', 11, 128, 73, 'espera', NULL, 'caso_gravisimo:73:admin:11', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #73', 'Se registró el caso #73 como Gravísima en Sala 10. Revisa sus antecedentes.', '2026-10-28 01:15:58.560337+00', false, '🚨', 17, 129, 73, 'espera', NULL, 'caso_gravisimo:73:admin:17', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #73', 'Se registró el caso #73 como Gravísima en Sala 10. Revisa sus antecedentes.', '2026-10-28 01:15:59.571442+00', false, '🚨', 19, 130, 73, 'espera', NULL, 'caso_gravisimo:73:admin:19', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #73', 'Se registró el caso #73 como Gravísima en Sala 10. Revisa sus antecedentes.', '2026-10-28 01:16:00.586108+00', false, '🚨', 21, 131, 73, 'espera', NULL, 'caso_gravisimo:73:admin:21', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #73', 'Se registró el caso #73 como Gravísima en Sala 10. Revisa sus antecedentes.', '2026-10-28 01:16:01.599746+00', false, '🚨', 23, 132, 73, 'espera', NULL, 'caso_gravisimo:73:admin:23', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #73', 'Se registró el caso #73 como Gravísima en Sala 10. Revisa sus antecedentes.', '2026-10-28 01:16:02.608446+00', false, '🚨', 25, 133, 73, 'espera', NULL, 'caso_gravisimo:73:admin:25', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #73', 'Se registró el caso #73 como Gravísima en Sala 10. Revisa sus antecedentes.', '2026-10-28 01:16:03.623389+00', false, '🚨', 26, 134, 73, 'espera', NULL, 'caso_gravisimo:73:admin:26', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #74 para Estudiante #12, Estudiante #68 en la zona Baños 2° piso.', '2026-11-07 00:49:39.679066+00', false, '🚨', 23, 135, 74, 'espera', NULL, 'caso_creado:74:usuario:23', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #74', 'Se registró el caso #74 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-07 00:49:40.930463+00', false, '🚨', 11, 136, 74, 'espera', NULL, 'caso_prioritario:74:admin:11', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #74', 'Se registró el caso #74 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-07 00:49:42.150291+00', false, '🚨', 17, 137, 74, 'espera', NULL, 'caso_prioritario:74:admin:17', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #74', 'Se registró el caso #74 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-07 00:49:43.385941+00', false, '🚨', 19, 138, 74, 'espera', NULL, 'caso_prioritario:74:admin:19', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #74', 'Se registró el caso #74 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-07 00:49:44.609835+00', false, '🚨', 21, 139, 74, 'espera', NULL, 'caso_prioritario:74:admin:21', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #74', 'Se registró el caso #74 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-07 00:49:45.901139+00', false, '🚨', 23, 140, 74, 'espera', NULL, 'caso_prioritario:74:admin:23', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #74', 'Se registró el caso #74 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-07 00:49:47.062856+00', false, '🚨', 25, 141, 74, 'espera', NULL, 'caso_prioritario:74:admin:25', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #74', 'Se registró el caso #74 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-07 00:49:48.188286+00', false, '🚨', 26, 142, 74, 'espera', NULL, 'caso_prioritario:74:admin:26', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #75 para XB024MA en la zona Baños 2° piso.', '2026-11-14 03:02:47.202406+00', false, '🚨', 28, 143, 75, 'espera', NULL, 'caso_creado:75:usuario:28', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #76 para Estudiante #76 en la zona Baños 2° piso.', '2026-11-14 03:04:34.37651+00', false, '🚨', 28, 144, 76, 'espera', NULL, 'caso_creado:76:usuario:28', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #76', 'Se registró el caso #76 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 03:04:35.487251+00', false, '🚨', 11, 145, 76, 'espera', NULL, 'caso_prioritario:76:admin:11', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #76', 'Se registró el caso #76 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 03:04:36.407304+00', false, '🚨', 17, 146, 76, 'espera', NULL, 'caso_prioritario:76:admin:17', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #76', 'Se registró el caso #76 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 03:04:37.333286+00', false, '🚨', 19, 147, 76, 'espera', NULL, 'caso_prioritario:76:admin:19', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #76', 'Se registró el caso #76 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 03:04:38.252466+00', false, '🚨', 21, 148, 76, 'espera', NULL, 'caso_prioritario:76:admin:21', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #76', 'Se registró el caso #76 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 03:04:39.172892+00', false, '🚨', 23, 149, 76, 'espera', NULL, 'caso_prioritario:76:admin:23', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #76', 'Se registró el caso #76 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 03:04:40.093088+00', false, '🚨', 25, 150, 76, 'espera', NULL, 'caso_prioritario:76:admin:25', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #76', 'Se registró el caso #76 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 03:04:41.014374+00', false, '🚨', 26, 151, 76, 'espera', NULL, 'caso_prioritario:76:admin:26', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #77 para Estudiante #10 en la zona Sala 10.', '2026-11-14 03:25:43.850885+00', false, '🚨', 36, 152, 77, 'espera', NULL, 'caso_creado:77:usuario:36', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #77', 'Se registró el caso #77 como Grave en Sala 10. Revisa sus antecedentes.', '2026-11-14 03:25:45.014818+00', false, '🚨', 11, 153, 77, 'espera', NULL, 'caso_prioritario:77:admin:11', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #77', 'Se registró el caso #77 como Grave en Sala 10. Revisa sus antecedentes.', '2026-11-14 03:25:45.883644+00', false, '🚨', 17, 154, 77, 'espera', NULL, 'caso_prioritario:77:admin:17', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #77', 'Se registró el caso #77 como Grave en Sala 10. Revisa sus antecedentes.', '2026-11-14 03:25:46.761872+00', false, '🚨', 19, 155, 77, 'espera', NULL, 'caso_prioritario:77:admin:19', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #77', 'Se registró el caso #77 como Grave en Sala 10. Revisa sus antecedentes.', '2026-11-14 03:25:47.632976+00', false, '🚨', 21, 156, 77, 'espera', NULL, 'caso_prioritario:77:admin:21', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #77', 'Se registró el caso #77 como Grave en Sala 10. Revisa sus antecedentes.', '2026-11-14 03:25:48.514939+00', false, '🚨', 23, 157, 77, 'espera', NULL, 'caso_prioritario:77:admin:23', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #77', 'Se registró el caso #77 como Grave en Sala 10. Revisa sus antecedentes.', '2026-11-14 03:25:49.379911+00', false, '🚨', 25, 158, 77, 'espera', NULL, 'caso_prioritario:77:admin:25', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #77', 'Se registró el caso #77 como Grave en Sala 10. Revisa sus antecedentes.', '2026-11-14 03:25:50.250248+00', false, '🚨', 26, 159, 77, 'espera', NULL, 'caso_prioritario:77:admin:26', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #78 para CF061MA en la zona Baños 2° piso.', '2026-11-14 20:14:52.553993+00', false, '🚨', 25, 162, 78, 'espera', NULL, 'caso_creado:78:usuario:25', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #78', 'Se registró el caso #78 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:14:53.600311+00', false, '🚨', 11, 163, 78, 'espera', NULL, 'caso_prioritario:78:admin:11', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #78', 'Se registró el caso #78 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:14:54.451712+00', false, '🚨', 17, 164, 78, 'espera', NULL, 'caso_prioritario:78:admin:17', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #78', 'Se registró el caso #78 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:14:55.306932+00', false, '🚨', 19, 165, 78, 'espera', NULL, 'caso_prioritario:78:admin:19', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #78', 'Se registró el caso #78 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:14:56.160084+00', false, '🚨', 21, 166, 78, 'espera', NULL, 'caso_prioritario:78:admin:21', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #78', 'Se registró el caso #78 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:14:57.017648+00', false, '🚨', 23, 167, 78, 'espera', NULL, 'caso_prioritario:78:admin:23', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #78', 'Se registró el caso #78 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:14:57.873385+00', false, '🚨', 25, 168, 78, 'espera', NULL, 'caso_prioritario:78:admin:25', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #78', 'Se registró el caso #78 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:14:58.729137+00', false, '🚨', 26, 169, 78, 'espera', NULL, 'caso_prioritario:78:admin:26', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #79 para RC011MA en la zona Baños 2° piso.', '2026-11-14 20:20:52.575946+00', false, '🚨', 25, 170, 79, 'espera', NULL, 'caso_creado:79:usuario:25', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #80 para RC011MA en la zona Baños 2° piso.', '2026-11-14 20:24:06.501963+00', false, '🚨', 25, 171, 80, 'espera', NULL, 'caso_creado:80:usuario:25', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #80', 'Se registró el caso #80 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:24:07.573023+00', false, '🚨', 11, 172, 80, 'espera', NULL, 'caso_prioritario:80:admin:11', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #80', 'Se registró el caso #80 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:24:08.461475+00', false, '🚨', 17, 173, 80, 'espera', NULL, 'caso_prioritario:80:admin:17', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #80', 'Se registró el caso #80 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:24:09.35039+00', false, '🚨', 19, 174, 80, 'espera', NULL, 'caso_prioritario:80:admin:19', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #80', 'Se registró el caso #80 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:24:10.23739+00', false, '🚨', 21, 175, 80, 'espera', NULL, 'caso_prioritario:80:admin:21', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #80', 'Se registró el caso #80 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:24:11.126318+00', false, '🚨', 23, 176, 80, 'espera', NULL, 'caso_prioritario:80:admin:23', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #80', 'Se registró el caso #80 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:24:12.020707+00', false, '🚨', 25, 177, 80, 'espera', NULL, 'caso_prioritario:80:admin:25', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #80', 'Se registró el caso #80 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:24:12.911243+00', false, '🚨', 26, 178, 80, 'espera', NULL, 'caso_prioritario:80:admin:26', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #81 para RC011MA en la zona Baños 2° piso.', '2026-11-14 20:31:08.99985+00', false, '🚨', 25, 179, 81, 'espera', NULL, 'caso_creado:81:usuario:25', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #82 para RC011MA en la zona Baños 2° piso.', '2026-11-14 20:31:38.551942+00', false, '🚨', 25, 180, 82, 'espera', NULL, 'caso_creado:82:usuario:25', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #82', 'Se registró el caso #82 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:31:39.617055+00', false, '🚨', 11, 181, 82, 'espera', NULL, 'caso_prioritario:82:admin:11', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #82', 'Se registró el caso #82 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:31:40.500225+00', false, '🚨', 17, 182, 82, 'espera', NULL, 'caso_prioritario:82:admin:17', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #82', 'Se registró el caso #82 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:31:41.382574+00', false, '🚨', 19, 183, 82, 'espera', NULL, 'caso_prioritario:82:admin:19', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #82', 'Se registró el caso #82 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:31:42.266137+00', false, '🚨', 21, 184, 82, 'espera', NULL, 'caso_prioritario:82:admin:21', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #82', 'Se registró el caso #82 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:31:43.150075+00', false, '🚨', 23, 185, 82, 'espera', NULL, 'caso_prioritario:82:admin:23', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #82', 'Se registró el caso #82 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:31:44.034088+00', false, '🚨', 25, 186, 82, 'espera', NULL, 'caso_prioritario:82:admin:25', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #82', 'Se registró el caso #82 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:31:44.914498+00', false, '🚨', 26, 187, 82, 'espera', NULL, 'caso_prioritario:82:admin:26', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #84 para RC011MA en la zona Gimnasio.', '2026-11-14 20:34:44.199947+00', false, '🚨', 25, 189, 84, 'espera', NULL, 'caso_creado:84:usuario:25', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #85 para RC011MA en la zona Gimnasio.', '2026-11-14 20:35:31.543321+00', false, '🚨', 25, 190, 85, 'espera', NULL, 'caso_creado:85:usuario:25', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #86 para RC011MA en la zona Patio central.', '2026-11-14 20:36:57.252642+00', false, '🚨', 25, 191, 86, 'espera', NULL, 'caso_creado:86:usuario:25', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #87 para RC011MA en la zona Gimnasio.', '2026-11-14 20:37:28.68593+00', false, '🚨', 25, 192, 87, 'espera', NULL, 'caso_creado:87:usuario:25', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #87', 'Se registró el caso #87 como Gravísima en Gimnasio. Revisa sus antecedentes.', '2026-11-14 20:37:29.777048+00', false, '🚨', 11, 193, 87, 'espera', NULL, 'caso_prioritario:87:admin:11', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #87', 'Se registró el caso #87 como Gravísima en Gimnasio. Revisa sus antecedentes.', '2026-11-14 20:37:30.683867+00', false, '🚨', 17, 194, 87, 'espera', NULL, 'caso_prioritario:87:admin:17', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #87', 'Se registró el caso #87 como Gravísima en Gimnasio. Revisa sus antecedentes.', '2026-11-14 20:37:31.589624+00', false, '🚨', 19, 195, 87, 'espera', NULL, 'caso_prioritario:87:admin:19', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #87', 'Se registró el caso #87 como Gravísima en Gimnasio. Revisa sus antecedentes.', '2026-11-14 20:37:32.494994+00', false, '🚨', 21, 196, 87, 'espera', NULL, 'caso_prioritario:87:admin:21', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #87', 'Se registró el caso #87 como Gravísima en Gimnasio. Revisa sus antecedentes.', '2026-11-14 20:37:33.401945+00', false, '🚨', 23, 197, 87, 'espera', NULL, 'caso_prioritario:87:admin:23', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #87', 'Se registró el caso #87 como Gravísima en Gimnasio. Revisa sus antecedentes.', '2026-11-14 20:37:34.305686+00', false, '🚨', 25, 198, 87, 'espera', NULL, 'caso_prioritario:87:admin:25', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso gravísimo #87', 'Se registró el caso #87 como Gravísima en Gimnasio. Revisa sus antecedentes.', '2026-11-14 20:37:35.215017+00', false, '🚨', 26, 199, 87, 'espera', NULL, 'caso_prioritario:87:admin:26', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio A supera los 10 casos de convivencia esta semana. Actualmente registra 11 casos.', '2026-11-14 20:39:16.063775+00', false, '⚠️', 15, 200, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio A supera los 10 casos de convivencia esta semana. Actualmente registra 11 casos.', '2026-11-14 20:39:16.432778+00', false, '⚠️', 18, 201, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio A supera los 10 casos de convivencia esta semana. Actualmente registra 11 casos.', '2026-11-14 20:39:16.80256+00', false, '⚠️', 12, 202, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio A supera los 10 casos de convivencia esta semana. Actualmente registra 11 casos.', '2026-11-14 20:39:17.172787+00', false, '⚠️', 21, 203, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio A supera los 10 casos de convivencia esta semana. Actualmente registra 11 casos.', '2026-11-14 20:39:17.541958+00', false, '⚠️', 19, 204, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio A supera los 10 casos de convivencia esta semana. Actualmente registra 11 casos.', '2026-11-14 20:39:17.91097+00', false, '⚠️', 26, 205, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio A supera los 10 casos de convivencia esta semana. Actualmente registra 11 casos.', '2026-11-14 20:39:18.280082+00', false, '⚠️', 16, 206, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio A supera los 10 casos de convivencia esta semana. Actualmente registra 11 casos.', '2026-11-14 20:39:18.648872+00', false, '⚠️', 17, 207, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio A supera los 10 casos de convivencia esta semana. Actualmente registra 11 casos.', '2026-11-14 20:39:19.01823+00', false, '⚠️', 37, 208, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio A supera los 10 casos de convivencia esta semana. Actualmente registra 11 casos.', '2026-11-14 20:39:19.387436+00', false, '⚠️', 28, 209, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio A supera los 10 casos de convivencia esta semana. Actualmente registra 11 casos.', '2026-11-14 20:39:19.759972+00', false, '⚠️', 14, 210, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio A supera los 10 casos de convivencia esta semana. Actualmente registra 11 casos.', '2026-11-14 20:39:20.129509+00', false, '⚠️', 23, 211, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio A supera los 10 casos de convivencia esta semana. Actualmente registra 11 casos.', '2026-11-14 20:39:20.499611+00', false, '⚠️', 11, 212, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Alerta: alta cantidad de casos', 'El curso 1° Medio A supera los 10 casos de convivencia esta semana. Actualmente registra 11 casos.', '2026-11-14 20:39:20.868689+00', false, '⚠️', 25, 213, NULL, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #88 para RC011MA en la zona Baños 2° piso.', '2026-11-14 20:39:23.27234+00', false, '🚨', 25, 215, 88, 'espera', NULL, 'caso_creado:88:usuario:25', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #88', 'Se registró el caso #88 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:39:24.68132+00', false, '🚨', 11, 216, 88, 'espera', NULL, 'caso_prioritario:88:admin:11', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #88', 'Se registró el caso #88 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:39:25.603573+00', false, '🚨', 17, 217, 88, 'espera', NULL, 'caso_prioritario:88:admin:17', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #88', 'Se registró el caso #88 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:39:26.525204+00', false, '🚨', 19, 218, 88, 'espera', NULL, 'caso_prioritario:88:admin:19', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #88', 'Se registró el caso #88 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:39:27.447908+00', false, '🚨', 21, 219, 88, 'espera', NULL, 'caso_prioritario:88:admin:21', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #88', 'Se registró el caso #88 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:39:28.367154+00', false, '🚨', 23, 220, 88, 'espera', NULL, 'caso_prioritario:88:admin:23', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #88', 'Se registró el caso #88 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:39:29.299108+00', false, '🚨', 25, 221, 88, 'espera', NULL, 'caso_prioritario:88:admin:25', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #88', 'Se registró el caso #88 como Grave en Baños 2° piso. Revisa sus antecedentes.', '2026-11-14 20:39:30.227273+00', false, '🚨', 26, 222, 88, 'espera', NULL, 'caso_prioritario:88:admin:26', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso actualizado', 'El caso #88 fue modificado por Felipe Trujillo.', '2026-11-15 12:29:26.073983+00', false, '✏️', 25, 226, 88, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, 'caso_actualizado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso actualizado', 'El caso #65 fue modificado por Felipe Trujillo.', '2026-11-15 12:35:06.39035+00', false, '✏️', 19, 227, 65, 'espera', NULL, NULL, NULL, NULL, NULL, NULL, 'caso_actualizado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #89 para XB024MA en la zona Patio central.', '2026-11-15 12:37:34.43455+00', false, '🚨', 38, 228, NULL, 'espera', NULL, 'caso_creado:89:usuario:38', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #89', 'Se registró el caso #89 como Grave en Patio central. Revisa sus antecedentes.', '2026-11-15 12:37:35.624703+00', false, '🚨', 11, 229, NULL, 'espera', NULL, 'caso_prioritario:89:admin:11', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #89', 'Se registró el caso #89 como Grave en Patio central. Revisa sus antecedentes.', '2026-11-15 12:37:36.614085+00', false, '🚨', 17, 230, NULL, 'espera', NULL, 'caso_prioritario:89:admin:17', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #89', 'Se registró el caso #89 como Grave en Patio central. Revisa sus antecedentes.', '2026-11-15 12:37:37.606342+00', false, '🚨', 19, 231, NULL, 'espera', NULL, 'caso_prioritario:89:admin:19', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso eliminado', 'El caso #89 que registraste fue eliminado por otro usuario.', '2026-11-15 15:32:49.639504+00', false, '🗑️', 38, 240, NULL, 'espera', NULL, 'caso_eliminado:89:creador:38', NULL, NULL, NULL, NULL, '');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #89', 'Se registró el caso #89 como Grave en Patio central. Revisa sus antecedentes.', '2026-11-15 12:37:38.596742+00', false, '🚨', 21, 232, NULL, 'espera', NULL, 'caso_prioritario:89:admin:21', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #89', 'Se registró el caso #89 como Grave en Patio central. Revisa sus antecedentes.', '2026-11-15 12:37:39.585772+00', false, '🚨', 23, 233, NULL, 'espera', NULL, 'caso_prioritario:89:admin:23', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #89', 'Se registró el caso #89 como Grave en Patio central. Revisa sus antecedentes.', '2026-11-15 12:37:40.574435+00', false, '🚨', 25, 234, NULL, 'espera', NULL, 'caso_prioritario:89:admin:25', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #89', 'Se registró el caso #89 como Grave en Patio central. Revisa sus antecedentes.', '2026-11-15 12:37:41.566036+00', false, '🚨', 26, 235, NULL, 'espera', NULL, 'caso_prioritario:89:admin:26', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Caso grave #89', 'Se registró el caso #89 como Grave en Patio central. Revisa sus antecedentes.', '2026-11-15 12:37:42.557721+00', false, '🚨', 38, 236, NULL, 'espera', NULL, 'caso_prioritario:89:admin:38', NULL, NULL, NULL, NULL, 'caso_creado');
INSERT INTO public.notificacion (notificacion_titulo, notificacion_mensaje, notificacion_fecha, notificacion_leido, notificacion_icono, usuario_id, notificacion_id, caso_id, estado, estudiante_id, evento_clave, fecha_limite, responsable_id, regla_id, version_reglamento_id, evento_tipo) VALUES ('Nuevo caso registrado', 'Se registró el caso #83 para RC011MA en la zona Patio central.', '2026-11-14 20:34:06.722676+00', false, '🚨', 25, 188, NULL, 'espera', NULL, 'caso_creado:83:usuario:25', NULL, NULL, NULL, NULL, 'caso_creado');


--
-- Data for Name: seguimiento_caso; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (1, 'abierto', '2026-10-13 21:01:21.079463+00', NULL, '', 59, 15, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (2, 'abierto', '2026-10-14 16:41:36.08374+00', NULL, '', 58, 63, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (3, 'abierto', '2026-10-14 16:42:18.434131+00', NULL, '', 60, 60, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (4, 'abierto', '2026-10-14 16:46:29.462042+00', NULL, '', 61, 63, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (5, 'abierto', '2026-10-15 15:04:27.682555+00', NULL, '', 62, 40, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (6, 'abierto', '2026-10-16 12:12:49.973054+00', NULL, '', 63, 63, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (7, 'abierto', '2026-10-16 19:05:21.161996+00', NULL, '', 64, 63, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (8, 'abierto', '2026-10-19 22:42:32.656658+00', NULL, '', 65, 60, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (9, 'abierto', '2026-10-19 22:42:33.908006+00', NULL, '', 65, 63, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (10, 'abierto', '2026-10-19 22:42:34.911711+00', NULL, '', 65, 41, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (14, 'abierto', '2026-10-28 01:02:06.594728+00', NULL, '', 70, 48, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (15, 'abierto', '2026-10-28 01:06:52.87079+00', NULL, '', 71, 68, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (16, 'abierto', '2026-10-28 01:11:49.965635+00', NULL, '', 72, 29, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (17, 'abierto', '2026-10-28 01:15:54.899335+00', NULL, '', 73, 52, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (18, 'abierto', '2026-11-07 00:49:37.025654+00', NULL, '', 74, 12, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (19, 'abierto', '2026-11-07 00:49:38.462612+00', NULL, '', 74, 68, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (20, 'abierto', '2026-11-14 03:02:45.968981+00', NULL, '', 75, 56, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (21, 'abierto', '2026-11-14 03:04:33.086831+00', NULL, '', 76, 76, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (22, 'abierto', '2026-11-14 03:25:42.601482+00', NULL, '', 77, 10, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (23, 'abierto', '2026-11-14 20:14:51.331692+00', NULL, '', 78, 29, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (24, 'abierto', '2026-11-14 20:20:51.332716+00', NULL, '', 79, 37, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (25, 'abierto', '2026-11-14 20:24:05.246095+00', NULL, '', 80, 37, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (26, 'abierto', '2026-11-14 20:31:07.768421+00', NULL, '', 81, 37, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (27, 'abierto', '2026-11-14 20:31:37.31134+00', NULL, '', 82, 37, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (29, 'abierto', '2026-11-14 20:34:42.914181+00', NULL, '', 84, 37, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (30, 'abierto', '2026-11-14 20:35:30.256015+00', NULL, '', 85, 37, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (31, 'abierto', '2026-11-14 20:36:55.967927+00', NULL, '', 86, 37, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (32, 'abierto', '2026-11-14 20:37:27.415732+00', NULL, '', 87, 37, NULL);
INSERT INTO public.seguimiento_caso (id, estado, creado_en, solucionado_en, motivo_cierre, caso_id, estudiante_id, solucionado_por_id) VALUES (33, 'abierto', '2026-11-14 20:39:21.977832+00', NULL, '', 88, 37, NULL);


--
-- Data for Name: accion_seguimiento; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: administrador; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.administrador (administrador_id, admin_nombre, admin_apaterno, admin_amaterno, usuario_id) VALUES (2, 'Felipe', 'Morales', 'Cárdenas', 11);
INSERT INTO public.administrador (administrador_id, admin_nombre, admin_apaterno, admin_amaterno, usuario_id) VALUES (4, 'Isaias', 'Abel', 'Ortiz', 21);
INSERT INTO public.administrador (administrador_id, admin_nombre, admin_apaterno, admin_amaterno, usuario_id) VALUES (6, 'Isaias', 'Ortiz', 'Castro', 19);
INSERT INTO public.administrador (administrador_id, admin_nombre, admin_apaterno, admin_amaterno, usuario_id) VALUES (7, 'Carlos', 'Frias', 'Peralta', 17);
INSERT INTO public.administrador (administrador_id, admin_nombre, admin_apaterno, admin_amaterno, usuario_id) VALUES (8, 'Osvaldo', 'Caraccioli', 'Cisterna', 25);
INSERT INTO public.administrador (administrador_id, admin_nombre, admin_apaterno, admin_amaterno, usuario_id) VALUES (9, 'Felipe', 'Trujillo', 'Lopez', 38);


--
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.django_content_type (id, app_label, model) VALUES (1, 'admin', 'logentry');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (2, 'auth', 'permission');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (3, 'auth', 'group');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (4, 'auth', 'user');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (5, 'contenttypes', 'contenttype');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (6, 'sessions', 'session');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (7, 'gestion_casos', 'caso');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (8, 'gestion_casos', 'curso');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (9, 'gestion_casos', 'lugar');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (10, 'gestion_casos', 'rol');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (11, 'gestion_casos', 'estudiante');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (12, 'gestion_casos', 'involucran');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (13, 'gestion_casos', 'usuario');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (14, 'gestion_casos', 'profesorjefe');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (15, 'gestion_casos', 'pconvivencia');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (16, 'gestion_casos', 'inspector');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (17, 'gestion_casos', 'administrador');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (18, 'gestion_casos', 'notificacion');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (19, 'gestion_casos', 'historialusuario');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (20, 'gestion_casos', 'sesionactiva');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (21, 'gestion_casos', 'documentoinstitucional');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (22, 'gestion_casos', 'accionseguimiento');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (23, 'gestion_casos', 'historialaccionseguimiento');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (24, 'gestion_casos', 'historialnotificacion');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (25, 'gestion_casos', 'reglainstitucional');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (26, 'gestion_casos', 'seguimientocaso');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (27, 'gestion_casos', 'historialseguimientocaso');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (28, 'gestion_casos', 'versionreglamento');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (29, 'gestion_casos', 'historialimportacionestudiantes');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (30, 'gestion_casos', 'solicitudcaso');


--
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (1, 'Can add log entry', 1, 'add_logentry');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (2, 'Can change log entry', 1, 'change_logentry');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (3, 'Can delete log entry', 1, 'delete_logentry');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (4, 'Can view log entry', 1, 'view_logentry');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (5, 'Can add permission', 2, 'add_permission');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (6, 'Can change permission', 2, 'change_permission');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (7, 'Can delete permission', 2, 'delete_permission');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (8, 'Can view permission', 2, 'view_permission');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (9, 'Can add group', 3, 'add_group');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (10, 'Can change group', 3, 'change_group');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (11, 'Can delete group', 3, 'delete_group');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (12, 'Can view group', 3, 'view_group');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (13, 'Can add user', 4, 'add_user');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (14, 'Can change user', 4, 'change_user');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (15, 'Can delete user', 4, 'delete_user');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (16, 'Can view user', 4, 'view_user');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (17, 'Can add content type', 5, 'add_contenttype');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (18, 'Can change content type', 5, 'change_contenttype');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (19, 'Can delete content type', 5, 'delete_contenttype');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (20, 'Can view content type', 5, 'view_contenttype');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (21, 'Can add session', 6, 'add_session');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (22, 'Can change session', 6, 'change_session');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (23, 'Can delete session', 6, 'delete_session');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (24, 'Can view session', 6, 'view_session');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (25, 'Can add caso', 7, 'add_caso');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (26, 'Can change caso', 7, 'change_caso');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (27, 'Can delete caso', 7, 'delete_caso');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (28, 'Can view caso', 7, 'view_caso');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (29, 'Can add curso', 8, 'add_curso');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (30, 'Can change curso', 8, 'change_curso');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (31, 'Can delete curso', 8, 'delete_curso');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (32, 'Can view curso', 8, 'view_curso');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (33, 'Can add lugar', 9, 'add_lugar');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (34, 'Can change lugar', 9, 'change_lugar');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (35, 'Can delete lugar', 9, 'delete_lugar');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (36, 'Can view lugar', 9, 'view_lugar');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (37, 'Can add rol', 10, 'add_rol');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (38, 'Can change rol', 10, 'change_rol');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (39, 'Can delete rol', 10, 'delete_rol');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (40, 'Can view rol', 10, 'view_rol');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (41, 'Can add estudiante', 11, 'add_estudiante');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (42, 'Can change estudiante', 11, 'change_estudiante');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (43, 'Can delete estudiante', 11, 'delete_estudiante');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (44, 'Can view estudiante', 11, 'view_estudiante');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (45, 'Can add involucran', 12, 'add_involucran');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (46, 'Can change involucran', 12, 'change_involucran');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (47, 'Can delete involucran', 12, 'delete_involucran');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (48, 'Can view involucran', 12, 'view_involucran');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (49, 'Can add usuario', 13, 'add_usuario');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (50, 'Can change usuario', 13, 'change_usuario');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (51, 'Can delete usuario', 13, 'delete_usuario');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (52, 'Can view usuario', 13, 'view_usuario');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (53, 'Can add profesor jefe', 14, 'add_profesorjefe');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (54, 'Can change profesor jefe', 14, 'change_profesorjefe');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (55, 'Can delete profesor jefe', 14, 'delete_profesorjefe');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (56, 'Can view profesor jefe', 14, 'view_profesorjefe');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (57, 'Can add p convivencia', 15, 'add_pconvivencia');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (58, 'Can change p convivencia', 15, 'change_pconvivencia');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (59, 'Can delete p convivencia', 15, 'delete_pconvivencia');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (60, 'Can view p convivencia', 15, 'view_pconvivencia');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (61, 'Can add inspector', 16, 'add_inspector');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (62, 'Can change inspector', 16, 'change_inspector');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (63, 'Can delete inspector', 16, 'delete_inspector');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (64, 'Can view inspector', 16, 'view_inspector');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (65, 'Can add administrador', 17, 'add_administrador');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (66, 'Can change administrador', 17, 'change_administrador');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (67, 'Can delete administrador', 17, 'delete_administrador');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (68, 'Can view administrador', 17, 'view_administrador');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (69, 'Can add notificacion', 18, 'add_notificacion');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (70, 'Can change notificacion', 18, 'change_notificacion');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (71, 'Can delete notificacion', 18, 'delete_notificacion');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (72, 'Can view notificacion', 18, 'view_notificacion');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (73, 'Can add historial usuario', 19, 'add_historialusuario');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (74, 'Can change historial usuario', 19, 'change_historialusuario');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (75, 'Can delete historial usuario', 19, 'delete_historialusuario');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (76, 'Can view historial usuario', 19, 'view_historialusuario');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (77, 'Can add sesion activa', 20, 'add_sesionactiva');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (78, 'Can change sesion activa', 20, 'change_sesionactiva');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (79, 'Can delete sesion activa', 20, 'delete_sesionactiva');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (80, 'Can view sesion activa', 20, 'view_sesionactiva');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (81, 'Can add documento institucional', 21, 'add_documentoinstitucional');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (82, 'Can change documento institucional', 21, 'change_documentoinstitucional');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (83, 'Can delete documento institucional', 21, 'delete_documentoinstitucional');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (84, 'Can view documento institucional', 21, 'view_documentoinstitucional');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (85, 'Can add accion seguimiento', 22, 'add_accionseguimiento');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (86, 'Can change accion seguimiento', 22, 'change_accionseguimiento');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (87, 'Can delete accion seguimiento', 22, 'delete_accionseguimiento');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (88, 'Can view accion seguimiento', 22, 'view_accionseguimiento');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (89, 'Can add historial accion seguimiento', 23, 'add_historialaccionseguimiento');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (90, 'Can change historial accion seguimiento', 23, 'change_historialaccionseguimiento');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (91, 'Can delete historial accion seguimiento', 23, 'delete_historialaccionseguimiento');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (92, 'Can view historial accion seguimiento', 23, 'view_historialaccionseguimiento');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (93, 'Can add historial notificacion', 24, 'add_historialnotificacion');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (94, 'Can change historial notificacion', 24, 'change_historialnotificacion');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (95, 'Can delete historial notificacion', 24, 'delete_historialnotificacion');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (96, 'Can view historial notificacion', 24, 'view_historialnotificacion');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (97, 'Can add regla institucional', 25, 'add_reglainstitucional');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (98, 'Can change regla institucional', 25, 'change_reglainstitucional');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (99, 'Can delete regla institucional', 25, 'delete_reglainstitucional');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (100, 'Can view regla institucional', 25, 'view_reglainstitucional');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (101, 'Can add seguimiento caso', 26, 'add_seguimientocaso');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (102, 'Can change seguimiento caso', 26, 'change_seguimientocaso');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (103, 'Can delete seguimiento caso', 26, 'delete_seguimientocaso');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (104, 'Can view seguimiento caso', 26, 'view_seguimientocaso');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (105, 'Can add historial seguimiento caso', 27, 'add_historialseguimientocaso');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (106, 'Can change historial seguimiento caso', 27, 'change_historialseguimientocaso');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (107, 'Can delete historial seguimiento caso', 27, 'delete_historialseguimientocaso');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (108, 'Can view historial seguimiento caso', 27, 'view_historialseguimientocaso');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (109, 'Can add version reglamento', 28, 'add_versionreglamento');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (110, 'Can change version reglamento', 28, 'change_versionreglamento');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (111, 'Can delete version reglamento', 28, 'delete_versionreglamento');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (112, 'Can view version reglamento', 28, 'view_versionreglamento');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (113, 'Can add historial importacion estudiantes', 29, 'add_historialimportacionestudiantes');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (114, 'Can change historial importacion estudiantes', 29, 'change_historialimportacionestudiantes');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (115, 'Can delete historial importacion estudiantes', 29, 'delete_historialimportacionestudiantes');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (116, 'Can view historial importacion estudiantes', 29, 'view_historialimportacionestudiantes');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (117, 'Can add solicitud caso', 30, 'add_solicitudcaso');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (118, 'Can change solicitud caso', 30, 'change_solicitudcaso');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (119, 'Can delete solicitud caso', 30, 'delete_solicitudcaso');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (120, 'Can view solicitud caso', 30, 'view_solicitudcaso');


--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: auth_user; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) VALUES (1, 'pbkdf2_sha256$1000000$3A6LeCqGzZKBRFSuEhhLdz$+uo6z4YUNUqMdwFaZZNg81klotV8MhI87jBJ39SoqA8=', NULL, true, 'admin', '', '', 'rodrgo.flores2003@gmail.com', true, true, '2026-06-11 02:25:00.406836+00');


--
-- Data for Name: auth_user_groups; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: auth_user_user_permissions; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.django_migrations (id, app, name, applied) VALUES (1, 'contenttypes', '0001_initial', '2026-06-11 02:13:05.570911+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (2, 'auth', '0001_initial', '2026-06-11 02:13:05.677461+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (3, 'admin', '0001_initial', '2026-06-11 02:13:05.707345+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (4, 'admin', '0002_logentry_remove_auto_add', '2026-06-11 02:13:05.707345+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (5, 'admin', '0003_logentry_add_action_flag_choices', '2026-06-11 02:13:05.721496+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (6, 'contenttypes', '0002_remove_content_type_name', '2026-06-11 02:13:05.739493+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (7, 'auth', '0002_alter_permission_name_max_length', '2026-06-11 02:13:05.748469+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (8, 'auth', '0003_alter_user_email_max_length', '2026-06-11 02:13:05.755998+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (9, 'auth', '0004_alter_user_username_opts', '2026-06-11 02:13:05.765863+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (10, 'auth', '0005_alter_user_last_login_null', '2026-06-11 02:13:05.772715+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (11, 'auth', '0006_require_contenttypes_0002', '2026-06-11 02:13:05.773715+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (12, 'auth', '0007_alter_validators_add_error_messages', '2026-06-11 02:13:05.7825+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (13, 'auth', '0008_alter_user_username_max_length', '2026-06-11 02:13:05.797316+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (14, 'auth', '0009_alter_user_last_name_max_length', '2026-06-11 02:13:05.804025+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (15, 'auth', '0010_alter_group_name_max_length', '2026-06-11 02:13:05.813161+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (16, 'auth', '0011_update_proxy_permissions', '2026-06-11 02:13:05.817959+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (17, 'auth', '0012_alter_user_first_name_max_length', '2026-06-11 02:13:05.826419+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (18, 'gestion_casos', '0001_initial', '2026-06-11 02:13:05.965861+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (19, 'sessions', '0001_initial', '2026-06-11 02:13:05.983419+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (20, 'gestion_casos', '0002_alter_administrador_options_alter_caso_options_and_more', '2026-06-11 05:31:12.214206+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (21, 'gestion_casos', '0003_alter_administrador_table_alter_caso_table_and_more', '2026-06-13 20:07:39.528816+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (22, 'gestion_casos', '0004_alter_notificacion_options_and_more', '2026-06-13 20:19:51.631061+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (23, 'gestion_casos', '0005_historialusuario', '2026-06-13 21:44:22.218487+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (24, 'gestion_casos', '0006_documentoinstitucional', '2026-09-01 05:27:49.789205+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (25, 'gestion_casos', '0007_sesionactiva', '2026-09-01 05:27:49.813325+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (26, 'gestion_casos', '0008_documentoinstitucional_checksum_sha256_and_more', '2026-10-12 04:50:58.659026+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (27, 'gestion_casos', '0009_reglainstitucional_umbral_anotaciones', '2026-10-12 04:50:59.447267+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (28, 'gestion_casos', '0010_notificacion_evento_tipo_and_more', '2026-10-12 04:51:01.48325+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (29, 'gestion_casos', '0011_reglainstitucional_disposicion_verificada', '2026-10-12 06:23:15.726542+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (30, 'gestion_casos', '0012_regla_tipo_medida_version_fuente', '2026-10-12 06:23:17.557903+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (31, 'gestion_casos', '0013_historialimportacionestudiantes', '2026-10-12 19:30:45.451858+00');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (32, 'gestion_casos', '0014_solicitudcaso', '2026-10-12 21:27:44.303264+00');


--
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('q2iuf0fjj06gszqbeanepl0zhpev23u7', '.eJyrViotLk0sysyPz0xRsjI00YHz8_Jzk4pSlayUXBLzMlNzEhXCUovSE4sSlRBKivJzgPIBzvl5ZZllqXnJmciSyflFRan5QPkUiH69Moh-h-T8nNT0zHy95BylWgBVTS3H:1wYAPd:Sj-0hruTjRWzKhtg7eG0M-bMqCUb6LuWLKOdOwFAMFI', '2026-06-26 22:31:41.034065+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('10xgqlmrqe4d67mynhws81mbskr8g30f', '.eJxNyzEOwjAQRNGroK1RlECXChoOwAUiExtrJa8HjeMKcXdWFEA5-m-e0lsPVCwaZZ6m_XdX2I1JZrkiUjN2lwKmJj9BFM_naFq1bQwR_KsryAQH9H_GcP_cD-N4PGULWoYV5vxBtcRFa_bqfGNPrzfdNDYp:1wYvXM:NnWh-jyD4Ia7kG-hx-1DlI7fOO6ragR5nka70ENuQ-o', '2026-06-29 00:50:48.129129+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('4517ul67lr2lfp2c8i9m4mfsg2g0ruer', '.eJyrViotLk0sysyPz0xRsjLUgXPz8nOTilKVrJSC8lOKMtPzFRxTcjPzMotLihJT8ouUEAqL8nOAqnDJJucXFaXmAxUkghQ4JOfnpKZn5usl5yjVAgDe1iz1:1wXXcQ:OVirJlwdlV1Nub1bSzHjugpvwz_Tn1Gh2R3gFpOKQTo', '2026-06-25 05:06:18.408136+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('s92woyn321q11cxyqhz27ompvmi0g7yq', '.eJyrViotLk0sysyPz0xRsjLUgXPz8nOTilKVrJSC8lOKMtPzFRxTcjPzMotLihJT8ouUEAqL8nOAqnDJJucXFaXmAxUkghQ4JOfnpKZn5usl5yjVAgDe1iz1:1wXght:FCSwmCkSSkF2mZb8LPid17KY7-A_rddyC3vXIU01BRg', '2026-06-25 14:48:33.499021+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('g7g1pv9ae0v0pj2wvlj6aozx8ytewmbm', '.eJxNyzEOwjAQRNGroK1RlECXChoOwAUiExtrJa8HjeMKcXdWFEA5-m-e0lsPVCwaZZ6m_XdX2I1JZrkiUjN2lwKmJj9BFM_naFq1bQwR_KsryAQH9H_GcP_cD-N4PGULWoYV5vxBtcRFa_bqfGNPrzfdNDYp:1x1Gw9:JXREQvPO5Y6zF8rZOVGOWTGS7Vr_IW_mPqxgMr0fnX4', '2026-09-15 05:21:33.238413+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('41lo6i30lcctnv316rz5q9ntjlk6x5w2', '.eJxNy7EKAjEQhOFXkdRyYOlVWlr5CMeaLDJwycps0ii--62NWg7_N680fAhhC0qaD8f9dzerN2qa08UF4rsrO57p12lrxHOpaPBOKca_mo1UC4DJPscsYeyEvNooU7Ya9kFU5YJ2p3rYzqHvDenXNSg:1x46zF:iSoNpyX0QhA70CjZph2QCl1DWvNpm2IakYY8jOlpLMA', '2026-09-23 01:20:29.072518+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('g080j9jc4hjw4310ximvciz3p5lhiv5d', '.eJxNy7EKAjEQhOFXkdRyYOlVWlr5CMeaLDJwycps0ii--62NWg7_N680fAhhC0qaD8f9dzerN2qa08UF4rsrO57p12lrxHOpaPBOKca_mo1UC4DJPscsYeyEvNooU7Ya9kFU5YJ2p3rYzqHvDenXNSg:1x47PD:4PUTQTHqJC8FNI12SAz4cNWiHNx8BKOlqRG4lJfJfL4', '2026-09-23 01:47:19.121421+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('8lxs6f6xygeyl5miv6anuzg39fqtbl28', '.eJxNi7EKwkAQBX8lXC1BLFMpWFn5B2GTfScHm1t559kE_90rxKQcZmYNtVRh8jFpGE7Hw5-zLxMRhnCVnGDdxd5CUQ9bQrfm7_SI4uxuiNjZ2Ul4C7SX3ztLedHPVbISZYKZ99DapifTAo4pP5poUxQr-HwBkfQ5lQ:1x5vXx:ej0757Zg42jjirTv6A8RIdEaY_YNfCl_eLPRJRXhunA', '2026-09-28 01:31:49.056264+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('bffsjw71uxy5fd57vqzuobfq8x87duns', '.eJxNy7EKAjEQhOFXka3lwNKrtLTyEY41iTKQZGX20ii-u2ujlsP_zVOGDyVsQZZ5t99-d7d2YZFZTq5Q35y54iG_TqsRj7mhw1dqNv7VZGSxAJjsc0waxg5I1UaekrWwd6IVLug3Fg971erl9QYeuDVz:1x7CDr:0nPIuu6UI9uE9vuhhOQ92jpUQ-Lf9QG_htrwQ_I-DJU', '2026-10-01 13:32:19.100238+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('vfoe301e323gyuoi4j71ejc8xsbmerm2', '.eJxNy7EKwkAQhOFXka3FwkpSCVZWPkJYN2tY2LsJc8ZGfHevipbD_81b1rYqA2NMMhxP-21XlDtdBrm1l-aE3UWpZoEM-SkiO7nWtrg9wb9iIB09ArY9z3PRyIOhdLkwinOMOtNblw_N5p8vHR41QA:1xD7Dt:ACFtIct_QtybE4KMOrufcbbf7w0rnkJzcBifNuT6b40', '2026-10-17 21:24:49.302979+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('9te79mmyspaad8x0opebx2cjf66kl73c', '.eJxNyrEKwlAMRuFXkcwiUhGhk44OPkNJe2MJ3DTy53YqvruZ1PFwvo3WWBnqgxbqu9P-24vbCKGeHtyUY3cfGWD6AXjNeyumi0YDF8ffnRwQT2Dc8gonm4-Xc3edjbUeJrfUL6gJhlyQSP3kGvL-AJmeNbU:1xD7He:ztC5hYUo1dRIwBXs5Y3wu31XtA1zFp4vt1oGzHd9tmg', '2026-10-17 21:28:42.980554+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('mplc86ksj98srbcep0wu7wbqsngovo0i', '.eJxNyrEKwjAUheFXKXcupSI4ZHITnHwAoaTpSYkkOeGGLC2-uwiijj__t0urzWrgFBYxx1P_7cw0K8TIDYuyuzBv9zaOOERs8mPK-DZKj0rtrvD4u46qoBgp2jDboXzcAx5nx4g1cHBM0kvRkKBTyKuiUoy3seL5Au3yOgE:1xGjUU:TW3MtVEEDobC4OR-aS-l-esA9ijBOqmsGqKp0-PVvu0', '2026-10-27 20:52:54.752909+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('1fjk47pggyn7b4gz77xgr6hoa71xitbz', '.eJxNy7EOwjAMhOFXQZ5RB7p1KiMDz1A5iaksJXF1bqaKdydigI6n_7uDmjeG2qKJptt4_e1qJUBooifvyn55BAaY_gCWe72nolV9ByfDqUYDxDoo3_uwoUngOVqWVW2IudsNWgSL1hXi3b44u7w_PS81bw:1x9nLG:QzuflX45LX9C9Ufztyldg6uhYhKWV1DKQVo20JUWVnw', '2026-10-08 17:34:42.646011+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('go7hhsbglr6fca1lm8p0g173a8a7uqut', '.eJxNyzEKAkEMheGryNSyhWCzleIBPMKSnUQJZBJ549iIdzfVavl43_8uow-CxqJc5sNxv22PtkLKXK79RcaxuxCoVg3T8lMIS3Lmpq79CeLA31sDkEgQU93qmlDgdBrkDOmrmMUkPDJ8QJtgUb_nkeGNrMvnC28LPOQ:1xDBfB:_W5ajvbgngz0S6Nkgm74xiZOrgUlQK_PT_oRUXSZeo4', '2026-10-18 02:09:17.509841+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('71jemtuurnwr3rvtbpxseukjbpgujg8t', '.eJxNyrEKwlAMRuFXkcwiUhGhk44OPkNJe2MJ3DTy53YqvruZ1PFwvo3WWBnqgxbqu9P-24vbCKGeHtyUY3cfGWD6AXjNeyumi0YDF8ffnRwQT2Dc8gonm4-Xc3edjbUeJrfUL6gJhlyQSP3kGvL-AJmeNbU:1xDCUH:DuOb0t_UQcI9AjGGfQjyZkbEuIeBHDXzyQcbTXyT154', '2026-10-18 03:02:05.459522+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('d2p33jqytqag0eq53gb7ju9a9xdjlyt7', '.eJxNyrEKwlAMRuFXkcwiUhGhk44OPkNJe2MJ3DTy53YqvruZ1PFwvo3WWBnqgxbqu9P-24vbCKGeHtyUY3cfGWD6AXjNeyumi0YDF8ffnRwQT2Dc8gonm4-Xc3edjbUeJrfUL6gJhlyQSP3kGvL-AJmeNbU:1x9rIj:gN6yYWZFNaQzqp-kNaUiFbrnKHNTrpZuALH5ivNdPQY', '2026-10-08 21:48:21.917365+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('660j3k3on7c75sh6i59ufs7b780ndsd7', '.eJxNyrEKwlAMRuFXkcwiUhGhk44OPkNJe2MJ3DTy53YqvruZ1PFwvo3WWBnqgxbqu9P-24vbCKGeHtyUY3cfGWD6AXjNeyumi0YDF8ffnRwQT2Dc8gonm4-Xc3edjbUeJrfUL6gJhlyQSP3kGvL-AJmeNbU:1xAzub:W2cUwU444QzQcqRYmN7xEfAekxtI9nZmDA_0wTyfTsg', '2026-10-12 01:12:09.457379+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('n39oyfpufonhgs7vsi0k82blrlgwnus2', '.eJxNy0EKwjAUhOGrlLeWUhFcZOVOcOUBhJKmkxJJ8sKUbCre3QiiLof_m4fUtVoGHcMs5nDcfXfWNBFi5IqZ2p01b7c6DNhHbPJj1Pg2VI9V2V3g8VedktAGCism25ePuzd2chqxBO2dpnYpDAkcQ17YhBhv44rnC-3yOgE:1xDEKK:oHGvMZ06naBgoGOHZDnM25jvhU02XEEjOMCzCN3WsNQ', '2026-10-18 04:59:56.329899+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('iccgh9izvrjq7rk4fjia6kp7vdytlr5u', '.eJxNyrEKwlAMRuFXkcwiUhGhk44OPkNJe2MJ3DTy53YqvruZ1PFwvo3WWBnqgxbqu9P-24vbCKGeHtyUY3cfGWD6AXjNeyumi0YDF8ffnRwQT2Dc8gonm4-Xc3edjbUeJrfUL6gJhlyQSP3kGvL-AJmeNbU:1xDEMD:R1grvU_5GvtgDHpnMVs5v1MTtTI38tshZml4uh_mUJc', '2026-10-18 05:01:53.146894+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('3r8fbhko50yggnpwwp8w4giyz4nml3k2', '.eJxNzLEOwjAQA9BfqW5GDIgpExIbC_xBdVyv1UlJjRzCgvh3MhVGy89-S6tNGRhjknQ47ra8otzpkuRaX5onDGelmgVyyE8RuZMbMXsFh4vP_tcaSEcHgG3r01I08t5QunwwinOMdWE_kPRk888Xqgk2JA:1xBEDI:8xWs6jlFw_Yonr3mjVgDFqOOsX1VAF-GE010i_Q6Vmo', '2026-10-12 16:28:24.782271+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('nza3kt2qi8p1pqs0h1pu99ntylmndkxw', '.eJxNyrEKwlAMRuFXkcwiUhGhk44OPkNJe2MJ3DTy53YqvruZ1PFwvo3WWBnqgxbqu9P-24vbCKGeHtyUY3cfGWD6AXjNeyumi0YDF8ffnRwQT2Dc8gonm4-Xc3edjbUeJrfUL6gJhlyQSP3kGvL-AJmeNbU:1xBEl6:ZZyvPvQKuQI3fS5VQgM2eMJ53qD3KGDql5_c6w0gr0E', '2026-10-12 17:03:20.102424+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('9q5pe6zy6862m07w22nsg04bv545slf3', '.eJxNy0EKwjAUhOGrlLeWUhFcZOVOcOUBhJKmkxJJ8sKUbCre3QiiLof_m4fUtVoGHcMs5nDcfXfWNBFi5IqZ2p01b7c6DNhHbPJj1Pg2VI9V2V3g8VedktAGCism25ePuzd2chqxBO2dpnYpDAkcQ17YhBhv44rnC-3yOgE:1xDRPl:Fb8YJZR8LJiW3oFZQxY2adCWjgQcl-PUiM4r-66ycGo', '2026-10-18 18:58:25.363068+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('ypum3zx77mmk44tsj7jo0k65y6b85p3g', '.eJxNyrEKwlAMRuFXkcwiUhGhk44OPkNJe2MJ3DTy53YqvruZ1PFwvo3WWBnqgxbqu9P-24vbCKGeHtyUY3cfGWD6AXjNeyumi0YDF8ffnRwQT2Dc8gonm4-Xc3edjbUeJrfUL6gJhlyQSP3kGvL-AJmeNbU:1xBEmV:UewdS6MFV1-O-Qhvt8qKeHtowFPKf5aaLW1MPeTGWCw', '2026-10-12 17:04:47.346257+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('h3vvto6t207aj7stwrngricbs03e89ry', '.eJxNy7EKAjEQhOFXka3lwNKrtLTyEY41iTKQZGX20ii-u2ujlsP_zVOGDyVsQZZ5t99-d7d2YZFZTq5Q35y54iG_TqsRj7mhw1dqNv7VZGSxAJjsc0waxg5I1UaekrWwd6IVLug3Fg971erl9QYeuDVz:1xDVdS:p7XvDsVXcY6ZIlGGke4MQqvJ_8t6GDKHt9qOD7bxcC4', '2026-10-18 23:28:50.526585+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('c9qvkhy0g7obz9e3eml50fvsqlhqqoak', '.eJxNyzEKAkEMheGryNSyhWCzleIBPMKSnUQJZBJ549iIdzfVavl43_8uow-CxqJc5sNxv22PtkLKXK79RcaxuxCoVg3T8lMIS3Lmpq79CeLA31sDkEgQU93qmlDgdBrkDOmrmMUkPDJ8QJtgUb_nkeGNrMvnC28LPOQ:1xDXpj:BK8JqyUI5lNJuh4ACtPhg4jvngx1GdF9kzDom-VXsqg', '2026-10-19 01:49:39.179037+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('x3xak81wbqqawfen5eispy735rvbo2yy', '.eJxNyrEKwlAMRuFXkcwiUhGhk44OPkNJe2MJ3DTy53YqvruZ1PFwvo3WWBnqgxbqu9P-24vbCKGeHtyUY3cfGWD6AXjNeyumi0YDF8ffnRwQT2Dc8gonm4-Xc3edjbUeJrfUL6gJhlyQSP3kGvL-AJmeNbU:1xBdXs:BRBs-KjNCuTe5eBQSerNfyJ1IHzix_pvgb3Wu1NiTzM', '2026-10-13 19:31:20.456284+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('g3lg91ur54dj5gclzeiptifu3ru9rp50', '.eJxNy7EKAjEQhOFXka3lwNKrtLTyEY41iTKQZGX20ii-u2ujlsP_zVOGDyVsQZZ5t99-d7d2YZFZTq5Q35y54iG_TqsRj7mhw1dqNv7VZGSxAJjsc0waxg5I1UaekrWwd6IVLug3Fg971erl9QYeuDVz:1xDkM1:DcUlD4rJ0LNwo1JQ4M6j_-HHe-Vq5IQYfLyeEcvM2dw', '2026-10-19 15:11:49.229767+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('db2ncjw2mcwb73fg7a5dewf0qkewbh23', '.eJxNyrEKwlAMRuFXkcwiUhGhk44OPkNJe2MJ3DTy53YqvruZ1PFwvo3WWBnqgxbqu9P-24vbCKGeHtyUY3cfGWD6AXjNeyumi0YDF8ffnRwQT2Dc8gonm4-Xc3edjbUeJrfUL6gJhlyQSP3kGvL-AJmeNbU:1xDl4E:cZ3xeh2eXdvwjDLW2OINIg6QScr5FLTrAQj0W75nL0Q', '2026-10-19 15:57:30.897211+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('a95vo6p1q6sou4wdoywzr7jvfk2na6nl', '.eJxNy7EKAjEQhOFXka3lwNKrtLTyEY41iTKQZGX20ii-u2ujlsP_zVOGDyVsQZZ5t99-d7d2YZFZTq5Q35y54iG_TqsRj7mhw1dqNv7VZGSxAJjsc0waxg5I1UaekrWwd6IVLug3Fg971erl9QYeuDVz:1xDl78:m00r6-R5TaJmTrKthLhxjmelsbymDkb-dIjY6Iw6fRY', '2026-10-19 16:00:30.507105+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('kc0fu3xm40zx4tl973po6eutpls6aky3', '.eJxNy7EKAjEQhOFXka3lwNKrtLTyEY41iTKQZGX20ii-u2ujlsP_zVOGDyVsQZZ5t99-d7d2YZFZTq5Q35y54iG_TqsRj7mhw1dqNv7VZGSxAJjsc0waxg5I1UaekrWwd6IVLug3Fg971erl9QYeuDVz:1xDqv7:a8B0pCI5WuV-bOGxeCJWpzP_2Jl2LNNMMy7m2BEggIE', '2026-10-19 22:12:29.517968+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('prnjelmgjzjh6w5jatja2oenowdmc28l', '.eJxNy7EKAjEQhOFXka3lwNKrtLTyEY41iTKQZGX20ii-u2ujlsP_zVOGDyVsQZZ5t99-d7d2YZFZTq5Q35y54iG_TqsRj7mhw1dqNv7VZGSxAJjsc0waxg5I1UaekrWwd6IVLug3Fg971erl9QYeuDVz:1xDqvw:8V7Nyxbj6NZfCgFJULW9Le72jcoIhrX181sYTHjkfY0', '2026-10-19 22:13:20.887549+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('wnyy8l75z2aq59jh5vzdwyah2iqw9278', '.eJxNy7EKAjEQhOFXka3lwNKrtLTyEY41iTKQZGX20ii-u2ujlsP_zVOGDyVsQZZ5t99-d7d2YZFZTq5Q35y54iG_TqsRj7mhw1dqNv7VZGSxAJjsc0waxg5I1UaekrWwd6IVLug3Fg971erl9QYeuDVz:1xDqyp:wULqUKYLX0ENj3gULf_hRl-SRywjgiZsoV86p7meg0I', '2026-10-19 22:16:19.436711+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('n6slqh7nijwn70p493ziix8v2o3w8zjc', '.eJxNy7EKAjEQhOFXka3lwNKrtLTyEY41iTKQZGX20ii-u2ujlsP_zVOGDyVsQZZ5t99-d7d2YZFZTq5Q35y54iG_TqsRj7mhw1dqNv7VZGSxAJjsc0waxg5I1UaekrWwd6IVLug3Fg971erl9QYeuDVz:1xDqzT:dNRZt6i4A4y25utGwpZvvbehsVWlvQ_Ysy6g40RAm4M', '2026-10-19 22:16:59.682048+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('kya5oopdzymctkpp29jqhrqfjm62ivxd', '.eJxNyrEKwkAQRdFfkVcHkYgIW2lp4TeESTIuAzs78nZTif9up5aXc1_Y2ia0mGxFGo_Dt2v4TEXCXbpJ291mIQW_gVGQcF3dqrVOWYN_ugSpgQSX3jpV3Go-nE_jJbtY2S_hGPCkuXKymqktkB5Smr4_mZ41tQ:1xGLXc:c3qXWARAJCtNtq5r0-DIW9l1J5ndBIyLf_TUo-JXtYc', '2026-10-26 19:18:32.878096+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('m3yojdt1v68o265chvual2quq8q0nwzb', '.eJxNyrEKwkAQRdFfkVcHkYgIW2lp4TeESTIuAzs78nZTif9up5aXc1_Y2ia0mGxFGo_Dt2v4TEXCXbpJ291mIQW_gVGQcF3dqrVOWYN_ugSpgQSX3jpV3Go-nE_jJbtY2S_hGPCkuXKymqktkB5Smr4_mZ41tQ:1xGNZJ:tU0cN0spS_xstTtPIPykwdF8u18nnhTnLnfLZE77V0E', '2026-10-26 21:28:25.563048+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('bffzwpt9mxu9w9lopa6agqc5v1az2z75', '.eJxNy7EKAjEQhOFXka3lwNKrtLTyEY41iTKQZGX20ii-u2ujlsP_zVOGDyVsQZZ5t99-d7d2YZFZTq5Q35y54iG_TqsRj7mhw1dqNv7VZGSxAJjsc0waxg5I1UaekrWwd6IVLug3Fg971erl9QYeuDVz:1xDr09:edFwu1Ay7h_zIgzFxQX29Smt27IVtUeIZevbLkRJVjk', '2026-10-19 22:17:41.522449+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('n6q4asb304lkey3tfpz4thh5mgpcb0us', '.eJxNy7EKAjEQhOFXka3lwNKrtLTyEY41iTKQZGX20ii-u2ujlsP_zVOGDyVsQZZ5t99-d7d2YZFZTq5Q35y54iG_TqsRj7mhw1dqNv7VZGSxAJjsc0waxg5I1UaekrWwd6IVLug3Fg971erl9QYeuDVz:1xDr0U:IxMwB_DcXp2DT1bUqAfyUJzzpAr92Y7MUdN99OhmWBg', '2026-10-19 22:18:02.009592+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('0r7guf22jrk7b2tgso6e4j65buajkvbe', '.eJxNy7EKAjEQhOFXka3lwNKrtLTyEY41iTKQZGX20ii-u2ujlsP_zVOGDyVsQZZ5t99-d7d2YZFZTq5Q35y54iG_TqsRj7mhw1dqNv7VZGSxAJjsc0waxg5I1UaekrWwd6IVLug3Fg971erl9QYeuDVz:1xDr0o:JiD5weaWtuv5Fpu9ZRjAu0nb4uxTR-Y_4pwjCalHQbA', '2026-10-19 22:18:22.528315+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('nmho9ynobsz7ffu6we3yjwvpppmxo242', '.eJxNizEKAkEMRa8iqZctBJupFA_gEZbsJEogM5GfHRvx7nar5eO996aRg2GxmFA5nqade7QVSoVu-WKXOFwZXKuFG_0qhFOhizTrlhtYAn-2BqBBhWKu-10tN0Xn8-Au0FzVPWaVQRM9YU2xWH9AM6jc2VM_X28LPOQ:1xGjai:3mFljm5ARLKUR5DW7eVB2Txuy8Gl7b45rLN6bfmPwSA', '2026-10-27 20:59:20.378592+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('wi6baav6w6oximl390cr0uva0m6axiut', '.eJxNy7EKAjEQhOFXka3lwNKrtLTyEY41iTKQZGX20ii-u2ujlsP_zVOGDyVsQZZ5t99-d7d2YZFZTq5Q35y54iG_TqsRj7mhw1dqNv7VZGSxAJjsc0waxg5I1UaekrWwd6IVLug3Fg971erl9QYeuDVz:1xDr1d:T5mQuEBcdKx__iJkl9lUtEJmnZJqA5T_1rdGY9GVu2Q', '2026-10-19 22:19:13.898689+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('raxamspo1i8nb9i55cgqnr5hxcyp2kkn', '.eJxNy7EOwjAMhOFXQZ5RVUY6wcjECyBVJjHIUhKjc7MU8e6YBRhP_3dP6t4ZarNmmnb77Xc3q1cITXRyvvRxlMy-OWPRlX4IVkIcc9WmvoCz4a8mA8QC6GCfY-IwdtBUrOchWQ37gFbBrO0O8bA3Li6vNw__NwQ:1xDri5:KgEfHY42VDZOxzCKEjflax7knp9J21F2STMMA7xNT6g', '2026-10-19 23:03:05.158969+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('ntw4dejsha5hvxlntmzjpgc0qsjfwvfd', '.eJxNy7EOwjAMhOFXQZ5RVUY6wcjECyBVJjHIUhKjc7MU8e6YBRhP_3dP6t4ZarNmmnb77Xc3q1cITXRyvvRxlMy-OWPRlX4IVkIcc9WmvoCz4a8mA8QC6GCfY-IwdtBUrOchWQ37gFbBrO0O8bA3Li6vNw__NwQ:1xExvq:802IzsWYHyD2Ase6mUajm4zf4AhdwD_TQAcmzPSK1sc', '2026-10-22 23:53:50.932858+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('gorplx4cot93tdvn8ryelwtqylcnjaxn', '.eJxNyrEKwlAMRuFXkcwiUhGhk44OPkNJe2MJ3DTy53YqvruZ1PFwvo3WWBnqgxbqu9P-24vbCKGeHtyUY3cfGWD6AXjNeyumi0YDF8ffnRwQT2Dc8gonm4-Xc3edjbUeJrfUL6gJhlyQSP3kGvL-AJmeNbU:1xEy7L:cdhxKXjkSrpGQrgjgyAJVM-00KJcsIBweUGqYT3XjJQ', '2026-10-23 00:05:43.332536+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('43gncw4kapvm9wyislnylj84yb3vvxr6', '.eJxNyrEKwkAQRdFfkVcHkYgIW2lp4TeESTIuAzs78nZTif9up5aXc1_Y2ia0mGxFGo_Dt2v4TEXCXbpJ291mIQW_gVGQcF3dqrVOWYN_ugSpgQSX3jpV3Go-nE_jJbtY2S_hGPCkuXKymqktkB5Smr4_mZ41tQ:1xLrv2:pJSvUypAbB2-dhEXLNABzWaTQ6fPukJOjMTrET7mOhY', '2026-11-11 00:53:32.897624+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('xrpzzsiyuej8aw8vi9ijvsf0l2tn57sn', '.eJxNy7EOwjAMhOFXQZ5RVUY6wcjECyBVJjHIUhKjc7MU8e6YBRhP_3dP6t4ZarNmmnb77Xc3q1cITXRyvvRxlMy-OWPRlX4IVkIcc9WmvoCz4a8mA8QC6GCfY-IwdtBUrOchWQ37gFbBrO0O8bA3Li6vNw__NwQ:1xPNMg:aGNVOQJuIN_6joOx_9o8paH6gID2l_0F3OtF2QtqSdI', '2026-11-20 17:04:34.55744+00');
INSERT INTO public.django_session (session_key, session_data, expire_date) VALUES ('2g20hh8cw7vlprcntew6akrrz56ss5te', '.eJxNyzEKAkEMheGryNSyhWCzleIBPMKSnUQJZBJ549iIdzfVavl43_8uow-CxqJc5sNxv22PtkLKXK79RcaxuxCoVg3T8lMIS3Lmpq79CeLA31sDkEgQU93qmlDgdBrkDOmrmMUkPDJ8QJtgUb_nkeGNrMvnC28LPOQ:1xPVrY:HCV7Hpal0DCYujmjah3lklLYQ1N2Lk559Pb7_u4_qZc', '2026-11-21 02:09:00.241352+00');


--
-- Data for Name: historial_accion_seguimiento; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: historial_importacion_estudiantes; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.historial_importacion_estudiantes (id, archivo, usuario_id_importo, usuario_correo_importo, realizado_en, alumnos_agregados, duplicados_detectados, filas_omitidas) VALUES (1, 'plantilla_importacion_alumnos_RF75.xlsx', 25, 'o.caracciolicisterna@uandresbello.edu', '2026-11-16 01:59:35.842169+00', '[]', '[]', 34);


--
-- Data for Name: historial_notificacion; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (1, 'espera', 'Notificación creada al registrar un caso.', '2026-10-13 21:01:22.804993+00', 36, 65);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (2, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-13 21:01:23.915708+00', 25, 66);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (3, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-13 21:01:24.838966+00', 25, 67);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (4, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-13 21:01:25.756925+00', 25, 68);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (5, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-13 21:01:26.680956+00', 25, 69);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (6, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-13 21:01:27.61167+00', 25, 70);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (7, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-13 21:01:28.533881+00', 25, 71);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (8, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-13 21:01:29.457352+00', 25, 72);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (9, 'espera', 'Notificación creada al registrar un caso.', '2026-10-14 16:42:20.442552+00', 19, 73);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (10, 'espera', 'Notificación creada al registrar un caso.', '2026-10-14 16:46:31.204374+00', 37, 74);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (11, 'espera', 'Notificación creada al registrar un caso.', '2026-10-15 15:04:29.779981+00', 19, 75);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (12, 'espera', 'Notificación creada al registrar un caso.', '2026-10-16 12:12:51.758281+00', 19, 76);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (13, 'espera', 'Notificación creada al registrar un caso.', '2026-10-16 19:05:23.48924+00', 19, 77);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (14, 'espera', 'Notificación creada al registrar un caso.', '2026-10-19 22:42:36.559129+00', 19, 78);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (39, 'espera', 'Notificación creada al registrar un caso.', '2026-10-28 01:02:08.488862+00', 19, 103);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (40, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:02:09.738452+00', 19, 104);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (41, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:02:10.790747+00', 19, 105);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (42, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:02:11.817861+00', 19, 106);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (43, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:02:12.840792+00', 19, 107);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (44, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:02:13.888317+00', 19, 108);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (45, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:02:14.946232+00', 19, 109);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (46, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:02:15.988171+00', 19, 110);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (47, 'espera', 'Notificación creada al registrar un caso.', '2026-10-28 01:06:54.744722+00', 19, 111);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (48, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:06:55.992185+00', 19, 112);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (49, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:06:57.038177+00', 19, 113);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (50, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:06:58.075136+00', 19, 114);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (51, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:06:59.111955+00', 19, 115);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (52, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:07:00.152131+00', 19, 116);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (53, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:07:01.191273+00', 19, 117);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (54, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:07:02.265858+00', 19, 118);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (55, 'espera', 'Notificación creada al registrar un caso.', '2026-10-28 01:11:51.854355+00', 19, 119);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (56, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:11:53.101111+00', 19, 120);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (57, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:11:54.137694+00', 19, 121);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (58, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:11:55.177764+00', 19, 122);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (59, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:11:56.214732+00', 19, 123);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (60, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:11:57.254519+00', 19, 124);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (61, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:11:58.293073+00', 19, 125);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (62, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:11:59.344568+00', 19, 126);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (63, 'espera', 'Notificación creada al registrar un caso.', '2026-10-28 01:15:56.732662+00', 19, 127);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (64, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:15:57.95539+00', 19, 128);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (65, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:15:58.963329+00', 19, 129);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (66, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:15:59.981387+00', 19, 130);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (67, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:16:00.988866+00', 19, 131);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (68, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:16:02.003016+00', 19, 132);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (69, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:16:03.016725+00', 19, 133);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (70, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-10-28 01:16:04.027286+00', 19, 134);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (71, 'espera', 'Notificación creada al registrar un caso.', '2026-11-07 00:49:40.110794+00', 23, 135);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (72, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-07 00:49:41.342488+00', 23, 136);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (73, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-07 00:49:42.66001+00', 23, 137);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (74, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-07 00:49:43.898056+00', 23, 138);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (75, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-07 00:49:45.117059+00', 23, 139);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (76, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-07 00:49:46.299362+00', 23, 140);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (77, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-07 00:49:47.544097+00', 23, 141);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (78, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-07 00:49:48.585612+00', 23, 142);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (79, 'espera', 'Notificación creada al registrar un caso.', '2026-11-14 03:02:47.557865+00', 28, 143);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (80, 'espera', 'Notificación creada al registrar un caso.', '2026-11-14 03:04:34.744897+00', 28, 144);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (81, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 03:04:35.857446+00', 28, 145);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (82, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 03:04:36.780226+00', 28, 146);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (83, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 03:04:37.702868+00', 28, 147);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (84, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 03:04:38.619202+00', 28, 148);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (85, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 03:04:39.541529+00', 28, 149);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (86, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 03:04:40.46295+00', 28, 150);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (87, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 03:04:41.383687+00', 28, 151);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (88, 'espera', 'Notificación creada al registrar un caso.', '2026-11-14 03:25:44.203379+00', 36, 152);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (89, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 03:25:45.360956+00', 19, 153);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (90, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 03:25:46.230253+00', 19, 154);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (91, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 03:25:47.111627+00', 19, 155);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (92, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 03:25:47.995768+00', 19, 156);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (93, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 03:25:48.861165+00', 19, 157);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (94, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 03:25:49.728562+00', 19, 158);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (95, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 03:25:50.597626+00', 19, 159);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (98, 'espera', 'Notificación creada al registrar un caso.', '2026-11-14 20:14:52.905769+00', 25, 162);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (99, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:14:53.940829+00', 25, 163);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (100, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:14:54.793567+00', 25, 164);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (101, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:14:55.648362+00', 25, 165);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (102, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:14:56.503733+00', 25, 166);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (103, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:14:57.360726+00', 25, 167);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (104, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:14:58.216014+00', 25, 168);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (105, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:14:59.069524+00', 25, 169);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (106, 'espera', 'Notificación creada al registrar un caso.', '2026-11-14 20:20:52.931721+00', 25, 170);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (107, 'espera', 'Notificación creada al registrar un caso.', '2026-11-14 20:24:06.857687+00', 25, 171);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (108, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:24:07.928905+00', 25, 172);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (109, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:24:08.817483+00', 25, 173);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (110, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:24:09.704672+00', 25, 174);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (111, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:24:10.593843+00', 25, 175);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (112, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:24:11.482789+00', 25, 176);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (113, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:24:12.376168+00', 25, 177);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (114, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:24:13.266628+00', 25, 178);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (115, 'espera', 'Notificación creada al registrar un caso.', '2026-11-14 20:31:09.350862+00', 25, 179);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (116, 'espera', 'Notificación creada al registrar un caso.', '2026-11-14 20:31:38.905194+00', 25, 180);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (117, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:31:39.969732+00', 25, 181);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (118, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:31:40.852114+00', 25, 182);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (119, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:31:41.735727+00', 25, 183);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (120, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:31:42.621024+00', 25, 184);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (121, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:31:43.503074+00', 25, 185);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (122, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:31:44.386622+00', 25, 186);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (123, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:31:45.267557+00', 25, 187);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (124, 'espera', 'Notificación creada al registrar un caso.', '2026-11-14 20:34:07.083626+00', 25, 188);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (125, 'espera', 'Notificación creada al registrar un caso.', '2026-11-14 20:34:44.566454+00', 25, 189);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (126, 'espera', 'Notificación creada al registrar un caso.', '2026-11-14 20:35:31.910419+00', 25, 190);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (127, 'espera', 'Notificación creada al registrar un caso.', '2026-11-14 20:36:57.617943+00', 25, 191);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (128, 'espera', 'Notificación creada al registrar un caso.', '2026-11-14 20:37:29.046591+00', 25, 192);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (129, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-11-14 20:37:30.13928+00', 25, 193);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (130, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-11-14 20:37:31.046331+00', 25, 194);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (131, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-11-14 20:37:31.951692+00', 25, 195);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (132, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-11-14 20:37:32.858199+00', 25, 196);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (133, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-11-14 20:37:33.764001+00', 25, 197);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (134, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-11-14 20:37:34.670294+00', 25, 198);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (135, 'espera', 'Alerta creada por el registro de un caso gravísimo.', '2026-11-14 20:37:35.580464+00', 25, 199);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (136, 'espera', 'Notificación creada al registrar un caso.', '2026-11-14 20:39:23.641801+00', 25, 215);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (137, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:39:25.048872+00', 25, 216);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (138, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:39:25.970428+00', 25, 217);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (139, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:39:26.894969+00', 25, 218);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (140, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:39:27.814467+00', 25, 219);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (141, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:39:28.735631+00', 25, 220);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (142, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:39:29.675477+00', 25, 221);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (143, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-14 20:39:30.593508+00', 25, 222);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (147, 'espera', 'Notificación creada al modificar un caso.', '2026-11-15 12:29:26.269838+00', 38, 226);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (148, 'espera', 'Notificación creada al modificar un caso.', '2026-11-15 12:35:06.593469+00', 38, 227);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (149, 'espera', 'Notificación creada al registrar un caso.', '2026-11-15 12:37:34.831356+00', 38, 228);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (150, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-15 12:37:36.01985+00', 38, 229);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (151, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-15 12:37:37.009865+00', 38, 230);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (152, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-15 12:37:38.001309+00', 38, 231);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (153, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-15 12:37:38.990925+00', 38, 232);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (154, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-15 12:37:39.983326+00', 38, 233);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (155, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-15 12:37:40.969745+00', 38, 234);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (156, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-15 12:37:41.964846+00', 38, 235);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (157, 'espera', 'Alerta creada por el registro de un caso grave.', '2026-11-15 12:37:42.951695+00', 38, 236);
INSERT INTO public.historial_notificacion (id, estado, motivo, cambiado_en, cambiado_por_id, notificacion_id) VALUES (161, 'espera', 'Notificación creada al eliminar un caso de otro usuario.', '2026-11-15 15:32:49.998891+00', 25, 240);


--
-- Data for Name: historial_seguimiento_caso; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (1, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-10-13 21:01:21.46112+00', 36, 1);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (2, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-10-14 16:41:36.483847+00', 19, 2);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (3, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-10-14 16:42:18.825474+00', 19, 3);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (4, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-10-14 16:46:29.848847+00', 37, 4);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (5, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-10-15 15:04:28.077049+00', 19, 5);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (6, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-10-16 12:12:50.365005+00', 19, 6);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (7, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-10-16 19:05:21.583017+00', 19, 7);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (8, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-10-19 22:42:33.072444+00', 19, 8);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (9, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-10-19 22:42:34.30897+00', 19, 9);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (10, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-10-19 22:42:35.330595+00', 19, 10);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (14, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-10-28 01:02:07.013178+00', 19, 14);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (15, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-10-28 01:06:53.285881+00', 19, 15);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (16, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-10-28 01:11:50.380993+00', 19, 16);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (17, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-10-28 01:15:55.301661+00', 19, 17);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (18, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-11-07 00:49:37.544195+00', 23, 18);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (19, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-11-07 00:49:38.868444+00', 23, 19);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (20, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-11-14 03:02:46.317959+00', 28, 20);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (21, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-11-14 03:04:33.456625+00', 28, 21);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (22, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-11-14 03:25:42.956194+00', 36, 22);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (23, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-11-14 20:14:51.685143+00', 25, 23);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (24, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-11-14 20:20:51.686025+00', 25, 24);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (25, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-11-14 20:24:05.600954+00', 25, 25);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (26, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-11-14 20:31:08.1167+00', 25, 26);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (27, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-11-14 20:31:37.665586+00', 25, 27);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (29, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-11-14 20:34:43.281346+00', 25, 29);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (30, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-11-14 20:35:30.622208+00', 25, 30);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (31, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-11-14 20:36:56.332835+00', 25, 31);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (32, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-11-14 20:37:27.779454+00', 25, 32);
INSERT INTO public.historial_seguimiento_caso (id, estado, motivo, cambiado_en, cambiado_por_id, seguimiento_id) VALUES (33, 'abierto', 'Seguimiento creado al registrar o actualizar un caso.', '2026-11-14 20:39:22.345454+00', 25, 33);


--
-- Data for Name: historial_usuario; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (1, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #20 [caso prueba 17 historial usuarios].', '2026-06-13 22:16:15.285747+00', 11);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (2, 'Modificación', 'Modificó los registros de la bitácora del caso #20 [caso prueba 17 historial usuarios].', '2026-06-13 22:17:59.87461+00', 11);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (3, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #21 [caso prueba 18].', '2026-06-14 22:56:06.632484+00', 11);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (4, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #22 [caso de prueba 19].', '2026-06-14 23:08:29.844129+00', 11);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (5, 'Modificación', 'Modificó los registros de la bitácora del caso #22 [caso de prueba 19].', '2026-06-14 23:10:00.855674+00', 11);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (6, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #23 [caso prueba 20].', '2026-06-14 23:25:43.906778+00', 11);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (7, 'Modificación', 'Modificó los registros de la bitácora del caso #23 [caso prueba 20].', '2026-06-14 23:31:25.151998+00', 11);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (8, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #24 [Caso prueba 21].', '2026-06-14 23:37:45.623625+00', 11);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (9, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #25 [Caso prueba notificaciones].', '2026-06-14 23:54:13.823275+00', 11);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (10, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #26 [caso prueba 22].', '2026-06-14 23:57:50.544427+00', 12);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (11, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #27 [Caso prueba 24].', '2026-06-15 00:22:18.767499+00', 11);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (12, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #28 [Batalla de aura] con 1 alumno(s) involucrado(s).', '2026-09-01 20:45:10.498796+00', 19);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (13, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #29 [Agresion Verbal al Docente] con 1 alumno(s) involucrado(s).', '2026-09-24 20:27:43.28773+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (14, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #30 [Agresion Verbal al Docente] con 1 alumno(s) involucrado(s).', '2026-09-24 20:27:49.840774+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (15, 'Eliminación', 'Eliminó el caso #29 de la bitácora de convivencia.', '2026-09-24 20:28:05.713136+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (16, 'Modificación', 'Modificó los registros de la bitácora del caso #28 [Batalla de aura].', '2026-09-28 17:17:37.70406+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (17, 'Eliminación', 'Eliminó el caso #27 de la bitácora de convivencia.', '2026-09-29 19:40:11.709531+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (18, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #31 [Copia] con 1 alumno(s) involucrado(s).', '2026-09-30 12:41:47.907716+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (19, 'Desactivación masiva', 'Desactivación masiva de 2 usuario(s): Osvaldo Caraccioli (#25), Osvaldo Caraccioli (#24).', '2026-09-30 18:31:00.102577+00', 19);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (20, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #32 [prueba de ingles ] con 1 alumno(s) involucrado(s).', '2026-10-03 19:51:55.335684+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (21, 'Modificación', 'Modificó los registros de la bitácora del caso #32 [prueba de ingles].', '2026-10-03 20:01:02.358088+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (22, 'Eliminación', 'Eliminó el caso #32 de la bitácora de convivencia.', '2026-10-03 20:01:25.602994+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (23, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #33 [alumno se salta la clase ] con 1 alumno(s) involucrado(s).', '2026-10-03 20:39:17.258864+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (24, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #34 [alumno insulta a su compañera  ] con 1 alumno(s) involucrado(s).', '2026-10-03 20:49:05.65123+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (25, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #35 [caso prueba  8] con 1 alumno(s) involucrado(s).', '2026-10-03 20:51:29.19649+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (26, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #36 [caso patio central ] con 1 alumno(s) involucrado(s).', '2026-10-03 20:52:59.588253+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (27, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #37 [retraso ] con 1 alumno(s) involucrado(s).', '2026-10-03 20:53:56.468351+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (28, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #38 [falta de respeto  ] con 1 alumno(s) involucrado(s).', '2026-10-03 20:54:50.101587+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (29, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #39 [caso10] con 1 alumno(s) involucrado(s).', '2026-10-03 20:57:27.413343+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (30, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #40 [caso 11 ] con 1 alumno(s) involucrado(s).', '2026-10-03 20:58:20.559487+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (31, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #41 [caso11 ] con 1 alumno(s) involucrado(s).', '2026-10-03 20:58:55.045355+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (32, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #42 [caso 13 ] con 1 alumno(s) involucrado(s).', '2026-10-03 21:00:10.721824+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (33, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #43 [caso 67] con 1 alumno(s) involucrado(s).', '2026-10-03 21:01:00.406232+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (34, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #44 [caso 69 ] con 1 alumno(s) involucrado(s).', '2026-10-03 21:02:11.26791+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (35, 'Eliminación masiva', 'Eliminación masiva de 1 usuario(s): Osvaldo Caraccioli (#24).', '2026-10-03 21:13:49.582581+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (36, 'Modificación', 'Modificó los registros de la bitácora del caso #28 [Batalla de aura].', '2026-10-03 21:29:53.636362+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (37, 'Modificación', 'Modificó los registros de la bitácora del caso #34 [alumno insulta a su compañera].', '2026-10-03 21:30:41.354831+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (38, 'Modificación', 'Modificó los registros de la bitácora del caso #44 [caso 69].', '2026-10-04 02:07:03.979831+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (39, 'Modificación', 'Modificó los registros de la bitácora del caso #44 [caso 69].', '2026-10-04 03:06:14.103405+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (40, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #45 [caso prueba 20] con 1 alumno(s) involucrado(s).', '2026-10-04 04:03:27.284942+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (41, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #46 [caso 21 ] con 1 alumno(s) involucrado(s).', '2026-10-04 04:04:07.886504+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (42, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #47 [caso prueba  22] con 1 alumno(s) involucrado(s).', '2026-10-04 04:05:18.491713+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (43, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #48 [caso 23 ] con 1 alumno(s) involucrado(s).', '2026-10-04 04:05:58.579505+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (44, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #49 [caso 24 ] con 1 alumno(s) involucrado(s).', '2026-10-04 04:06:57.205355+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (45, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #50 [caso 25 ] con 1 alumno(s) involucrado(s).', '2026-10-04 04:07:31.816867+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (46, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #51 [caso 26] con 1 alumno(s) involucrado(s).', '2026-10-04 04:08:18.709122+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (47, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #52 [caso 27] con 1 alumno(s) involucrado(s).', '2026-10-04 04:09:11.533222+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (48, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #53 [caso 28] con 1 alumno(s) involucrado(s).', '2026-10-04 04:09:49.955832+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (49, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #54 [caso 29] con 1 alumno(s) involucrado(s).', '2026-10-04 04:10:38.69849+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (50, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #55 [caso 30] con 1 alumno(s) involucrado(s).', '2026-10-04 04:11:22.627693+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (51, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #56 [caso 31] con 1 alumno(s) involucrado(s).', '2026-10-04 04:12:11.88276+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (52, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #57 [caso 32] con 1 alumno(s) involucrado(s).', '2026-10-04 05:02:51.434224+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (53, 'Modificación', 'Modificó los registros de la bitácora del caso #48 [caso 23].', '2026-10-05 15:54:01.169099+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (54, 'Modificación', 'Modificó los registros de la bitácora del caso #57 [caso 32e].', '2026-10-05 15:55:15.708184+00', 19);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (55, 'Modificación', 'Modificó los registros de la bitácora del caso #35 [caso prueba  8].', '2026-10-05 15:55:26.8902+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (56, 'Creación', 'Registró exitosamente una nueva bitácora de caso: #58 [Caso Isa] con 1 alumno(s) involucrado(s).', '2026-10-05 15:56:00.989757+00', 19);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (57, 'Modificación', 'Modificó los registros de la bitácora del caso #58 [Caso Isa].', '2026-10-05 16:18:06.461367+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (58, 'Modificación', 'Modificó los registros de la bitácora del caso #58 [Caso Isa].', '2026-10-11 22:22:11.280011+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (59, 'Eliminación', 'Eliminó el documento institucional "Reglamento Interno 2026" (ID 6), junto con 1 versión(es) y 316 propuesta(s) asociada(s).', '2026-10-12 06:51:02.349215+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (60, 'Eliminación', 'Eliminó el documento institucional "Reglamento Interno 2026" (ID 6), junto con 1 versión(es) y 316 propuesta(s) asociada(s).', '2026-10-12 06:51:03.779252+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (61, 'Eliminación', 'Eliminó el documento institucional "Reglamento Interno 2026" (ID 6), junto con 1 versión(es) y 316 propuesta(s) asociada(s).', '2026-10-12 06:51:04.740718+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (62, 'Eliminación', 'Eliminó el documento institucional "Reglamento Interno 2026" (ID 6), junto con 1 versión(es) y 316 propuesta(s) asociada(s).', '2026-10-12 06:51:04.824375+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (63, 'Eliminación', 'Eliminó el documento institucional "Reglamento Interno 2026" (ID 6), junto con 1 versión(es) y 316 propuesta(s) asociada(s).', '2026-10-12 06:51:05.034079+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (64, 'Eliminación', 'Eliminó el documento institucional "Reglamento Interno 2026" (ID 6), junto con 0 versión(es) y 0 propuesta(s) asociada(s).', '2026-10-12 06:51:05.788527+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (65, 'Eliminación', 'Eliminó el documento institucional "Reglamento Interno 2026" (ID 6), junto con 0 versión(es) y 0 propuesta(s) asociada(s).', '2026-10-12 06:51:05.859688+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (66, 'Eliminación', 'Eliminó el documento institucional "Reglamento Interno 2026" (ID 6), junto con 0 versión(es) y 0 propuesta(s) asociada(s).', '2026-10-12 06:51:06.150964+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (67, 'Creación', 'Registró exitosamente el caso #59 con 1 estudiante(s): Matias Urria Vera.', '2026-10-13 21:01:29.645559+00', 36);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (68, 'Aprobación de caso', 'Revisó la solicitud #1 del Profesor Jefe Pedro: Aprobada.', '2026-10-13 21:01:30.016528+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (69, 'Modificación', 'Modificó los registros del caso #58. Estudiantes: Agustin Alvarado rojas.', '2026-10-14 16:41:37.342122+00', 19);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (70, 'Creación', 'Registró exitosamente el caso #60 con 1 estudiante(s): Antonia Aguilar Vergara.', '2026-10-14 16:42:20.644235+00', 19);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (71, 'Creación', 'Registró exitosamente el caso #61 con 1 estudiante(s): Agustin Alvarado rojas.', '2026-10-14 16:46:31.404+00', 37);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (72, 'Creación', 'Registró exitosamente el caso #62 con 1 estudiante(s): Florencia Delgado Zapata.', '2026-10-15 15:04:29.981319+00', 19);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (73, 'Creación', 'Registró exitosamente el caso #63 con 1 estudiante(s): Agustin Alvarado rojas.', '2026-10-16 12:12:51.956783+00', 19);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (74, 'Creación', 'Registró exitosamente el caso #64 con 1 estudiante(s): Agustin Alvarado rojas.', '2026-10-16 19:05:23.704686+00', 19);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (75, 'Creación', 'Registró exitosamente el caso #65 con 3 estudiante(s): Antonia Aguilar Vergara, Agustin Alvarado rojas, Paulina Sepúlveda Orellana.', '2026-10-19 22:42:36.77221+00', 19);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (76, 'Creación', 'Registró exitosamente el caso #70 con 1 estudiante(s): Ignacia Figueroa Ulloa.', '2026-10-28 01:02:16.199891+00', 19);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (77, 'Creación', 'Registró exitosamente el caso #71 con 1 estudiante(s): Diego Alejandro Castillo Morales.', '2026-10-28 01:07:02.473049+00', 19);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (78, 'Creación', 'Registró exitosamente el caso #72 con 1 estudiante(s): Constanza Flores Farias.', '2026-10-28 01:11:59.553559+00', 19);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (79, 'Creación', 'Registró exitosamente el caso #73 con 1 estudiante(s): Esteban Jara Fuentealba.', '2026-10-28 01:16:04.229307+00', 19);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (80, 'Creación', 'Registró exitosamente el caso #74 con 2 estudiante(s): Vicente Flores Flores, Diego Alejandro Castillo Morales.', '2026-11-07 00:49:48.784875+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (81, 'Eliminación', 'Eliminó el documento institucional "Reglamento Interno" (ID 7), con 1 versión(es) y 0 propuesta(s).', '2026-11-07 00:52:36.832747+00', 23);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (82, 'Modificación de usuario', 'Actualizó la cuenta de Osvaldo Caraccioli (#28).', '2026-11-14 00:44:16.161922+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (83, 'Modificación de usuario', 'Actualizó la cuenta de Rodrigo Flores (#16).', '2026-11-14 00:51:10.712069+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (84, 'Modificación de usuario', 'Actualizó la cuenta de Rodrigo Flores (#16).', '2026-11-14 00:53:27.915749+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (85, 'Modificación de usuario', 'Actualizó la cuenta de Rodrigo Flores (#16).', '2026-11-14 01:12:19.276461+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (86, 'Creación', 'Registró exitosamente el caso #75 con 1 estudiante(s): Ximena Bahamondez Novoa.', '2026-11-14 03:02:47.74282+00', 28);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (87, 'Creación', 'Registró exitosamente el caso #76 con 1 estudiante(s): Agustin Alvarado rojas.', '2026-11-14 03:04:41.599513+00', 28);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (88, 'Modificación de usuario', 'Actualizó la cuenta de Pedro González (#36).', '2026-11-14 03:11:54.865588+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (89, 'Modificación de usuario', 'Actualizó la cuenta de Pedro González (#36).', '2026-11-14 03:12:44.855656+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (90, 'Creación', 'Registró exitosamente el caso #77 con 1 estudiante(s): Rodrigo Flores Flores.', '2026-11-14 03:25:50.78084+00', 36);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (91, 'Aprobación de caso', 'Revisó la solicitud #2 del Profesor Jefe Pedro: Aprobada.', '2026-11-14 03:25:51.131494+00', 19);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (92, 'Modificación de usuario', 'Actualizó la cuenta de Rodrigo Flores (#16).', '2026-11-14 08:53:17.555959+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (93, 'Modificación de usuario', 'Actualizó la cuenta de Daniel Alvarado (#20).', '2026-11-14 20:12:39.505315+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (94, 'Creación', 'Registró exitosamente el caso #78 con 1 estudiante(s): Constanza Flores Farias.', '2026-11-14 20:14:59.244467+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (95, 'Creación', 'Registró exitosamente el caso #79 con 1 estudiante(s): Rocío Cortés Xamenaa.', '2026-11-14 20:20:53.109026+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (96, 'Creación', 'Registró exitosamente el caso #80 con 1 estudiante(s): Rocío Cortés Xamenaa.', '2026-11-14 20:24:13.444745+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (97, 'Creación', 'Registró exitosamente el caso #81 con 1 estudiante(s): Rocío Cortés Xamenaa.', '2026-11-14 20:31:09.527665+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (98, 'Creación', 'Registró exitosamente el caso #82 con 1 estudiante(s): Rocío Cortés Xamenaa.', '2026-11-14 20:31:45.443912+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (99, 'Creación', 'Registró exitosamente el caso #83 con 1 estudiante(s): Rocío Cortés Xamenaa.', '2026-11-14 20:34:07.281193+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (100, 'Creación', 'Registró exitosamente el caso #84 con 1 estudiante(s): Rocío Cortés Xamenaa.', '2026-11-14 20:34:44.749845+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (101, 'Creación', 'Registró exitosamente el caso #85 con 1 estudiante(s): Rocío Cortés Xamenaa.', '2026-11-14 20:35:32.094423+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (102, 'Creación', 'Registró exitosamente el caso #86 con 1 estudiante(s): Rocío Cortés Xamenaa.', '2026-11-14 20:36:57.80039+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (103, 'Creación', 'Registró exitosamente el caso #87 con 1 estudiante(s): Rocío Cortés Xamenaa.', '2026-11-14 20:37:35.761626+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (104, 'Creación', 'Registró exitosamente el caso #88 con 1 estudiante(s): Rocío Cortés Xamenaa.', '2026-11-14 20:39:30.777214+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (105, 'Modificación de usuario', 'Actualizó la cuenta de Osvaldo Caraccioli (#28).', '2026-11-14 20:59:56.070221+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (106, 'Modificación', 'Modificó los registros del caso #88.', '2026-11-15 12:29:26.465668+00', 38);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (107, 'Modificación', 'Modificó los registros del caso #65.', '2026-11-15 12:35:06.793515+00', 38);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (108, 'Creación', 'Registró exitosamente el caso #89 con 1 estudiante(s): Ximena Bahamondez Novoa.', '2026-11-15 12:37:43.152545+00', 38);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (109, 'Eliminación', 'Eliminó el caso #89 de la bitácora de convivencia.', '2026-11-15 15:32:51.572532+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (110, 'Eliminación', 'Eliminó el caso #83 de la bitácora de convivencia.', '2026-11-15 19:56:31.983148+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (111, 'Modificación de usuario', 'Actualizó la cuenta de Pedro González (#36).', '2026-11-15 23:51:20.11157+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (112, 'Modificación de usuario', 'Actualizó la cuenta de Pedro González (#36).', '2026-11-15 23:55:12.411639+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (113, 'Modificación de usuario', 'Actualizó la cuenta de Pedro González (#36).', '2026-11-15 23:56:26.975932+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (114, 'Modificación de usuario', 'Actualizó la cuenta de Pedro González (#36).', '2026-11-15 23:58:06.970822+00', 25);
INSERT INTO public.historial_usuario (historial_id, historial_accion, historial_detalle, historial_fecha, usuario_id) VALUES (115, 'Modificación de usuario', 'Actualizó la cuenta de Pedro González (#36).', '2026-11-16 00:48:55.761524+00', 25);


--
-- Data for Name: inspector; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.inspector (inspector_id, inspector_nombre, inspector_apaterno, inspector_amaterno, usuario_id) VALUES (3, 'Pamela', 'Ibáñez', 'Salinas', 12);
INSERT INTO public.inspector (inspector_id, inspector_nombre, inspector_apaterno, inspector_amaterno, usuario_id) VALUES (4, 'Sebastián', 'Navarro', 'Orellana', 15);
INSERT INTO public.inspector (inspector_id, inspector_nombre, inspector_apaterno, inspector_amaterno, usuario_id) VALUES (8, 'Isaias', 'Ortiz', 'Inspector', 37);
INSERT INTO public.inspector (inspector_id, inspector_nombre, inspector_apaterno, inspector_amaterno, usuario_id) VALUES (10, 'Osvaldo', 'Caraccioli', 'Cisterna', 28);
INSERT INTO public.inspector (inspector_id, inspector_nombre, inspector_apaterno, inspector_amaterno, usuario_id) VALUES (11, 'Benjamin', 'Orellana', 'Orellana', 39);


--
-- Data for Name: involucran; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (10, 4, 'Leve');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (11, 5, 'Grave');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (12, 6, 'Grave');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (13, 7, 'Grave');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (15, 9, 'Grave');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (28, 22, 'Grave');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (30, 23, 'Gravísima');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (33, 25, 'Gravísima');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (34, 26, 'Gravísima');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (60, 30, 'Grave');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (60, 31, 'Grave');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (60, 33, 'Leve');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (46, 36, 'Gravísima');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (10, 37, 'Grave');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (10, 38, 'Leve');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (46, 39, 'Gravísima');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (46, 40, 'Gravísima');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (46, 41, 'Gravísima');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (5, 42, 'Gravísima');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (46, 43, 'Grave');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (10, 28, 'Gravísima');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (42, 34, 'Gravísima');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (10, 44, 'Grave');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (46, 45, 'Gravísima');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (46, 46, 'Grave');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (46, 47, 'Gravísima');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (46, 49, 'Gravísima');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (46, 50, 'Leve');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (46, 51, 'Gravísima');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (46, 52, 'Gravísima');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (46, 53, 'Leve');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (46, 54, 'Leve');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (46, 55, 'Leve');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (46, 56, 'Gravísima');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (46, 48, 'Grave');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (46, 57, 'Grave');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (10, 35, 'Grave');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (15, 59, 'Gravísima');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (63, 58, 'Leve');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (60, 60, 'Grave');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (63, 61, 'Leve');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (40, 62, 'Leve');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (63, 63, 'Leve');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (63, 64, 'Grave');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (48, 70, 'Gravísima');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (68, 71, 'Gravísima');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (29, 72, 'Gravísima');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (52, 73, 'Gravísima');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (12, 74, 'Grave');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (68, 74, 'Grave');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (56, 75, 'Leve');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (76, 76, 'Grave');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (10, 77, 'Grave');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (29, 78, 'Grave');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (37, 79, 'Leve');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (37, 80, 'Grave');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (37, 81, 'Leve');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (37, 82, 'Grave');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (37, 84, 'Leve');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (37, 85, 'Leve');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (37, 86, 'Leve');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (37, 87, 'Gravísima');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (37, 88, 'Grave');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (60, 65, 'Grave');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (63, 65, 'Grave');
INSERT INTO public.involucran (estudiante_id, caso_id, tipo_falta) VALUES (41, 65, 'Grave');


--
-- Data for Name: pconvivencia; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.pconvivencia (pconvivencia_id, convivencia_nombre, convivencia_apaterno, convivencia_amaterno, usuario_id) VALUES (1, 'Daniela', 'Vergara', 'Palma', 14);
INSERT INTO public.pconvivencia (pconvivencia_id, convivencia_nombre, convivencia_apaterno, convivencia_amaterno, usuario_id) VALUES (5, 'Rodrigo', 'Flores', 'Prueba1', 16);


--
-- Data for Name: profesorjefe; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.profesorjefe (profesorjefe_id, profesor_nombre, profesor_apaterno, profesor_amaterno, curso_id, usuario_id) VALUES (2, 'Jorge', 'Contreras', 'Espinoza', 3, 13);
INSERT INTO public.profesorjefe (profesorjefe_id, profesor_nombre, profesor_apaterno, profesor_amaterno, curso_id, usuario_id) VALUES (4, 'Sheldon', 'Cooper', 'L', 4, 22);
INSERT INTO public.profesorjefe (profesorjefe_id, profesor_nombre, profesor_apaterno, profesor_amaterno, curso_id, usuario_id) VALUES (35, 'Pedro', 'González', 'Pérez', 1, 36);


--
-- Data for Name: sesion_activa; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.sesion_activa (id, session_key, fecha_inicio, usuario_id) VALUES (1, '3n75cb1uthquexmlmku4d84wh014u93l', '2026-09-01 05:29:36.177708+00', 11);
INSERT INTO public.sesion_activa (id, session_key, fecha_inicio, usuario_id) VALUES (39, 'mplc86ksj98srbcep0wu7wbqsngovo0i', '2026-10-13 20:52:53.970299+00', 36);
INSERT INTO public.sesion_activa (id, session_key, fecha_inicio, usuario_id) VALUES (43, '43gncw4kapvm9wyislnylj84yb3vvxr6', '2026-10-28 00:53:32.109963+00', 23);
INSERT INTO public.sesion_activa (id, session_key, fecha_inicio, usuario_id) VALUES (47, 'xrpzzsiyuej8aw8vi9ijvsf0l2tn57sn', '2026-11-06 17:04:33.868188+00', 19);
INSERT INTO public.sesion_activa (id, session_key, fecha_inicio, usuario_id) VALUES (44, '2g20hh8cw7vlprcntew6akrrz56ss5te', '2026-11-07 02:08:59.540936+00', 25);


--
-- Data for Name: solicitud_caso; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.solicitud_caso (id, fecha_evento, titulo, descripcion, tipo_falta, evidencia, estudiantes, estado, comentario_revision, creada_en, revisada_en, lugar_id, revisada_por_id, solicitante_id) VALUES (1, '0033-04-03', 'judas vende a jesus', 'matias traciona a jesus por unas monedas de plata', 'Gravísima', '', '[{"nombre": "Matias", "curso_id": 2, "numero_lista": null, "estudiante_id": 15, "apellido_materno": "Vera", "apellido_paterno": "Urria"}]', 'aprobada', 'pateen a jesus por judio', '2026-10-13 20:58:01.801313+00', '2026-10-13 21:01:29.832704+00', 1, 25, 36);
INSERT INTO public.solicitud_caso (id, fecha_evento, titulo, descripcion, tipo_falta, evidencia, estudiantes, estado, comentario_revision, creada_en, revisada_en, lugar_id, revisada_por_id, solicitante_id) VALUES (2, '2026-11-08', 'insulta a su profesor', 'insulta a su profesor en clase y le dice pelao ctm', 'Grave', '', '[{"nombre": "Rodrigo", "curso_id": 2, "numero_lista": null, "estudiante_id": 10, "apellido_materno": "Flores", "apellido_paterno": "Flores"}]', 'aprobada', 'aaaa', '2026-11-14 03:14:56.555438+00', '2026-11-14 03:25:50.956815+00', 2, 19, 36);


--
-- Name: accion_seguimiento_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.accion_seguimiento_id_seq', 1, false);


--
-- Name: administrador_administrador_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.administrador_administrador_id_seq', 9, true);


--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_group_id_seq', 1, false);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_group_permissions_id_seq', 1, false);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_permission_id_seq', 120, true);


--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_user_groups_id_seq', 1, false);


--
-- Name: auth_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_user_id_seq', 1, true);


--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_user_user_permissions_id_seq', 1, false);


--
-- Name: caso_caso_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.caso_caso_id_seq', 89, true);


--
-- Name: curso_curso_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.curso_curso_id_seq', 9, true);


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_admin_log_id_seq', 1, false);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_content_type_id_seq', 30, true);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_migrations_id_seq', 32, true);


--
-- Name: documento_institucional_documento_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.documento_institucional_documento_id_seq', 8, true);


--
-- Name: estudiante_estudiante_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.estudiante_estudiante_id_seq', 76, true);


--
-- Name: historial_accion_seguimiento_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.historial_accion_seguimiento_id_seq', 1, false);


--
-- Name: historial_importacion_estudiantes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.historial_importacion_estudiantes_id_seq', 1, true);


--
-- Name: historial_notificacion_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.historial_notificacion_id_seq', 161, true);


--
-- Name: historial_seguimiento_caso_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.historial_seguimiento_caso_id_seq', 34, true);


--
-- Name: historial_usuario_historial_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.historial_usuario_historial_id_seq', 115, true);


--
-- Name: inspector_inspector_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.inspector_inspector_id_seq', 11, true);


--
-- Name: lugar_lugar_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.lugar_lugar_id_seq', 5, true);


--
-- Name: notificacion_notificacion_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.notificacion_notificacion_id_seq', 240, true);


--
-- Name: pconvivencia_pconvivencia_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.pconvivencia_pconvivencia_id_seq', 5, true);


--
-- Name: profesorjefe_profesorjefe_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.profesorjefe_profesorjefe_id_seq', 35, true);


--
-- Name: regla_institucional_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.regla_institucional_id_seq', 316, true);


--
-- Name: rol_rol_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.rol_rol_id_seq', 4, true);


--
-- Name: seguimiento_caso_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.seguimiento_caso_id_seq', 34, true);


--
-- Name: sesion_activa_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sesion_activa_id_seq', 48, true);


--
-- Name: solicitud_caso_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.solicitud_caso_id_seq', 2, true);


--
-- Name: usuario_usuario_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.usuario_usuario_id_seq', 39, true);


--
-- Name: version_reglamento_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.version_reglamento_id_seq', 2, true);


--
-- PostgreSQL database dump complete
--

\unrestrict ihP8hHzXfbbLZmnQ7BswkFJKNAnGUUikzNRqA8FfS58Zrqb2x1GaOwiiZ4UNZlm

