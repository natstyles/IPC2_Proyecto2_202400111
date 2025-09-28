from xml.dom.minidom import Document
from ListaSimpleEnlazada import ListaEnlazada

class SimulacionRiego:
    def __init__(self, plan_riego, invernadero):
        self.plan_riego = plan_riego.secuencia_ubicacion_riego
        self.matriz_plantas = invernadero.matriz_plantas
        self.lista_drones_asignados = invernadero.lista_drones_asignados
        self.lista_plantas_a_regar = ListaEnlazada()
        self.tiempo_total = 0  # ⏱ Contador de tiempo en segundos

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
                dron =  actual_dron.dato
                if planta.hilera == dron.hilera_asignada:
                    dron.plantas_a_regar.encolar(planta)
                actual_dron = actual_dron.siguiente
            actual_planta = actual_planta.siguiente

    def simular(self):
        actual_planta_a_regar = self.lista_plantas_a_regar.primero

        while actual_planta_a_regar:
            planta_a_regar = actual_planta_a_regar.dato
            planta_no_regada = True

            while planta_no_regada:
                actual_dron_asignado = self.lista_drones_asignados.primero

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
                        #Mover atras
                        elif posicion_actual > posicion_objetivo:
                            paso = dron.mover_atras()
                            dron.pasos.insertar(paso)
                        #Esperar
                        elif posicion_actual == posicion_objetivo and planta_a_regar.hilera != dron.hilera_asignada:
                            paso = dron.esperar()
                            dron.pasos.insertar(paso)
                        #Regar
                        elif posicion_actual == posicion_objetivo and planta_a_regar.hilera == dron.hilera_asignada:
                            paso = dron.regar(planta_a_regar)
                            dron.pasos.insertar(paso)
                            planta_no_regada = False
                            dron.posicion_objetivo = None
                    else:
                        planta_no_regada = False

                    actual_dron_asignado = actual_dron_asignado.siguiente

                # Cada ciclo de intento de riego cuenta como 1 segundo
                self.tiempo_total += 1

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

    def imprimir_resumen(self):
        print("\n===== Resumen de la Simulación =====")
        print(f"Tiempo óptimo: {self.tiempo_total} segundos")

        total_agua = 0
        total_fertilizante = 0

        actual_dron = self.lista_drones_asignados.primero
        while actual_dron:
            dron = actual_dron.dato
            print(f"Dron {dron.nombre} → Agua usada: {dron.litros_agua_usados} L, Fertilizante usado: {dron.gramos_fertilizante_usados} g")
            total_agua += dron.litros_agua_usados
            total_fertilizante += dron.gramos_fertilizante_usados
            actual_dron = actual_dron.siguiente

        print(f"TOTAL Agua: {total_agua} L")
        print(f"TOTAL Fertilizante: {total_fertilizante} g")
        print("=====================================")

    def generar_xml_salida(self, nombre_invernadero, nombre_plan, ruta_salida="salida.xml"):
        doc = Document()

        # Nodo raíz
        datos_salida = doc.createElement("datosSalida")
        doc.appendChild(datos_salida)

        # Nodo invernadero
        invernadero_node = doc.createElement("invernadero")
        invernadero_node.setAttribute("nombre", nombre_invernadero)
        datos_salida.appendChild(invernadero_node)

        # Nodo plan
        plan_node = doc.createElement("plan")
        plan_node.setAttribute("nombre", nombre_plan)
        invernadero_node.appendChild(plan_node)

        # Tiempo total
        tiempo_node = doc.createElement("tiempoTotal")
        tiempo_node.appendChild(doc.createTextNode(str(self.tiempo_total)))
        plan_node.appendChild(tiempo_node)

        # Totales globales
        total_agua = 0
        total_fertilizante = 0

        # Nodo drones
        drones_node = doc.createElement("drones")
        plan_node.appendChild(drones_node)

        actual_dron = self.lista_drones_asignados.primero
        while actual_dron:
            dron = actual_dron.dato
            total_agua += dron.litros_agua_usados
            total_fertilizante += dron.gramos_fertilizante_usados

            dron_node = doc.createElement("dron")
            dron_node.setAttribute("nombre", dron.nombre)
            dron_node.setAttribute("agua", str(dron.litros_agua_usados))
            dron_node.setAttribute("fertilizante", str(dron.gramos_fertilizante_usados))
            drones_node.appendChild(dron_node)

            actual_dron = actual_dron.siguiente

        # Agua total
        agua_node = doc.createElement("aguaTotal")
        agua_node.appendChild(doc.createTextNode(str(total_agua)))
        plan_node.appendChild(agua_node)

        # Fertilizante total
        ferti_node = doc.createElement("fertilizanteTotal")
        ferti_node.appendChild(doc.createTextNode(str(total_fertilizante)))
        plan_node.appendChild(ferti_node)

        # Instrucciones por tiempo
        instrucciones_node = doc.createElement("instrucciones")
        plan_node.appendChild(instrucciones_node)

        tiempo = 1
        actual_dron = self.lista_drones_asignados.primero
        while actual_dron:
            dron = actual_dron.dato
            actual_paso = dron.pasos.primero
            while actual_paso:
                paso = actual_paso.dato
                paso_node = doc.createElement("paso")
                paso_node.setAttribute("tiempo", str(tiempo))
                paso_node.appendChild(doc.createTextNode(f"{dron.nombre} {paso}"))
                instrucciones_node.appendChild(paso_node)
                actual_paso = actual_paso.siguiente
                tiempo += 1
            actual_dron = actual_dron.siguiente

        # Guardar en archivo
        with open(ruta_salida, "w", encoding="utf-8") as f:
            f.write(doc.toprettyxml(indent="  "))

        print(f"✅ Archivo XML generado en: {ruta_salida}")