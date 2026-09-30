import click
from sqlalchemy import inspect, text
from flask import current_app

from .data.academic import DATA, INITIAL_DATA
from .data.users import INITIAL_USER_ACCOUNTS, USER_ACCOUNTS
from .extensions import db
from .models import Institution, Municipality, UserAccount


def _seed_reference_data():
    if Municipality.query.count() == 0:
        db.session.add_all([
            Municipality(id=item["id"], name=item["nome"], state=item["uf"], code=item["codigo"], status=item["status"])
            for item in INITIAL_DATA["municipios"]
        ])
        db.session.flush()
    if Institution.query.count() == 0:
        db.session.add_all([
            Institution(id=item["id"], name=item["nome"], municipality_id=item["municipio_id"], code=item["codigo"], status=item["status"])
            for item in INITIAL_DATA["instituicoes"]
        ])
        db.session.flush()
    if UserAccount.query.count() == 0:
        db.session.add_all([
            UserAccount(
                id=item["id"], name=item["nome"], cpf=item["cpf"], email=item["email"], role=item["cargo"],
                municipality_id=item["municipio_id"] or None, institution_id=item["instituicao_id"] or None,
                status=item["status"],
            )
            for item in INITIAL_USER_ACCOUNTS
        ])
    db.session.commit()


def _refresh_compatibility_data():
    DATA["municipios"][:] = [item.to_record() for item in Municipality.query.order_by(Municipality.id).all()]
    DATA["instituicoes"][:] = [item.to_record() for item in Institution.query.order_by(Institution.id).all()]
    USER_ACCOUNTS[:] = [item.to_record() for item in UserAccount.query.order_by(UserAccount.id).all()]


def create_and_seed_database():
    db.create_all()
    if db.engine.dialect.name == "mysql":
        unique_names = {item.get("name") for item in inspect(db.engine).get_unique_constraints("assessment_attempts")}
        if "uq_attempt_assessment_student" in unique_names:
            db.session.execute(text("ALTER TABLE assessment_attempts DROP INDEX uq_attempt_assessment_student"))
            db.session.commit()
    _seed_reference_data()
    _refresh_compatibility_data()


def init_database(app):
    db.init_app(app)

    @app.cli.command("init-db")
    def init_db_command():
        """Create the configured database tables and initial records."""
        if not current_app.config["DATABASE_ENABLED"]:
            raise click.ClickException("Configure instance/mysql.env antes de inicializar o MySQL.")
        create_and_seed_database()
        click.echo("Tabelas criadas e dados iniciais carregados.")

    @app.cli.command("db-status")
    def db_status_command():
        """Show whether persistent database storage is enabled."""
        if not current_app.config["DATABASE_ENABLED"]:
            click.echo("Banco persistente desativado: configure instance/mysql.env.")
            return
        try:
            db.session.execute(db.select(Municipality).limit(1))
            click.echo("MySQL conectado e respondendo.")
        except Exception as exc:
            raise click.ClickException(f"Falha na conexão: {exc}") from exc

    if app.config["DATABASE_ENABLED"]:
        with app.app_context():
            create_and_seed_database()
