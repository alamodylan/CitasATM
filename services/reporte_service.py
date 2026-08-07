# services/reporte_service.py

from datetime import datetime

from models.reporte_model import (
    get_report_navieras,
    get_merchant_report
)


# =========================================================
# NORMALIZAR PREDIOS
# =========================================================
def normalize_predios(predios):

    if not predios:

        return []

    normalized = []

    for predio_id in predios:

        try:

            normalized.append(
                int(predio_id)
            )

        except (
            TypeError,
            ValueError
        ):

            continue

    return normalized


# =========================================================
# OBTENER NAVIERAS PARA FILTRO
# =========================================================
def get_available_report_navieras():

    rows = get_report_navieras() or []

    navieras = []

    for row in rows:

        naviera = (
            row.get("naviera")
            if hasattr(row, "get")
            else row["naviera"]
        )

        if not naviera:

            continue

        naviera = (
            str(naviera)
            .strip()
            .upper()
        )

        if naviera:

            navieras.append(
                naviera
            )

    return navieras


# =========================================================
# VALIDAR FECHA
# =========================================================
def parse_report_date(
    value,
    field_name
):

    value = (
        value or ""
    ).strip()

    if not value:

        raise ValueError(
            f"Debe seleccionar la fecha {field_name}."
        )

    try:

        return datetime.strptime(
            value,
            "%Y-%m-%d"
        ).date()

    except ValueError:

        raise ValueError(
            f"La fecha {field_name} no es válida."
        )


# =========================================================
# GENERAR REPORTE MERCHANT
# =========================================================
def generate_merchant_report(
    fecha_desde,
    fecha_hasta,
    naviera=None,
    predios=None
):

    # =====================================================
    # VALIDAR FECHAS
    # =====================================================
    desde = parse_report_date(
        fecha_desde,
        "desde"
    )

    hasta = parse_report_date(
        fecha_hasta,
        "hasta"
    )

    if desde > hasta:

        raise ValueError(
            "La fecha desde no puede ser mayor "
            "que la fecha hasta."
        )

    # =====================================================
    # NORMALIZAR NAVIERA
    # =====================================================
    naviera_normalizada = (
        naviera or ""
    ).strip().upper()

    if (
        not naviera_normalizada
        or naviera_normalizada == "TODAS"
    ):

        naviera_normalizada = None

    # =====================================================
    # NORMALIZAR PREDIOS
    # =====================================================
    predios_normalizados = normalize_predios(
        predios
    )

    if not predios_normalizados:

        return {
            "success": True,
            "registros": [],
            "total": 0,
            "fecha_desde": desde,
            "fecha_hasta": hasta,
            "naviera": naviera_normalizada
        }

    # =====================================================
    # CONSULTAR REPORTE
    # =====================================================
    registros = get_merchant_report(
        fecha_desde=desde,
        fecha_hasta=hasta,
        naviera=naviera_normalizada,
        predios=predios_normalizados
    ) or []

    # =====================================================
    # RESPUESTA
    # =====================================================
    return {
        "success": True,
        "registros": registros,
        "total": len(
            registros
        ),
        "fecha_desde": desde,
        "fecha_hasta": hasta,
        "naviera": naviera_normalizada
    }