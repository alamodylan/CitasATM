# models/user_model.py

from db import execute_query


# =========================================================
# OBTENER USUARIO POR USERNAME
# =========================================================
def get_user_by_username(username):

    query = """
        SELECT *
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
        SELECT *
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
        SELECT *
        FROM users
        ORDER BY username ASC
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
    role
):

    query = """
        INSERT INTO users (
            username,
            password_hash,
            role
        )
        VALUES (%s, %s, %s)
    """

    execute_query(
        query,
        (username, password_hash, role),
        commit=True
    )


# =========================================================
# ACTUALIZAR ESTADO
# =========================================================
def update_user_status(
    user_id,
    activo
):

    query = """
        UPDATE users
        SET activo = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """

    execute_query(
        query,
        (activo, user_id),
        commit=True
    )