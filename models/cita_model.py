# models/cita_model.py

from db import execute_query


# =========================================================
# PENDIENTES
# =========================================================
def get_pending_citas(predios):

    query = """
        SELECT
            c.*,
            p.nombre AS predio_nombre
        FROM citas c
        LEFT JOIN predios p
            ON p.id = c.predio_id
        WHERE c.estado = 'Pendiente'
          AND c.predio_id = ANY(%s)
        ORDER BY
            c.fecha ASC,
            c.horario ASC
    """

    return execute_query(
        query,
        (predios,),
        fetchall=True
    )


# =========================================================
# COMPLETADAS
# =========================================================
def get_completed_citas(predios):

    query = """
        SELECT
            c.*,
            p.nombre AS predio_nombre
        FROM citas c
        LEFT JOIN predios p
            ON p.id = c.predio_id
        WHERE c.estado = 'Completada'
          AND c.predio_id = ANY(%s)
        ORDER BY
            c.fecha DESC,
            c.horario DESC
    """

    return execute_query(
        query,
        (predios,),
        fetchall=True
    )


# =========================================================
# VENCIDAS
# =========================================================
def get_expired_citas(predios):

    query = """
        SELECT
            c.*,
            p.nombre AS predio_nombre
        FROM citas c
        LEFT JOIN predios p
            ON p.id = c.predio_id
        WHERE c.estado = 'Vencida'
          AND c.predio_id = ANY(%s)
        ORDER BY
            c.fecha DESC,
            c.horario DESC
    """

    return execute_query(
        query,
        (predios,),
        fetchall=True
    )


# =========================================================
# OBTENER POR ID
# =========================================================
def get_cita_by_id(cita_id):

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
# CREAR
# =========================================================
def create_cita(
    contenedor,
    chofer_nombre,
    chofer_cedula,
    cabezal_placa,
    fecha,
    horario,
    naviera,
    estado_contenedor,
    tipo_operacion,
    predio_id,
    created_by
):

    query = """
        INSERT INTO citas (
            contenedor,
            chofer_nombre,
            chofer_cedula,
            cabezal_placa,
            fecha,
            horario,
            naviera,
            estado_contenedor,
            tipo_operacion,
            estado,
            predio_id,
            created_by
        )
        VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, 'Pendiente',
            %s, %s
        )
    """

    execute_query(
        query,
        (
            contenedor,
            chofer_nombre,
            chofer_cedula,
            cabezal_placa,
            fecha,
            horario,
            naviera,
            estado_contenedor,
            tipo_operacion,
            predio_id,
            created_by
        ),
        commit=True
    )


# =========================================================
# COMPLETAR
# =========================================================
def complete_cita(
    cita_id,
    contenedor_registrado,
    servicio_terminal,
    confirmado_por
):

    query = """
        UPDATE citas
        SET
            estado = 'Completada',
            contenedor_registrado = %s,
            servicio_terminal = %s,
            confirmado_por = %s,
            fecha_confirmacion = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """

    execute_query(
        query,
        (
            contenedor_registrado,
            servicio_terminal,
            confirmado_por,
            cita_id
        ),
        commit=True
    )


# =========================================================
# ELIMINAR
# =========================================================
def delete_cita(cita_id):

    query = """
        DELETE FROM citas
        WHERE id = %s
    """

    execute_query(
        query,
        (cita_id,),
        commit=True
    )