# SoporteYa

Proyecto final de Programación Back End para la gestión de tickets de una mesa de ayuda TI.

## Estado actual

Aplicación completa con arquitectura hexagonal, scripts Oracle, CRUD, autenticación, roles, API REST, pruebas, reporte SLA y frontend React.

La conexión SQLNet con Oracle FreeSQL 26ai fue validada y los scripts cargaron correctamente 5 empresas, 5 categorías, 5 técnicos, 5 tickets y 5 comentarios en el esquema configurado localmente.

## Tecnologías requeridas

- Python 3.12+
- Django 5.2 LTS
- Django REST Framework
- Oracle FreeSQL con `oracledb` en modo thin
- React + Vite
- Node.js 20+

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
- R3: un ticket está vencido cuando supera las horas de SLA de su categoría sin llegar a `RESUELTO` o `CERRADO`.

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
pnpm install
Copy-Item .env.example .env
pnpm dev
```

Usuarios demostrativos locales (cambiar antes de entregar):

- `supervisor` / `Cambiar123!`
- `tecnico` / `Cambiar123!`

## API principal

- `GET /api/auth/csrf/`
- `POST /api/auth/login/`
- `GET /api/auth/me/`
- `POST /api/auth/logout/`
- CRUD `/api/empresas/`, `/api/categorias/`, `/api/tecnicos/`
- `/api/tickets/`
- `POST /api/tickets/{id}/comentarios/`
- `POST /api/tickets/{id}/estado/`
- `GET /api/reportes/soporte/`

## Pruebas

```powershell
cd backEnd
pytest -q
```

