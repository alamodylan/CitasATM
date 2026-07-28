# services/user_service.py

from models.user_model import (
    get_all_users,
    get_user_by_id,
    get_user_by_username,
    get_active_navieras,
    create_user,
    update_user_status,
    unlock_user,
    update_user_password
)

from models.predio_model import (
    get_all_predios,
    assign_predio_to_user,
    remove_all_user_predios,
    get_predios_by_user
)

from services.auth_service import (
    create_password_hash
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
# OBTENER TODOS LOS USUARIOS
# =========================================================
def get_users():

    return get_all_users()


# =========================================================
# OBTENER USUARIO
# =========================================================
def get_user(user_id):

    return get_user_by_id(
        user_id
    )


# =========================================================
# OBTENER PREDIOS DEL USUARIO
# =========================================================
def get_user_predios(user_id):

    return get_predios_by_user(
        user_id
    )


# =========================================================
# OBTENER TODOS LOS PREDIOS
# =========================================================
def get_predios():

    return get_all_predios()


# =========================================================
# OBTENER NAVIERAS ACTIVAS
# =========================================================
def get_navieras():

    return get_active_navieras()


# =========================================================
# VALIDAR NAVIERA ACTIVA
# =========================================================
def naviera_is_valid(naviera):

    if not naviera:

        return False

    naviera = naviera.strip().upper()

    navieras = get_active_navieras()

    navieras_validas = {
        item["codigo"]
        for item in navieras
    }

    return naviera in navieras_validas


# =========================================================
# CREAR USUARIO
# =========================================================
def create_new_user(
    username,
    password,
    role,
    predios,
    naviera=None
):

    # =====================================================
    # NORMALIZAR
    # =====================================================
    username = username.strip().lower()
    password = password.strip()
    role = role.strip().upper()

    naviera = (
        naviera.strip().upper()
        if naviera
        else None
    )

    predios = predios or []

    # =====================================================
    # VALIDACIONES GENERALES
    # =====================================================
    if not username:

        return {
            "success": False,
            "message": "Debe ingresar usuario."
        }

    if not password:

        return {
            "success": False,
            "message": "Debe ingresar contraseña."
        }

    if role not in ALLOWED_ROLES:

        return {
            "success": False,
            "message": "Rol inválido."
        }

    if not predios:

        return {
            "success": False,
            "message": (
                "Debe seleccionar "
                "al menos un predio."
            )
        }

    # =====================================================
    # VALIDAR USUARIO EXISTENTE
    # =====================================================
    existing_user = get_user_by_username(
        username
    )

    if existing_user:

        return {
            "success": False,
            "message": "El usuario ya existe."
        }

    # =====================================================
    # VALIDAR NAVIERA SEGÚN ROL
    # =====================================================
    if role == "NAVIERA":

        if not naviera:

            return {
                "success": False,
                "message": (
                    "Debe seleccionar una naviera."
                )
            }

        if not naviera_is_valid(naviera):

            return {
                "success": False,
                "message": (
                    "La naviera seleccionada "
                    "no es válida o está inactiva."
                )
            }

    else:

        # Usuarios internos no deben quedar asociados
        # a una naviera.
        naviera = None

    # =====================================================
    # HASH DE CONTRASEÑA
    # =====================================================
    password_hash = create_password_hash(
        password
    )

    # =====================================================
    # CREAR USUARIO
    # =====================================================
    create_user(
        username=username,
        password_hash=password_hash,
        role=role,
        naviera=naviera
    )

    # =====================================================
    # RECUPERAR USUARIO
    # =====================================================
    user = get_user_by_username(
        username
    )

    if not user:

        return {
            "success": False,
            "message": (
                "No fue posible recuperar "
                "el usuario después de crearlo."
            )
        }

    # =====================================================
    # ASIGNAR PREDIOS
    # =====================================================
    for predio_id in predios:

        assign_predio_to_user(
            user["id"],
            predio_id
        )

    return {
        "success": True,
        "user": user
    }


# =========================================================
# ACTUALIZAR PREDIOS
# =========================================================
def update_user_predios(
    user_id,
    predios
):

    user = get_user_by_id(
        user_id
    )

    if not user:

        return {
            "success": False,
            "message": "Usuario no encontrado."
        }

    if not predios:

        return {
            "success": False,
            "message": (
                "Debe seleccionar "
                "al menos un predio."
            )
        }

    remove_all_user_predios(
        user_id
    )

    for predio_id in predios:

        assign_predio_to_user(
            user_id,
            predio_id
        )

    return {
        "success": True
    }


# =========================================================
# ACTIVAR / DESACTIVAR
# =========================================================
def change_user_status(
    user_id,
    activo
):

    user = get_user_by_id(
        user_id
    )

    if not user:

        return {
            "success": False,
            "message": "Usuario no encontrado."
        }

    update_user_status(
        user_id,
        activo
    )

    return {
        "success": True
    }


# =========================================================
# DESBLOQUEAR USUARIO
# =========================================================
def unlock_user_account(user_id):

    user = get_user_by_id(
        user_id
    )

    if not user:

        return {
            "success": False,
            "message": "Usuario no encontrado."
        }

    if not user.get("is_locked"):

        return {
            "success": False,
            "message": (
                "El usuario no se encuentra bloqueado."
            )
        }

    result = unlock_user(
        user_id
    )

    if not result:

        return {
            "success": False,
            "message": (
                "No fue posible desbloquear "
                "el usuario."
            )
        }

    return {
        "success": True,
        "user": result
    }


# =========================================================
# RESTABLECER CONTRASEÑA
# =========================================================
def reset_user_password(
    user_id,
    new_password
):

    user = get_user_by_id(
        user_id
    )

    if not user:

        return {
            "success": False,
            "message": "Usuario no encontrado."
        }

    new_password = new_password.strip()

    if not new_password:

        return {
            "success": False,
            "message": (
                "Debe ingresar la nueva contraseña."
            )
        }

    password_hash = create_password_hash(
        new_password
    )

    result = update_user_password(
        user_id,
        password_hash
    )

    if not result:

        return {
            "success": False,
            "message": (
                "No fue posible restablecer "
                "la contraseña."
            )
        }

    return {
        "success": True,
        "user": result
    }