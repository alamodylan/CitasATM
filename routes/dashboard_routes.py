# routes/dashboard_routes.py

from datetime import timezone
from zoneinfo import ZoneInfo

from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash
)

from services.auth_service import (
    login_required,
    role_required,
    user_has_predio_access
)

from db import execute_query

# =========================================================
# BLUEPRINT
# =========================================================
dashboard_bp = Blueprint(
    "dashboard",
    __name__
)


# =========================================================
# DASHBOARD PRINCIPAL
# =========================================================
@dashboard_bp.route("/dashboard")
@login_required
@role_required(["ADMIN", "PREDIO"])
def dashboard():

    # =====================================================
    # PREDIO ACTIVO
    # =====================================================
    active_predio_id = session.get(
        "active_predio_id"
    )

    if not active_predio_id:

        flash(
            "Debe seleccionar un predio.",
            "warning"
        )

        return redirect(
            url_for("citas.home")
        )

    if not user_has_predio_access(
        active_predio_id
    ):

        flash(
            "No tiene acceso a este predio.",
            "danger"
        )

        return redirect(
            url_for("citas.home")
        )

    user_predios = [active_predio_id]

    # =====================================================
    # FILTROS
    # =====================================================
    fecha = request.args.get(
        "fecha",
        ""
    )

    naviera = request.args.get(
        "naviera",
        ""
    )

    tipo_operacion = request.args.get(
        "tipo_operacion",
        ""
    )

    horario = request.args.get(
        "horario",
        ""
    )

    estado = request.args.get(
        "estado",
        ""
    )

    estado_contenedor = request.args.get(
        "estado_contenedor",
        ""
    )

    # =====================================================
    # QUERY BASE
    # =====================================================
    query = """
        SELECT
            c.*,
            p.nombre AS predio_nombre
        FROM citas c
        LEFT JOIN predios p
            ON p.id = c.predio_id
        WHERE c.predio_id = ANY(%s)
    """

    params = [user_predios]

    # =====================================================
    # FILTROS DINÁMICOS
    # =====================================================
    if fecha:

        query += " AND c.fecha = %s"
        params.append(fecha)

    if naviera:

        query += " AND c.naviera = %s"
        params.append(naviera)

    if tipo_operacion:

        query += (
            " AND c.tipo_operacion = %s"
        )

        params.append(tipo_operacion)

    if horario:

        query += " AND c.horario = %s"
        params.append(horario)

    if estado:

        query += " AND c.estado = %s"
        params.append(estado)

    if estado_contenedor:

        query += (
            " AND c.estado_contenedor = %s"
        )

        params.append(
            estado_contenedor
        )

    query += """
        ORDER BY
            c.fecha DESC,
            c.horario ASC
    """

    citas = execute_query(
        query,
        tuple(params),
        fetchall=True
    )

    # =====================================================
    # FECHA/HORA CONFIRMACIÓN EN HORA COSTA RICA
    # =====================================================
    cr_tz = ZoneInfo("America/Costa_Rica")

    for cita in citas:

        fecha_confirmacion = cita.get(
            "fecha_confirmacion"
        )

        if fecha_confirmacion:

            if fecha_confirmacion.tzinfo is None:

                fecha_confirmacion = fecha_confirmacion.replace(
                    tzinfo=timezone.utc
                )

            cita["fecha_confirmacion_cr"] = (
                fecha_confirmacion.astimezone(
                    cr_tz
                )
            )

        else:

            cita["fecha_confirmacion_cr"] = None

    # =====================================================
    # ESTADÍSTICAS
    # =====================================================
    stats_query = """
        SELECT

            COUNT(*) AS total_citas,

            COUNT(*) FILTER (
                WHERE estado = 'Pendiente'
            ) AS pendientes,

            COUNT(*) FILTER (
                WHERE estado = 'Completada'
            ) AS completadas,

            COUNT(*) FILTER (
                WHERE estado = 'Vencida'
            ) AS vencidas

        FROM citas
        WHERE predio_id = ANY(%s)
    """

    stats = execute_query(
        stats_query,
        (user_predios,),
        fetchone=True
    )

    # =====================================================
    # HORARIOS
    # =====================================================
    horarios_query = """
        SELECT DISTINCT horario
        FROM citas
        WHERE predio_id = ANY(%s)
        ORDER BY horario ASC
    """

    horarios = execute_query(
        horarios_query,
        (user_predios,),
        fetchall=True
    )

    # =====================================================
    # PREDIOS
    # =====================================================
    predios_query = """
        SELECT *
        FROM predios
        WHERE id = ANY(%s)
        ORDER BY nombre ASC
    """

    predios = execute_query(
        predios_query,
        (user_predios,),
        fetchall=True
    )

    # =====================================================
    # RENDER
    # =====================================================
    return render_template(
        "dashboard.html",

        citas=citas,

        total_citas=stats["total_citas"],

        pendientes=stats["pendientes"],

        completadas=stats["completadas"],

        vencidas=stats["vencidas"],

        horarios=horarios,

        predios=predios,

        filtros={
            "fecha": fecha,
            "naviera": naviera,
            "tipo_operacion":
                tipo_operacion,
            "horario": horario,
            "estado": estado,
            "estado_contenedor":
                estado_contenedor
        }
    )