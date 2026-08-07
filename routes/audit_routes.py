# routes/audit_routes.py

from flask import (
    Blueprint,
    render_template,
    request
)

from services.auth_service import (
    login_required,
    role_required
)

from services.audit_query_service import (
    search_audit_logs,
    get_audit_filters
)


# =========================================================
# BLUEPRINT
# =========================================================
audit_bp = Blueprint(
    "audit",
    __name__
)


# =========================================================
# AUDITORÍA
# =========================================================
@audit_bp.route(
    "/auditoria",
    methods=[
        "GET",
        "POST"
    ]
)
@login_required
@role_required([
    "SUPERADMIN"
])
def auditoria():

    filtros = get_audit_filters()

    form_data = {

        "fecha_desde": "",
        "fecha_hasta": "",
        "username": "",
        "module": "",
        "action": ""

    }

    registros = []

    total = 0

    page = 1

    pages = 1

    page_size = 100

    error = None

    # =====================================================
    # GET
    # =====================================================
    if request.method == "GET":

        page = request.args.get(
            "page",
            1
        )

        form_data = {

            "fecha_desde": (
                request.args.get(
                    "fecha_desde"
                ) or ""
            ).strip(),

            "fecha_hasta": (
                request.args.get(
                    "fecha_hasta"
                ) or ""
            ).strip(),

            "username": (
                request.args.get(
                    "username"
                ) or ""
            ).strip(),

            "module": (
                request.args.get(
                    "module"
                ) or ""
            ).strip().upper(),

            "action": (
                request.args.get(
                    "action"
                ) or ""
            ).strip().upper()

        }

    # =====================================================
    # POST
    # =====================================================
    else:

        page = 1

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

            "username": (
                request.form.get(
                    "username"
                ) or ""
            ).strip(),

            "module": (
                request.form.get(
                    "module"
                ) or ""
            ).strip().upper(),

            "action": (
                request.form.get(
                    "action"
                ) or ""
            ).strip().upper()

        }

    # =====================================================
    # CONSULTAR
    # =====================================================
    try:

        result = search_audit_logs(

            fecha_desde=form_data[
                "fecha_desde"
            ],

            fecha_hasta=form_data[
                "fecha_hasta"
            ],

            username=form_data[
                "username"
            ],

            module=form_data[
                "module"
            ],

            action=form_data[
                "action"
            ],

            page=page,

            page_size=100

        )

        registros = result[
            "registros"
        ]

        total = result[
            "total"
        ]

        page = result[
            "page"
        ]

        pages = result[
            "pages"
        ]

        page_size = result[
            "page_size"
        ]

    except Exception as e:

        error = str(e)

    return render_template(

        "auditoria.html",

        registros=registros,

        total=total,

        filtros=filtros,

        form_data=form_data,

        page=page,

        pages=pages,

        page_size=page_size,

        error=error

    )