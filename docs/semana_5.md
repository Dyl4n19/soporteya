# Semana 5 — API REST de SoporteYa

Entrega individual. Verificación: 26 de noviembre de 2026.

## Correspondencia con la pauta

| Requisito | Implementación y evidencia |
| --- | --- |
| 1. DRF y CORS configurados | `backEnd/soporteya_project/settings.py`: DRF, JSON, autenticación con cookie, CSRF, paginación y manejo de errores. `CorsMiddleware` se ejecuta antes de `CommonMiddleware`; el origen de `FRONTEND_ORIGIN` puede usar cookies. Las pruebas comprueban preflight, credenciales y exclusión de otros orígenes. |
| 2. Serializers de las cinco, detalle anidado | Los serializers validan largos, rangos, correo y formato del RUT. El servidor asigna las fechas de creación y cierre. El ticket devuelve los nombres relacionados y los comentarios anidados. Una línea inválida identifica su índice y campo. |
| 3. Rutas REST, códigos HTTP y errores JSON | `urls.py`, `views.py` y `exceptions.py` del adaptador API. CRUD, acción de estado, sesión y reporte. Errores con `message` y `field`, incluidas rutas desconocidas, JSON mal formado, método o formato no permitido. |
| 4. Permisos por rol, búsqueda, filtro y paginación | `permissions.py`, `pagination.py`, serializers de consulta y repositorios. Supervisor con acceso completo; técnico limitado a sus tickets y operaciones permitidas. Las cinco listas tienen búsqueda, filtros, orden y páginas. |
| 5. Reporte y colección Postman | `GET /api/reportes/soporte/` entrega vencidos y promedio de resolución por técnico. La colección cubre los 17 casos del Anexo B con 101 solicitudes y 281 comprobaciones aprobadas. [Colección](postman_collection.json) · [Evidencia](evidencias/semana5_api.json). |

Las columnas de entrega y calificación las completa el docente. Esta guía corresponde a la pauta de API REST; no acredita otras semanas ni datos administrativos pendientes.

## Ejecutar la demostración completa desde la terminal

Abrir la carpeta del proyecto en Visual Studio Code. Desde la raíz:

```powershell
cd backEnd
.\.venv\Scripts\python.exe manage.py verificar_semana5 --postman
```

El comando ejecuta todas las pruebas y levanta automáticamente un servidor Django temporal en un puerto libre. Newman envía las solicitudes HTTP reales, conserva las cookies, obtiene y renueva el CSRF y comprueba cada respuesta. Prepara los dos roles y los datos necesarios en dos bases SQLite de prueba en memoria. Fuerza `soporteya_project.test_settings`, aunque se invoque desde la configuración habitual de Oracle.

Se necesitan las dependencias de `requirements.txt`, Node.js y pnpm. `pnpm dlx newman@6.2.1` descarga Newman la primera vez. No es necesario mantener `runserver` abierto para esta demostración aislada.

Resultado obtenido:

```text
166 passed
Semana 5 verificada correctamente.
```

Ese total incluye 165 pruebas de Python y una integración que ejecuta la colección completa. Postman comprueba el token por cabecera con las cookies desactivadas, los tres conflictos R1–R3 y el listado que devuelve `401` justo después del logout.

Para ejecutar solo Python:

```powershell
.\.venv\Scripts\python.exe manage.py verificar_semana5
```

El resultado es `165 passed, 1 skipped` al omitir la integración Postman. Este comando regenera el resumen de solicitudes, códigos HTTP y aserciones.

```powershell
.\.venv\Scripts\python.exe manage.py verificar_semana5 --postman --evidencia ..\docs\evidencias\semana5_api.json
```

La evidencia indica que esta ejecución HTTP utiliza SQLite temporal. La comprobación reproducible del esquema Oracle se mantiene disponible mediante `verificar_semana1`; el CRUD y rollback en la base configurada se demuestran con `verificar_semana3 --crud`.

Con el cliente de pruebas de Django conectado a Oracle, las cinco listas y el reporte devolvieron `200`. En una transacción aparte se verificaron un RUT inválido, su normalización, un duplicado guardado sin puntos, un ticket con dos comentarios, el rechazo de un vencimiento contradictorio y un comentario incompleto. Tras el rollback las cinco tablas conservaron sus cinco registros originales. [Resultados de Oracle](evidencias/semana5_oracle.json).

## Importar la colección en Postman

1. Iniciar el backend con `python manage.py runserver`, con Oracle o con una base SQLite de demostración preparada según el README.
2. Ejecutar `python manage.py setup_demo`. Para una base SQLite nueva, ejecutar también sus migraciones de negocio y `python manage.py seed_business`.
3. Importar `docs/postman_collection.json` en Postman.
4. Revisar las variables de la colección: `baseUrl`, `frontendOrigin`, usuarios y contraseñas. `tecnicoEmail` debe coincidir con el correo del técnico asociado al usuario; por defecto es Camila Rojas.
5. Ejecutar una iteración de la colección en orden, con las cookies habilitadas. Las peticiones de prueba por cabecera desactivan las cookies individualmente y usan el token de la sesión actual.

La colección obtiene los identificadores al crear o buscar registros y genera nombres y RUT de demostración distintos en cada ejecución. El CSRF se actualiza después de cada login. Las contraseñas iniciales son de desarrollo; `setup_demo` conserva las de cuentas existentes.

Para probar la cabecera, la colección lee la cookie HttpOnly de la respuesta de login de Postman, mantiene el valor en una variable temporal de la ejecución y llama a `GET /api/auth/me/` con `Authorization: Token <valor>`. El resultado es `200` con usuario y rol. La petición siguiente usa un token inválido y obtiene `401`. En las escrituras se exige además una cookie CSRF válida y la cabecera `X-CSRFToken`.

Al ejecutar manualmente contra una base persistente se crean datos de demostración. El ticket que llega a `CERRADO`, su empresa, categoría y comentarios se conservan por las reglas de negocio. La ejecución mediante `verificar_semana5 --postman` elimina sus bases temporales al finalizar.

## Rutas y códigos

Todas las rutas indicadas requieren la barra final y responden JSON, salvo respuestas sin cuerpo como `204`. Los cuerpos de escritura usan `Content-Type: application/json`.

| Ruta | Métodos y comportamiento |
| --- | --- |
| `/api/empresas/`, `/api/categorias/`, `/api/tecnicos/` | `GET` lista paginada; `POST` crea con `201`. |
| `/api/empresas/{id}/`, `/api/categorias/{id}/`, `/api/tecnicos/{id}/` | `GET`, `PUT` completo y `PATCH` parcial con `200`; `DELETE` libre con `204`. |
| `/api/tickets/` | `GET` lista paginada; `POST` crea principal y comentarios en una transacción con `201`. |
| `/api/tickets/{id}/` | `GET`, `PUT` y `PATCH` con `200`; eliminación de un ticket inicial y su detalle con `204`. |
| `/api/tickets/{id}/estado/` | `POST` valida la transición y devuelve `200`. |
| `/api/tickets/{id}/comentarios/` | `GET` lista paginada; `POST` crea con autor de la sesión y número automático, `201`. |
| `/api/tickets/{id}/comentarios/{numero}/` | `GET`, `PUT`, `PATCH` con `200`; `DELETE` permitido con `204`. La identidad combina ticket y número. |
| `/api/auth/csrf/`, `/api/auth/login/`, `/api/auth/me/`, `/api/auth/logout/` | CSRF `GET 200`, login `POST 200`, identidad `GET 200` y logout `POST 204`. Login incorrecto: `400`. |
| `/api/reportes/soporte/` | `GET 200`, reservado al supervisor. |

| Código de error | Caso |
| --- | --- |
| `400` | Validación, JSON mal formado, campos no permitidos o tamaño de página inválido. |
| `401` | Credencial de autenticación ausente, inválida o revocada tras el logout. |
| `403` | Operación sin permiso o CSRF ausente/inválido. |
| `404` | Recurso o ruta inexistente, página fuera de rango o ticket ajeno al técnico. |
| `405` | Método no permitido. |
| `406` | El cliente exige un formato de respuesta distinto de JSON. |
| `409` | Duplicado, registro referenciado, regla de negocio o transición inválida. |
| `415` | Formato del cuerpo no soportado. |
| `500` | Error inesperado: mensaje genérico JSON; el detalle se registra en el servidor. |

Ejemplo de detalle inválido en la segunda línea, antes de guardar el ticket:

```json
{
  "message": "Asegúrese de que este campo tenga al menos 2 caracteres.",
  "field": "comentarios.1.texto"
}
```

La redacción del mensaje depende de la traducción de DRF. `field` identifica el campo o vale `null` si el error es general. Los índices de detalle comienzan en cero.

## Consultas de las cinco listas

Todas aceptan `search`, `ordering`, `page` y `page_size`. Se entregan diez resultados por defecto; `page_size` debe ser un entero entre 1 y 100. La respuesta tiene `count`, `next`, `previous` y `results`.

| Lista | Búsqueda | Filtros | Campos de orden permitidos |
| --- | --- | --- | --- |
| Empresas | RUT y razón social | `plan`, `activo` | `id_empresa`, `rut`, `razon_social`, `plan`, `activo` |
| Categorías | Nombre | `activo` | `id_categoria`, `nombre`, `horas_sla`, `activo` |
| Técnicos | RUT, nombre y correo | `activo` | `id_tecnico`, `rut`, `nombre`, `email`, `activo` |
| Tickets | Título, descripción y empresa | `estado`, `prioridad`, `categoria_id`, `tecnico_id` | `id_ticket`, `titulo`, `prioridad`, `estado`, `fecha_creacion`, `fecha_cierre` |
| Comentarios | Texto y autor dentro del ticket | `autor`, `numero` | `numero`, `fecha`, `autor` |

Un signo `-` indica orden descendente. Los términos de búsqueda se combinan; los campos de orden se limitan a una lista permitida. El filtro de técnico enviado por un usuario no amplía sus permisos: siempre se restringen las consultas a los tickets asociados a su correo.

Ejemplos:

```text
/api/empresas/?search=Andina&plan=PREMIUM&activo=true&page_size=1
/api/categorias/?search=Red&ordering=nombre&page=2&page_size=1
/api/tickets/?estado=ASIGNADO&prioridad=ALTA&ordering=-fecha_creacion
/api/tickets/1/comentarios/?search=diagnostico&ordering=-numero&page_size=1
```

## Permisos y reporte

El supervisor administra las cinco entidades y consulta el reporte. El técnico ve la empresa, categoría y detalles de sus tickets asignados, avanza sus estados válidos y agrega comentarios. Consultar los catálogos globales, modificar la cabecera o consultar el reporte con este rol devuelve `403`. Consultar un ticket ajeno devuelve `404`.

El reporte contiene `tickets_vencidos` y `promedio_resolucion_por_tecnico`, en horas numéricas. R3 considera vencido un ticket que haya superado el SLA y siga sin resolver. La prueba HTTP incluye un ticket de cinco horas con SLA de cuatro. Otra prueba comprueba un promedio exacto de dos horas.

Para el caso 12 del Anexo B, Postman envía `PATCH /api/tickets/{id}/` con `{"vencido": true}` para un ticket recién creado. El caso de uso calcula el vencimiento a partir de la fecha, el estado y el SLA de la categoría. Si el valor enviado contradice el cálculo, responde `409` con el campo `vencido` y revierte la edición. Una actualización normal o un cambio de estado pueden continuar aunque el ticket esté vencido.

## Referencias técnicas

La paginación y la traducción de excepciones se basan en las guías oficiales de [DRF Pagination](https://www.django-rest-framework.org/api-guide/pagination/) y [DRF Exceptions](https://www.django-rest-framework.org/api-guide/exceptions/). La configuración del middleware y credenciales sigue [django-cors-headers 4.9.0](https://pypi.org/project/django-cors-headers/4.9.0/). La colección usa el formato 2.1 compatible con [Newman](https://learning.postman.com/docs/reference/newman-cli/command-line-integration-with-newman/).
