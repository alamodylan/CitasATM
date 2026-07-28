# services/cita_service.py

from datetime import datetime, timedelta

import pytz

from config import Config

from models.cita_model import (
    get_pending_citas,
    get_completed_citas,
    get_expired_citas,
    get_cancelled_citas,
    get_cita_by_id,
    create_cita,
    update_cita,
    complete_cita,
    cancel_cita,
    expire_cita,
    delete_cita
)

from db import execute_query


# =========================================================
# HORARIOS DISPONIBLES
# =========================================================
def generate_time_slots():

    time_slots = []

    for hour in range(8, 17):

        time_slots.extend([
            f"{hour:02d}:00-{hour:02d}:15",
            f"{hour:02d}:15-{hour:02d}:30",
            f"{hour:02d}:30-{hour:02d}:45",
            f"{hour:02d}:45-{(hour + 1):02d}:00"
        ])

    return time_slots


# =========================================================
# NORMALIZAR LISTA DE PREDIOS
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
# VALIDAR ACCESO AL PREDIO
# =========================================================
def validate_predio_access(
    predio_id,
    allowed_predios
):

    """
    Valida que el predio de la cita esté dentro de los
    predios asignados al usuario.

    Si allowed_predios es None, no se aplica restricción.
    Esto permite reutilizar la función en procesos internos.
    """

    if allowed_predios is None:

        return True

    normalized_predios = normalize_predios(
        allowed_predios
    )

    try:

        predio_id = int(
            predio_id
        )

    except (
        TypeError,
        ValueError
    ):

        return False

    return predio_id in normalized_predios


# =========================================================
# VALIDAR LÍMITE DE CITAS
# =========================================================
def validate_slot_capacity(
    fecha,
    horario,
    predio_id,
    limite=4,
    exclude_cita_id=None
):

    query = """
        SELECT
            COUNT(*) AS total
        FROM citas
        WHERE fecha = %s
          AND horario = %s
          AND predio_id = %s
          AND estado = 'Pendiente'
    """

    params = [
        fecha,
        horario,
        predio_id
    ]

    if exclude_cita_id is not None:

        query += """
          AND id <> %s
        """

        params.append(
            exclude_cita_id
        )

    result = execute_query(
        query,
        tuple(params),
        fetchone=True
    )

    total = (
        result["total"]
        if result
        else 0
    )

    return total < limite


# =========================================================
# RESOLVER NAVIERA DE LA CITA
# =========================================================
def resolve_cita_naviera(
    data,
    user_role=None,
    user_naviera=None
):

    """
    Para usuarios NAVIERA, la naviera se toma de la sesión
    y nunca del formulario.

    Para usuarios internos, se permite la naviera recibida
    desde el formulario.
    """

    role = (
        user_role or ""
    ).strip().upper()

    if role == "NAVIERA":

        naviera = (
            user_naviera or ""
        ).strip().upper()

        if not naviera:

            raise ValueError(
                "El usuario no tiene una naviera asignada."
            )

        return naviera

    naviera = (
        data.get("naviera") or ""
    ).strip().upper()

    if not naviera:

        raise ValueError(
            "Debe seleccionar una naviera."
        )

    return naviera


# =========================================================
# CREAR CITA
# =========================================================
def create_new_cita(
    data,
    created_by,
    user_role=None,
    user_naviera=None,
    allowed_predios=None
):

    try:

        predio_id = int(
            data["predio_id"]
        )

    except (
        KeyError,
        TypeError,
        ValueError
    ):

        raise ValueError(
            "El predio seleccionado no es válido."
        )

    # ================================================
    # VALIDAR PREDIO DEL USUARIO
    # ================================================
    if not validate_predio_access(
        predio_id,
        allowed_predios
    ):

        raise ValueError(
            "No tiene permiso para crear citas "
            "en el predio seleccionado."
        )

    # ================================================
    # RESOLVER NAVIERA
    # ================================================
    naviera = resolve_cita_naviera(
        data=data,
        user_role=user_role,
        user_naviera=user_naviera
    )

    # ================================================
    # VALIDAR CAPACIDAD
    # ================================================
    has_capacity = validate_slot_capacity(
        fecha=data["fecha"],
        horario=data["horario"],
        predio_id=predio_id
    )

    if not has_capacity:

        raise ValueError(
            "El horario seleccionado ya alcanzó "
            "el límite de citas."
        )

    return create_cita(
        contenedor=data["contenedor"],
        chofer_nombre=data["chofer_nombre"],
        chofer_cedula=data["chofer_cedula"],
        cabezal_placa=data["cabezal_placa"],
        fecha=data["fecha"],
        horario=data["horario"],
        naviera=naviera,
        estado_contenedor=data["estado_contenedor"],
        tipo_operacion=data["tipo_operacion"],
        predio_id=predio_id,
        created_by=created_by
    )


# =========================================================
# CREACIÓN MASIVA
# =========================================================
def create_multiple_citas(
    citas,
    created_by,
    user_role=None,
    user_naviera=None,
    allowed_predios=None
):

    created = 0
    errors = []

    for index, cita in enumerate(
        citas
    ):

        try:

            create_new_cita(
                data=cita,
                created_by=created_by,
                user_role=user_role,
                user_naviera=user_naviera,
                allowed_predios=allowed_predios
            )

            created += 1

        except Exception as error:

            errors.append(
                f"Fila {index + 1}: "
                f"{str(error)}"
            )

    return {
        "created": created,
        "errors": errors
    }

# =========================================================
# ACTUALIZAR CITA
# =========================================================
def update_existing_cita(
    cita_id,
    data,
    user_role=None,
    user_naviera=None,
    allowed_predios=None
):

    normalized_predios = None

    if allowed_predios is not None:

        normalized_predios = normalize_predios(
            allowed_predios
        )

    cita = get_cita_by_id(
        cita_id=cita_id,
        predios=normalized_predios,
        naviera=(
            user_naviera
            if (
                user_role or ""
            ).strip().upper() == "NAVIERA"
            else None
        )
    )

    if not cita:

        return {
            "success": False,
            "message": (
                "Cita no encontrada o sin permiso "
                "para acceder a ella."
            )
        }

    if cita["estado"] != "Pendiente":

        return {
            "success": False,
            "message": (
                "Solo se pueden editar citas pendientes."
            )
        }

    try:

        predio_id = int(
            data["predio_id"]
        )

    except (
        KeyError,
        TypeError,
        ValueError
    ):

        return {
            "success": False,
            "message": (
                "El predio seleccionado no es válido."
            )
        }

    if not validate_predio_access(
        predio_id,
        allowed_predios
    ):

        return {
            "success": False,
            "message": (
                "No tiene permiso para utilizar "
                "el predio seleccionado."
            )
        }

    try:

        naviera = resolve_cita_naviera(
            data=data,
            user_role=user_role,
            user_naviera=user_naviera
        )

    except ValueError as error:

        return {
            "success": False,
            "message": str(error)
        }

    has_capacity = validate_slot_capacity(
        fecha=data.get("fecha"),
        horario=data.get("horario"),
        predio_id=predio_id,
        exclude_cita_id=cita_id
    )

    if not has_capacity:

        return {
            "success": False,
            "message": (
                "El horario seleccionado ya alcanzó "
                "el límite de citas."
            )
        }

    update_cita(
        cita_id=cita_id,
        contenedor=data.get("contenedor"),
        chofer_nombre=data.get("chofer_nombre"),
        chofer_cedula=data.get("chofer_cedula"),
        cabezal_placa=data.get("cabezal_placa"),
        fecha=data.get("fecha"),
        horario=data.get("horario"),
        naviera=naviera,
        estado_contenedor=data.get(
            "estado_contenedor"
        ),
        tipo_operacion=data.get(
            "tipo_operacion"
        ),
        predio_id=predio_id
    )

    return {
        "success": True,
        "message": (
            "Cita actualizada correctamente."
        )
    }

# =========================================================
# OBTENER CITAS PENDIENTES
# =========================================================
def get_all_pending_citas(
    predios,
    naviera=None
):

    return get_pending_citas(
        predios=normalize_predios(
            predios
        ),
        naviera=naviera
    )


# =========================================================
# OBTENER CITAS COMPLETADAS
# =========================================================
def get_all_completed_citas(
    predios,
    naviera=None
):

    return get_completed_citas(
        predios=normalize_predios(
            predios
        ),
        naviera=naviera
    )


# =========================================================
# OBTENER CITAS VENCIDAS
# =========================================================
def get_all_expired_citas(
    predios,
    naviera=None
):

    return get_expired_citas(
        predios=normalize_predios(
            predios
        ),
        naviera=naviera
    )


# =========================================================
# OBTENER CITAS CANCELADAS
# =========================================================
def get_all_cancelled_citas(
    predios,
    naviera=None
):

    return get_cancelled_citas(
        predios=normalize_predios(
            predios
        ),
        naviera=naviera
    )


# =========================================================
# OBTENER CITA
# =========================================================
def get_cita(
    cita_id,
    predios=None,
    naviera=None
):

    normalized_predios = None

    if predios is not None:

        normalized_predios = normalize_predios(
            predios
        )

    return get_cita_by_id(
        cita_id=cita_id,
        predios=normalized_predios,
        naviera=naviera
    )


# =========================================================
# CANCELAR CITA
# =========================================================
def cancel_cita_by_user(
    cita_id,
    cancelada_por,
    motivo_cancelacion,
    predios,
    naviera=None
):

    """
    Cancela una cita validando que pertenezca tanto a los
    predios permitidos como a la naviera del usuario.

    Para usuarios internos, naviera será None.
    Para usuarios NAVIERA, se enviará la naviera de sesión.
    """

    motivo_cancelacion = (
        motivo_cancelacion or ""
    ).strip()

    if not motivo_cancelacion:

        return {
            "success": False,
            "message": (
                "Debe indicar el motivo "
                "de la cancelación."
            )
        }

    cita = get_cita_by_id(
        cita_id=cita_id,
        predios=normalize_predios(
            predios
        ),
        naviera=naviera
    )

    if not cita:

        return {
            "success": False,
            "message": (
                "Cita no encontrada o sin permiso "
                "para acceder a ella."
            )
        }

    if cita["estado"] != "Pendiente":

        return {
            "success": False,
            "message": (
                "Solo se pueden cancelar "
                "citas pendientes."
            )
        }

    cancel_cita(
        cita_id=cita_id,
        cancelada_por=cancelada_por,
        motivo_cancelacion=motivo_cancelacion
    )

    return {
        "success": True,
        "message": (
            "Cita cancelada correctamente."
        )
    }


# =========================================================
# COMPLETAR DESDE PORTÓN
# =========================================================
def complete_cita_from_porton(
    cita_id,
    contenedor_registrado,
    servicio_terminal,
    confirmado_por
):

    cita = get_cita_by_id(
        cita_id
    )

    if not cita:

        return {
            "success": False,
            "message": (
                "Cita no encontrada."
            )
        }

    if cita["estado"] != "Pendiente":

        return {
            "success": False,
            "message": (
                "Solo se pueden completar "
                "citas pendientes."
            )
        }

    complete_cita(
        cita_id=cita_id,
        contenedor_registrado=contenedor_registrado,
        servicio_terminal=servicio_terminal,
        confirmado_por=confirmado_por
    )

    return {
        "success": True,
        "message": (
            "Cita completada correctamente."
        )
    }


# =========================================================
# ELIMINAR CITA
# =========================================================
def remove_cita(
    cita_id
):

    """
    La restricción de SUPERADMIN debe aplicarse también
    en la ruta mediante role_required.
    """

    cita = get_cita_by_id(
        cita_id
    )

    if not cita:

        return {
            "success": False,
            "message": (
                "Cita no encontrada."
            )
        }

    delete_cita(
        cita_id
    )

    return {
        "success": True,
        "message": (
            "Cita eliminada correctamente."
        )
    }


# =========================================================
# VERIFICAR CITAS VENCIDAS
# =========================================================
def check_expired_citas():

    zona_local = pytz.timezone(
        Config.TIMEZONE
    )

    now = datetime.now(
        zona_local
    )

    query = """
        SELECT
            id,
            fecha,
            horario
        FROM citas
        WHERE estado = 'Pendiente'
    """

    pendientes = execute_query(
        query,
        fetchall=True
    )

    for cita in pendientes:

        try:

            cita_date = cita["fecha"]

            cita_end_time = (
                cita["horario"]
                .split("-")[1]
            )

            cita_end_datetime = datetime.strptime(
                f"{cita_date} {cita_end_time}",
                "%Y-%m-%d %H:%M"
            )

            cita_end_datetime = (
                zona_local.localize(
                    cita_end_datetime
                )
            )

            expiration_datetime = (
                cita_end_datetime
                + timedelta(hours=2)
            )

            if expiration_datetime < now:

                expire_cita(
                    cita["id"]
                )

        except Exception as error:

            print(
                "[ERROR VENCIMIENTO] "
                f"Cita {cita.get('id')}: "
                f"{error}"
            )