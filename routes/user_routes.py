# routes/user_routes.py

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from services.auth_service import (
    login_required,
    role_required
)

from services.user_service import (
    get_users,
    get_user,
    get_user_predios,
    get_predios,
    create_new_user,
    update_user_predios,
    change_user_status
)

# =========================================================
# BLUEPRINT
# =========================================================
user_bp = Blueprint(
    "users",
    __name__
)


# =========================================================
# LISTADO DE USUARIOS
# =========================================================
@user_bp.route("/usuarios")
@login_required
@role_required(["SUPERADMIN"])
def usuarios():

    users = get_users()

    return render_template(
        "usuarios.html",
        users=users
    )


# =========================================================
# CREAR USUARIO
# =========================================================
@user_bp.route(
    "/usuarios/crear",
    methods=["GET", "POST"]
)
@login_required
@role_required(["SUPERADMIN"])
def crear_usuario():

    predios = get_predios()

    if request.method == "POST":

        username = (
            request.form
            .get("username", "")
            .strip()
        )

        password = (
            request.form
            .get("password", "")
            .strip()
        )

        role = (
            request.form
            .get("role", "")
            .strip()
        )

        predios_selected = (
            request.form
            .getlist("predios")
        )

        predios_selected = [
            int(predio_id)
            for predio_id in predios_selected
        ]

        # ================================================
        # VALIDACIONES
        # ================================================
        if not username:

            flash(
                "Debe ingresar usuario.",
                "danger"
            )

            return render_template(
                "crear_usuario.html",
                predios=predios,
                form_data={
                    "username": username,
                    "role": role,
                    "predios_selected": predios_selected
                }
            )

        if not password:

            flash(
                "Debe ingresar contraseña.",
                "danger"
            )

            return render_template(
                "crear_usuario.html",
                predios=predios,
                form_data={
                    "username": username,
                    "role": role,
                    "predios_selected": predios_selected
                }
            )

        if not predios_selected:

            flash(
                "Debe seleccionar "
                "al menos un predio.",
                "danger"
            )

            return render_template(
                "crear_usuario.html",
                predios=predios,
                form_data={
                    "username": username,
                    "role": role,
                    "predios_selected": predios_selected
                }
            )

        # ================================================
        # CREAR
        # ================================================
        result = create_new_user(
            username=username,
            password=password,
            role=role,
            predios=predios_selected
        )

        if not result["success"]:

            flash(
                result["message"],
                "danger"
            )

            return render_template(
                "crear_usuario.html",
                predios=predios,
                form_data={
                    "username": username,
                    "role": role,
                    "predios_selected": predios_selected
                }
            )

        flash(
            "Usuario creado correctamente.",
            "success"
        )

        return redirect(
            url_for("users.usuarios")
        )

    return render_template(
        "crear_usuario.html",
        predios=predios,
        form_data={}
    )


# =========================================================
# EDITAR PREDIOS USUARIO
# =========================================================
@user_bp.route(
    "/usuarios/<int:user_id>/predios",
    methods=["GET", "POST"]
)
@login_required
@role_required(["SUPERADMIN"])
def editar_predios_usuario(user_id):

    user = get_user(user_id)

    if not user:

        flash(
            "Usuario no encontrado.",
            "danger"
        )

        return redirect(
            url_for("users.usuarios")
        )

    predios = get_predios()

    user_predios = get_user_predios(
        user_id
    )

    user_predios_ids = [
        predio["id"]
        for predio in user_predios
    ]

    if request.method == "POST":

        predios_selected = (
            request.form
            .getlist("predios")
        )

        predios_selected = [
            int(predio_id)
            for predio_id in predios_selected
        ]

        result = update_user_predios(
            user_id,
            predios_selected
        )

        if not result["success"]:

            flash(
                result["message"],
                "danger"
            )

            return redirect(
                url_for(
                    "users.editar_predios_usuario",
                    user_id=user_id
                )
            )

        flash(
            "Predios actualizados.",
            "success"
        )

        return redirect(
            url_for("users.usuarios")
        )

    return render_template(
        "editar_predios_usuario.html",
        user=user,
        predios=predios,
        user_predios_ids=user_predios_ids
    )


# =========================================================
# ACTIVAR / DESACTIVAR
# =========================================================
@user_bp.route(
    "/usuarios/<int:user_id>/estado",
    methods=["POST"]
)
@login_required
@role_required(["SUPERADMIN"])
def cambiar_estado_usuario(user_id):

    activo = (
        request.form.get("activo")
        == "true"
    )

    result = change_user_status(
        user_id,
        activo
    )

    if not result["success"]:

        flash(
            result["message"],
            "danger"
        )

        return redirect(
            url_for("users.usuarios")
        )

    flash(
        "Estado actualizado.",
        "success"
    )

    return redirect(
        url_for("users.usuarios")
    )