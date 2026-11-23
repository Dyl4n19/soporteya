# Semana 2 — SoporteYa, Mesa de Ayuda TI

Entrega individual. Fecha de verificación: 23 de noviembre de 2026.

Repositorio: [Dyl4n19/soporteya](https://github.com/Dyl4n19/soporteya).

## Correspondencia con la pauta

| Punto solicitado | Implementación y evidencia |
| --- | --- |
| 1. Entidades y puertos de las 5 tablas | Cinco entidades en `backEnd/soporte/domain/entities/` y cinco contratos específicos en `backEnd/soporte/domain/ports/`. Los puertos usan entidades y tipos de Python, sin importar Django. |
| 2. Excepciones de negocio | `BusinessError`, `NotFoundError`, `DuplicateError`, `InUseError`, `RuleViolationError` e `InvalidStateError` en `backEnd/soporte/application/exceptions.py`. Adaptación a respuestas HTTP en `backEnd/soporte/adapters/api/exceptions.py`. |
| 3. Casos de uso CRUD de al menos 3 maestras | `EmpresaUseCases`, `CategoriaUseCases` y `TecnicoUseCases`: listar, obtener, crear, actualizar y eliminar. Sus archivos están en `backEnd/soporte/application/use_cases/`. La API utiliza estos casos de uso. |
| 4. Modelos y repositorios de esas 3 | `EmpresaModel`, `CategoriaModel` y `TecnicoModel` en `backEnd/soporte/infrastructure/models/`; sus implementaciones `DjangoEmpresaRepository`, `DjangoCategoriaRepository` y `DjangoTecnicoRepository` en `backEnd/soporte/infrastructure/repositories/`. |
| 5. Commits de cada integrante | La entrega es individual y los commits se registran con la identidad Git de Dylan. Se comprueban con `git log`. La bitácora describe los aportes y el uso de IA. |

Commit de implementación y pruebas: [`290899f — feat: completar dominio y CRUD de semana 2`](https://github.com/Dyl4n19/soporteya/commit/290899f), autor Dylan.

Las columnas de entrega, integrantes activos, asistencia, porcentaje S2 y feedback corresponden al seguimiento del docente; esta guía no asigna una nota ni registra asistencia.

## Las cinco tablas

| Tabla Oracle | Entidad de dominio | Puerto específico |
| --- | --- | --- |
| `EMPRESAS` | `Empresa` | `EmpresaRepositoryPort` |
| `CATEGORIAS_TICKET` | `Categoria` | `CategoriaRepositoryPort` |
| `TECNICOS` | `Tecnico` | `TecnicoRepositoryPort` |
| `TICKETS` | `Ticket` | `TicketRepositoryPort` |
| `COMENTARIOS_TICKET` | `Comentario` | `ComentarioRepositoryPort` |

Los puertos CRUD declaran `list`, `get`, `save` y `delete`. `save` recibe datos y, al actualizar, el identificador del registro; `delete` recibe el identificador. El puerto de comentarios declara consultar por ticket y agregar un comentario. El puerto de tickets también declara las consultas para el reporte SLA.

Los repositorios traducen modelos ORM a entidades. Por ejemplo, `DjangoEmpresaRepository.get` devuelve una `Empresa`, sin métodos de persistencia de Django. Los casos de uso pueden importarse sin configurar Django. `container.py` conecta cada puerto con su implementación.

## CRUD de las tres maestras

| Maestra | Colección | Registro individual |
| --- | --- | --- |
| Empresas | `/api/empresas/` | `/api/empresas/{id}/` |
| Categorías | `/api/categorias/` | `/api/categorias/{id}/` |
| Técnicos | `/api/tecnicos/` | `/api/tecnicos/{id}/` |

- `GET` sobre la colección lista con paginación; admite `search`, `activo` y `ordering`. Empresas también permite filtrar por `plan`.
- `GET` sobre un registro obtiene su detalle.
- `POST` sobre la colección crea un registro.
- `PUT` reemplaza los campos editables y `PATCH` actualiza parcialmente un registro.
- `DELETE` elimina un registro si no está relacionado con un ticket.

La entrada se valida en los serializadores. La vista llama al caso de uso, el caso de uso utiliza el puerto y el repositorio realiza la operación en la base `negocio`. El supervisor puede modificar las maestras; el técnico autenticado puede consultarlas.

Un dato duplicado produce `409`; un identificador inexistente, `404`; una maestra utilizada por un ticket no puede eliminarse y devuelve `409`. Los errores de validación de entrada devuelven `400`. El formato de error es `{"message": "...", "field": "..."}`.

## Demostración desde PowerShell

En este equipo, abrir una terminal y ejecutar:

```powershell
Set-Location "C:\Users\Dylan\Desktop\SoporteYa\backEnd"
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py verificar_semana2 --crud
.\.venv\Scripts\python.exe -m pytest -q
git log --format="%h | %an | %s"
```

`verificar_semana2` usa la base configurada en el archivo local `.env`. La verificación del 23 de noviembre se realizó con Oracle FreeSQL: se leyeron 5 empresas, 5 categorías, 5 técnicos, 5 tickets y 5 comentarios. La opción `--crud` crea registros temporales en las tres maestras, comprueba su lectura, edición y eliminación, y revierte la transacción. Los registros existentes se conservan.

Para una comprobación que solo consulta las cinco tablas:

```powershell
.\.venv\Scripts\python.exe manage.py verificar_semana2
```

Pytest utiliza dos bases SQLite en memoria con `soporteya_project.test_settings`. Las pruebas no usan Oracle ni las bases SQLite locales de la aplicación. Esto permite repetir los casos de error sin alterar los datos de demostración.

La suite comprueba el CRUD completo de cada maestra, la delegación de la API a los casos de uso, los duplicados al crear y editar, los registros inexistentes, las eliminaciones protegidas, las reglas fuera de HTTP, las consultas y los permisos. También comprueba las reglas de tickets, sus comentarios y cierre, el reporte SLA y la conservación de datos del comando de verificación.

Resultado de la verificación: **62 pruebas aprobadas**, `manage.py check` sin errores, ningún cambio de migraciones pendiente con la configuración de prueba y compilación de React con `pnpm build` exitosa.

Para mostrar los nombres de cada prueba:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

En otro equipo, clonar el repositorio, crear el entorno virtual e instalar `backEnd/requirements.txt`, siguiendo el README. Para comprobar Oracle se debe preparar un `.env` propio; las pruebas automatizadas funcionan sin credenciales de Oracle.

## Guion para explicar el avance

1. Mostrar una entidad y su puerto. Explicar que la entidad representa los datos y el puerto define las operaciones que necesita la aplicación.
2. Abrir `empresa_use_cases.py`, `base.py` de los casos de uso y `empresa_repository.py`. Seguir una creación o actualización desde el caso de uso hasta el repositorio.
3. Mostrar `EmpresaViewSet` y explicar que los serializadores validan la entrada mientras la persistencia pasa por los casos de uso.
4. Ejecutar la comprobación de Oracle y las pruebas. Mostrar los casos de duplicado, registro en uso y registro inexistente.
5. Mostrar `git log` y `docs/bitacora.md` como evidencia del avance individual.
