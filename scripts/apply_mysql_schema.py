from pathlib import Path

import pymysql


HOST = "8.152.207.153"
PORT = 3306
USER = "root"
PASSWORD = "wzlwzl200114"
SQL_FILE = Path(__file__).resolve().parents[1] / "sql" / "init_fund_codex.sql"


def main() -> None:
    sql = SQL_FILE.read_text(encoding="utf-8")
    connection = pymysql.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        charset="utf8mb4",
        autocommit=True,
        client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS,
    )

    try:
        with connection.cursor() as cursor:
            for statement in [s.strip() for s in sql.split(";") if s.strip()]:
                cursor.execute(statement)

            cursor.execute("SHOW DATABASES LIKE 'fund_codex'")
            db_exists = cursor.fetchone()

            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'fund_codex'
                ORDER BY table_name
                """
            )
            tables = [row[0] for row in cursor.fetchall()]
    finally:
        connection.close()

    print(f"database_exists={bool(db_exists)}")
    print("tables=")
    for table in tables:
        print(table)


if __name__ == "__main__":
    main()
