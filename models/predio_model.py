# models/predio_model.py

from db import execute_query


def get_all_predios():

    query = """
        SELECT *
        FROM predios
        WHERE activo = TRUE
        ORDER BY nombre ASC
    """

    return execute_query(
        query,
        fetchall=True
    )


def get_predios_by_user(user_id):

    query = """
        SELECT
            p.*
        FROM user_predios up
        INNER JOIN predios p
            ON p.id = up.predio_id
        WHERE up.user_id = %s
        ORDER BY p.nombre ASC
    """

    return execute_query(
        query,
        (user_id,),
        fetchall=True
    )


def assign_predio_to_user(user_id, predio_id):

    query = """
        INSERT INTO user_predios (
            user_id,
            predio_id
        )
        VALUES (%s, %s)
        ON CONFLICT (user_id, predio_id)
        DO NOTHING
    """

    execute_query(
        query,
        (user_id, predio_id),
        commit=True
    )


def remove_all_user_predios(user_id):

    query = """
        DELETE FROM user_predios
        WHERE up.user_id = %s
          AND p.activo = TRUE
    """

    execute_query(
        query,
        (user_id,),
        commit=True
    )