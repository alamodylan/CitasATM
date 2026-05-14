# db.py

import psycopg2

from psycopg2.extras import (
    RealDictCursor
)

from config import Config


# =========================================================
# CONEXIÓN
# =========================================================
def get_db_connection():
    """
    Retorna conexión PostgreSQL.
    """

    try:

        conn = psycopg2.connect(
            Config.DATABASE_URL,
            cursor_factory=RealDictCursor
        )

        return conn

    except Exception as e:

        print(
            f"[ERROR BD] {e}"
        )

        raise


# =========================================================
# EJECUTAR QUERY
# =========================================================
def execute_query(
    query,
    params=None,
    fetchone=False,
    fetchall=False,
    commit=False
):
    """
    Ejecuta consultas reutilizables.
    """

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor()

        # ================================================
        # EJECUTAR
        # ================================================
        if params is not None:

            cursor.execute(
                query,
                params
            )

        else:

            cursor.execute(
                query
            )

        # ================================================
        # COMMIT
        # ================================================
        if commit:

            conn.commit()

        # ================================================
        # FETCH
        # ================================================
        if fetchone:

            return cursor.fetchone()

        if fetchall:

            return cursor.fetchall()

        return None

    except Exception as e:

        if conn:

            conn.rollback()

        print(
            f"[ERROR QUERY] {e}"
        )

        raise

    finally:

        if cursor:

            cursor.close()

        if conn:

            conn.close()