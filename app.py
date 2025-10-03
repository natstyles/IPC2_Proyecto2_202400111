import os
from flask import Flask, render_template, request, send_from_directory, redirect, url_for
from src.Sistema import Sistema
from src.SimulacionRiego import SimulacionRiego

# Configuración base
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"

# Asegurar carpetas necesarias
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Variables globales
ultima_simulacion = None
ultimo_invernadero = None
ultimo_plan = None
ultimo_plan_numero = None
sistema_global = None  # Guardamos el sistema cargado para reutilizarlo

def obtener_drones_lista(lista_drones):
    """Convierte lista enlazada de drones a lista normal (para mostrar en template)."""
    drones = []
    actual = lista_drones.primero
    while actual:
        drones.append(actual.dato)
        actual = actual.siguiente
    return drones

def obtener_pasos_lista(lista_pasos):
    """Convierte lista enlazada de pasos a lista normal (para mostrar en template)."""
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

@app.route("/simulacion", methods=["POST"])
def simulacion():
    global ultima_simulacion, ultimo_invernadero, ultimo_plan, ultimo_plan_numero, sistema_global

    invernadero_id = int(request.form["invernadero"])
    numero_plan = int(request.form["plan"])

    if not sistema_global:
        return render_template("error.html", titulo="Error", mensaje="Primero carga un archivo XML.")

    print("Iniciando simulación")

    # Obtenemos el invernadero y plan seleccionados
    invernadero = sistema_global.obtener_invernadero(invernadero_id)
    print(f"Invernadero seleccionado: {invernadero.nombre}")

    plan = sistema_global.obtener_plan_riego(numero_plan, invernadero)
    print(f"Plan seleccionado: {plan.nombre}")

    # Ejecutamos simulación
    simulacion = SimulacionRiego(plan, invernadero)

    print("Inicializando datos de drones")
    simulacion.inicializar_datos_drones()

    print("Creando lista de plantas a regar")
    simulacion.crear_lista_plantas_a_regar()

    print("Asignando plantas a drones")
    simulacion.asignar_plantas_a_regar_a_dron()

    print("Iniciando simulación...")
    simulacion.simular()
    print("Simulación terminada")

    # Guardar referencias globales
    ultima_simulacion = simulacion
    ultimo_invernadero = invernadero
    ultimo_plan = plan
    ultimo_plan_numero = numero_plan

    # Generar reporte HTML
    reporte_nombre = f"Reporte_plan{numero_plan}.html"
    ruta_reporte = os.path.join(app.config["UPLOAD_FOLDER"], reporte_nombre)
    print("Generando reporte HTML...")
    simulacion.generar_html_reporte(invernadero.nombre, plan.nombre, ruta_reporte)
    print("Reporte generado:", ruta_reporte)

    # Preparamos datos de drones
    drones = []
    for dron in obtener_drones_lista(invernadero.lista_drones_asignados):
        drones.append({
            "nombre": dron.nombre,
            "hilera_asignada": dron.hilera_asignada,
            "agua_usada": dron.litros_agua_usados,
            "fertilizante_usado": dron.gramos_fertilizante_usados,
            "pasos": obtener_pasos_lista(dron.pasos)
        })

    # Tiempo total de la simulación
    tiempo_total = max((t["segundo"] for t in simulacion.linea_tiempo), default=0)

    print("Renderizando resultado en HTML")
    return render_template(
        "resultado.html",
        titulo="Resultado de Simulación",
        invernadero=invernadero,
        plan_nombre=plan.nombre,
        tiempo_total=tiempo_total,
        reporte=reporte_nombre,
        drones=drones,
        plan_numero=numero_plan
    )

@app.route("/cargar_archivo", methods=["GET", "POST"])
def cargar_archivo():
    global sistema_global

    if request.method == "POST":
        archivo = request.files.get("archivo")
        if not archivo or archivo.filename == "":
            return render_template("error.html", titulo="Error", mensaje="No se seleccionó archivo")

        # Guardar archivo subido
        ruta_archivo = os.path.join(app.config["UPLOAD_FOLDER"], archivo.filename)
        archivo.save(ruta_archivo)

        # Procesar archivo con el Sistema
        sistema = Sistema()
        sistema.leer_archivo(ruta_archivo)
        sistema_global = sistema

    #Si no hay sistema cargado aún
    if not sistema_global:
        return redirect(url_for("inicio"))

    # Convertir a estructura serializable para el template
    invernaderos_data = []
    inv_id = 1
    actual_inv = sistema_global.lista_invernaderos.primero
    while actual_inv:
        inv = actual_inv.dato

        planes_js = []
        plan_id = 1
        actual_plan = inv.lista_planes_riego.primero
        while actual_plan:
            plan = actual_plan.dato
            planes_js.append({"id": plan_id, "nombre": plan.nombre})
            plan_id += 1
            actual_plan = actual_plan.siguiente

        invernaderos_data.append({
            "id": inv_id,
            "nombre": inv.nombre,
            "planes": planes_js
        })

        inv_id += 1
        actual_inv = actual_inv.siguiente

    print("Invernaderos cargados:", invernaderos_data)  # Debug

    return render_template("simulacion.html", titulo="Nueva Simulación", invernaderos=invernaderos_data)

#Rutas de archivo
@app.route("/uploads/<path:filename>")
def ver_archivo(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/descargar/<path:filename>")
def descargar_archivo(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

@app.route("/descargar_xml")
def descargar_xml():
    if ultima_simulacion and ultimo_invernadero and ultimo_plan:
        return ultima_simulacion.generar_xml_salida(ultimo_invernadero.nombre, ultimo_plan.nombre)
    else:
        return render_template("error.html", titulo="Error", mensaje="No hay simulación disponible para exportar.")

#Reportes TDA
@app.route("/tda/<int:numero_plan>")
def reporte_tda(numero_plan):
    global ultima_simulacion

    if not ultima_simulacion:
        return render_template("error.html", titulo="Error", mensaje="No hay simulación cargada.")

    ruta_img = ultima_simulacion.generar_reporte_tda(f"tda_plan{numero_plan}.png")
    return render_template(
        "reporte_tda.html",
        imagen=os.path.basename(ruta_img),
        plan_numero=numero_plan,
        tiempo=0
    )

@app.route("/tda/<int:numero_plan>/tiempo", methods=["POST"])
def reporte_tda_tiempo(numero_plan):
    global ultima_simulacion, ultimo_invernadero, ultimo_plan

    if not ultima_simulacion or not ultimo_invernadero or not ultimo_plan:
        return render_template("error.html", titulo="Error", mensaje="No hay simulación cargada.")

    tiempo = int(request.form.get("tiempo", 0))
    ruta_img = ultima_simulacion.generar_reporte_tda(f"tda_plan{numero_plan}_t{tiempo}.png", tiempo)

    return render_template(
        "reporte_tda.html",
        imagen=os.path.basename(ruta_img),
        plan_numero=numero_plan,
        tiempo=tiempo
    )


#Otras rutas

@app.route("/ayuda")
def ayuda():
    return render_template("ayuda.html", titulo="Ayuda")


@app.route("/descargar_xml_global")
def descargar_xml_global():
    global sistema_global
    if not sistema_global:
        return render_template("error.html", titulo="Error", mensaje="No hay archivo cargado.")
    return sistema_global.generar_xml_global()


#Ejecutar servidor
if __name__ == "__main__":
    app.run(debug=True)
