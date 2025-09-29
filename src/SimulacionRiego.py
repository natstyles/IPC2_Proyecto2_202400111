from .ListaSimpleEnlazada import ListaEnlazada
import xml.etree.ElementTree as ET
from flask import render_template, Response
from io import BytesIO
from graphviz import Digraph
import os

class SimulacionRiego:
    def __init__(self, plan_riego, invernadero):
        self.plan_riego = plan_riego.secuencia_ubicacion_riego
        self.matriz_plantas = invernadero.matriz_plantas
        self.lista_drones_asignados = invernadero.lista_drones_asignados
        self.lista_plantas_a_regar = ListaEnlazada()
        self.linea_tiempo = []
        self.invernadero = invernadero

    def inicializar_datos_drones(self):
        actual_dron_asignado = self.lista_drones_asignados.primero
        while actual_dron_asignado:
            dron = actual_dron_asignado.dato
            dron.reiniciar_datos()
            if hasattr(dron, "finalizado"):
                dron.finalizado = False
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
            asignado = False
            actual_dron = self.lista_drones_asignados.primero
            while actual_dron:
                dron = actual_dron.dato
                if planta.hilera == dron.hilera_asignada:
                    dron.plantas_a_regar.encolar(planta)
                    asignado = True
                    print(f"[DEBUG] Planta H{planta.hilera}P{planta.posicion} asignada a {dron.nombre}")
                actual_dron = actual_dron.siguiente
            if not asignado:
                print(f"[WARNING] Planta H{planta.hilera}P{planta.posicion} NO tiene dron asignado")
            actual_planta = actual_planta.siguiente

    def simular(self):
        actual_planta_a_regar = self.lista_plantas_a_regar.primero
        self.segundo_actual = 1

        while actual_planta_a_regar:
            planta_a_regar = actual_planta_a_regar.dato
            planta_no_regada = True

            while planta_no_regada:
                actual_dron_asignado = self.lista_drones_asignados.primero
                eventos_segundo = []

                while actual_dron_asignado:
                    dron = actual_dron_asignado.dato
                    posicion_actual = dron.posicion_actual

                    if dron.posicion_objetivo is None and not dron.plantas_a_regar.esta_vacia():
                        planta = dron.plantas_a_regar.desencolar()
                        if planta:
                            dron.posicion_objetivo = planta.posicion

                    posicion_objetivo = dron.posicion_objetivo

                    if posicion_objetivo is not None:
                        if posicion_actual < posicion_objetivo:
                            paso = dron.mover_adelante()
                            dron.pasos.insertar(paso)
                            eventos_segundo.append({"dron": dron.nombre, "accion": paso})

                        elif posicion_actual > posicion_objetivo:
                            paso = dron.mover_atras()
                            dron.pasos.insertar(paso)
                            eventos_segundo.append({"dron": dron.nombre, "accion": paso})

                        else:
                            if planta_a_regar.hilera == dron.hilera_asignada:
                                paso = dron.regar(planta_a_regar)
                                dron.pasos.insertar(paso)
                                eventos_segundo.append({"dron": dron.nombre, "accion": paso})
                                planta_no_regada = False
                                dron.posicion_objetivo = None
                            else:
                                paso = dron.esperar()
                                dron.pasos.insertar(paso)
                                eventos_segundo.append({"dron": dron.nombre, "accion": paso})

                    actual_dron_asignado = actual_dron_asignado.siguiente

                if eventos_segundo:
                    self.linea_tiempo.append({
                        "segundo": self.segundo_actual,
                        "eventos": eventos_segundo
                    })

                self.segundo_actual += 1

            actual_planta_a_regar = actual_planta_a_regar.siguiente

    # SNAPSHOT Y NORMALIZACIÓN
    def _normalizar_linea_tiempo_con_fin(self):
        #nombres de los drones
        dron_nombres = []
        actual_dron = self.lista_drones_asignados.primero
        while actual_dron:
            dron_nombres.append(actual_dron.dato.nombre)
            actual_dron = actual_dron.siguiente

        # último segundo real ignoranddo el FIN
        ultimo_evento = {d: 0 for d in dron_nombres}
        for tick in self.linea_tiempo:
            for evento in tick["eventos"]:
                acc = str(evento.get("accion", "")).upper()
                if acc == "FIN":
                    continue  #no considerar FIN como evento real
                ultimo_evento[evento["dron"]] = max(ultimo_evento[evento["dron"]], tick["segundo"])

        # segundo exacto del FIN por dron
        fin_por_dron = {d: (ultimo_evento[d] + 1 if ultimo_evento[d] > 0 else 0) for d in dron_nombres}
        fin_ticks = [t for t in fin_por_dron.values() if t > 0]

        ultimo_tick_util = max(fin_ticks) if fin_ticks else max((t["segundo"] for t in self.linea_tiempo), default=0)

        nueva = []
        for s in range(1, ultimo_tick_util + 1):
            # eventos reales del segundo s
            eventos_s = [e for t in self.linea_tiempo if t["segundo"] == s for e in t["eventos"]]

            for d in dron_nombres:
                if fin_por_dron[d] == s:
                    if not any(e.get("dron") == d and str(e.get("accion", "")).upper() == "FIN" for e in eventos_s):
                        eventos_s.append({"dron": d, "accion": "FIN"})

            if eventos_s:
                nueva.append({"segundo": s, "eventos": eventos_s})

        return nueva

    def snapshot_resultados(self):
        resumen = []
        actual = self.lista_drones_asignados.primero
        while actual:
            dr = actual.dato
            resumen.append({
                "nombre": dr.nombre,
                "litros_agua": dr.litros_agua_usados,
                "gramos_fertilizante": dr.gramos_fertilizante_usados
            })
            actual = actual.siguiente

        linea_norm = self._normalizar_linea_tiempo_con_fin()
        tiempo_total = max((t["segundo"] for t in linea_norm), default=0)

        return {
            "tiempo_total": tiempo_total,
            "resumen_drones": resumen,
            "linea_tiempo_normalizada": linea_norm
        }

    # XML INDIVIDUAL usando snapshot
    def generar_xml_salida(self, nombre_invernadero, nombre_plan):
        snap = self.snapshot_resultados()
        tiempo_total = snap["tiempo_total"]
        resumen_drones = snap["resumen_drones"]
        linea_tiempo = snap["linea_tiempo_normalizada"]

        root = ET.Element("datosSalida")
        lista_invernaderos_elem = ET.SubElement(root, "listaInvernaderos")
        invernadero_elem = ET.SubElement(lista_invernaderos_elem, "invernadero", {"nombre": nombre_invernadero})
        plan_elem = ET.SubElement(invernadero_elem, "plan", {"nombre": nombre_plan})

        agua_total = sum(d["litros_agua"] for d in resumen_drones)
        fert_total = sum(d["gramos_fertilizante"] for d in resumen_drones)

        ET.SubElement(plan_elem, "tiempoOptimoSegundos").text = str(tiempo_total -1)
        ET.SubElement(plan_elem, "aguaRequeridaLitros").text = str(agua_total)
        ET.SubElement(plan_elem, "fertilizanteRequeridoGramos").text = str(fert_total)

        eff = ET.SubElement(plan_elem, "eficienciaDronesRegadores")
        for d in resumen_drones:
            ET.SubElement(eff, "dron", {
                "nombre": d["nombre"],
                "litrosAgua": str(d["litros_agua"]),
                "gramosFertilizante": str(d["gramos_fertilizante"])
            })

        instrucciones = ET.SubElement(plan_elem, "instrucciones")
        for tick in linea_tiempo:
            t_elem = ET.SubElement(instrucciones, "tiempo", {"segundos": str(tick["segundo"])})
            for evento in tick["eventos"]:
                accion = evento["accion"]
                if " " in accion and "H" in accion and "P" in accion:
                    partes = accion.split()
                    if len(partes) == 2:
                        accion = f"{partes[0]}({partes[1]})"
                if accion.upper() == "FIN":
                    accion = "Fin"
                ET.SubElement(t_elem, "dron", {"nombre": evento["dron"], "accion": accion})

        buffer = BytesIO()
        ET.ElementTree(root).write(buffer, encoding="utf-8", xml_declaration=True)
        buffer.seek(0)
        return Response(
            buffer,
            mimetype="application/xml",
            headers={"Content-Disposition": f"attachment; filename=salida_{nombre_plan}.xml"}
        )

    #XML GENERAL
    @staticmethod
    def generar_xml_general(invernaderos):
        root = ET.Element("datosSalida")
        lista_invernaderos_elem = ET.SubElement(root, "listaInvernaderos")

        for inv in invernaderos:
            invernadero_elem = ET.SubElement(lista_invernaderos_elem, "invernadero", {"nombre": inv.nombre})
            for plan in getattr(inv, "lista_planes", []):
                if not hasattr(plan, "resultado"):
                    continue
                res = plan.resultado
                tiempo_total = res["tiempo_total"]
                resumen_drones = res["resumen_drones"]
                linea_tiempo = res["linea_tiempo_normalizada"]

                plan_elem = ET.SubElement(invernadero_elem, "plan", {"nombre": plan.nombre})
                agua_total = sum(d["litros_agua"] for d in resumen_drones)
                fert_total = sum(d["gramos_fertilizante"] for d in resumen_drones)

                ET.SubElement(plan_elem, "tiempoOptimoSegundos").text = str(tiempo_total -1)
                ET.SubElement(plan_elem, "aguaRequeridaLitros").text = str(agua_total)
                ET.SubElement(plan_elem, "fertilizanteRequeridoGramos").text = str(fert_total)

                eficiencia_elem = ET.SubElement(plan_elem, "eficienciaDronesRegadores")
                for d in resumen_drones:
                    ET.SubElement(eficiencia_elem, "dron", {
                        "nombre": d["nombre"],
                        "litrosAgua": str(d["litros_agua"]),
                        "gramosFertilizante": str(d["gramos_fertilizante"])
                    })

                instrucciones_elem = ET.SubElement(plan_elem, "instrucciones")
                for tick in linea_tiempo:
                    tiempo_elem = ET.SubElement(instrucciones_elem, "tiempo", {"segundos": str(tick["segundo"])})
                    for e in tick["eventos"]:
                        accion = e["accion"]
                        if " " in accion and "H" in accion and "P" in accion:
                            partes = accion.split()
                            if len(partes) == 2:
                                accion = f"{partes[0]}({partes[1]})"
                        if accion.upper() == "FIN":
                            accion = "Fin"
                        ET.SubElement(tiempo_elem, "dron", {"nombre": e["dron"], "accion": accion})

        buffer = BytesIO()
        ET.ElementTree(root).write(buffer, encoding="utf-8", xml_declaration=True)
        buffer.seek(0)
        return Response(
            buffer,
            mimetype="application/xml",
            headers={"Content-Disposition": "attachment; filename=salida_general.xml"}
        )

    #REPORTE HTML
    def generar_html_reporte(self, nombre_invernadero, nombre_plan, ruta_salida):
        tiempo_total = max((tick["segundo"] for tick in self.linea_tiempo), default=0)
        agua_total, fertilizante_total, drones = 0, 0, []

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
        ultimo_evento = {d: 0 for d in dron_nombres}
        for tick in self.linea_tiempo:
            for evento in tick["eventos"]:
                if str(evento.get("accion","")).upper() == "FIN":
                    continue
                ultimo_evento[evento["dron"]] = tick["segundo"]

        fin_por_dron = {d: ultimo_evento[d] + 1 for d in dron_nombres}
        linea_tiempo_html = []
        ultimo_tick_util = max(fin_por_dron.values(), default=tiempo_total)
        for s in range(1, ultimo_tick_util + 1):
            tick = {"segundo": s, "eventos": []}
            #eventos reales
            for e in [e for t in self.linea_tiempo if t["segundo"] == s for e in t["eventos"]]:
                tick["eventos"].append(e)
            #FIN si corresponde y no existe
            for d in dron_nombres:
                if fin_por_dron[d] == s and not any(
                    e.get("dron") == d and str(e.get("accion","")).upper() == "FIN" for e in tick["eventos"]
                ):
                    tick["eventos"].append({"dron": d, "accion": "FIN"})
            if tick["eventos"]:
                linea_tiempo_html.append(tick)

        contenido = render_template(
            "reporte.html",
            invernadero_nombre=nombre_invernadero,
            plan_nombre=nombre_plan,
            tiempo_total=ultimo_tick_util,
            agua_total=agua_total,
            fertilizante_total=fertilizante_total,
            drones=drones,
            dron_nombres=dron_nombres,
            linea_tiempo=linea_tiempo_html
        )
        with open(ruta_salida, "w", encoding="utf-8") as f:
            f.write(contenido)

        print(f"Reporte HTML generado en: {ruta_salida}")

    #REPORTE TDA
    def generar_reporte_tda(self, nombre_archivo, tiempo=None):
        dot = Digraph(comment="Reporte TDA")
        dot.attr(rankdir="TB", bgcolor="transparent")
        dot.attr('node', shape='ellipse', fontcolor='white', color='#00bbf9')
        dot.attr('edge', color='#00bbf9', fontcolor='white')

        for dron in self.lista_drones_asignados:
            actual = dron.pasos.primero
            anterior = None
            paso_actual = 1
            while actual:
                if tiempo is not None and paso_actual > tiempo:
                    break
                nodo = f"{dron.nombre}_{paso_actual}"
                dot.node(nodo, actual.dato)
                if anterior:
                    dot.edge(anterior, nodo)
                anterior = nodo
                actual = actual.siguiente
                paso_actual += 1

        ruta = os.path.join("uploads", nombre_archivo)
        dot.render(ruta, format="svg", cleanup=True)
        return ruta + ".svg"
