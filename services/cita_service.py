# services/cita_service.py

from datetime import datetime, timedelta

import pytz

from config import Config

from models.cita_model import (
    get_pending_citas,
    get_completed_citas,
    get_expired_citas,
    get_cita_by_id,
    create_cita,
    complete_cita,
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
# VALIDAR LÍMITE DE CITAS
# =========================================================
def validate_slot_capacity(
    fecha,
    horario,
    predio_id,
    limite=5
):

    query = """
        SELECT COUNT(*) AS total
        FROM citas
        WHERE fecha = %s
          AND horario = %s
          AND predio_id = %s
    """

    result = execute_query(
        query,
        (
            fecha,
            horario,
            predio_id
        ),
        fetchone=True
    )

    return result["total"] < limite


# =========================================================
# CREAR CITA
# =========================================================
def create_new_cita(
    data,
    created_by
):

    return create_cita(
        contenedor=data["contenedor"],
        chofer_nombre=data["chofer_nombre"],
        chofer_cedula=data["chofer_cedula"],
        cabezal_placa=data["cabezal_placa"],
        fecha=data["fecha"],
        horario=data["horario"],
        naviera=data["naviera"],
        estado_contenedor=data["estado_contenedor"],
        tipo_operacion=data["tipo_operacion"],
        predio_id=data["predio_id"],
        created_by=created_by
    )


# =========================================================
# CREACIÓN MASIVA
# =========================================================
def create_multiple_citas(
    citas,
    created_by
):

    created = 0

    errors = []

    for index, cita in enumerate(citas):

        try:

            has_capacity = validate_slot_capacity(
                cita["fecha"],
                cita["horario"],
                cita["predio_id"]
            )

            if not has_capacity:

                errors.append(
                    f"Fila {index + 1}: "
                    f"Horario lleno."
                )

                continue

            create_new_cita(
                cita,
                created_by
            )

            created += 1

        except Exception as e:

            errors.append(
                f"Fila {index + 1}: {str(e)}"
            )

    return {
        "created": created,
        "errors": errors
    }


# =========================================================
# OBTENER CITAS
# =========================================================
def get_all_pending_citas(
    predios
):

    return get_pending_citas(
        predios
    )


def get_all_completed_citas(
    predios
):

    return get_completed_citas(
        predios
    )


def get_all_expired_citas(
    predios
):

    return get_expired_citas(
        predios
    )


# =========================================================
# OBTENER CITA
# =========================================================
def get_cita(cita_id):

    return get_cita_by_id(
        cita_id
    )


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
        cita_id,
        contenedor_registrado,
        servicio_terminal,
        confirmado_por
    )

    return {
        "success": True
    }


# =========================================================
# ELIMINAR CITA
# =========================================================
def remove_cita(cita_id):

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
        "success": True
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
            c.*,
            p.nombre AS predio_nombre
        FROM citas c
        LEFT JOIN predios p
            ON p.id = c.predio_id
        WHERE c.estado = 'Pendiente'
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

            if (
                cita_end_datetime +
                timedelta(hours=2)
            ) < now:

                query = """
                    UPDATE citas
                    SET estado = 'Vencida',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """

                execute_query(
                    query,
                    (cita["id"],),
                    commit=True
                )

        except Exception as e:

            print(
                f"[ERROR VENCIMIENTO] "
                f"{e}"
            )