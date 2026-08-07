# services/audit_service.py

import json

from flask import (
    session,
    request
)

from db import execute_query


# =========================================================
# NORMALIZAR DETALLES
# =========================================================
def normalize_details(details):

    """
    Convierte los detalles a texto seguro para almacenar.

    Acepta:
        - str
        - dict
        - list
        - cualquier otro valor convertible a texto
    """

    if details is None:

        return None

    if isinstance(
        details,
        (
            dict,
            list
        )
    ):

        try:

            return json.dumps(
                details,
                ensure_ascii=False,
                default=str
            )

        except Exception:

            return str(
                details
            )

    return str(
        details
    )


# =========================================================
# OBTENER IP DEL CLIENTE
# =========================================================
def get_client_ip():

    """
    Intenta obtener la IP real del cliente.

    Si la aplicación está detrás de un proxy como Render,
    primero revisa X-Forwarded-For.
    """

    forwarded_for = request.headers.get(
        "X-Forwarded-For"
    )

    if forwarded_for:

        return (
            forwarded_for
            .split(",")[0]
            .strip()
        )

    return request.remote_addr


# =========================================================
# OBTENER USER AGENT
# =========================================================
def get_user_agent():

    user_agent = request.headers.get(
        "User-Agent"
    )

    if not user_agent:

        return None

    return user_agent[:500]


# =========================================================
# REGISTRAR ACCIÓN
# =========================================================
def log_action(
    action,
    module,
    entity_id=None,
    details=None,
    user_id=None,
    username=None,
    role=None
):

    """
    Registra una acción en audit_logs.

    Por defecto toma los datos del usuario desde session.

    También permite enviar usuario manualmente, útil para
    auditoría de login fallido cuando todavía no existe
    una sesión autenticada.
    """

    # =====================================================
    # NORMALIZAR ACCIÓN
    # =====================================================
    action = (
        action or ""
    ).strip().upper()

    if not action:

        raise ValueError(
            "La acción de auditoría es obligatoria."
        )

    # =====================================================
    # NORMALIZAR MÓDULO
    # =====================================================
    module = (
        module or ""
    ).strip().upper()

    if not module:

        raise ValueError(
            "El módulo de auditoría es obligatorio."
        )

    # =====================================================
    # DATOS DEL USUARIO
    # =====================================================
    if user_id is None:

        user_id = session.get(
            "user_id"
        )

    if username is None:

        username = session.get(
            "username"
        )

    if role is None:

        role = session.get(
            "role"
        )

    # =====================================================
    # NORMALIZAR USERNAME
    # =====================================================
    if username:

        username = str(
            username
        ).strip()

    # =====================================================
    # NORMALIZAR ROL
    # =====================================================
    if role:

        role = (
            str(role)
            .strip()
            .upper()
        )

    # =====================================================
    # NORMALIZAR ENTITY ID
    # =====================================================
    if entity_id is not None:

        try:

            entity_id = int(
                entity_id
            )

        except (
            TypeError,
            ValueError
        ):

            entity_id = None

    # =====================================================
    # NORMALIZAR DETALLES
    # =====================================================
    details_text = normalize_details(
        details
    )

    # =====================================================
    # OBTENER DATOS DE LA PETICIÓN
    # =====================================================
    try:

        ip_address = get_client_ip()

    except RuntimeError:

        ip_address = None

    try:

        user_agent = get_user_agent()

    except RuntimeError:

        user_agent = None

    try:

        request_method = request.method

    except RuntimeError:

        request_method = None

    try:

        request_path = request.path

    except RuntimeError:

        request_path = None

    # =====================================================
    # INSERTAR AUDITORÍA
    # =====================================================
    query = """
        INSERT INTO audit_logs (
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
            request_path
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
    """

    execute_query(
        query,
        (
            user_id,
            username,
            role,
            action,
            module,
            entity_id,
            details_text,
            ip_address,
            user_agent,
            request_method,
            request_path
        ),
        commit=True
    )


# =========================================================
# REGISTRAR AUDITORÍA SIN ROMPER EL FLUJO PRINCIPAL
# =========================================================
def safe_log_action(
    action,
    module,
    entity_id=None,
    details=None,
    user_id=None,
    username=None,
    role=None
):

    """
    Igual que log_action(), pero captura cualquier error.

    Úsala en operaciones donde una falla en auditoría NO
    debe impedir que la acción principal del sistema se
    complete.

    Ejemplo:
        crear cita
        editar cita
        completar cita
        exportar reporte
    """

    try:

        log_action(
            action=action,
            module=module,
            entity_id=entity_id,
            details=details,
            user_id=user_id,
            username=username,
            role=role
        )

        return True

    except Exception as error:

        print(
            "[AUDITORIA ERROR] "
            f"{action} | "
            f"{module} | "
            f"{error}"
        )

        return False


# =========================================================
# AUDITAR LOGIN CORRECTO
# =========================================================
def log_login_success(
    user
):

    if not user:

        return False

    return safe_log_action(
        action="LOGIN_EXITOSO",
        module="AUTH",
        entity_id=user.get(
            "id"
        ),
        user_id=user.get(
            "id"
        ),
        username=user.get(
            "username"
        ),
        role=user.get(
            "role"
        ),
        details={
            "resultado": "Login correcto"
        }
    )


# =========================================================
# AUDITAR LOGIN FALLIDO
# =========================================================
def log_login_failed(
    username,
    reason=None,
    user_id=None,
    role=None
):

    username = (
        username or ""
    ).strip().lower()

    return safe_log_action(
        action="LOGIN_FALLIDO",
        module="AUTH",
        entity_id=user_id,
        user_id=user_id,
        username=username or None,
        role=role,
        details={
            "motivo": (
                reason or
                "Credenciales incorrectas"
            )
        }
    )


# =========================================================
# AUDITAR LOGOUT
# =========================================================
def log_logout():

    return safe_log_action(
        action="LOGOUT",
        module="AUTH",
        details={
            "resultado": "Sesión cerrada"
        }
    )