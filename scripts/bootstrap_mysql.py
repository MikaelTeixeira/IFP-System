"""Create the local MySQL database and a dedicated application user."""

from getpass import getpass
from pathlib import Path
import secrets
import subprocess
import sys

import pymysql


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_NAME = "instituto_fabiana_pinto"
APPLICATION_USER = "ifp_app"


def main():
    admin_user = input("Usuário administrador do MySQL [root]: ").strip() or "root"
    admin_password = getpass("Senha do administrador MySQL: ")
    application_password = secrets.token_urlsafe(24)

    connection = pymysql.connect(
        host="127.0.0.1",
        port=3306,
        user=admin_user,
        password=admin_password,
        charset="utf8mb4",
        autocommit=True,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DATABASE_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            for host in ("localhost", "127.0.0.1"):
                cursor.execute(
                    f"CREATE USER IF NOT EXISTS '{APPLICATION_USER}'@'{host}' IDENTIFIED BY %s",
                    (application_password,),
                )
                cursor.execute(
                    f"ALTER USER '{APPLICATION_USER}'@'{host}' IDENTIFIED BY %s",
                    (application_password,),
                )
                cursor.execute(
                    f"GRANT ALL PRIVILEGES ON `{DATABASE_NAME}`.* TO '{APPLICATION_USER}'@'{host}'"
                )
            cursor.execute("FLUSH PRIVILEGES")
    finally:
        connection.close()

    instance_dir = PROJECT_ROOT / "instance"
    instance_dir.mkdir(exist_ok=True)
    settings_path = instance_dir / "mysql.env"
    settings_path.write_text(
        "\n".join([
            "IFP_MYSQL_HOST=127.0.0.1",
            "IFP_MYSQL_PORT=3306",
            f"IFP_MYSQL_DATABASE={DATABASE_NAME}",
            f"IFP_MYSQL_USER={APPLICATION_USER}",
            f"IFP_MYSQL_PASSWORD={application_password}",
            "",
        ]),
        encoding="utf-8",
    )

    subprocess.run(
        [sys.executable, "-m", "flask", "--app", "run.py", "init-db"],
        cwd=PROJECT_ROOT,
        check=True,
    )
    print("MySQL configurado. Reinicie o servidor Flask para usar a conexão persistente.")


if __name__ == "__main__":
    main()
