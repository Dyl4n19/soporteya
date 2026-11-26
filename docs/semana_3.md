# Semana 3 — SoporteYa, Mesa de Ayuda TI

Entrega individual. Verificación: 23 de noviembre de 2026.

Commit de implementación y pruebas: [`5603b21 — feat: completar semana 3 con transacciones y seguridad`](https://github.com/Dyl4n19/soporteya/commit/5603b21), autor Dylan.

## Correspondencia con la pauta

| Requisito | Implementación |
| --- | --- |
| 1. CRUD de las cinco, principal con detalle en transacción | Empresas, categorías, técnicos, tickets y comentarios tienen casos de uso. `TicketUseCases.crear` crea el ticket y sus comentarios dentro de la unidad de trabajo; al fallar una línea, no queda cabecera ni detalle parcial. |
| 2. Estados y reglas R1–R3 | Transiciones, asignación, prioridad PREMIUM y cálculo de vencidos en `backEnd/soporte/application/use_cases/ticket_use_cases.py`. Los comentarios también protegen el último detalle de un ticket resuelto. |
| 3. Administrador con búsqueda y filtros | Cinco entidades registradas en `backEnd/soporte/admin.py`, con columnas de negocio, búsquedas y filtros. Tickets incluye comentarios inline y acciones de estado validadas. |
| 4. Superusuario, dos roles y usuarios | `setup_demo` prepara `admin`, `supervisor` y `tecnico`, los grupos `SUPERVISOR` y `TECNICO` y permisos distintos. Las contraseñas iniciales están documentadas en el README. |
| 5. Login, logout y me con cookie y CSRF | `/api/auth/csrf/`, `/api/auth/login/`, `/api/auth/me/` y `/api/auth/logout/`. Cookie HttpOnly, CSRF obligatorio en escrituras, renovación al ingresar y revocación al salir. |

Las columnas de entrega y calificación las completa el docente.

## Transacción principal y detalle

Los casos de uso dependen de `UnitOfWorkPort`. La implementación `DjangoUnitOfWork`, elegida en `container.py`, usa `transaction.atomic(using="negocio")`. El dominio y la aplicación no importan Django.

`POST /api/tickets/` admite comentarios iniciales anidados. Por ejemplo, utilizando identificadores existentes:

```json
{
  "empresa_id": 1,
  "categoria_id": 1,
  "tecnico_id": null,
  "titulo": "Cuenta de usuario bloqueada",
  "descripcion": "El usuario no puede iniciar sesión en su equipo",
  "prioridad": "MEDIA",
  "comentarios": [
    {"texto": "Se recibe la solicitud del cliente."},
    {"texto": "Se valida la identidad del usuario."}
  ]
}
```

La respuesta es `201` y contiene el ticket con sus comentarios. Número y autor se asignan en el servidor. Si falla el segundo comentario, la transacción revierte también el primer comentario y el ticket. Se puede abrir un ticket sin comentarios; R1 impide resolverlo mientras no tenga al menos uno.

Los comentarios se identifican por ticket y número: `/api/tickets/{id}/comentarios/{numero}/`. El repositorio consulta ambos valores, respetando la clave compuesta de Oracle. La columna única `id_comentario` permite integrar el modelo con Django Admin; el número y el ticket no se cambian al editar el texto.

## Estados y reglas

| Estado actual | Siguiente estado permitido |
| --- | --- |
| `ABIERTO` | `ASIGNADO`, con técnico activo. |
| `ASIGNADO` | `EN_PROGRESO`. |
| `EN_PROGRESO` | `RESUELTO`, con al menos un comentario. |
| `RESUELTO` | `CERRADO` o `EN_PROGRESO` para reabrir. |
| `CERRADO` | Sin transiciones posteriores. |

- **R1:** no se asigna a un técnico inactivo y no se resuelve sin comentario. Se bloquea el ticket durante la operación para coordinar cambios de estado y detalle.
- **R2:** al crear un ticket PREMIUM, una prioridad BAJA o MEDIA se eleva a ALTA; CRITICA se conserva. Intentar rebajar después esa prioridad devuelve `409`.
- **R3:** el caso de uso compara el tiempo transcurrido con las horas SLA. Solo está vencido si las supera estrictamente y su estado no es RESUELTO ni CERRADO. Exactamente al límite todavía no está vencido.

Un ticket abierto permite corregir sus datos y asignarlo. Fuera del estado inicial, la actualización permite el avance de estados y los comentarios correspondientes. Solo se elimina un ticket ABIERTO, junto con su detalle. En uno cerrado no se agregan, editan ni eliminan comentarios; uno resuelto conserva al menos un comentario.

## Operaciones disponibles

| Recurso | Colección | Registro |
| --- | --- | --- |
| Empresas | `/api/empresas/` | `/api/empresas/{id}/` |
| Categorías | `/api/categorias/` | `/api/categorias/{id}/` |
| Técnicos | `/api/tecnicos/` | `/api/tecnicos/{id}/` |
| Tickets | `/api/tickets/` | `/api/tickets/{id}/` |
| Comentarios de un ticket | `/api/tickets/{id}/comentarios/` | `/api/tickets/{id}/comentarios/{numero}/` |

En una colección, `GET` lista y `POST` crea. En un registro, `GET` consulta, `PUT/PATCH` actualiza y `DELETE` elimina. Para avanzar estados de un ticket también existe `POST /api/tickets/{id}/estado/`; `PUT/PATCH` con solo `estado` utiliza las mismas reglas.

Las reglas viven en aplicación. Los adaptadores traducen las excepciones a JSON con `message` y `field`: `400` para entrada inválida, `401` sin autenticación, `403` por falta de permiso o CSRF, `404` inexistente y `409` por conflicto o regla de negocio.

## Roles y sesiones

El superusuario administra Django. El supervisor tiene acceso al CRUD, asignaciones, estados, comentarios y reporte. El técnico consulta los datos de empresa y categoría en sus tickets asignados, avanza esos tickets y agrega comentarios. La consulta de los catálogos completos está reservada al supervisor.

El vínculo usuario–técnico se realiza por correo. El usuario `tecnico` de demostración corresponde a Camila Rojas. Un ticket ajeno no aparece en su listado y su acceso directo responde `404`; una operación reservada responde `403`.

Flujo de sesión:

1. Solicitar `GET /api/auth/csrf/`.
2. Enviar usuario y contraseña a `POST /api/auth/login/` con `X-CSRFToken` y la cookie CSRF.
3. El servidor inicia la sesión, entrega el token en cookie HttpOnly y renueva el CSRF. Usar el CSRF nuevo en las siguientes escrituras.
4. `GET /api/auth/me/` devuelve el usuario y su rol.
5. `POST /api/auth/logout/`, con CSRF válido, revoca el token y elimina la cookie y la sesión. Una consulta posterior responde `401`.

El navegador se autentica con la cookie HttpOnly. Desde la semana 5, los clientes que omiten la cookie de autenticación pueden identificarse con `Authorization: Token <valor>`. Ambos modos exigen CSRF en escrituras. El logout revoca el token para los dos.

El frontend implementa este flujo. En Postman, ejecutar CSRF y login antes de las peticiones de negocio y dejar logout para el final; la colección actualiza la variable CSRF con la respuesta y las cookies.

## Administrador

Abrir `http://localhost:8000/admin/` con `admin` o `supervisor`. El técnico no tiene acceso al panel de administración.

Las cinco entidades tienen búsqueda y filtros. El formulario de ticket permite guardar su cabecera y comentarios inline en una transacción. Los estados se muestran como solo lectura en el formulario y se cambian mediante acciones que llaman a los casos de uso. Las reglas también se validan en los formularios, de modo que un técnico inactivo se muestra como error y no se guarda.

`soporte/models.py` expone los modelos de infraestructura al descubrimiento normal de Django. Esto permite crear sus tipos de contenido y permisos sin mover la persistencia fuera de su capa. La migración `0002` ajusta opciones de los modelos sin alterar tablas de Oracle: quedan con `managed=False`; SQLite de pruebas utiliza `managed=True`.

## Comandos para demostrar al profesor

En el equipo del proyecto:

```powershell
Set-Location "C:\Users\Dylan\Desktop\SoporteYa\backEnd"
.\.venv\Scripts\python.exe manage.py migrate --database default
.\.venv\Scripts\python.exe manage.py setup_demo
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py verificar_semana3 --crud
.\.venv\Scripts\python.exe -m pytest -q
git log --format="%h | %an | %s"
```

`verificar_semana3 --crud` usa la base local configurada, comprueba los roles, las cinco tablas y sus operaciones, las reglas, los estados, el reporte y una falla controlada en el segundo comentario. Usa registros temporales y revierte la transacción, conservando los datos originales. Sin `--crud`, solo comprueba roles y consulta las tablas.

Para iniciar el backend:

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

En otra terminal, iniciar la interfaz:

```powershell
Set-Location "C:\Users\Dylan\Desktop\SoporteYa\frontend"
pnpm install --frozen-lockfile
pnpm dev
```

Abrir `http://localhost:5173`. Los usuarios y contraseñas iniciales están en el README; `setup_demo` no restablece contraseñas que ya se hayan cambiado.

## Evidencia de verificación

- **117 pruebas aprobadas** en SQLite en memoria, incluyendo clientes con comprobación real de CSRF y formularios del administrador.
- Verificación transaccional completa en Oracle FreeSQL: cinco tablas, CRUD, estados, R1–R3 y rollback por fallo del segundo detalle. Los datos existentes se conservaron.
- Lecturas de la API con Oracle y filtrado del técnico comprobados.
- Compilación de React mediante `pnpm build` correcta.
- Revisión en navegador: login/logout del supervisor, formulario de ticket con varios comentarios, edición y asignación de abierto, vista del técnico con solo su ticket y acceso del superusuario al administrador con búsqueda y filtros.

Para que Oracle thin pueda recuperar los timestamps nuevos, cada conexión de negocio utiliza zona de sesión numérica `+00:00`. El promedio de resolución se calcula desde las fechas recuperadas para evitar convertir intervalos de Oracle a números.

## Guion de demostración de 5–7 minutos

1. Mostrar los cinco recursos y los archivos de sus capas.
2. Crear un ticket con dos comentarios; enseñar dónde está la transacción y ejecutar la prueba de rollback.
3. Intentar asignar sin técnico o con uno inactivo, intentar resolver sin comentario y mostrar el mínimo de prioridad PREMIUM. Explicar R3 y su límite de tiempo.
4. Mostrar búsqueda y filtros en el administrador y sus acciones de estado.
5. Ingresar como técnico para mostrar que solo ve su ticket y no tiene operaciones de supervisor; cerrar sesión y mostrar `401`.
6. Mostrar la bitácora y los commits individuales.

La cookie HttpOnly impide que JavaScript lea el token de autenticación. CSRF comprueba que una escritura proviene de un cliente que dispone del token CSRF esperado. La transacción evita guardar un ticket incompleto si falla una línea del detalle.

Referencias técnicas consultadas: [autenticación de Django REST Framework](https://www.django-rest-framework.org/api-guide/authentication/), [CSRF en Django](https://docs.djangoproject.com/en/5.2/ref/csrf/) y [transacciones de Django](https://docs.djangoproject.com/en/5.2/topics/db/transactions/).
