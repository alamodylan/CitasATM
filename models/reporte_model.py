# models/reporte_model.py

from db import execute_query


# =========================================================
# OBTENER NAVIERAS DISPONIBLES PARA REPORTES
# =========================================================
def get_report_navieras():

    query = """
        SELECT DISTINCT
            naviera
        FROM citas
        WHERE naviera IS NOT NULL
          AND TRIM(naviera) <> ''
        ORDER BY naviera ASC
    """

    return execute_query(
        query,
        fetchall=True
    )


# =========================================================
# REPORTE MERCHANT
# =========================================================
def get_merchant_report(
    fecha_desde,
    fecha_hasta,
    naviera=None,
    predios=None
):

    """
    Obtiene citas completadas para el reporte Merchant.

    Filtros:
        - Rango de fechas obligatorio.
        - Naviera opcional.
        - Predios opcional.

    El contenedor mostrado se resuelve así:
        1. contenedor registrado originalmente en la cita.
        2. contenedor registrado en portón.
        3. '-' si ninguno existe.
    """

    query = """
        SELECT
            c.id,

            COALESCE(
                NULLIF(TRIM(c.contenedor), ''),
                NULLIF(TRIM(c.contenedor_registrado), ''),
                '-'
            ) AS contenedor_reporte,

            COALESCE(
                NULLIF(TRIM(c.bk_bl), ''),
                '-'
            ) AS bk_bl,

            c.fecha,

            COALESCE(
                NULLIF(TRIM(c.servicio_terminal), ''),
                '-'
            ) AS servicio_terminal,

            COALESCE(
                NULLIF(TRIM(c.chofer_nombre), ''),
                '-'
            ) AS chofer_nombre,

            COALESCE(
                NULLIF(TRIM(c.cabezal_placa), ''),
                '-'
            ) AS cabezal_placa,

            COALESCE(
                NULLIF(TRIM(c.naviera), ''),
                '-'
            ) AS naviera,

            COALESCE(
                NULLIF(TRIM(p.nombre), ''),
                '-'
            ) AS predio_nombre

        FROM citas c

        LEFT JOIN predios p
            ON p.id = c.predio_id

        WHERE c.estado = 'Completada'
          AND c.fecha::date BETWEEN %s AND %s
    """

    params = [
        fecha_desde,
        fecha_hasta
    ]

    # =====================================================
    # FILTRO POR NAVIERA
    # =====================================================
    if naviera:

        query += """
          AND c.naviera = %s
        """

        params.append(
            naviera
        )

    # =====================================================
    # FILTRO POR PREDIOS
    # =====================================================
    if predios:

        query += """
          AND c.predio_id = ANY(%s)
        """

        params.append(
            predios
        )

    # =====================================================
    # ORDEN
    # =====================================================
    query += """
        ORDER BY
            c.fecha ASC,
            c.horario ASC,
            c.id ASC
    """

    return execute_query(
        query,
        tuple(params),
        fetchall=True
    )