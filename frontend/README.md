# Frontend SoporteYa

## Ejecutar

```bash
pnpm install --frozen-lockfile
copy .env.example .env
pnpm dev
```

La aplicación queda disponible en `http://localhost:5173` y espera la API en `http://localhost:8000/api`.

La sesión usa una cookie HttpOnly; el frontend recupera al usuario con `/api/auth/me/` y envía CSRF en solicitudes de escritura.

El supervisor puede crear tickets con varios comentarios, editar y asignar los abiertos, eliminarlos y gestionar el detalle. El técnico solo ve sus tickets, avanza estados y comenta. La autorización también se valida en el backend.

Los usuarios locales y los comandos de verificación están en el [README principal](../README.md) y en la [guía de semana 3](../docs/semana_3.md).

