# routes/porton_routes.py

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from services.auth_service import (
    login_required,
    role_required,
    user_has_predio_access
)

from services.porton_service import (
    get_pending_citas_for_porton,
    get_porton_cita_detail,
    confirm_cita_from_porton,
    get_porton_stats
)

# =========================================================
# BLUEPRINT
# =========================================================
porton_bp = Blueprint(
    "porton",
    __name__
)


# =========================================================
# HOME PORTÓN
# =========================================================
@porton_bp.route("/porton")
@login_required
@role_required(["GUARDA", "ADMIN"])
def porton_home():

    predio_id = session.get(
        "active_predio_id"
    )

    if not predio_id:

        flash(
            "Debe seleccionar un predio.",
            "warning"
        )

        return redirect(
            url_for("citas.home")
        )

    if not user_has_predio_access(
        predio_id
    ):

        flash(
            "No tiene acceso a este predio.",
            "danger"
        )

        return redirect(
            url_for("citas.home")
        )

    citas = get_pending_citas_for_porton(
        [predio_id]
    )

    stats = get_porton_stats(
        [predio_id]
    )

    return render_template(
        "porton.html",
        citas=citas,
        stats=stats,
        predio_actual=predio_id
    )


# =========================================================
# DETALLE DE CITA
# =========================================================
@porton_bp.route(
    "/porton/cita/<int:cita_id>"
)
@login_required
@role_required(["GUARDA", "ADMIN"])
def porton_cita_detail(cita_id):

    cita = get_porton_cita_detail(
        cita_id
    )

    if not cita:

        flash(
            "Cita no encontrada.",
            "danger"
        )

        return redirect(
            url_for("porton.porton_home")
        )

    # ================================================
    # VALIDAR ACCESO A PREDIO
    # ================================================
    if not user_has_predio_access(
        cita["predio_id"]
    ):

        flash(
            "No tiene acceso a este predio.",
            "danger"
        )

        return redirect(
            url_for("porton.porton_home")
        )

    return render_template(
        "porton_detalle.html",
        cita=cita
    )


# =========================================================
# CONFIRMAR CITA
# =========================================================
@porton_bp.route(
    "/porton/confirmar/<int:cita_id>",
    methods=["POST"]
)
@login_required
@role_required(["GUARDA", "ADMIN"])
def confirmar_cita_porton(cita_id):

    cita = get_porton_cita_detail(
        cita_id
    )

    if not cita:

        flash(
            "Cita no encontrada.",
            "danger"
        )

        return redirect(
            url_for("porton.porton_home")
        )

    if not user_has_predio_access(
        cita["predio_id"]
    ):

        flash(
            "No tiene acceso a este predio.",
            "danger"
        )

        return redirect(
            url_for("porton.porton_home")
        )

    contenedor_registrado = (
        request.form.get(
            "contenedor_registrado",
            ""
        ).strip()
    )

    servicio_terminal = (
        request.form.get(
            "servicio_terminal",
            ""
        ).strip()
    )

    result = confirm_cita_from_porton(
        cita_id=cita_id,
        contenedor_registrado=contenedor_registrado,
        servicio_terminal=servicio_terminal,
        user_id=session["user_id"]
    )

    if not result["success"]:

        flash(
            result["message"],
            "danger"
        )

        return redirect(
            url_for(
                "porton.porton_cita_detail",
                cita_id=cita_id
            )
        )

    flash(
        "Cita confirmada correctamente.",
        "success"
    )

    return redirect(
        url_for("porton.porton_home")
    )