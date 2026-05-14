# services/auth_service.py

from functools import wraps

from flask import (
    session,
    redirect,
    url_for,
    flash
)

from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

from models.user_model import (
    get_user_by_username,
    get_user_by_id
)

from models.predio_model import (
    get_predios_by_user
)


# =========================================================
# LOGIN
# =========================================================
def login_user(username, password):

    username = username.strip().lower()

    user = get_user_by_username(username)

    if not user:
        return {
            "success": False,
            "message": "Usuario no encontrado."
        }

    if not user["activo"]:
        return {
            "success": False,
            "message": "Usuario inactivo."
        }

    # =====================================================
    # TEMPORAL:
    # Permite login texto plano mientras migramos hashes
    # =====================================================
    valid_password = False

    stored_password = user.get("password_hash")

    if stored_password:

        if (
            stored_password.startswith("scrypt:")
            or stored_password.startswith("pbkdf2:")
        ):

            valid_password = check_password_hash(
                stored_password,
                password
            )

        elif stored_password == password:

            valid_password = True

    if not valid_password:
        return {
            "success": False,
            "message": "Contraseña incorrecta."
        }

    # =====================================================
    # OBTENER PREDIOS
    # =====================================================
    predios = get_predios_by_user(
        user["id"]
    )

    # =====================================================
    # CREAR SESIÓN
    # =====================================================
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]

    session["predios"] = [
        predio["id"]
        for predio in predios
    ]

    if predios:

        session["active_predio_id"] = predios[0]["id"]
        session["active_predio_nombre"] = predios[0]["nombre"]

    else:

        session["active_predio_id"] = None
        session["active_predio_nombre"] = None

    return {
        "success": True,
        "user": user
    }


# =========================================================
# LOGOUT
# =========================================================
def logout_user():

    session.clear()


# =========================================================
# USUARIO ACTUAL
# =========================================================
def get_current_user():

    user_id = session.get("user_id")

    if not user_id:

        return None

    return get_user_by_id(
        user_id
    )


# =========================================================
# VALIDAR LOGIN
# =========================================================
def login_required(view_func):

    @wraps(view_func)
    def wrapped_view(*args, **kwargs):

        if "user_id" not in session:

            flash(
                "Debe iniciar sesión.",
                "warning"
            )

            return redirect(
                url_for("auth.login")
            )

        return view_func(*args, **kwargs)

    return wrapped_view


# =========================================================
# VALIDAR ROL
# =========================================================
def role_required(roles_permitidos):

    def decorator(view_func):

        @wraps(view_func)
        def wrapped_view(*args, **kwargs):

            role = session.get("role")

            if role not in roles_permitidos:

                flash(
                    "No tiene permisos para acceder.",
                    "danger"
                )

                return redirect(
                    url_for("root")
                )

            return view_func(*args, **kwargs)

        return wrapped_view

    return decorator


# =========================================================
# VALIDAR PREDIO
# =========================================================
def user_has_predio_access(predio_id):

    predios = session.get(
        "predios",
        []
    )

    return predio_id in predios


# =========================================================
# HASH PASSWORD
# =========================================================
def create_password_hash(password):

    return generate_password_hash(
        password
    )