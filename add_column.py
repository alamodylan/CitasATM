import psycopg2

DATABASE_URL = "postgresql://citasatm_user:SlwK1sFIPJal7m8KaDtlRlYu1NseKxnV@dpg-ctdis2jv2p9s73ai7op0-a.oregon-postgres.render.com/citasatm_db"

def add_anotaciones_column():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Añadir la columna 'anotaciones' si no existe
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name='citas' AND column_name='anotaciones'
                ) THEN
                    ALTER TABLE citas ADD COLUMN anotaciones TEXT;
                END IF;
            END
            $$;
        """)
        conn.commit()
        print("Columna 'anotaciones' añadida correctamente.")
    except Exception as e:
        print(f"Error al añadir la columna: {e}")
    finally:
        cursor.close()
        conn.close()

# Ejecutar el script
add_anotaciones_column()