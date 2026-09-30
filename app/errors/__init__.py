from flask import render_template


def register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html", page_title="Acesso restrito"), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html", page_title="Página não encontrada"), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template("errors/500.html", page_title="Algo não funcionou"), 500

