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
    get_navieras,
    create_new_user,
    update_user_predios,
    change_user_status,
    unlock_user_account,
    reset_user_password
)

from services.audit_service import (
    safe_log_action
)


# =========================================================
# BLUEPRINT
# =========================================================
user_bp = Blueprint(
    "users",
    __name__
)


# =========================================================
# ROLES PERMITIDOS
# =========================================================
ALLOWED_ROLES = {
    "ADMIN",
    "PREDIO",
    "GUARDA",
    "NAVIERA"
}


# =========================================================
# CONVERTIR PREDIOS DEL FORMULARIO
# =========================================================
def parse_predios_selected():

    predios_raw = request.form.getlist(
        "predios"
    )

    try:

        return [
            int(predio_id)
            for predio_id in predios_raw
        ]

    except (TypeError, ValueError):

        return None


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
    navieras = get_navieras()

    if request.method == "POST":

        username = (
            request.form
            .get("username", "")
            .strip()
            .lower()
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
            .upper()
        )

        naviera = (
            request.form
            .get("naviera", "")
            .strip()
            .upper()
        )

        predios_selected = parse_predios_selected()

        form_data = {
            "username": username,
            "role": role,
            "naviera": naviera,
            "predios_selected": (
                predios_selected
                if predios_selected is not None
                else []
            )
        }

        # ================================================
        # VALIDAR PREDIOS RECIBIDOS
        # ================================================
        if predios_selected is None:

            flash(
                "La selección de predios no es válida.",
                "danger"
            )

            return render_template(
                "crear_usuario.html",
                predios=predios,
                navieras=navieras,
                form_data=form_data
            )

        # ================================================
        # VALIDAR USUARIO
        # ================================================
        if not username:

            flash(
                "Debe ingresar usuario.",
                "danger"
            )

            return render_template(
                "crear_usuario.html",
                predios=predios,
                navieras=navieras,
                form_data=form_data
            )

        # ================================================
        # VALIDAR CONTRASEÑA
        # ================================================
        if not password:

            flash(
                "Debe ingresar contraseña.",
                "danger"
            )

            return render_template(
                "crear_usuario.html",
                predios=predios,
                navieras=navieras,
                form_data=form_data
            )

        # ================================================
        # VALIDAR ROL
        # ================================================
        if role not in ALLOWED_ROLES:

            flash(
                "El rol seleccionado no es válido.",
                "danger"
            )

            return render_template(
                "crear_usuario.html",
                predios=predios,
                navieras=navieras,
                form_data=form_data
            )

        # ================================================
        # VALIDAR NAVIERA
        # ================================================
        if role == "NAVIERA":

            if not naviera:

                flash(
                    "Debe seleccionar una naviera.",
                    "danger"
                )

                return render_template(
                    "crear_usuario.html",
                    predios=predios,
                    navieras=navieras,
                    form_data=form_data
                )

        else:

            # Los usuarios internos no deben tener
            # una naviera asociada.
            naviera = None
            form_data["naviera"] = ""

        # ================================================
        # VALIDAR PREDIOS
        # Todos los usuarios, incluido NAVIERA,
        # deben tener al menos un predio.
        # ================================================
        if not predios_selected:

            flash(
                "Debe seleccionar al menos un predio.",
                "danger"
            )

            return render_template(
                "crear_usuario.html",
                predios=predios,
                navieras=navieras,
                form_data=form_data
            )

        # ================================================
        # CREAR USUARIO
        # ================================================
        result = create_new_user(
            username=username,
            password=password,
            role=role,
            predios=predios_selected,
            naviera=naviera
        )

        if not result["success"]:

            flash(
                result["message"],
                "danger"
            )

            return render_template(
                "crear_usuario.html",
                predios=predios,
                navieras=navieras,
                form_data=form_data
            )

        created_user = result.get(
            "user"
        ) or {}

        safe_log_action(
            action="CREAR_USUARIO",
            module="USUARIOS",
            entity_id=created_user.get(
                "id"
            ),
            details={
                "usuario_creado": username,
                "rol": role,
                "naviera": naviera,
                "predios": predios_selected
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
        navieras=navieras,
        form_data={}
    )


# =========================================================
# EDITAR PREDIOS DEL USUARIO
# =========================================================
@user_bp.route(
    "/usuarios/<int:user_id>/predios",
    methods=["GET", "POST"]
)
@login_required
@role_required(["SUPERADMIN"])
def editar_predios_usuario(user_id):

    user = get_user(
        user_id
    )

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

        predios_selected = parse_predios_selected()

        if predios_selected is None:

            flash(
                "La selección de predios no es válida.",
                "danger"
            )

            return redirect(
                url_for(
                    "users.editar_predios_usuario",
                    user_id=user_id
                )
            )

        if not predios_selected:

            flash(
                "Debe seleccionar al menos un predio.",
                "danger"
            )

            return render_template(
                "editar_predios_usuario.html",
                user=user,
                predios=predios,
                user_predios_ids=[]
            )

        result = update_user_predios(
            user_id,
            predios_selected
        )

        if not result["success"]:

            flash(
                result["message"],
                "danger"
            )

            return render_template(
                "editar_predios_usuario.html",
                user=user,
                predios=predios,
                user_predios_ids=predios_selected
            )

        safe_log_action(
            action="EDITAR_PREDIOS_USUARIO",
            module="USUARIOS",
            entity_id=user_id,
            details={
                "usuario": user.get(
                    "username"
                ),
                "predios_anteriores": user_predios_ids,
                "predios_nuevos": predios_selected
            }
        )

        flash(
            "Predios actualizados correctamente.",
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
# ACTIVAR / DESACTIVAR USUARIO
# =========================================================
@user_bp.route(
    "/usuarios/<int:user_id>/estado",
    methods=["POST"]
)
@login_required
@role_required(["SUPERADMIN"])
def cambiar_estado_usuario(user_id):

    activo_value = (
        request.form
        .get("activo", "")
        .strip()
        .lower()
    )

    if activo_value not in {
        "true",
        "false"
    }:

        flash(
            "El estado recibido no es válido.",
            "danger"
        )

        return redirect(
            url_for("users.usuarios")
        )

    activo = activo_value == "true"

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

    target_user = get_user(
        user_id
    )

    if activo:

        message = "Usuario activado correctamente."
        audit_action = "ACTIVAR_USUARIO"

    else:

        message = "Usuario desactivado correctamente."
        audit_action = "DESACTIVAR_USUARIO"

    safe_log_action(
        action=audit_action,
        module="USUARIOS",
        entity_id=user_id,
        details={
            "usuario": (
                target_user.get(
                    "username"
                )
                if target_user
                else None
            ),
            "activo": activo
        }
    )

    flash(
        message,
        "success"
    )

    return redirect(
        url_for("users.usuarios")
    )


# =========================================================
# DESBLOQUEAR USUARIO
# =========================================================
@user_bp.route(
    "/usuarios/<int:user_id>/desbloquear",
    methods=["POST"]
)
@login_required
@role_required(["SUPERADMIN"])
def desbloquear_usuario(user_id):

    result = unlock_user_account(
        user_id
    )

    if not result["success"]:

        flash(
            result["message"],
            "danger"
        )

        return redirect(
            url_for("users.usuarios")
        )

    target_user = get_user(
        user_id
    )

    safe_log_action(
        action="DESBLOQUEAR_USUARIO",
        module="USUARIOS",
        entity_id=user_id,
        details={
            "usuario": (
                target_user.get(
                    "username"
                )
                if target_user
                else None
            )
        }
    )

    flash(
        "Usuario desbloqueado correctamente.",
        "success"
    )

    return redirect(
        url_for("users.usuarios")
    )


# =========================================================
# RESTABLECER CONTRASEÑA
# =========================================================
@user_bp.route(
    "/usuarios/<int:user_id>/restablecer-password",
    methods=["GET", "POST"]
)
@login_required
@role_required(["SUPERADMIN"])
def restablecer_password_usuario(user_id):

    user = get_user(
        user_id
    )

    if not user:

        flash(
            "Usuario no encontrado.",
            "danger"
        )

        return redirect(
            url_for("users.usuarios")
        )

    if request.method == "POST":

        new_password = (
            request.form
            .get("new_password", "")
            .strip()
        )

        confirm_password = (
            request.form
            .get("confirm_password", "")
            .strip()
        )

        if not new_password:

            flash(
                "Debe ingresar la nueva contraseña.",
                "danger"
            )

            return render_template(
                "restablecer_password.html",
                user=user
            )

        if new_password != confirm_password:

            flash(
                "Las contraseñas no coinciden.",
                "danger"
            )

            return render_template(
                "restablecer_password.html",
                user=user
            )

        result = reset_user_password(
            user_id,
            new_password
        )

        if not result["success"]:

            flash(
                result["message"],
                "danger"
            )

            return render_template(
                "restablecer_password.html",
                user=user
            )

        safe_log_action(
            action="RESTABLECER_PASSWORD",
            module="USUARIOS",
            entity_id=user_id,
            details={
                "usuario": user.get(
                    "username"
                )
            }
        )

        flash(
            "Contraseña restablecida correctamente.",
            "success"
        )

        return redirect(
            url_for("users.usuarios")
        )

    return render_template(
        "restablecer_password.html",
        user=user
    )