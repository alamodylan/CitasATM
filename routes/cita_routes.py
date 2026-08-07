# routes/cita_routes.py

from datetime import datetime

import pytz
from db import execute_query
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from services.audit_service import (
    safe_log_action
)

from config import Config

from services.auth_service import (
    login_required,
    role_required,
    user_has_predio_access
)

from services.cita_service import (
    generate_time_slots,
    get_time_slots_status,
    create_new_cita,
    create_multiple_citas,
    update_existing_cita,
    get_all_pending_citas,
    get_all_completed_citas,
    get_all_expired_citas,
    get_all_cancelled_citas,
    get_cita,
    cancel_cita_by_user,
    remove_cita,
    check_expired_citas
)

from models.predio_model import (
    get_predios_by_user
)

from services.audit_service import (
    safe_log_action
)


# =========================================================
# BLUEPRINT
# =========================================================
cita_bp = Blueprint(
    "citas",
    __name__
)


# =========================================================
# OBTENER ROL ACTUAL
# =========================================================
def get_current_role():

    return (
        session.get("role") or ""
    ).strip().upper()


# =========================================================
# OBTENER NAVIERA DE FILTRO
# =========================================================
def get_current_naviera_filter():

    if get_current_role() == "NAVIERA":

        naviera = (
            session.get("naviera") or ""
        ).strip().upper()

        return naviera or None

    return None


# =========================================================
# OBTENER FECHA LOCAL ACTUAL
# =========================================================
def get_local_today():

    zona_local = pytz.timezone(
        Config.TIMEZONE
    )

    return datetime.now(
        zona_local
    ).date()


# =========================================================
# OBTENER FECHA LOCAL EN FORMATO HTML
# =========================================================
def get_local_today_string():

    return get_local_today().strftime(
        "%Y-%m-%d"
    )


# =========================================================
# OBTENER IDS DE PREDIOS
# =========================================================
def get_predio_ids(predios):

    predio_ids = []

    for predio in predios or []:

        try:

            predio_ids.append(
                int(predio["id"])
            )

        except (
            KeyError,
            TypeError,
            ValueError
        ):

            continue

    return predio_ids


# =========================================================
# HELPER PREDIO ACTIVO
# =========================================================
def get_active_predio_id(predios):

    if not predios:

        session.pop(
            "active_predio_id",
            None
        )

        session.pop(
            "active_predio_nombre",
            None
        )

        return None

    predio_ids = get_predio_ids(
        predios
    )

    try:

        predio_id = int(
            session.get(
                "active_predio_id"
            )
        )

    except (
        TypeError,
        ValueError
    ):

        predio_id = None

    # Si el predio guardado en sesión ya no está asignado
    # al usuario, seleccionamos el primero permitido.
    if predio_id not in predio_ids:

        predio_id = int(
            predios[0]["id"]
        )

        session[
            "active_predio_id"
        ] = predio_id

        session[
            "active_predio_nombre"
        ] = predios[0]["nombre"]

    return predio_id


# =========================================================
# CARGAR CONTEXTO DEL USUARIO
# =========================================================
def get_user_cita_context():

    user_id = session.get(
        "user_id"
    )

    predios = get_predios_by_user(
        user_id
    )

    predio_id = get_active_predio_id(
        predios
    )

    return {
        "user_id": user_id,
        "role": get_current_role(),
        "naviera": get_current_naviera_filter(),
        "predios": predios,
        "predio_ids": get_predio_ids(
            predios
        ),
        "predio_id": predio_id
    }


# =========================================================
# VALIDAR PREDIO ACTIVO
# =========================================================
def validate_active_predio(context):

    predio_id = context.get(
        "predio_id"
    )

    if not predio_id:

        return False

    return user_has_predio_access(
        predio_id
    )


# =========================================================
# REDIRECCIÓN POR FALTA DE PREDIO
# =========================================================
def redirect_no_predio_access():

    flash(
        "No tiene acceso a ese predio.",
        "danger"
    )

    return redirect(
        url_for("auth.logout")
    )


# =========================================================
# DATOS DEL FORMULARIO
# =========================================================
def build_cita_form_data(
    predio_id
):

    return {
        "contenedor": (
            request.form.get(
                "contenedor"
            ) or ""
        ).strip().upper(),

        "bk_bl": (
            request.form.get(
                "bk_bl"
            ) or ""
        ).strip().upper(),

        "chofer_nombre": (
            request.form.get(
                "chofer_nombre"
            ) or ""
        ).strip(),

        "chofer_cedula": (
            request.form.get(
                "chofer_cedula"
            ) or ""
        ).strip(),

        "cabezal_placa": (
            request.form.get(
                "cabezal_placa"
            ) or ""
        ).strip().upper(),

        "fecha": request.form.get(
            "fecha"
        ),

        "horario": request.form.get(
            "horario"
        ),

        "naviera": (
            request.form.get(
                "naviera"
            ) or ""
        ).strip().upper(),

        "estado_contenedor": (
            request.form.get(
                "estado_contenedor"
            ) or ""
        ).strip(),

        "tipo_operacion": (
            request.form.get(
                "tipo_operacion"
            ) or ""
        ).strip(),

        "predio_id": predio_id
    }


# =========================================================
# HOME / PENDIENTES
# =========================================================
@cita_bp.route("/inicio")
@login_required
def home():

    check_expired_citas()

    context = get_user_cita_context()

    if not validate_active_predio(
        context
    ):

        return redirect_no_predio_access()

    citas = get_all_pending_citas(
        predios=[
            context["predio_id"]
        ],
        naviera=context["naviera"]
    )

    completadas = get_all_completed_citas(
        predios=[
            context["predio_id"]
        ],
        naviera=context["naviera"]
    )

    vencidas = get_all_expired_citas(
        predios=[
            context["predio_id"]
        ],
        naviera=context["naviera"]
    )

    canceladas = get_all_cancelled_citas(
        predios=[
            context["predio_id"]
        ],
        naviera=context["naviera"]
    )

    return render_template(
        "index.html",
        citas=citas,
        completadas_count=len(
            completadas
        ),
        vencidas_count=len(
            vencidas
        ),
        canceladas_count=len(
            canceladas
        ),
        predios=context["predios"],
        predio_actual=context["predio_id"],
        user_role=context["role"],
        user_naviera=context["naviera"]
    )


# =========================================================
# VENCIDAS
# =========================================================
@cita_bp.route("/vencidas")
@login_required
def vencidas():

    context = get_user_cita_context()

    if not validate_active_predio(
        context
    ):

        return redirect_no_predio_access()

    citas = get_all_expired_citas(
        predios=[
            context["predio_id"]
        ],
        naviera=context["naviera"]
    )

    return render_template(
        "vencidas.html",
        citas=citas,
        predios=context["predios"],
        predio_actual=context["predio_id"],
        user_role=context["role"],
        user_naviera=context["naviera"]
    )


# =========================================================
# COMPLETADAS
# =========================================================
@cita_bp.route("/completadas")
@login_required
def completadas():

    context = get_user_cita_context()

    if not validate_active_predio(
        context
    ):

        return redirect_no_predio_access()

    citas = get_all_completed_citas(
        predios=[
            context["predio_id"]
        ],
        naviera=context["naviera"]
    )

    return render_template(
        "completadas.html",
        citas=citas,
        predios=context["predios"],
        predio_actual=context["predio_id"],
        user_role=context["role"],
        user_naviera=context["naviera"]
    )


# =========================================================
# CANCELADAS
# =========================================================
@cita_bp.route("/canceladas")
@login_required
def canceladas():

    context = get_user_cita_context()

    if not validate_active_predio(
        context
    ):

        return redirect_no_predio_access()

    citas = get_all_cancelled_citas(
        predios=[
            context["predio_id"]
        ],
        naviera=context["naviera"]
    )

    return render_template(
        "canceladas.html",
        citas=citas,
        predios=context["predios"],
        predio_actual=context["predio_id"],
        user_role=context["role"],
        user_naviera=context["naviera"]
    )


# =========================================================
# CONSULTAR ESTADO DE HORARIOS
# =========================================================
@cita_bp.route(
    "/horarios-disponibles",
    methods=["GET"]
)
@login_required
@role_required([
    "SUPERADMIN",
    "ADMIN",
    "PREDIO",
    "NAVIERA"
])
def horarios_disponibles():

    context = get_user_cita_context()

    if not validate_active_predio(
        context
    ):

        return {
            "success": False,
            "message": (
                "No tiene acceso al predio activo."
            ),
            "horarios": []
        }, 403

    fecha_texto = (
        request.args.get(
            "fecha"
        ) or ""
    ).strip()

    cita_id_texto = (
        request.args.get(
            "cita_id"
        ) or ""
    ).strip()

    if not fecha_texto:

        return {
            "success": False,
            "message": (
                "Debe seleccionar una fecha."
            ),
            "horarios": []
        }, 400

    try:

        fecha_seleccionada = datetime.strptime(
            fecha_texto,
            "%Y-%m-%d"
        ).date()

    except ValueError:

        return {
            "success": False,
            "message": (
                "La fecha seleccionada no es válida."
            ),
            "horarios": []
        }, 400

    if fecha_seleccionada < get_local_today():

        return {
            "success": False,
            "message": (
                "No puede seleccionar una fecha anterior "
                "a la fecha actual."
            ),
            "horarios": []
        }, 400

    exclude_cita_id = None
    predio_id = context["predio_id"]

    # =====================================================
    # SI VIENE CITA_ID, ES UNA CONSULTA DESDE EDICIÓN
    # =====================================================
    if cita_id_texto:

        try:

            exclude_cita_id = int(
                cita_id_texto
            )

        except (
            TypeError,
            ValueError
        ):

            return {
                "success": False,
                "message": (
                    "El identificador de la cita "
                    "no es válido."
                ),
                "horarios": []
            }, 400

        cita = get_cita(
            cita_id=exclude_cita_id,
            predios=context["predio_ids"],
            naviera=context["naviera"]
        )

        if not cita:

            return {
                "success": False,
                "message": (
                    "Cita no encontrada o sin permiso "
                    "para acceder a ella."
                ),
                "horarios": []
            }, 404

        if cita["estado"] != "Pendiente":

            return {
                "success": False,
                "message": (
                    "Solo se pueden consultar horarios "
                    "para citas pendientes."
                ),
                "horarios": []
            }, 400

        # En edición se utiliza el predio real de la cita.
        predio_id = int(
            cita["predio_id"]
        )

    horarios = get_time_slots_status(
        fecha=fecha_texto,
        predio_id=predio_id,
        limite=4,
        exclude_cita_id=exclude_cita_id
    )

    return {
        "success": True,
        "message": "",
        "horarios": horarios
    }


# =========================================================
# CREAR CITA
# =========================================================
@cita_bp.route(
    "/crear-cita",
    methods=["GET", "POST"]
)
@login_required
@role_required([
    "SUPERADMIN",
    "ADMIN",
    "PREDIO",
    "NAVIERA"
])
def crear_cita():

    context = get_user_cita_context()

    if not validate_active_predio(
        context
    ):

        return redirect_no_predio_access()

    form_data = {}

    fecha_hoy = get_local_today_string()

    if request.method == "POST":

        form_data = build_cita_form_data(
            context["predio_id"]
        )

        try:

            create_new_cita(
                data=form_data,
                created_by=context[
                    "user_id"
                ],
                user_role=context[
                    "role"
                ],
                user_naviera=session.get(
                    "naviera"
                ),
                allowed_predios=context[
                    "predio_ids"
                ]
            )

            safe_log_action(
                action="CREAR_CITA",
                module="CITAS",
                details={
                    "bk_bl": form_data.get(
                        "bk_bl"
                    ),
                    "contenedor": form_data.get(
                        "contenedor"
                    ),
                    "naviera": (
                        context["naviera"]
                        or form_data.get(
                            "naviera"
                        )
                    ),
                    "predio_id": form_data.get(
                        "predio_id"
                    ),
                    "fecha": form_data.get(
                        "fecha"
                    ),
                    "horario": form_data.get(
                        "horario"
                    )
                }
            )

        except Exception as error:

            flash(
                str(error),
                "danger"
            )

            return render_template(
                "crear_cita.html",
                time_slots=generate_time_slots(),
                predios=context["predios"],
                predio_actual=context[
                    "predio_id"
                ],
                user_role=context["role"],
                user_naviera=context[
                    "naviera"
                ],
                form_data=form_data,
                fecha_hoy=fecha_hoy
            )

        flash(
            "Cita creada correctamente.",
            "success"
        )

        return redirect(
            url_for("citas.home")
        )

    return render_template(
        "crear_cita.html",
        time_slots=generate_time_slots(),
        predios=context["predios"],
        predio_actual=context["predio_id"],
        user_role=context["role"],
        user_naviera=context["naviera"],
        form_data=form_data,
        fecha_hoy=fecha_hoy
    )


# =========================================================
# CREACIÓN MASIVA
# =========================================================
@cita_bp.route(
    "/crear-citas-masivas",
    methods=["POST"]
)
@login_required
@role_required([
    "SUPERADMIN",
    "ADMIN",
    "PREDIO",
    "NAVIERA"
])
def crear_citas_masivas():

    context = get_user_cita_context()

    if not validate_active_predio(
        context
    ):

        return {
            "success": False,
            "created": 0,
            "errors": [
                "No tiene acceso al predio activo."
            ]
        }, 403

    payload = request.get_json(
        silent=True
    ) or {}

    citas = payload.get(
        "citas",
        []
    )

    if not isinstance(
        citas,
        list
    ):

        return {
            "success": False,
            "created": 0,
            "errors": [
                "El formato enviado no es válido."
            ]
        }, 400

    # Todas las citas masivas quedan en el predio activo.
    # No se acepta un predio enviado desde el navegador.
    normalized_citas = []

    for cita in citas:

        if not isinstance(
            cita,
            dict
        ):

            continue

        cita_data = dict(
            cita
        )

        cita_data[
            "predio_id"
        ] = context["predio_id"]

        normalized_citas.append(
            cita_data
        )

    result = create_multiple_citas(
        citas=normalized_citas,
        created_by=context["user_id"],
        user_role=context["role"],
        user_naviera=session.get(
            "naviera"
        ),
        allowed_predios=context[
            "predio_ids"
        ]
    )

    safe_log_action(
        action="CREAR_CITAS_MASIVAS",
        module="CITAS",
        details={
            "creadas": result.get(
                "created",
                0
            ),
            "errores": len(
                result.get(
                    "errors",
                    []
                )
            ),
            "predio_id": context.get(
                "predio_id"
            )
        }
    )

    if result["errors"]:

        flash(
            (
                f"Se crearon "
                f"{result['created']} citas. "
                "Algunas filas presentaron errores."
            ),
            "warning"
        )

    else:

        flash(
            "Citas creadas correctamente.",
            "success"
        )

    return {
        "success": (
            len(result["errors"]) == 0
        ),
        "created": result["created"],
        "errors": result["errors"]
    }


# =========================================================
# EDITAR CITA
# =========================================================
@cita_bp.route(
    "/editar-cita/<int:cita_id>",
    methods=["GET", "POST"]
)
@login_required
@role_required([
    "SUPERADMIN",
    "ADMIN",
    "NAVIERA"
])
def editar_cita(cita_id):

    context = get_user_cita_context()

    if not validate_active_predio(
        context
    ):

        return redirect_no_predio_access()

    fecha_hoy = get_local_today_string()

    cita = get_cita(
        cita_id=cita_id,
        predios=context["predio_ids"],
        naviera=context["naviera"]
    )

    if not cita:

        flash(
            (
                "Cita no encontrada o no tiene "
                "permiso para acceder a ella."
            ),
            "danger"
        )

        return redirect(
            url_for("citas.home")
        )

    if cita["estado"] != "Pendiente":

        flash(
            "Solo se pueden editar citas pendientes.",
            "warning"
        )

        return redirect(
            url_for("citas.home")
        )

    if request.method == "POST":

        # Se conserva el predio de la cita.
        # No se cambia silenciosamente al predio activo.
        form_data = build_cita_form_data(
            cita["predio_id"]
        )

        result = update_existing_cita(
            cita_id=cita_id,
            data=form_data,
            user_role=context["role"],
            user_naviera=session.get(
                "naviera"
            ),
            allowed_predios=context[
                "predio_ids"
            ]
        )

        if not result["success"]:

            flash(
                result["message"],
                "danger"
            )

            edited_cita = dict(
                cita
            )

            edited_cita.update(
                form_data
            )

            return render_template(
                "editar_cita.html",
                cita=edited_cita,
                time_slots=generate_time_slots(),
                predios=context["predios"],
                predio_actual=context[
                    "predio_id"
                ],
                user_role=context["role"],
                user_naviera=context[
                    "naviera"
                ],
                fecha_hoy=fecha_hoy
            )

        safe_log_action(
            action="EDITAR_CITA",
            module="CITAS",
            entity_id=cita_id,
            details={
                "bk_bl": form_data.get(
                    "bk_bl"
                ),
                "contenedor": form_data.get(
                    "contenedor"
                ),
                "fecha": form_data.get(
                    "fecha"
                ),
                "horario": form_data.get(
                    "horario"
                ),
                "naviera": (
                    context["naviera"]
                    or form_data.get(
                        "naviera"
                    )
                )
            }
        )

        flash(
            result["message"],
            "success"
        )

        return redirect(
            url_for("citas.home")
        )

    return render_template(
        "editar_cita.html",
        cita=cita,
        time_slots=generate_time_slots(),
        predios=context["predios"],
        predio_actual=context["predio_id"],
        user_role=context["role"],
        user_naviera=context["naviera"],
        fecha_hoy=fecha_hoy
    )


# =========================================================
# CANCELAR CITA
# =========================================================
@cita_bp.route(
    "/cancelar-cita/<int:cita_id>",
    methods=["POST"]
)
@login_required
@role_required([
    "SUPERADMIN",
    "ADMIN",
    "PREDIO",
    "NAVIERA"
])
def cancelar_cita(cita_id):

    context = get_user_cita_context()

    if not validate_active_predio(
        context
    ):

        return redirect_no_predio_access()

    motivo_cancelacion = (
        request.form.get(
            "motivo_cancelacion"
        ) or ""
    ).strip()

    result = cancel_cita_by_user(
        cita_id=cita_id,
        cancelada_por=context[
            "user_id"
        ],
        motivo_cancelacion=motivo_cancelacion,
        predios=context["predio_ids"],
        naviera=context["naviera"]
    )

    if result["success"]:

        safe_log_action(
            action="CANCELAR_CITA",
            module="CITAS",
            entity_id=cita_id,
            details={
                "motivo": motivo_cancelacion
            }
        )

    flash(
        result["message"],
        (
            "success"
            if result["success"]
            else "danger"
        )
    )

    return redirect(
        url_for("citas.home")
    )

# =========================================================
# GUARDAR ANOTACIÓN EN CITA
# =========================================================
@cita_bp.route(
    "/guardar-anotacion/<int:cita_id>",
    methods=["POST"]
)
@login_required
@role_required([
    "SUPERADMIN",
    "ADMIN",
    "PREDIO"
])
def guardar_anotacion(cita_id):

    context = get_user_cita_context()

    cita = get_cita(
        cita_id=cita_id,
        predios=context["predio_ids"],
        naviera=context["naviera"]
    )

    if not cita:

        flash(
            "Cita no encontrada o sin permiso para acceder.",
            "danger"
        )

        return redirect(
            url_for("citas.vencidas")
        )

    anotacion = (
        request.form.get(
            "anotacion"
        ) or ""
    ).strip()

    if not anotacion:

        flash(
            "Debe ingresar una anotación.",
            "warning"
        )

        return redirect(
            url_for("citas.vencidas")
        )

    query = """
        UPDATE citas
        SET
            anotaciones = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """

    execute_query(
        query,
        (
            anotacion,
            cita_id
        ),
        commit=True
    )

    safe_log_action(
        action="GUARDAR_ANOTACION",
        module="CITAS",
        entity_id=cita_id,
        details={
            "anotacion": anotacion
        }
    )

    flash(
        "Anotación guardada correctamente.",
        "success"
    )

    return redirect(
        url_for("citas.vencidas")
    )

# =========================================================
# ELIMINAR CITA
# =========================================================
@cita_bp.route(
    "/eliminar-cita/<int:cita_id>",
    methods=["POST"]
)
@login_required
@role_required([
    "SUPERADMIN",
    "ADMIN"
])
def eliminar_cita(cita_id):

    context = get_user_cita_context()

    cita = get_cita(
        cita_id=cita_id,
        predios=context["predio_ids"]
    )

    if not cita:

        flash(
            (
                "Cita no encontrada o no tiene "
                "permiso para acceder a ella."
            ),
            "danger"
        )

        return redirect(
            url_for("citas.home")
        )

    result = remove_cita(
        cita_id
    )

    if result["success"]:

        safe_log_action(
            action="ELIMINAR_CITA",
            module="CITAS",
            entity_id=cita_id,
            details={
                "bk_bl": cita.get(
                    "bk_bl"
                ),
                "contenedor": cita.get(
                    "contenedor"
                ),
                "naviera": cita.get(
                    "naviera"
                ),
                "predio_id": cita.get(
                    "predio_id"
                )
            }
        )

    flash(
        result.get(
            "message",
            (
                "Cita eliminada."
                if result["success"]
                else "No fue posible eliminar la cita."
            )
        ),
        (
            "success"
            if result["success"]
            else "danger"
        )
    )

    return redirect(
        url_for("citas.home")
    )