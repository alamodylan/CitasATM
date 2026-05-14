# services/porton_service.py

from db import execute_query

from models.cita_model import (
    get_cita_by_id
)

from services.cita_service import (
    complete_cita_from_porton
)


# =========================================================
# CITAS PENDIENTES PARA PORTÓN
# =========================================================
def get_pending_citas_for_porton(user_predios):

    query = """
        SELECT
            c.id,
            c.contenedor,
            c.chofer_nombre,
            c.cabezal_placa,
            c.fecha,
            c.horario,
            c.naviera,
            c.tipo_operacion,
            c.estado,
            p.nombre AS predio_nombre
        FROM citas c
        LEFT JOIN predios p
            ON p.id = c.predio_id
        WHERE c.estado = 'Pendiente'
        AND c.predio_id = ANY(%s)
        ORDER BY c.fecha ASC,
                 c.horario ASC
    """

    return execute_query(
        query,
        (user_predios,),
        fetchall=True
    )


# =========================================================
# DETALLE DE CITA PARA GUARDA
# =========================================================
def get_porton_cita_detail(cita_id):

    query = """
        SELECT
            c.*,
            p.nombre AS predio_nombre
        FROM citas c
        LEFT JOIN predios p
            ON p.id = c.predio_id
        WHERE c.id = %s
        LIMIT 1
    """

    return execute_query(
        query,
        (cita_id,),
        fetchone=True
    )


# =========================================================
# CONFIRMAR CITA DESDE PORTÓN
# =========================================================
def confirm_cita_from_porton(
    cita_id,
    contenedor_registrado,
    servicio_terminal,
    user_id
):

    # =====================================================
    # VALIDACIONES
    # =====================================================
    if not contenedor_registrado:

        return {
            "success": False,
            "message": (
                "Debe ingresar "
                "el contenedor."
            )
        }

    if not servicio_terminal:

        return {
            "success": False,
            "message": (
                "Debe ingresar "
                "el servicio terminal."
            )
        }

    cita = get_cita_by_id(cita_id)

    if not cita:

        return {
            "success": False,
            "message": (
                "La cita no existe."
            )
        }

    if cita["estado"] != "Pendiente":

        return {
            "success": False,
            "message": (
                "La cita ya no "
                "está pendiente."
            )
        }

    # =====================================================
    # COMPLETAR CITA
    # =====================================================
    result = complete_cita_from_porton(
        cita_id=cita_id,
        contenedor_registrado=contenedor_registrado,
        servicio_terminal=servicio_terminal,
        confirmado_por=user_id
    )

    return result


# =========================================================
# DASHBOARD OPERATIVO PORTÓN
# =========================================================
def get_porton_stats(user_predios):

    query = """
        SELECT
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

    result = execute_query(
        query,
        (user_predios,),
        fetchone=True
    )

    return result