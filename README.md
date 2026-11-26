# SoporteYa

Proyecto final de Programación Back End para la gestión de tickets de una mesa de ayuda TI.

## Estado actual

SoporteYa gestiona tickets, empresas, categorías, técnicos y comentarios con Django, Oracle y una interfaz React. El backend expone el CRUD y el reporte de SLA a través de una API REST.

La conexión SQLNet con Oracle FreeSQL 26ai fue validada y los scripts cargaron correctamente 5 empresas, 5 categorías, 5 técnicos, 5 tickets y 5 comentarios en el esquema configurado localmente.

## Avance de semana 1

Entrega individual que abarca las cinco entidades. El [Anexo A](docs/anexo_a.md) identifica el problema y el reparto; el número administrativo de grupo, la sección y la inscripción quedan por confirmar con el docente.

La [guía de semana 1](docs/semana_1.md) contiene el modelo, el diccionario, los scripts, la captura del informe de consulta real a Oracle y el comando `python manage.py verificar_semana1` para repetir la comprobación sin modificar datos.

## Avance de semana 2

Entrega individual. Se implementaron las entidades y puertos de las cinco tablas, las excepciones de negocio y el CRUD de empresas, categorías y técnicos mediante casos de uso y repositorios. Los repositorios devuelven entidades de dominio; los casos de uso no dependen de Django.

La [guía de semana 2](docs/semana_2.md) relaciona cada punto de la pauta con sus archivos y contiene los comandos para demostrarlo. Los aportes están registrados en la [bitácora](docs/bitacora.md) y en el historial de Git.

## Avance de semana 3

CRUD de las cinco tablas, tickets con comentarios anidados en una transacción, transiciones y reglas R1–R3 en los casos de uso, administrador con búsqueda y filtros, superusuario y dos roles con permisos distintos. Login, logout y `me` utilizan token en cookie HttpOnly y CSRF; el técnico solo accede a sus tickets.

Verificado con 117 pruebas automatizadas, una demostración transaccional en Oracle FreeSQL y revisión de las pantallas en navegador. La [guía de semana 3](docs/semana_3.md) contiene la evidencia, los comandos y el guion de demostración.

## Avance de semana 5 — API REST

DRF y CORS configurados, serializers de entrada y salida para las cinco entidades, comentarios anidados en tickets, rutas REST y errores JSON uniformes. Las cinco listas permiten búsqueda, filtros, orden y paginación; los permisos distinguen supervisor y técnico. El reporte incluye tickets vencidos y promedio de resolución por técnico.

Pasaron **166 pruebas**. La colección ejecutó **101 solicitudes HTTP y 281 comprobaciones**, cubriendo los 17 casos del Anexo B con bases temporales. La guía explica cómo repetir la demostración. [Guía de semana 5](docs/semana_5.md) · [Colección Postman](docs/postman_collection.json) · [Resultados](docs/evidencias/semana5_api.json).

En Oracle se comprobaron las cinco listas, el reporte y seis casos con una transacción temporal, entre ellos el RUT duplicado y el conflicto de SLA. Después de revertir la transacción había cinco registros en cada tabla. [Evidencia de Oracle](docs/evidencias/semana5_oracle.json).

## Tecnologías requeridas

- Python 3.12+
- Django 5.2 LTS
- Django REST Framework
- Oracle FreeSQL con `oracledb` en modo thin
- React + Vite
- Node.js 22.12+ y pnpm

## Estructura

```text
soporteya/
├── backEnd/
│   └── sql/
├── docs/
├── frontend/
├── .env.example
├── .gitignore
└── README.md
```

## Reglas de negocio

- R1: para asignar un ticket se exige un técnico activo; para resolverlo debe existir al menos un comentario.
- R2: los tickets de empresas con plan `PREMIUM` se crean, como mínimo, con prioridad `ALTA`.
- R3: un ticket está vencido cuando supera las horas de SLA de su categoría sin llegar a `RESUELTO` o `CERRADO`. Se calcula en el caso de uso.

## Roles

- `SUPERVISOR`: acceso completo.
- `TECNICO`: ve y avanza únicamente sus tickets y puede agregar comentarios.

## Ejecución inicial de Oracle

Ejecutar en este orden dentro del esquema personal de cada integrante:

1. `backEnd/sql/01_crear_tablas.sql`
2. `backEnd/sql/02_datos_ejemplo.sql`

No subir credenciales reales al repositorio. Cada integrante debe copiar `.env.example` como `.env` y completar sus propios valores.

## Ejecutar el backend

```powershell
cd backEnd
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py setup_demo
python manage.py runserver
```

Para una demostración local sin Oracle, defina `BUSINESS_DB_ENGINE=sqlite`, ejecute además `python manage.py migrate --database negocio` y `python manage.py seed_business`.

Para Oracle FreeSQL, defina `BUSINESS_DB_ENGINE=oracle`, complete `ORACLE_USER`, `ORACLE_PASSWORD` y `ORACLE_DSN`, ejecute los dos scripts SQL desde FreeSQL y luego inicie Django. Las tablas del negocio usan `managed = False`; Django no intentará crearlas ni modificarlas.

## Ejecutar el frontend

```powershell
cd frontend
pnpm install --frozen-lockfile
Copy-Item .env.example .env
pnpm dev
```

## Usuarios de demostración local

`python manage.py setup_demo` prepara estos usuarios. Las contraseñas de usuarios que ya existían se conservan.

| Usuario | Contraseña inicial | Acceso |
| --- | --- | --- |
| `admin` | `CambiarAdmin123!` | Superusuario y panel Django. |
| `supervisor` | `Cambiar123!` | Rol `SUPERVISOR`, CRUD completo y panel de negocio; no es superusuario. |
| `tecnico` | `Cambiar123!` | Rol `TECNICO`, consulta y avance de sus tickets y creación de comentarios. |

Administrador: `http://localhost:8000/admin/`. El técnico de demostración se asocia por correo a Camila Rojas. Estos usuarios y contraseñas son exclusivamente para desarrollo local.

## API principal

- `GET /api/auth/csrf/`
- `POST /api/auth/login/`
- `GET /api/auth/me/`
- `POST /api/auth/logout/`
- CRUD `/api/empresas/`, `/api/categorias/`, `/api/tecnicos/`
- CRUD `/api/tickets/`, `/api/tickets/{id}/`
- Comentarios: `GET/POST /api/tickets/{id}/comentarios/`
- Comentario individual: `GET/PUT/PATCH/DELETE /api/tickets/{id}/comentarios/{numero}/`
- `POST /api/tickets/{id}/estado/`
- `GET /api/reportes/soporte/`

Antes del login, pedir `GET /api/auth/csrf/` y enviar el valor recibido en `X-CSRFToken`. Al iniciar sesión se renueva el CSRF y el navegador recibe la cookie de autenticación HttpOnly. Postman también puede enviar el token en la cabecera `Authorization: Token <valor>`. Las escrituras y el logout exigen la cookie CSRF y el encabezado correspondiente en ambos modos.

## Pruebas

```powershell
cd backEnd
python -m pytest -q
```

Pytest utiliza `soporteya_project.test_settings`: las dos bases de prueba son SQLite en memoria y no modifican Oracle ni las bases locales de la aplicación.

Para verificar la conexión y las entidades de las cinco tablas en la base configurada:

```powershell
python manage.py verificar_semana2
```

Para demostrar además el CRUD de las tres maestras con registros temporales y una transacción que se revierte al terminar:

```powershell
python manage.py verificar_semana2 --crud
```

Para demostrar la semana 3 en la base configurada, incluidos el CRUD de las cinco tablas, las reglas y un fallo controlado del segundo comentario:

```powershell
python manage.py verificar_semana3 --crud
```

La demostración utiliza registros temporales y revierte la transacción al finalizar. Para ejecutar solo las comprobaciones de roles y consultas, omitir `--crud`.

Para verificar esta entrega de API REST, incluida la colección Postman ejecutada por HTTP con cookies y CSRF:

```powershell
python manage.py verificar_semana5 --postman
```

Requiere Node.js y pnpm; Newman 6.2.1 se descarga la primera vez. El comando fuerza la configuración de pruebas y prepara sus usuarios y datos en bases temporales. Para ejecutar solo las pruebas de Python, usar `python manage.py verificar_semana5`. Las consultas de listas responden con `count`, `next`, `previous` y `results`; `page_size` admite de 1 a 100 y el tamaño predeterminado es 10.
