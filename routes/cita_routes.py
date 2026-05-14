# routes/cita_routes.py

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

from services.cita_service import (
    generate_time_slots,
    validate_slot_capacity,
    create_new_cita,
    create_multiple_citas,
    get_all_pending_citas,
    get_all_completed_citas,
    get_all_expired_citas,
    get_cita,
    remove_cita,
    check_expired_citas
)

from models.predio_model import (
    get_predios_by_user
)

from db import execute_query


# =========================================================
# BLUEPRINT
# =========================================================
cita_bp = Blueprint(
    "citas",
    __name__
)


# =========================================================
# HELPER PREDIO ACTIVO
# =========================================================
def get_active_predio_id(predios):

    predio_id = session.get("active_predio_id")

    if not predio_id and predios:

        predio_id = predios[0]["id"]
        session["active_predio_id"] = predio_id
        session["active_predio_nombre"] = predios[0]["nombre"]

    return predio_id


# =========================================================
# HOME
# =========================================================
@cita_bp.route("/inicio")
@login_required
def home():

    check_expired_citas()

    user_id = session.get("user_id")

    predios = get_predios_by_user(
        user_id
    )

    predio_id = get_active_predio_id(
        predios
    )

    if not predio_id or not user_has_predio_access(
        predio_id
    ):

        flash(
            "No tiene acceso a ese predio.",
            "danger"
        )

        return redirect(
            url_for("auth.logout")
        )

    citas = get_all_pending_citas(
        [predio_id]
    )

    return render_template(
        "index.html",
        citas=citas,
        predios=predios,
        predio_actual=predio_id
    )


# =========================================================
# VENCIDAS
# =========================================================
@cita_bp.route("/vencidas")
@login_required
def vencidas():

    user_id = session.get("user_id")

    predios = get_predios_by_user(
        user_id
    )

    predio_id = get_active_predio_id(
        predios
    )

    if not predio_id or not user_has_predio_access(
        predio_id
    ):

        flash(
            "No tiene acceso a ese predio.",
            "danger"
        )

        return redirect(
            url_for("auth.logout")
        )

    citas = get_all_expired_citas(
        [predio_id]
    )

    return render_template(
        "vencidas.html",
        citas=citas,
        predios=predios,
        predio_actual=predio_id
    )


# =========================================================
# COMPLETADAS
# =========================================================
@cita_bp.route("/completadas")
@login_required
def completadas():

    user_id = session.get("user_id")

    predios = get_predios_by_user(
        user_id
    )

    predio_id = get_active_predio_id(
        predios
    )

    if not predio_id or not user_has_predio_access(
        predio_id
    ):

        flash(
            "No tiene acceso a ese predio.",
            "danger"
        )

        return redirect(
            url_for("auth.logout")
        )

    citas = get_all_completed_citas(
        [predio_id]
    )

    return render_template(
        "completadas.html",
        citas=citas,
        predios=predios,
        predio_actual=predio_id
    )


# =========================================================
# CREAR CITA
# =========================================================
@cita_bp.route(
    "/crear-cita",
    methods=["GET", "POST"]
)
@login_required
@role_required(["ADMIN", "PREDIO"])
def crear_cita():

    user_id = session.get("user_id")

    predios = get_predios_by_user(
        user_id
    )

    predio_id = get_active_predio_id(
        predios
    )

    if request.method == "POST":

        data = {
            "contenedor":
                request.form.get("contenedor"),

            "chofer_nombre":
                request.form.get("chofer_nombre"),

            "chofer_cedula":
                request.form.get("chofer_cedula"),

            "cabezal_placa":
                request.form.get("cabezal_placa"),

            "fecha":
                request.form.get("fecha"),

            "horario":
                request.form.get("horario"),

            "naviera":
                request.form.get("naviera"),

            "estado_contenedor":
                request.form.get("estado_contenedor"),

            "tipo_operacion":
                request.form.get("tipo_operacion"),

            "predio_id":
                predio_id
        }

        if not data["predio_id"] or not user_has_predio_access(
            data["predio_id"]
        ):

            flash(
                "No tiene acceso a ese predio.",
                "danger"
            )

            return redirect(
                url_for("citas.home")
            )

        has_capacity = validate_slot_capacity(
            data["fecha"],
            data["horario"],
            data["predio_id"]
        )

        if not has_capacity:

            flash(
                "El horario ya alcanzó el límite permitido.",
                "danger"
            )

            return render_template(
                "crear_cita.html",
                time_slots=generate_time_slots(),
                predios=predios,
                predio_actual=predio_id
            )

        create_new_cita(
            data,
            user_id
        )

        flash(
            "Cita creada correctamente.",
            "success"
        )

        return redirect(
            url_for("citas.home")
        )

    return render_template(
        "crear_cita.html",
        time_slots=generate_time_slots(),
        predios=predios,
        predio_actual=predio_id
    )


# =========================================================
# CREACIÓN MASIVA
# =========================================================
@cita_bp.route(
    "/crear-citas-masivas",
    methods=["POST"]
)
@login_required
@role_required(["ADMIN", "PREDIO"])
def crear_citas_masivas():

    citas = request.json.get(
        "citas",
        []
    )

    result = create_multiple_citas(
        citas,
        session["user_id"]
    )

    if result["errors"]:

        flash(
            f"Se crearon {result['created']} citas.",
            "warning"
        )

    else:

        flash(
            "Citas creadas correctamente.",
            "success"
        )

    return {
        "success": True,
        "created": result["created"],
        "errors": result["errors"]
    }


# =========================================================
# EDITAR CITA
# =========================================================
@cita_bp.route(
    "/editar-cita/<int:cita_id>",
    methods=["GET", "POST"]
)
@login_required
@role_required(["ADMIN"])
def editar_cita(cita_id):

    user_id = session.get("user_id")

    predios = get_predios_by_user(
        user_id
    )

    cita = get_cita(cita_id)

    if not cita:

        flash(
            "Cita no encontrada.",
            "danger"
        )

        return redirect(
            url_for("citas.home")
        )

    if not user_has_predio_access(
        cita["predio_id"]
    ):

        flash(
            "No tiene acceso a ese predio.",
            "danger"
        )

        return redirect(
            url_for("citas.home")
        )

    if request.method == "POST":

        predio_id = session.get("active_predio_id")

        if not predio_id or not user_has_predio_access(
            predio_id
        ):

            flash(
                "No tiene acceso a ese predio.",
                "danger"
            )

            return redirect(
                url_for("citas.home")
            )

        query = """
            UPDATE citas
            SET
                contenedor = %s,
                chofer_nombre = %s,
                chofer_cedula = %s,
                cabezal_placa = %s,
                fecha = %s,
                horario = %s,
                naviera = %s,
                estado_contenedor = %s,
                tipo_operacion = %s,
                predio_id = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """

        execute_query(
            query,
            (
                request.form.get("contenedor"),
                request.form.get("chofer_nombre"),
                request.form.get("chofer_cedula"),
                request.form.get("cabezal_placa"),
                request.form.get("fecha"),
                request.form.get("horario"),
                request.form.get("naviera"),
                request.form.get("estado_contenedor"),
                request.form.get("tipo_operacion"),
                predio_id,
                cita_id
            ),
            commit=True
        )

        flash(
            "Cita actualizada.",
            "success"
        )

        return redirect(
            url_for("citas.home")
        )

    return render_template(
        "editar_cita.html",
        cita=cita,
        time_slots=generate_time_slots(),
        predios=predios,
        predio_actual=session.get("active_predio_id")
    )


# =========================================================
# ELIMINAR
# =========================================================
@cita_bp.route(
    "/eliminar-cita/<int:cita_id>",
    methods=["POST"]
)
@login_required
@role_required(["ADMIN"])
def eliminar_cita(cita_id):

    cita = get_cita(cita_id)

    if not cita:

        flash(
            "Cita no encontrada.",
            "danger"
        )

        return redirect(
            url_for("citas.home")
        )

    if not user_has_predio_access(
        cita["predio_id"]
    ):

        flash(
            "No tiene acceso a ese predio.",
            "danger"
        )

        return redirect(
            url_for("citas.home")
        )

    result = remove_cita(
        cita_id
    )

    if not result["success"]:

        flash(
            result["message"],
            "danger"
        )

        return redirect(
            url_for("citas.home")
        )

    flash(
        "Cita eliminada.",
        "success"
    )

    return redirect(
        url_for("citas.home")
    )