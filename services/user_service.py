# services/user_service.py

from models.user_model import (
    get_all_users,
    get_user_by_id,
    get_user_by_username,
    create_user,
    update_user_status
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
# OBTENER TODOS LOS USUARIOS
# =========================================================
def get_users():

    return get_all_users()


# =========================================================
# OBTENER USUARIO
# =========================================================
def get_user(user_id):

    return get_user_by_id(user_id)


# =========================================================
# OBTENER PREDIOS DEL USUARIO
# =========================================================
def get_user_predios(user_id):

    return get_predios_by_user(user_id)


# =========================================================
# OBTENER TODOS LOS PREDIOS
# =========================================================
def get_predios():

    return get_all_predios()


# =========================================================
# CREAR USUARIO
# =========================================================
def create_new_user(
    username,
    password,
    role,
    predios
):

    # =====================================================
    # NORMALIZAR
    # =====================================================
    username = username.strip().lower()

    # =====================================================
    # VALIDAR PREDIOS
    # =====================================================
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
            "message": (
                "El usuario ya existe."
            )
        }

    # =====================================================
    # VALIDAR ROL
    # =====================================================
    allowed_roles = [
        "ADMIN",
        "PREDIO",
        "GUARDA"
    ]

    if role not in allowed_roles:

        return {
            "success": False,
            "message": (
                "Rol inválido."
            )
        }

    # =====================================================
    # HASH PASSWORD
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
        role=role
    )

    # =====================================================
    # OBTENER USUARIO NUEVO
    # =====================================================
    user = get_user_by_username(
        username
    )

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

    # =====================================================
    # VALIDAR
    # =====================================================
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

    user = get_user_by_id(user_id)

    if not user:

        return {
            "success": False,
            "message": (
                "Usuario no encontrado."
            )
        }

    update_user_status(
        user_id,
        activo
    )

    return {
        "success": True
    }