# routes/export_routes.py

from io import BytesIO

from flask import (
    Blueprint,
    send_file,
    request,
    session,
    flash,
    redirect,
    url_for
)

from openpyxl import Workbook

from services.auth_service import (
    login_required,
    role_required,
    user_has_predio_access
)

from db import execute_query

# =========================================================
# BLUEPRINT
# =========================================================
export_bp = Blueprint(
    "exports",
    __name__
)


# =========================================================
# EXPORTAR CITAS FILTRADAS
# =========================================================
@export_bp.route("/exportar-citas")
@login_required
@role_required(["ADMIN", "PREDIO"])
def exportar_citas():

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
    # QUERY
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
    # EXCEL
    # =====================================================
    wb = Workbook()

    ws = wb.active

    ws.title = "Citas"

    # =====================================================
    # HEADERS
    # =====================================================
    headers = [
        "ID",
        "Predio",
        "Contenedor",
        "Contenedor Registrado",
        "Servicio Terminal",
        "Chofer",
        "Cédula",
        "Placa",
        "Naviera",
        "Estado Contenedor",
        "Tipo Operación",
        "Fecha",
        "Horario",
        "Estado"
    ]

    ws.append(headers)

    # =====================================================
    # DATA
    # =====================================================
    for cita in citas:

        ws.append([

            cita["id"],

            cita["predio_nombre"],

            cita["contenedor"],

            cita["contenedor_registrado"],

            cita["servicio_terminal"],

            cita["chofer_nombre"],

            cita["chofer_cedula"],

            cita["cabezal_placa"],

            cita["naviera"],

            cita["estado_contenedor"],

            cita["tipo_operacion"],

            str(cita["fecha"]),

            cita["horario"],

            cita["estado"]
        ])

    # =====================================================
    # GUARDAR
    # =====================================================
    output = BytesIO()

    wb.save(output)

    output.seek(0)

    # =====================================================
    # RETORNAR
    # =====================================================
    return send_file(
        output,
        as_attachment=True,
        download_name="citas.xlsx",
        mimetype=(
            "application/"
            "vnd.openxmlformats-"
            "officedocument."
            "spreadsheetml.sheet"
        )
    )


# =========================================================
# EXPORTAR TODO
# =========================================================
@export_bp.route("/exportar-todas-citas")
@login_required
@role_required(["ADMIN"])
def exportar_todas_citas():

    return redirect(
        url_for("exports.exportar_citas")
    )