from .ListaSimpleEnlazada import ListaEnlazada
import xml.etree.ElementTree as ET

class SimulacionRiego:
    def __init__(self, plan_riego, invernadero):
        self.plan_riego = plan_riego.secuencia_ubicacion_riego
        self.matriz_plantas = invernadero.matriz_plantas
        self.lista_drones_asignados = invernadero.lista_drones_asignados
        self.lista_plantas_a_regar = ListaEnlazada()

        # Nueva estructura: línea de tiempo global
        self.linea_tiempo = []  # Lista de dicts: {"segundo": n, "eventos": [...]}

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
        self.segundo_actual = 1  # Contador global de tiempo

        while actual_planta_a_regar:
            planta_a_regar = actual_planta_a_regar.dato
            planta_no_regada = True

            while planta_no_regada:
                actual_dron_asignado = self.lista_drones_asignados.primero
                eventos_segundo = []  # Acciones de todos los drones en este segundo

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