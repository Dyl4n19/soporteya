INSERT INTO empresas (rut, razon_social, plan, activo) VALUES ('76.111.111-1', 'Comercial Andina SpA', 'PREMIUM', 1);
INSERT INTO empresas (rut, razon_social, plan, activo) VALUES ('77.222.222-2', 'Transportes del Pacífico Ltda.', 'BASICO', 1);
INSERT INTO empresas (rut, razon_social, plan, activo) VALUES ('78.333.333-3', 'Servicios Médicos Sur SpA', 'PREMIUM', 1);
INSERT INTO empresas (rut, razon_social, plan, activo) VALUES ('79.444.444-4', 'Constructora Horizonte Ltda.', 'BASICO', 1);
INSERT INTO empresas (rut, razon_social, plan, activo) VALUES ('80.555.555-5', 'Agrícola Valle Verde SpA', 'BASICO', 1);

INSERT INTO categorias_ticket (nombre, horas_sla, activo) VALUES ('Acceso y contraseñas', 4, 1);
INSERT INTO categorias_ticket (nombre, horas_sla, activo) VALUES ('Correo electrónico', 8, 1);
INSERT INTO categorias_ticket (nombre, horas_sla, activo) VALUES ('Red y conectividad', 4, 1);
INSERT INTO categorias_ticket (nombre, horas_sla, activo) VALUES ('Equipos y periféricos', 24, 1);
INSERT INTO categorias_ticket (nombre, horas_sla, activo) VALUES ('Software empresarial', 12, 1);

INSERT INTO tecnicos (rut, nombre, email, activo) VALUES ('15.111.111-1', 'Camila Rojas', 'camila.rojas@soporteya.cl', 1);
INSERT INTO tecnicos (rut, nombre, email, activo) VALUES ('16.222.222-2', 'Diego Morales', 'diego.morales@soporteya.cl', 1);
INSERT INTO tecnicos (rut, nombre, email, activo) VALUES ('17.333.333-3', 'Valentina Soto', 'valentina.soto@soporteya.cl', 1);
INSERT INTO tecnicos (rut, nombre, email, activo) VALUES ('18.444.444-4', 'Martín Silva', 'martin.silva@soporteya.cl', 1);
INSERT INTO tecnicos (rut, nombre, email, activo) VALUES ('19.555.555-5', 'Paula Contreras', 'paula.contreras@soporteya.cl', 0);

INSERT INTO tickets (id_empresa, id_categoria, id_tecnico, titulo, descripcion, prioridad, fecha_creacion, estado)
VALUES (1, 3, 1, 'Sin conexión en oficina central', 'Los equipos del segundo piso no acceden a la red corporativa.', 'CRITICA', SYS_EXTRACT_UTC(SYSTIMESTAMP) - INTERVAL '6' HOUR, 'EN_PROGRESO');

INSERT INTO tickets (id_empresa, id_categoria, id_tecnico, titulo, descripcion, prioridad, fecha_creacion, estado)
VALUES (2, 1, 2, 'Usuario bloqueado', 'La cuenta del encargado de despacho quedó bloqueada.', 'MEDIA', SYS_EXTRACT_UTC(SYSTIMESTAMP) - INTERVAL '2' HOUR, 'ASIGNADO');

INSERT INTO tickets (id_empresa, id_categoria, id_tecnico, titulo, descripcion, prioridad, fecha_creacion, estado)
VALUES (3, 5, 3, 'Error al emitir informe', 'El sistema muestra un error al generar el informe mensual.', 'ALTA', SYS_EXTRACT_UTC(SYSTIMESTAMP) - INTERVAL '14' HOUR, 'EN_PROGRESO');

INSERT INTO tickets (id_empresa, id_categoria, titulo, descripcion, prioridad, fecha_creacion, estado)
VALUES (4, 4, 'Impresora no responde', 'La impresora de administración aparece desconectada.', 'BAJA', SYS_EXTRACT_UTC(SYSTIMESTAMP) - INTERVAL '1' HOUR, 'ABIERTO');

INSERT INTO tickets (id_empresa, id_categoria, id_tecnico, titulo, descripcion, prioridad, fecha_creacion, fecha_cierre, estado)
VALUES (5, 2, 4, 'Correo no sincronizaba', 'Se corrigió la configuración del cliente de correo.', 'MEDIA', SYS_EXTRACT_UTC(SYSTIMESTAMP) - INTERVAL '20' HOUR, SYS_EXTRACT_UTC(SYSTIMESTAMP) - INTERVAL '12' HOUR, 'CERRADO');

INSERT INTO comentarios_ticket (id_ticket, numero, autor, texto) VALUES (1, 1, 'Camila Rojas', 'Se detectó una falla en el switch del segundo piso.');
INSERT INTO comentarios_ticket (id_ticket, numero, autor, texto) VALUES (1, 2, 'Camila Rojas', 'Se reemplazó el equipo y se están validando los puntos de red.');
INSERT INTO comentarios_ticket (id_ticket, numero, autor, texto) VALUES (2, 1, 'Diego Morales', 'Se solicitó validación de identidad antes del desbloqueo.');
INSERT INTO comentarios_ticket (id_ticket, numero, autor, texto) VALUES (3, 1, 'Valentina Soto', 'Se reprodujo el error y se revisarán los permisos del módulo.');
INSERT INTO comentarios_ticket (id_ticket, numero, autor, texto) VALUES (5, 1, 'Martín Silva', 'Configuración corregida y validada con el usuario.');

COMMIT;

