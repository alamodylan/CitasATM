import sqlite3

def init_db():
    conn = sqlite3.connect("citas.db")
    cursor = conn.cursor()
    
    # Crear la tabla si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS citas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contenedor TEXT NOT NULL,
            chofer_nombre TEXT NOT NULL,
            chofer_cedula TEXT NOT NULL,
            cabezal_placa TEXT NOT NULL,
            horario TEXT NOT NULL,
            estado_contenedor TEXT NOT NULL DEFAULT 'Vacío',
            tipo_operacion TEXT NOT NULL DEFAULT 'Entrega',
            fecha TEXT NOT NULL DEFAULT '',
            estado TEXT NOT NULL DEFAULT 'Pendiente',
            anotaciones TEXT DEFAULT NULL,
            naviera TEXT NOT NULL CHECK (naviera IN ('COSCO', 'OOCL', 'ONE'))
        )
    """)
    
    # Verificar las columnas existentes y agregar las faltantes
    cursor.execute("PRAGMA table_info(citas)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "estado_contenedor" not in columns:
        cursor.execute("ALTER TABLE citas ADD COLUMN estado_contenedor TEXT NOT NULL DEFAULT 'Vacío'")
    
    if "tipo_operacion" not in columns:
        cursor.execute("ALTER TABLE citas ADD COLUMN tipo_operacion TEXT NOT NULL DEFAULT 'Entrega'")
    
    if "fecha" not in columns:
        cursor.execute("ALTER TABLE citas ADD COLUMN fecha TEXT NOT NULL DEFAULT ''")
    
    if "estado" not in columns:
        cursor.execute("ALTER TABLE citas ADD COLUMN estado TEXT NOT NULL DEFAULT 'Pendiente'")
    
    if "anotaciones" not in columns:
        cursor.execute("ALTER TABLE citas ADD COLUMN anotaciones TEXT DEFAULT NULL")

    if "naviera" not in columns:
        cursor.execute("""
            ALTER TABLE citas ADD COLUMN naviera TEXT NOT NULL DEFAULT 'COSCO'
        """)
        # Cambiar el valor por defecto para las filas existentes si no es válido
        cursor.execute("""
            UPDATE citas SET naviera = 'COSCO' WHERE naviera NOT IN ('COSCO', 'OOCL', 'ONE') OR naviera IS NULL
        """)
        conn.commit()
    
    conn.close()
    print("Base de datos inicializada correctamente.")

# Inicializar la base de datos
init_db()