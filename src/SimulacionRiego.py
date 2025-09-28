from .ListaSimpleEnlazada import ListaEnlazada
import xml.etree.ElementTree as ET
from flask import render_template
from io import BytesIO

class SimulacionRiego:
    def __init__(self, plan_riego, invernadero):
        self.plan_riego = plan_riego.secuencia_ubicacion_riego
        self.matriz_plantas = invernadero.matriz_plantas
        self.lista_drones_asignados = invernadero.lista_drones_asignados
        self.lista_plantas_a_regar = ListaEnlazada()
        self.linea_tiempo = []

    def inicializar_datos_drones(self):
        actual_dron_asignado = self.lista_drones_asignados.primero
        while actual_dron_asignado:
            dron = actual_dron_asignado.dato
            dron.reiniciar_datos()
            actual_dron_asignado = actual_dron_asignado.siguiente

    def crear_lista_plantas_a_regar(self):
        ubicaciones_riego = self.plan_riego.split(',')
        for ubicacion_riego in ubicaciones_riego:
            ubicacion_riego = ubicacion_riego.strip()
            if ubicacion_riego:
                partes = ubicacion_riego.split('-')
                hilera = int(partes[0][1:])
                posicion = int(partes[1][1:])
                self.lista_plantas_a_regar.insertar(self.matriz_plantas.obtener(hilera, posicion))

    def asignar_plantas_a_regar_a_dron(self):
        actual_planta = self.lista_plantas_a_regar.primero
        while actual_planta:
            planta = actual_planta.dato
            actual_dron = self.lista_drones_asignados.primero
            while actual_dron:
                dron = actual_dron.dato
                if planta.hilera == dron.hilera_asignada:
                    dron.plantas_a_regar.encolar(planta)
                actual_dron = actual_dron.siguiente
            actual_planta = actual_planta.siguiente

    def simular(self):
        actual_planta_a_regar = self.lista_plantas_a_regar.primero
        self.segundo_actual = 1  #Contador global de tiempo

        while actual_planta_a_regar:
            planta_a_regar = actual_planta_a_regar.dato
            planta_no_regada = True

            while planta_no_regada:
                actual_dron_asignado = self.lista_drones_asignados.primero
                eventos_segundo = []  #Acciones de todos los drones en este segundo

                while actual_dron_asignado:
                    dron = actual_dron_asignado.dato
                    posicion_actual = dron.posicion_actual
                    
                    if dron.posicion_objetivo == None:
                        planta = dron.plantas_a_regar.desencolar()
                        if planta:
                            dron.posicion_objetivo = planta.posicion
                            posicion_objetivo = dron.posicion_objetivo
                        else:
                            posicion_objetivo = None
                    else:
                        posicion_objetivo = dron.posicion_objetivo

                    if posicion_objetivo != None:
                        #Mover adelante
                        if posicion_actual < posicion_objetivo:
                            paso = dron.mover_adelante()
                            dron.pasos.insertar(paso)
                            eventos_segundo.append({"dron": dron.nombre, "accion": paso})
                        #Mover atras
                        elif posicion_actual > posicion_objetivo:
                            paso = dron.mover_atras()
                            dron.pasos.insertar(paso)
                            eventos_segundo.append({"dron": dron.nombre, "accion": paso})
                        #Esperar
                        elif posicion_actual == posicion_objetivo and planta_a_regar.hilera != dron.hilera_asignada:
                            paso = dron.esperar()
                            dron.pasos.insertar(paso)
                            eventos_segundo.append({"dron": dron.nombre, "accion": paso})
                        #Regar
                        elif posicion_actual == posicion_objetivo and planta_a_regar.hilera == dron.hilera_asignada:
                            paso = dron.regar(planta_a_regar)
                            dron.pasos.insertar(paso)
                            eventos_segundo.append({"dron": dron.nombre, "accion": paso})
                            planta_no_regada = False
                            dron.posicion_objetivo = None
                    else:
                        planta_no_regada = False

                    actual_dron_asignado = actual_dron_asignado.siguiente

                # Guardamos todos los eventos ocurridos en este segundo
                if eventos_segundo:
                    self.linea_tiempo.append({
                        "segundo": self.segundo_actual,
                        "eventos": eventos_segundo
                    })

                self.segundo_actual += 1  # Avanza el tiempo

            actual_planta_a_regar = actual_planta_a_regar.siguiente

    def imprimir_pasos(self):
        actual_dron = self.lista_drones_asignados.primero
        while actual_dron:
            dron = actual_dron.dato
            print("Dron: ", dron.nombre)
            actual_paso = dron.pasos.primero
            while actual_paso:
                paso = actual_paso.dato
                print(paso)
                actual_paso = actual_paso.siguiente
            actual_dron = actual_dron.siguiente

    def generar_xml_salida(self, nombre_invernadero, nombre_plan, ruta_salida):
        root = ET.Element("datosSalida")
        lista_invernaderos_elem = ET.SubElement(root, "listaInvernaderos")

        invernadero_elem = ET.SubElement(lista_invernaderos_elem, "invernadero", {"nombre": nombre_invernadero})
        lista_planes_elem = ET.SubElement(invernadero_elem, "listaPlanes")

        plan_elem = ET.SubElement(lista_planes_elem, "plan", {"nombre": nombre_plan})

        # Calcular métricas globales
        tiempo_total = max((tick["segundo"] for tick in self.linea_tiempo), default=0)
        agua_total = 0
        fertilizante_total = 0

        actual_dron = self.lista_drones_asignados.primero
        while actual_dron:
            dron = actual_dron.dato
            agua_total += dron.litros_agua_usados
            fertilizante_total += dron.gramos_fertilizante_usados
            actual_dron = actual_dron.siguiente

        # Insertar métricas
        ET.SubElement(plan_elem, "tiempoOptimoSegundos").text = str(tiempo_total)
        ET.SubElement(plan_elem, "aguaRequeridaLitros").text = str(agua_total)
        ET.SubElement(plan_elem, "fertilizanteRequeridoGramos").text = str(fertilizante_total)

        eficiencia_elem = ET.SubElement(plan_elem, "eficienciaDronesRegadores")
        actual_dron = self.lista_drones_asignados.primero
        while actual_dron:
            dron = actual_dron.dato
            ET.SubElement(eficiencia_elem, "dron", {
                "nombre": dron.nombre,
                "litrosAgua": str(dron.litros_agua_usados),
                "gramosFertilizante": str(dron.gramos_fertilizante_usados)
            })
            actual_dron = actual_dron.siguiente

        instrucciones_elem = ET.SubElement(plan_elem, "instrucciones")
        for tick in self.linea_tiempo:
            tiempo_elem = ET.SubElement(instrucciones_elem, "tiempo", {"segundos": str(tick["segundo"])})
            for evento in tick["eventos"]:
                ET.SubElement(tiempo_elem, "dron", {
                    "nombre": evento["dron"],
                    "accion": evento["accion"]
                })

        tree = ET.ElementTree(root)
        tree.write(ruta_salida, encoding="utf-8", xml_declaration=True)

    def generar_html_reporte(self, nombre_invernadero, nombre_plan, ruta_salida):
        #métricas globales
        tiempo_total = max((tick["segundo"] for tick in self.linea_tiempo), default=0)
        agua_total = 0
        fertilizante_total = 0

        drones = []
        actual_dron = self.lista_drones_asignados.primero
        while actual_dron:
            dron = actual_dron.dato
            agua_total += dron.litros_agua_usados
            fertilizante_total += dron.gramos_fertilizante_usados

            pasos = []
            actual_paso = dron.pasos.primero
            while actual_paso:
                pasos.append(actual_paso.dato)
                actual_paso = actual_paso.siguiente

            drones.append({
                "nombre": dron.nombre,
                "hilera_asignada": dron.hilera_asignada,
                "agua_usada": dron.litros_agua_usados,
                "fertilizante_usado": dron.gramos_fertilizante_usados,
                "pasos": pasos
            })

            actual_dron = actual_dron.siguiente

        dron_nombres = [d["nombre"] for d in drones]

        #Post-procesar linea_tiempo para insertar FIN
        #Guardamos el último segundo en que actuó cada dron
        ultimo_evento = {d: 0 for d in dron_nombres}
        for tick in self.linea_tiempo:
            for evento in tick["eventos"]:
                ultimo_evento[evento["dron"]] = tick["segundo"]

        #Ahora creamos un mapa de segundo en que debe aparecer FIN
        fin_por_dron = {d: ultimo_evento[d] + 1 for d in dron_nombres}

        #Recorremos los segundos hasta el maximo + 1 y construimos nueva linea
        nueva_linea_tiempo = []
        for s in range(1, tiempo_total + 2):  # +1 para permitir los FIN
            tick = {"segundo": s, "eventos": []}
            # Copiamos eventos normales
            for e in [e for t in self.linea_tiempo if t["segundo"] == s for e in t["eventos"]]:
                tick["eventos"].append(e)
            # Agregamos FIN si corresponde
            for d in dron_nombres:
                if s == fin_por_dron[d]:
                    tick["eventos"].append({"dron": d, "accion": "FIN"})
            # Guardamos solo si hay eventos
            if tick["eventos"]:
                nueva_linea_tiempo.append(tick)

        self.linea_tiempo = nueva_linea_tiempo

        #render del HTML con Jinja
        contenido = render_template(
            "reporte.html",
            invernadero_nombre=nombre_invernadero,
            plan_nombre=nombre_plan,
            tiempo_total=tiempo_total,
            agua_total=agua_total,
            fertilizante_total=fertilizante_total,
            drones=drones,
            dron_nombres=dron_nombres,
            linea_tiempo=self.linea_tiempo
        )

        with open(ruta_salida, "w", encoding="utf-8") as f:
            f.write(contenido)

        print(f"Reporte HTML generado en: {ruta_salida}")