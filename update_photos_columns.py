import psycopg2

DATABASE_URL = "postgresql://citasatm_user:SlwK1sFIPJal7m8KaDtlRlYu1NseKxnV@dpg-ctdis2jv2p9s73ai7op0-a.oregon-postgres.render.com/citasatm_db"

try:
    # Conectar a la base de datos
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Agregar columnas para almacenar las rutas de las fotos
    cursor.execute("""
        ALTER TABLE citas
        ADD COLUMN IF NOT EXISTS foto1 TEXT,
        ADD COLUMN IF NOT EXISTS foto2 TEXT,
        ADD COLUMN IF NOT EXISTS foto3 TEXT;
    """)
    conn.commit()

    print("Las columnas para las fotos se han agregado exitosamente.")
except Exception as e:
    print(f"Error al modificar la tabla: {e}")
finally:
    if conn:
        cursor.close()
        conn.close()