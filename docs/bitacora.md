# Bitácora del proyecto

Entrega individual. Integrante: Dylan Ortiz; el historial de Git utiliza el nombre de autor Dylan. Los aportes se respaldan con el historial del repositorio `Dyl4n19/soporteya`.

## Semana 1 — Diseño, Oracle y conexión

### Integrante: Dylan

- Trabajo realizado: definición inicial del modelo de datos, diccionario y scripts Oracle.
- Archivos: `docs/modelo_datos.md`, `docs/diccionario_datos.md`, `backEnd/sql/01_crear_tablas.sql` y `backEnd/sql/02_datos_ejemplo.sql`.
- Problema encontrado: conectar Django al esquema personal de Oracle sin publicar las credenciales.
- Solución aplicada: configurar `python-oracledb` en modo thin, las variables locales de conexión y la exclusión de `.env` mediante `.gitignore`.
- Próxima semana: implementar dominio, puertos y casos de uso de las entidades asignadas.
- Uso de IA: se utilizó IA para proponer una estructura inicial; el equipo debe revisar, ejecutar y adaptar cada archivo antes de registrarlo como aporte propio.

### Evidencia técnica de conexión

- Se configuró Oracle FreeSQL 26ai mediante SQLNet en modo thin.
- Django confirmó la conexión contra el esquema personal.
- `01_crear_tablas.sql` y `02_datos_ejemplo.sql` finalizaron sin errores.
- Verificación ORM: 5 empresas, 5 categorías, 5 técnicos, 5 tickets y 5 comentarios.
- La contraseña permanece únicamente en `.env`, archivo excluido por `.gitignore`.

### Cierre documental y comprobación de semana 1 — 23 de noviembre de 2026

- Se preparó `docs/anexo_a.md` con Dylan Ortiz como integrante individual y responsable de las cinco entidades y tareas comunes. El número administrativo de grupo, la sección y la inscripción quedan por confirmar con el docente; G12 identifica el problema desarrollado en la pauta.
- Se alinearon el diagrama ER y el diccionario con la columna única `id_comentario`, las opciones IDENTITY NOCACHE y la restricción de la fecha de cierre.
- Se consultaron `USER_TABLES`, `USER_CONSTRAINTS` y `USER_CONS_COLUMNS` del esquema propio y se comprobaron los registros: cinco tablas, cinco filas por tabla, cinco PK, cuatro FK, cinco UNIQUE y nueve CHECK explícitos.
- La captura del informe de consulta real, sus resultados JSON y el HTML se guardaron en `docs/evidencias/`. La imagen no representa la interfaz web de FreeSQL.
- Se añadió el comando de solo lectura `verificar_semana1` para reproducir la comprobación sin volver a crear tablas ni modificar datos.
- Uso de IA: se solicitó apoyo a Codex para completar los documentos y organizar la evidencia; no se inventaron datos administrativos ni una firma.

## Semana 2 — Dominio, puertos y CRUD de maestras

### Integrante: Dylan

- Fecha de verificación: 23 de noviembre de 2026.
- Commit de implementación y pruebas: [`290899f`](https://github.com/Dyl4n19/soporteya/commit/290899f), `feat: completar dominio y CRUD de semana 2`, autor Dylan.
- Trabajo realizado: completar los contratos de los cinco puertos; convertir los resultados ORM en entidades de dominio; conectar los casos de uso CRUD de empresas, categorías y técnicos con la API y sus repositorios.
- Excepciones de negocio: registro inexistente, duplicado, registro en uso, regla incumplida y transición de estado inválida. La API responde con `message` y `field`.
- Problema encontrado: los serializadores de las maestras escribían directamente mediante el ORM, omitiendo los casos de uso existentes; algunos métodos de los puertos no coincidían con la implementación.
- Solución aplicada: serializadores de entrada dedicados a validar datos, operaciones CRUD delegadas a los casos de uso, contratos tipados y repositorios que reciben identificadores y devuelven entidades.
- Archivos principales: `backEnd/soporte/domain/`, `backEnd/soporte/application/`, `backEnd/soporte/infrastructure/repositories/`, `backEnd/soporte/adapters/api/` y `backEnd/soporte/container.py`.
- Verificación automatizada: 62 pruebas aprobadas. Incluyen el CRUD completo de las tres maestras, duplicados, registros inexistentes, eliminación de registros en uso, validación de datos, filtros, búsqueda, paginación y permisos; regresión del ciclo de tickets y del reporte SLA.
- Aislamiento de las pruebas: SQLite en memoria mediante `soporteya_project.test_settings`, sin modificar las bases de la aplicación.
- Evidencia en Oracle FreeSQL: consulta de las cinco tablas y ejecución de crear, obtener, actualizar y eliminar en las tres maestras mediante `python manage.py verificar_semana2 --crud`. Los registros temporales se probaron dentro de una transacción revertida al finalizar.
- Comprobación del frontend: `pnpm build` terminó correctamente después de reparar los enlaces locales de dependencias que apuntaban a la ubicación anterior del proyecto.
- Documentación: `docs/semana_2.md` contiene la relación con la pauta y el guion de demostración.
- Uso de IA: se utilizó Codex como apoyo para implementar y comprobar los cambios. La demostración y la explicación del proyecto corresponden al estudiante.
- Próximo avance: contrastar la siguiente entrega con la pauta de la semana correspondiente y preparar la demostración de los flujos solicitados.

## Semana 3 — Entidad principal, reglas y seguridad

### Integrante: Dylan

- Fecha de verificación: 23 de noviembre de 2026.
- Commit de implementación y pruebas: [`5603b21`](https://github.com/Dyl4n19/soporteya/commit/5603b21), `feat: completar semana 3 con transacciones y seguridad`, autor Dylan.
- Trabajo realizado: completar el CRUD de tickets y comentarios, la creación de tickets con varias líneas de detalle en una sola transacción y el control de estados. Se implementó un puerto de unidad de trabajo que mantiene Django fuera de los casos de uso.
- Reglas: R1 valida técnico activo y comentario antes de resolver; R2 asegura prioridad mínima ALTA para empresas PREMIUM y rechaza rebajas; R3 calcula el vencimiento por SLA en aplicación, excluyendo tickets resueltos o cerrados.
- Seguridad: login con CSRF incluso sin sesión, cookie de token HttpOnly, renovación del CSRF al ingresar, logout que revoca el token y acceso por rol. El técnico solo puede consultar y avanzar sus tickets y comentar; las operaciones reservadas devuelven 403.
- Usuarios: se preparó un superusuario `admin`, un usuario supervisor sin privilegios de superusuario y un técnico, con dos grupos y permisos distintos. El comando `setup_demo` conserva las contraseñas existentes.
- Administrador: cinco entidades con búsqueda y filtros, comentarios inline, autor y número automáticos, validación de reglas y acciones para cambiar estados mediante casos de uso.
- Interfaz: creación con varios comentarios iniciales, edición y asignación de tickets abiertos, eliminación de abiertos con su detalle y edición/eliminación de comentarios por el supervisor. Los controles se ajustan al rol.
- Problemas encontrados: Django no generaba los permisos de modelos ubicados en la carpeta de infraestructura; Oracle thin rechazaba timestamps guardados con zona horaria nombrada y el cálculo anterior del promedio intentaba promediar intervalos como números.
- Soluciones: exponer los modelos a Django en `soporte/models.py`; crear los permisos mediante migración de la base interna; fijar la sesión Oracle a `+00:00`; calcular el promedio desde las fechas recuperadas; añadir una migración de metadatos que conserva `managed=False` en Oracle y permite el modo SQLite de pruebas.
- Archivos: `backEnd/soporte/application/use_cases/`, `domain/ports/`, `infrastructure/`, `adapters/api/`, `adapters/admin_forms.py`, `admin.py`, `models.py`, `management/commands/`, `migrations/0002_business_model_management.py` y `frontend/src/App.jsx`.
- Pruebas: 117 aprobadas en bases SQLite en memoria. Incluyen CRUD de las cinco tablas, transacciones con rollback, estados, R1–R3, permisos, login/logout/me con comprobación real de CSRF y formularios del administrador.
- Evidencia Oracle: `python manage.py verificar_semana3 --crud` terminó correctamente, conservando los registros originales. Se probaron las cinco tablas, los cambios de estado, R1–R3, el reporte y la reversión al fallar el segundo comentario.
- Evidencia visual: acceso del supervisor, formulario con varios comentarios y edición de ticket abierto; acceso del técnico mostrando solo su ticket; inicio de sesión del superusuario y listado con búsqueda y filtros en Django Admin. La revisión del navegador no alteró tickets existentes.
- Compilación: `pnpm build` finalizó correctamente. Django no reportó errores ni cambios de modelos pendientes en la configuración Oracle o la de pruebas.
- Documentación: guía `docs/semana_3.md`, usuarios y comandos del README y colección de Postman con manejo de CSRF renovado.
- Uso de IA: se pidió apoyo a Codex para contrastar la pauta e implementar y probar los faltantes. Se ajustaron las reglas al problema de mesa de ayuda, la persistencia a Oracle thin, la transacción principal-detalle y el control de acceso. El estudiante debe poder explicar estos cambios en la defensa.
- Próximo avance: preparar la demostración y las preguntas individuales de la revisión del backend de semana 4.

