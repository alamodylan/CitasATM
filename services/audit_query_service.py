# services/audit_query_service.py

from datetime import (
    datetime,
    timedelta
)

from models.audit_model import (
    get_audit_logs,
    count_audit_logs,
    get_audit_usernames,
    get_audit_modules,
    get_audit_actions
)


# =========================================================
# CONSULTAR AUDITORÍA
# =========================================================
def search_audit_logs(
    fecha_desde=None,
    fecha_hasta=None,
    username=None,
    module=None,
    action=None,
    page=1,
    page_size=100
):

    """
    Obtiene registros de auditoría aplicando filtros
    y paginación.
    """

    # =====================================================
    # NORMALIZAR FECHAS
    # =====================================================
    fecha_desde_dt = None
    fecha_hasta_dt = None

    if fecha_desde:

        fecha_desde_dt = datetime.strptime(
            fecha_desde,
            "%Y-%m-%d"
        )

    if fecha_hasta:

        fecha_hasta_dt = (
            datetime.strptime(
                fecha_hasta,
                "%Y-%m-%d"
            )
            + timedelta(days=1)
        )

    # =====================================================
    # NORMALIZAR FILTROS
    # =====================================================
    username = (
        username or ""
    ).strip()

    module = (
        module or ""
    ).strip().upper()

    action = (
        action or ""
    ).strip().upper()

    if not username:

        username = None

    if not module:

        module = None

    if not action:

        action = None

    # =====================================================
    # PAGINACIÓN
    # =====================================================
    try:

        page = int(page)

    except Exception:

        page = 1

    if page < 1:

        page = 1

    try:

        page_size = int(page_size)

    except Exception:

        page_size = 100

    if page_size < 1:

        page_size = 100

    offset = (
        page - 1
    ) * page_size

    # =====================================================
    # CONSULTA
    # =====================================================
    registros = get_audit_logs(
        fecha_desde=fecha_desde_dt,
        fecha_hasta=fecha_hasta_dt,
        username=username,
        module=module,
        action=action,
        limit=page_size,
        offset=offset
    )

    total = count_audit_logs(
        fecha_desde=fecha_desde_dt,
        fecha_hasta=fecha_hasta_dt,
        username=username,
        module=module,
        action=action
    )

    return {

        "registros": registros,

        "total": total,

        "page": page,

        "page_size": page_size,

        "pages": (
            (total + page_size - 1)
            // page_size
        )

    }


# =========================================================
# COMBOS DE FILTROS
# =========================================================
def get_audit_filters():

    usuarios = get_audit_usernames()

    modulos = get_audit_modules()

    acciones = get_audit_actions()

    return {

        "usuarios": usuarios,

        "modulos": modulos,

        "acciones": acciones

    }