# Bitácora del proyecto

Entrega individual. Integrante: Dylan. Los aportes se respaldan con el historial de Git del repositorio `Dyl4n19/soporteya`.

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

