# app.py

from flask import Flask, redirect, url_for, session

from config import Config
from models.predio_model import get_predios_by_user

# =========================================================
# IMPORTACIÓN DE BLUEPRINTS
# =========================================================
from routes.auth_routes import auth_bp
from routes.cita_routes import cita_bp
from routes.porton_routes import porton_bp
from routes.dashboard_routes import dashboard_bp
from routes.export_routes import export_bp
from routes.user_routes import user_bp
from routes.predio_routes import predio_bp

# =========================================================
# CREACIÓN DE APP
# =========================================================
app = Flask(__name__)

# =========================================================
# CONFIGURACIÓN
# =========================================================
app.config.from_object(Config)

# =========================================================
# REGISTRO DE BLUEPRINTS
# =========================================================
app.register_blueprint(auth_bp)
app.register_blueprint(cita_bp)
app.register_blueprint(porton_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(export_bp)
app.register_blueprint(user_bp)
app.register_blueprint(predio_bp)


# =========================================================
# RUTA PRINCIPAL
# =========================================================
@app.route("/")
def root():

    if "user_id" not in session:

        return redirect(
            url_for("auth.login")
        )

    role = session.get("role")

    if role == "GUARDA":

        return redirect(
            url_for("porton.porton_home")
        )

    return redirect(
        url_for("citas.home")
    )


# =========================================================
# CONTEXTO GLOBAL PARA TEMPLATES
# =========================================================
@app.context_processor
def inject_user():

    user_id = session.get("user_id")

    predios_disponibles = []

    if user_id:

        predios_disponibles = get_predios_by_user(
            user_id
        )

    return {
        "current_user": {
            "id": session.get("user_id"),
            "username": session.get("username"),
            "role": session.get("role")
        },
        "user_predios": session.get("predios", []),
        "predios_disponibles": predios_disponibles,
        "active_predio_id": session.get("active_predio_id"),
        "active_predio_nombre": session.get("active_predio_nombre")
    }


# =========================================================
# EJECUCIÓN
# =========================================================
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=Config.DEBUG
    )


