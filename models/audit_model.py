# models/audit_model.py

from db import execute_query


# =========================================================
# OBTENER REGISTROS DE AUDITORÍA
# =========================================================
def get_audit_logs(
    fecha_desde=None,
    fecha_hasta=None,
    username=None,
    module=None,
    action=None,
    limit=500,
    offset=0
):

    query = """
        SELECT
            id,
            user_id,
            username,
            role,
            action,
            module,
            entity_id,
            details,
            ip_address,
            user_agent,
            request_method,
            request_path,
            created_at
        FROM audit_logs
        WHERE 1 = 1
    """

    params = []

    # =====================================================
    # FECHA DESDE
    # =====================================================
    if fecha_desde:

        query += """
          AND created_at >= %s
        """

        params.append(
            fecha_desde
        )

    # =====================================================
    # FECHA HASTA
    # =====================================================
    if fecha_hasta:

        query += """
          AND created_at < %s
        """

        params.append(
            fecha_hasta
        )

    # =====================================================
    # USUARIO
    # =====================================================
    if username:

        query += """
          AND LOWER(username) = LOWER(%s)
        """

        params.append(
            username
        )

    # =====================================================
    # MÓDULO
    # =====================================================
    if module:

        query += """
          AND module = %s
        """

        params.append(
            module
        )

    # =====================================================
    # ACCIÓN
    # =====================================================
    if action:

        query += """
          AND action = %s
        """

        params.append(
            action
        )

    # =====================================================
    # ORDEN
    # =====================================================
    query += """
        ORDER BY
            created_at DESC,
            id DESC
        LIMIT %s
        OFFSET %s
    """

    params.extend([
        limit,
        offset
    ])

    return execute_query(
        query,
        tuple(params),
        fetchall=True
    )


# =========================================================
# CONTAR REGISTROS
# =========================================================
def count_audit_logs(
    fecha_desde=None,
    fecha_hasta=None,
    username=None,
    module=None,
    action=None
):

    query = """
        SELECT
            COUNT(*) AS total
        FROM audit_logs
        WHERE 1 = 1
    """

    params = []

    if fecha_desde:

        query += """
          AND created_at >= %s
        """

        params.append(
            fecha_desde
        )

    if fecha_hasta:

        query += """
          AND created_at < %s
        """

        params.append(
            fecha_hasta
        )

    if username:

        query += """
          AND LOWER(username) = LOWER(%s)
        """

        params.append(
            username
        )

    if module:

        query += """
          AND module = %s
        """

        params.append(
            module
        )

    if action:

        query += """
          AND action = %s
        """

        params.append(
            action
        )

    result = execute_query(
        query,
        tuple(params),
        fetchone=True
    )

    if not result:

        return 0

    return int(
        result["total"] or 0
    )


# =========================================================
# OBTENER USUARIOS PRESENTES EN AUDITORÍA
# =========================================================
def get_audit_usernames():

    query = """
        SELECT DISTINCT
            username
        FROM audit_logs
        WHERE username IS NOT NULL
          AND TRIM(username) <> ''
        ORDER BY username ASC
    """

    return execute_query(
        query,
        fetchall=True
    )


# =========================================================
# OBTENER MÓDULOS PRESENTES EN AUDITORÍA
# =========================================================
def get_audit_modules():

    query = """
        SELECT DISTINCT
            module
        FROM audit_logs
        WHERE module IS NOT NULL
          AND TRIM(module) <> ''
        ORDER BY module ASC
    """

    return execute_query(
        query,
        fetchall=True
    )


# =========================================================
# OBTENER ACCIONES PRESENTES EN AUDITORÍA
# =========================================================
def get_audit_actions():

    query = """
        SELECT DISTINCT
            action
        FROM audit_logs
        WHERE action IS NOT NULL
          AND TRIM(action) <> ''
        ORDER BY action ASC
    """

    return execute_query(
        query,
        fetchall=True
    )


# =========================================================
# OBTENER REGISTRO POR ID
# =========================================================
def get_audit_log_by_id(
    audit_id
):

    query = """
        SELECT
            id,
            user_id,
            username,
            role,
            action,
            module,
            entity_id,
            details,
            ip_address,
            user_agent,
            request_method,
            request_path,
            created_at
        FROM audit_logs
        WHERE id = %s
        LIMIT 1
    """

    return execute_query(
        query,
        (audit_id,),
        fetchone=True
    )