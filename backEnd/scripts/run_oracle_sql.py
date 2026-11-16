import os
import sys
from pathlib import Path

import oracledb
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def statements(path: Path):
    buffer = []
    plsql = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not buffer and (not line or line.startswith("--")):
            continue
        if not buffer:
            plsql = line.upper().startswith(("BEGIN", "DECLARE"))
        if plsql and line == "/":
            yield "\n".join(buffer)
            buffer, plsql = [], False
            continue
        buffer.append(raw)
        if not plsql and line.endswith(";"):
            yield "\n".join(buffer)[:-1]
            buffer = []
    if buffer:
        yield "\n".join(buffer)


def main():
    dsn = os.environ["ORACLE_DSN"]
    user = os.environ["ORACLE_USER"]
    password = os.environ["ORACLE_PASSWORD"]
    paths = [ROOT / "backEnd/sql/01_crear_tablas.sql", ROOT / "backEnd/sql/02_datos_ejemplo.sql"]
    with oracledb.connect(user=user, password=password, dsn=dsn) as connection:
        with connection.cursor() as cursor:
            count = 0
            for path in paths:
                for sql in statements(path):
                    cursor.execute(sql)
                    count += 1
                print(f"OK: {path.name}")
        connection.commit()
        print(f"Oracle configurado correctamente ({count} sentencias).")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise

