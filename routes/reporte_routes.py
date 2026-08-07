# routes/reporte_routes.py

from flask import (
    Blueprint,
    render_template,
    request,
    session,
    send_file
)

from services.auth_service import (
    login_required,
    role_required
)

from services.reporte_service import (
    get_available_report_navieras,
    generate_merchant_report
)

from services.reporte_excel_service import (
    create_merchant_excel
)

from services.audit_service import (
    safe_log_action
)


# =========================================================
# BLUEPRINT
# =========================================================
reporte_bp = Blueprint(
    "reportes",
    __name__
)


# =========================================================
# REPORTE MERCHANT
# =========================================================
@reporte_bp.route(
    "/reportes/merchant",
    methods=[
        "GET",
        "POST"
    ]
)
@login_required
@role_required([
    "SUPERADMIN",
    "ADMIN",
    "PREDIO"
])
def merchant_report():

    navieras = (
        get_available_report_navieras()
    )

    registros = []

    total = 0

    form_data = {
        "fecha_desde": "",
        "fecha_hasta": "",
        "naviera": "TODAS"
    }

    error = None

    if request.method == "POST":

        form_data = {

            "fecha_desde": (
                request.form.get(
                    "fecha_desde"
                ) or ""
            ).strip(),

            "fecha_hasta": (
                request.form.get(
                    "fecha_hasta"
                ) or ""
            ).strip(),

            "naviera": (
                request.form.get(
                    "naviera"
                ) or "TODAS"
            ).strip().upper()

        }

        try:

            result = generate_merchant_report(

                fecha_desde=form_data[
                    "fecha_desde"
                ],

                fecha_hasta=form_data[
                    "fecha_hasta"
                ],

                naviera=(
                    None
                    if form_data["naviera"]
                    == "TODAS"
                    else form_data["naviera"]
                ),

                predios=session.get(
                    "predios",
                    []
                )

            )

            registros = result[
                "registros"
            ]

            total = result[
                "total"
            ]

            # =================================================
            # AUDITORÍA
            # =================================================
            safe_log_action(
                action="GENERAR_REPORTE_MERCHANT",
                module="REPORTES",
                details={
                    "fecha_desde": form_data[
                        "fecha_desde"
                    ],
                    "fecha_hasta": form_data[
                        "fecha_hasta"
                    ],
                    "naviera": form_data[
                        "naviera"
                    ],
                    "predios": session.get(
                        "predios",
                        []
                    ),
                    "total_registros": total
                }
            )

        except Exception as e:

            error = str(e)

    return render_template(

        "reportes.html",

        navieras=navieras,

        registros=registros,

        total=total,

        form_data=form_data,

        error=error

    )


# =========================================================
# EXPORTAR REPORTE MERCHANT A EXCEL
# =========================================================
@reporte_bp.route(
    "/reportes/merchant/excel",
    methods=["POST"]
)
@login_required
@role_required([
    "SUPERADMIN",
    "ADMIN",
    "PREDIO"
])
def merchant_report_excel():

    # =====================================================
    # OBTENER FILTROS
    # =====================================================
    fecha_desde = (
        request.form.get(
            "fecha_desde"
        ) or ""
    ).strip()

    fecha_hasta = (
        request.form.get(
            "fecha_hasta"
        ) or ""
    ).strip()

    naviera = (
        request.form.get(
            "naviera"
        ) or "TODAS"
    ).strip().upper()

    # =====================================================
    # GENERAR DATOS DEL REPORTE
    # =====================================================
    result = generate_merchant_report(

        fecha_desde=fecha_desde,

        fecha_hasta=fecha_hasta,

        naviera=(
            None
            if naviera == "TODAS"
            else naviera
        ),

        predios=session.get(
            "predios",
            []
        )

    )

    registros = result[
        "registros"
    ]

    # =====================================================
    # GENERAR ARCHIVO EXCEL
    # =====================================================
    excel_file = create_merchant_excel(

        registros=registros,

        fecha_desde=fecha_desde,

        fecha_hasta=fecha_hasta,

        naviera=naviera,

        username=session.get(
            "username"
        ) or "Sistema"

    )

    # =====================================================
    # AUDITORÍA
    # =====================================================
    safe_log_action(
        action="EXPORTAR_EXCEL_MERCHANT",
        module="REPORTES",
        details={
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
            "naviera": naviera,
            "predios": session.get(
                "predios",
                []
            ),
            "total_registros": len(
                registros
            )
        }
    )

    # =====================================================
    # NOMBRE DEL ARCHIVO
    # =====================================================
    filename = (
        f"Reporte_Merchant_"
        f"{fecha_desde}_"
        f"{fecha_hasta}.xlsx"
    )

    # =====================================================
    # DESCARGAR
    # =====================================================
    return send_file(

        excel_file,

        as_attachment=True,

        download_name=filename,

        mimetype=(
            "application/"
            "vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )

    )