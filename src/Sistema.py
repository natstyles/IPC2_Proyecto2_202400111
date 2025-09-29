from xml.dom.minidom import parse
from .Cola import Cola
from .ListaSimpleEnlazada import ListaEnlazada
from .Dron import Dron
from .Planta import Planta
from .PlanRiego import PlanRiego
from .Invernadero import Invernadero
from flask import Response
import xml.etree.cElementTree as ET

class Sistema:
    def __init__(self):
        self.lista_invernaderos = ListaEnlazada()

    def leer_archivo(self, ruta_archivo):
        dom = parse(ruta_archivo)

        #DRONES
        lista_drones = ListaEnlazada()
        drones = dom.getElementsByTagName('dron')
        for dron in drones:
            id = int(dron.getAttribute('id'))
            nombre = dron.getAttribute('nombre')
            nuevo_dron = Dron(id, nombre, None, 0, None, 0, 0, Cola(), ListaEnlazada())
            lista_drones.insertar(nuevo_dron)

        #INVERNADEROS
        lista_invernaderos = dom.getElementsByTagName('invernadero')
        for invernadero in lista_invernaderos:
            nombre_invernadero = invernadero.getAttribute('nombre')
            numero_hileras = int(invernadero.getElementsByTagName('numeroHileras')[0].firstChild.data)
            plantas_x_hilera = int(invernadero.getElementsByTagName('plantasXhilera')[0].firstChild.data)

            #PLANTAS
            lista_plantas = ListaEnlazada()
            plantas = invernadero.getElementsByTagName('planta')
            for planta in plantas:
                hilera = int(planta.getAttribute('hilera'))
                posicion = int(planta.getAttribute('posicion'))
                litros_agua = int(planta.getAttribute('litrosAgua'))
                gramos_fertilizante = int(planta.getAttribute('gramosFertilizante'))
                tipo_planta = planta.firstChild.data.strip()

                nueva_planta = Planta(hilera, posicion, litros_agua, gramos_fertilizante, tipo_planta)
                lista_plantas.insertar(nueva_planta)

            #DRONES ASIGNADOS
            lista_drones_asignados = ListaEnlazada()
            asignacion_drones = invernadero.getElementsByTagName('dron')
            for dron in asignacion_drones:
                id = int(dron.getAttribute('id'))
                hilera = int(dron.getAttribute('hilera'))

                indice = lista_drones.buscar_indice(id)
                dron = lista_drones.obtener(indice)
                dron.hilera_asignada = hilera

                lista_drones_asignados.insertar(dron)

            #PLANES DE RIEGO
            lista_planes_riego = ListaEnlazada()
            planes_riego = invernadero.getElementsByTagName('plan')
            for plan_riego in planes_riego:
                nombre = plan_riego.getAttribute('nombre')
                secuencia_ubicacion_riego = plan_riego.firstChild.data.strip()
                nuevo_plan_riego = PlanRiego(nombre, secuencia_ubicacion_riego)
                lista_planes_riego.insertar(nuevo_plan_riego)

            #CREAR INVERNADERO
            nuevo_invernadero = Invernadero(
                nombre_invernadero,
                numero_hileras,
                plantas_x_hilera,
                lista_plantas,
                lista_drones_asignados,
                lista_planes_riego
            )
            nuevo_invernadero.crear_matrices()

            self.lista_invernaderos.insertar(nuevo_invernadero)

    def listar_invernaderos(self):
        print("----------- Invernaderos Disponibles ------------")
        posicion = 1
        invernadero_actual = self.lista_invernaderos.primero
        while invernadero_actual:
            invernadero = invernadero_actual.dato
            print(f"{posicion}. - {invernadero.nombre}")
            invernadero_actual = invernadero_actual.siguiente
            posicion += 1

    def obtener_invernadero(self, posicion):
        invernadero_actual = self.lista_invernaderos.primero
        for pos in range(1, posicion):
            invernadero_actual = invernadero_actual.siguiente
        return invernadero_actual.dato

    def listar_planes_riego(self, invernadero):
        print("------------ Planes de riego ------------")
        posicion = 1
        lista_planes_riego = invernadero.lista_planes_riego
        plan_riego_actual = lista_planes_riego.primero
        while plan_riego_actual:
            plan_riego = plan_riego_actual.dato
            print(f"{posicion}.  -  {plan_riego.nombre}")
            plan_riego_actual = plan_riego_actual.siguiente
            posicion += 1

    def obtener_plan_riego(self, posicion, invernadero):
        plan_riego_actual = invernadero.lista_planes_riego.primero
        for _ in range(1, posicion):
            if plan_riego_actual is None:
                return None  #La posición no existe
            plan_riego_actual = plan_riego_actual.siguiente
        return plan_riego_actual.dato if plan_riego_actual else None
    
    def generar_xml_global(self):
        # Nodo raíz
        root = ET.Element("Invernaderos")

        # Recorremos todos los invernaderos
        invernadero_actual = self.lista_invernaderos.primero
        while invernadero_actual:
            inv = invernadero_actual.dato
            inv_elem = ET.SubElement(root, "Invernadero", nombre=inv.nombre)

            # Recorremos planes de riego
            plan_actual = inv.lista_planes_riego.primero
            contador = 1
            while plan_actual:
                plan = plan_actual.dato
                plan_elem = ET.SubElement(inv_elem, "PlanRiego", numero=str(contador), nombre=plan.nombre)

                # Agregamos lista de drones
                drones_elem = ET.SubElement(plan_elem, "Drones")
                dron_actual = inv.lista_drones_asignados.primero
                while dron_actual:
                    dron = dron_actual.dato
                    dron_elem = ET.SubElement(drones_elem, "Dron", nombre=dron.nombre, hilera=str(dron.hilera_asignada))
                    ET.SubElement(dron_elem, "AguaUsada").text = str(dron.litros_agua_usados)
                    ET.SubElement(dron_elem, "FertilizanteUsado").text = str(dron.gramos_fertilizante_usados)
                    dron_actual = dron_actual.siguiente

                contador += 1
                plan_actual = plan_actual.siguiente

            invernadero_actual = invernadero_actual.siguiente

        # Convertimos el XML en string bonito
        xml_str = ET.tostring(root, encoding="utf-8")

        # Devolvemos como archivo descargable en Flask
        return Response(
            xml_str,
            mimetype="application/xml",
            headers={"Content-Disposition": "attachment;filename=Reporte_Global.xml"}
        )