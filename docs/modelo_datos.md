# Modelo de datos — SoporteYa

```mermaid
erDiagram
    EMPRESAS ||--o{ TICKETS : registra
    CATEGORIAS_TICKET ||--o{ TICKETS : clasifica
    TECNICOS o|--o{ TICKETS : atiende
    TICKETS ||--o{ COMENTARIOS_TICKET : contiene

    EMPRESAS {
        number id_empresa PK
        varchar2 rut UK
        varchar2 razon_social
        varchar2 plan
        number activo
    }

    CATEGORIAS_TICKET {
        number id_categoria PK
        varchar2 nombre UK
        number horas_sla
        number activo
    }

    TECNICOS {
        number id_tecnico PK
        varchar2 rut UK
        varchar2 nombre
        varchar2 email UK
        number activo
    }

    TICKETS {
        number id_ticket PK
        number id_empresa FK
        number id_categoria FK
        number id_tecnico FK
        varchar2 titulo
        clob descripcion
        varchar2 prioridad
        timestamp fecha_creacion
        timestamp fecha_cierre
        varchar2 estado
    }

    COMENTARIOS_TICKET {
        number id_ticket PK,FK
        number numero PK
        timestamp fecha
        varchar2 autor
        clob texto
    }
```

## Cardinalidades

- Una empresa puede registrar muchos tickets; cada ticket pertenece a una empresa.
- Una categoría puede clasificar muchos tickets; cada ticket tiene una categoría.
- Un técnico puede atender muchos tickets; un ticket puede estar todavía sin técnico mientras permanezca abierto.
- Un ticket puede contener muchos comentarios; cada comentario pertenece a un único ticket.

La clave de `comentarios_ticket` es compuesta por `id_ticket` y `numero`.

