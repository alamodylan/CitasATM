import sqlite3
import os

def modificar_base_de_datos():
    db_folder = "database"
    db_path = os.path.join(db_folder, "citas.db")

    # Verifica si la base de datos existe
    if not os.path.exists(db_path):
        print("La base de datos no existe. Por favor, asegúrate de haberla creado.")
        return

    # Conecta a la base de datos
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Verifica si el campo 'fecha' existe en la tabla 'citas'
    cursor.execute("PRAGMA table_info(citas);")
    columns = [column[1] for column in cursor.fetchall()]

    if "fecha" not in columns:
        print("Agregando columna 'fecha'...")
        cursor.execute("ALTER TABLE citas ADD COLUMN fecha TEXT NOT NULL DEFAULT '2000-01-01';")

    if "llegada_tardia" not in columns:
        print("Agregando columna 'llegada_tardia'...")
        cursor.execute("ALTER TABLE citas ADD COLUMN llegada_tardia TEXT;")

    # Verifica si las filas existentes tienen valores válidos en 'fecha'
    cursor.execute("SELECT id, fecha FROM citas;")
    citas = cursor.fetchall()

    for cita in citas:
        id_cita, fecha = cita
        if fecha == "2000-01-01":
            print(f"Actualizando fecha para la cita ID {id_cita}...")
            cursor.execute("UPDATE citas SET fecha = ? WHERE id = ?;", ("2024-12-05", id_cita))

    # Confirma los cambios
    conn.commit()
    conn.close()
    print("Base de datos modificada con éxito.")

if __name__ == "__main__":
    modificar_base_de_datos()
