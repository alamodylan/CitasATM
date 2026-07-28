# models/user_model.py

from db import execute_query


# =========================================================
# OBTENER USUARIO POR USERNAME
# =========================================================
def get_user_by_username(username):

    query = """
        SELECT
            id,
            username,
            password_hash,
            role,
            activo,
            created_at,
            updated_at,
            naviera,
            failed_login_attempts,
            is_locked,
            locked_at,
            lock_reason
        FROM users
        WHERE LOWER(username) = LOWER(%s)
        LIMIT 1
    """

    return execute_query(
        query,
        (username,),
        fetchone=True
    )


# =========================================================
# OBTENER USUARIO POR ID
# =========================================================
def get_user_by_id(user_id):

    query = """
        SELECT
            id,
            username,
            password_hash,
            role,
            activo,
            created_at,
            updated_at,
            naviera,
            failed_login_attempts,
            is_locked,
            locked_at,
            lock_reason
        FROM users
        WHERE id = %s
        LIMIT 1
    """

    return execute_query(
        query,
        (user_id,),
        fetchone=True
    )


# =========================================================
# OBTENER TODOS LOS USUARIOS
# =========================================================
def get_all_users():

    query = """
        SELECT
            u.id,
            u.username,
            u.role,
            u.activo,
            u.created_at,
            u.updated_at,
            u.naviera,
            u.failed_login_attempts,
            u.is_locked,
            u.locked_at,
            u.lock_reason
        FROM users u
        ORDER BY u.username ASC
    """

    return execute_query(
        query,
        fetchall=True
    )


# =========================================================
# OBTENER NAVIERAS ACTIVAS
# =========================================================
def get_active_navieras():

    query = """
        SELECT
            codigo,
            nombre
        FROM navieras
        WHERE activo = TRUE
        ORDER BY nombre ASC
    """

    return execute_query(
        query,
        fetchall=True
    )


# =========================================================
# CREAR USUARIO
# =========================================================
def create_user(
    username,
    password_hash,
    role,
    naviera=None
):

    query = """
        INSERT INTO users (
            username,
            password_hash,
            role,
            naviera,
            activo,
            failed_login_attempts,
            is_locked
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            TRUE,
            0,
            FALSE
        )
        RETURNING id
    """

    return execute_query(
        query,
        (
            username,
            password_hash,
            role,
            naviera
        ),
        commit=True,
        fetchone=True
    )


# =========================================================
# ACTUALIZAR USUARIO
# =========================================================
def update_user(
    user_id,
    username,
    role,
    naviera=None
):

    query = """
        UPDATE users
        SET
            username = %s,
            role = %s,
            naviera = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """

    execute_query(
        query,
        (
            username,
            role,
            naviera,
            user_id
        ),
        commit=True
    )


# =========================================================
# ACTUALIZAR ESTADO ACTIVO / INACTIVO
# =========================================================
def update_user_status(
    user_id,
    activo
):

    query = """
        UPDATE users
        SET
            activo = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """

    execute_query(
        query,
        (
            activo,
            user_id
        ),
        commit=True
    )


# =========================================================
# REGISTRAR INTENTO DE LOGIN FALLIDO
# =========================================================
def register_failed_login(user_id):

    query = """
        UPDATE users
        SET
            failed_login_attempts =
                COALESCE(failed_login_attempts, 0) + 1,

            is_locked =
                CASE
                    WHEN COALESCE(failed_login_attempts, 0) + 1 >= 3
                    THEN TRUE
                    ELSE FALSE
                END,

            locked_at =
                CASE
                    WHEN COALESCE(failed_login_attempts, 0) + 1 >= 3
                    THEN CURRENT_TIMESTAMP
                    ELSE locked_at
                END,

            lock_reason =
                CASE
                    WHEN COALESCE(failed_login_attempts, 0) + 1 >= 3
                    THEN 'Tres intentos de contraseña incorrecta'
                    ELSE lock_reason
                END,

            updated_at = CURRENT_TIMESTAMP

        WHERE id = %s

        RETURNING
            failed_login_attempts,
            is_locked,
            locked_at,
            lock_reason
    """

    return execute_query(
        query,
        (user_id,),
        commit=True,
        fetchone=True
    )


# =========================================================
# REINICIAR INTENTOS DESPUÉS DE LOGIN CORRECTO
# =========================================================
def reset_failed_login(user_id):

    query = """
        UPDATE users
        SET
            failed_login_attempts = 0,
            is_locked = FALSE,
            locked_at = NULL,
            lock_reason = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """

    execute_query(
        query,
        (user_id,),
        commit=True
    )


# =========================================================
# DESBLOQUEAR USUARIO DESDE ADMINISTRACIÓN
# =========================================================
def unlock_user(user_id):

    query = """
        UPDATE users
        SET
            failed_login_attempts = 0,
            is_locked = FALSE,
            locked_at = NULL,
            lock_reason = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING id, username
    """

    return execute_query(
        query,
        (user_id,),
        commit=True,
        fetchone=True
    )


# =========================================================
# CAMBIAR CONTRASEÑA
# =========================================================
def update_user_password(
    user_id,
    password_hash
):

    query = """
        UPDATE users
        SET
            password_hash = %s,
            failed_login_attempts = 0,
            is_locked = FALSE,
            locked_at = NULL,
            lock_reason = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING id, username
    """

    return execute_query(
        query,
        (
            password_hash,
            user_id
        ),
        commit=True,
        fetchone=True
    )


# =========================================================
# VALIDAR SI EL USERNAME YA EXISTE
# =========================================================
def username_exists(
    username,
    exclude_user_id=None
):

    if exclude_user_id:

        query = """
            SELECT id
            FROM users
            WHERE LOWER(username) = LOWER(%s)
              AND id <> %s
            LIMIT 1
        """

        params = (
            username,
            exclude_user_id
        )

    else:

        query = """
            SELECT id
            FROM users
            WHERE LOWER(username) = LOWER(%s)
            LIMIT 1
        """

        params = (username,)

    result = execute_query(
        query,
        params,
        fetchone=True
    )

    return result is not None