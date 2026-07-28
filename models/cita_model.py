# models/cita_model.py

from db import execute_query


# =========================================================
# CONSULTAR CITAS POR ESTADO
# =========================================================
def get_citas_by_estado(
    predios,
    estado,
    naviera=None
):

    """
    Obtiene citas de un estado específico.

    Siempre limita la consulta a los predios asignados.

    Cuando naviera tiene valor, también restringe las citas
    a esa naviera. Esto se utilizará para usuarios con rol
    NAVIERA.
    """

    query = """
        SELECT
            c.*,
            p.nombre AS predio_nombre
        FROM citas c
        LEFT JOIN predios p
            ON p.id = c.predio_id
        WHERE c.estado = %s
          AND c.predio_id = ANY(%s)
    """

    params = [
        estado,
        predios
    ]

    if naviera:

        query += """
          AND c.naviera = %s
        """

        params.append(
            naviera
        )

    if estado == "Pendiente":

        query += """
        ORDER BY
            c.fecha ASC,
            c.horario ASC,
            c.id ASC
        """

    else:

        query += """
        ORDER BY
            c.fecha DESC,
            c.horario DESC,
            c.id DESC
        """

    return execute_query(
        query,
        tuple(params),
        fetchall=True
    )


# =========================================================
# PENDIENTES
# =========================================================
def get_pending_citas(
    predios,
    naviera=None
):

    return get_citas_by_estado(
        predios=predios,
        estado="Pendiente",
        naviera=naviera
    )


# =========================================================
# COMPLETADAS
# =========================================================
def get_completed_citas(
    predios,
    naviera=None
):

    return get_citas_by_estado(
        predios=predios,
        estado="Completada",
        naviera=naviera
    )


# =========================================================
# VENCIDAS
# =========================================================
def get_expired_citas(
    predios,
    naviera=None
):

    return get_citas_by_estado(
        predios=predios,
        estado="Vencida",
        naviera=naviera
    )


# =========================================================
# CANCELADAS
# =========================================================
def get_cancelled_citas(
    predios,
    naviera=None
):

    return get_citas_by_estado(
        predios=predios,
        estado="Cancelada",
        naviera=naviera
    )


# =========================================================
# OBTENER POR ID
# =========================================================
def get_cita_by_id(
    cita_id,
    predios=None,
    naviera=None
):

    """
    Obtiene una cita por ID.

    predios:
        Cuando se proporciona, limita la cita a los predios
        permitidos del usuario.

    naviera:
        Cuando se proporciona, limita la cita a la naviera
        asociada al usuario.
    """

    query = """
        SELECT
            c.*,
            p.nombre AS predio_nombre
        FROM citas c
        LEFT JOIN predios p
            ON p.id = c.predio_id
        WHERE c.id = %s
    """

    params = [
        cita_id
    ]

    if predios is not None:

        query += """
          AND c.predio_id = ANY(%s)
        """

        params.append(
            predios
        )

    if naviera:

        query += """
          AND c.naviera = %s
        """

        params.append(
            naviera
        )

    query += """
        LIMIT 1
    """

    return execute_query(
        query,
        tuple(params),
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
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            'Pendiente',
            %s,
            %s
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
# ACTUALIZAR
# =========================================================
def update_cita(
    cita_id,
    contenedor,
    chofer_nombre,
    chofer_cedula,
    cabezal_placa,
    fecha,
    horario,
    naviera,
    estado_contenedor,
    tipo_operacion,
    predio_id
):

    query = """
        UPDATE citas
        SET
            contenedor = %s,
            chofer_nombre = %s,
            chofer_cedula = %s,
            cabezal_placa = %s,
            fecha = %s,
            horario = %s,
            naviera = %s,
            estado_contenedor = %s,
            tipo_operacion = %s,
            predio_id = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
          AND estado = 'Pendiente'
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
            cita_id
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
          AND estado = 'Pendiente'
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
# CANCELAR
# =========================================================
def cancel_cita(
    cita_id,
    cancelada_por,
    motivo_cancelacion
):

    """
    Cancela únicamente citas que todavía estén pendientes.

    No elimina la cita físicamente.
    Conserva el historial de quién la canceló, cuándo y por qué.
    """

    query = """
        UPDATE citas
        SET
            estado = 'Cancelada',
            cancelada_por = %s,
            fecha_cancelacion = CURRENT_TIMESTAMP,
            motivo_cancelacion = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
          AND estado = 'Pendiente'
    """

    execute_query(
        query,
        (
            cancelada_por,
            motivo_cancelacion,
            cita_id
        ),
        commit=True
    )


# =========================================================
# MARCAR COMO VENCIDA
# =========================================================
def expire_cita(
    cita_id
):

    query = """
        UPDATE citas
        SET
            estado = 'Vencida',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
          AND estado = 'Pendiente'
    """

    execute_query(
        query,
        (cita_id,),
        commit=True
    )


# =========================================================
# ELIMINAR
# =========================================================
def delete_cita(
    cita_id
):

    """
    Eliminación física.

    Esta función debe quedar restringida desde servicio
    y rutas únicamente para SUPERADMIN.

    Los usuarios NAVIERA no deben eliminar citas:
    solamente cancelarlas.
    """

    query = """
        DELETE FROM citas
        WHERE id = %s
    """

    execute_query(
        query,
        (cita_id,),
        commit=True
    )