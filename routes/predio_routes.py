# routes/predio_routes.py

from flask import (
    Blueprint,
    session,
    flash,
    redirect,
    request,
    url_for
)

from services.auth_service import (
    login_required,
    user_has_predio_access
)

from models.predio_model import (
    get_all_predios
)

# =========================================================
# BLUEPRINT
# =========================================================
predio_bp = Blueprint(
    "predios",
    __name__
)


# =========================================================
# CAMBIAR PREDIO ACTIVO
# =========================================================
@predio_bp.route(
    "/cambiar-predio/<int:predio_id>"
)
@login_required
def cambiar_predio(predio_id):

    # ================================================
    # VALIDAR ACCESO
    # ================================================
    if not user_has_predio_access(
        predio_id
    ):

        flash(
            "No tiene acceso a ese predio.",
            "danger"
        )

        return redirect(
            url_for("citas.home")
        )

    # ================================================
    # OBTENER NOMBRE DEL PREDIO
    # ================================================
    predios = get_all_predios()

    predio_nombre = None

    for predio in predios:

        if predio["id"] == predio_id:

            predio_nombre = predio["nombre"]
            break

    if not predio_nombre:

        flash(
            "Predio no encontrado.",
            "danger"
        )

        return redirect(
            url_for("citas.home")
        )

    # ================================================
    # GUARDAR EN SESIÓN
    # ================================================
    session["active_predio_id"] = predio_id
    session["active_predio_nombre"] = predio_nombre

    flash(
        f"Predio activo: {predio_nombre}",
        "success"
    )

    # ================================================
    # REDIRECCIONAR
    # ================================================
    previous_url = request.referrer

    if previous_url:

        return redirect(
            previous_url
        )

    return redirect(
        url_for("citas.home")
    )