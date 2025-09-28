import os
from flask import Flask, render_template, request, send_from_directory
from src.Sistema import Sistema
from src.SimulacionRiego import SimulacionRiego

#Configuración base
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"

#Asegurar carpetas necesarias
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

def obtener_drones_lista(lista_drones):
    """Convierte lista enlazada de drones a lista normal"""
    drones = []
    actual = lista_drones.primero
    while actual:
        drones.append(actual.dato)
        actual = actual.siguiente
    return drones

def obtener_pasos_lista(lista_pasos):
    """Convierte lista enlazada de pasos a lista normal"""
    pasos = []
    actual = lista_pasos.primero
    while actual:
        pasos.append(actual.dato)
        actual = actual.siguiente
    return pasos

#Rutas principales
@app.route("/")
def inicio():
    return render_template("inicio.html", titulo="Página de inicio")


@app.route("/simulacion", methods=["GET", "POST"])
def simulacion():
    if request.method == "POST":
        archivo = request.files["archivo"]
        numero_plan = int(request.form["plan"])  #Capturamos el plan elegido (1 o 2 por ahora)

        if archivo.filename == "":
            return render_template("error.html", titulo="Error", mensaje="No se seleccionó archivo")

        #Guardamos el archivo subido
        ruta_archivo = os.path.join(app.config["UPLOAD_FOLDER"], archivo.filename)
        archivo.save(ruta_archivo)

        #Procesar archivo
        sistema = Sistema()
        sistema.leer_archivo(ruta_archivo)

        #De momento tomamos el primer invernadero
        invernadero = sistema.obtener_invernadero(1)

        #Obtenemos el plan seleccionado
        plan = sistema.obtener_plan_riego(numero_plan, invernadero)

        #Ejecutamos simulación
        simulacion = SimulacionRiego(plan, invernadero)
        simulacion.inicializar_datos_drones()
        simulacion.crear_lista_plantas_a_regar()
        simulacion.asignar_plantas_a_regar_a_dron()
        simulacion.simular()

        #Guardamos archivo de salida
        salida_nombre = f"salida_plan{numero_plan}.xml"
        ruta_salida = os.path.join(app.config["UPLOAD_FOLDER"], salida_nombre)
        simulacion.generar_xml_salida(invernadero.nombre, plan.nombre, ruta_salida)

        #Generar reporte HTML
        reporte_nombre = f"Reporte_plan{numero_plan}.html"
        ruta_reporte = os.path.join(app.config["UPLOAD_FOLDER"], reporte_nombre)
        simulacion.generar_html_reporte(invernadero.nombre, plan.nombre, ruta_reporte)

        #Preparamos los datos de drones para renderizar
        drones = []
        for dron in obtener_drones_lista(invernadero.lista_drones_asignados):
            drones.append({
                "nombre": dron.nombre,
                "hilera_asignada": dron.hilera_asignada,
                "agua_usada": dron.litros_agua_usados,
                "fertilizante_usado": dron.gramos_fertilizante_usados,
                "pasos": obtener_pasos_lista(dron.pasos)
            })

        return render_template(
            "resultado.html",
            titulo="Resultado de Simulación",
            invernadero=invernadero,
            plan_nombre=plan.nombre,
            tiempo_total = simulacion.segundo_actual - 1,
            salida=salida_nombre,
            reporte = reporte_nombre,
            drones=drones
        )

    #Si es GET → mostrar formulario
    return render_template("simulacion.html", titulo="Nueva Simulación")

@app.route("/uploads/<path:filename>")
def ver_archivo(filename):
    """Muestra el archivo directamente en el navegador (ej: HTML, XML crudo)"""
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/descargar/<path:filename>")
def descargar_archivo(filename):
    """Fuerza descarga del archivo (ej: XML)"""
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

#Ejecutar servidor

if __name__ == "__main__":
    app.run(debug=True)