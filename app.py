import re
from flask import Flask, render_template, request, redirect, url_for, send_file
from datetime import datetime, timedelta
import pytz
import os
from fpdf import FPDF
from openpyxl import Workbook
from flask import send_file
from flask import jsonify, render_template
from io import BytesIO
from openpyxl import Workbook
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

class PDF(FPDF):
    def header(self):
        self.image('static/LogoAlamo.png', 10, 8, 33) 
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Álamo Terminales Marítimos - Detalle de Cita', border=False, ln=True, align='C')
        self.ln(20) 

    def footer(self):
        self.set_y(-30) 
        self.image('static/BASC.png', 10, self.get_y(), 33)  
        self.set_y(-25)  
        self.set_font('Arial', 'I', 8)
        self.multi_cell(0, 5, "Terminales - Transporte - Reparación - Certificado # CRSJO001581-1", align='C')
        self.set_y(-15)  
        self.cell(0, 10, f'Página {self.page_no()}', align='C')

def get_db_connection():
    DATABASE_URL = "postgresql://citasatm_user:SlwK1sFIPJal7m8KaDtlRlYu1NseKxnV@dpg-ctdis2jv2p9s73ai7op0-a.oregon-postgres.render.com/citasatm_db"
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS citas (
            id SERIAL PRIMARY KEY,
            contenedor TEXT NOT NULL,
            chofer_nombre TEXT NOT NULL,
            chofer_cedula TEXT NOT NULL,
            cabezal_placa TEXT NOT NULL,
            fecha TEXT NOT NULL,
            horario TEXT NOT NULL,
            naviera TEXT NOT NULL,
            estado_contenedor TEXT NOT NULL,
            tipo_operacion TEXT NOT NULL,
            estado TEXT DEFAULT 'Pendiente'
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

@app.route("/")
def home():
    zona_local = pytz.timezone('America/Costa_Rica')
    now = datetime.now(zona_local)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM citas WHERE estado = 'Pendiente'")
    pendientes = cursor.fetchall()

    for cita in pendientes:
        cita_date = cita["fecha"]
        cita_end_time = cita["horario"].split("-")[1]
        cita_end_datetime = datetime.strptime(f"{cita_date} {cita_end_time}", "%Y-%m-%d %H:%M")
        cita_end_datetime = zona_local.localize(cita_end_datetime)

        if cita_end_datetime + timedelta(hours=1) < now and cita["estado"] == "Pendiente":
            cursor.execute("UPDATE citas SET estado = 'Vencida' WHERE id = %s", (cita["id"],))

    conn.commit()
    cursor.close()
    conn.close()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM citas WHERE estado = 'Pendiente'")
    pendientes = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("index.html", citas=pendientes)

@app.route("/vencidas")
def vencidas():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM citas WHERE estado = 'Vencida'")
    vencidas = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("vencidas.html", citas=vencidas)

@app.route("/completadas")
def completadas():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM citas WHERE estado = 'Completada'")
    completadas = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("completadas.html", citas=completadas)

@app.route("/crear-cita", methods=["GET", "POST"])
def crear_cita():
    if request.method == "POST":
        contenedor = request.form["contenedor"]
        chofer_nombre = request.form["chofer_nombre"]
        chofer_cedula = request.form["chofer_cedula"]
        cabezal_placa = request.form["cabezal_placa"]
        fecha = request.form["fecha"]
        horario = request.form["horario"]
        naviera = request.form["naviera"]
        estado_contenedor = request.form["estado_contenedor"]
        tipo_operacion = request.form["tipo_operacion"]

        if not re.match(r"^[A-Z]{4}[0-9]{7}$", contenedor):
            return render_template("crear_cita.html", error="El contenedor debe contener 4 letras seguidas de 7 números (ejemplo: ABCD1234567)")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM citas WHERE fecha = %s AND horario = %s", (fecha, horario))
        total_citas = cursor.fetchone()["total"]

        if total_citas >= 5:
            cursor.close()
            conn.close()
            return render_template("crear_cita.html", error=f"El intervalo {horario} ya tiene el máximo de 5 citas.")

        cursor.execute(
            """
            INSERT INTO citas (contenedor, chofer_nombre, chofer_cedula, cabezal_placa, fecha, horario, naviera, estado_contenedor, tipo_operacion)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (contenedor, chofer_nombre, chofer_cedula, cabezal_placa, fecha, horario, naviera, estado_contenedor, tipo_operacion)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for("home"))

    current_date = datetime.now().strftime("%Y-%m-%d")
    time_slots = []
    for hour in range(8, 17):
        time_slots.extend([
            f"{hour:02d}:00-{hour:02d}:15",
            f"{hour:02d}:15-{hour:02d}:30",
            f"{hour:02d}:30-{hour:02d}:45",
            f"{hour:02d}:45-{(hour + 1):02d}:00"
        ])

    return render_template("crear_cita.html", time_slots=time_slots, current_date=current_date)

if __name__ == "__main__":
    init_db()

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)




