# Frontend SoporteYa

## Ejecutar

```bash
pnpm install
copy .env.example .env
pnpm dev
```

La aplicación queda disponible en `http://localhost:5173` y espera la API en `http://localhost:8000/api`.

La sesión usa una cookie HttpOnly; el frontend recupera al usuario con `/api/auth/me/` y envía CSRF en solicitudes de escritura.

