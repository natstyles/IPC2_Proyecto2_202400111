from .Sistema import Sistema
from .SimulacionRiego import SimulacionRiego

def main():
    sistema = Sistema()

    while True:
        print("Sistema de riego:")
        print("1. Cargar archivo")
        print("2. Procesar")
        print("3. Salir")

        opcion = input("Selecciona una opcion: ")

        if opcion == "1":
            ruta_archivo = input("Ingresa la ruta del archivo: ")
            sistema.leer_archivo(ruta_archivo)
        elif opcion == "2":
            sistema.listar_invernaderos()
            pos = int(input("Ingrese el numero de invernadero: "))

            invernadero = sistema.obtener_invernadero(pos)
            sistema.listar_planes_riego(invernadero)
            pos = int(input("Ingrese el numero de plan de riego: "))

            plan_riego = sistema.obtener_plan_riego(pos, invernadero)

            simulacion = SimulacionRiego(plan_riego, invernadero)
            simulacion.inicializar_datos_drones()
            simulacion.crear_lista_plantas_a_regar()
            simulacion.asignar_plantas_a_regar_a_dron()
            simulacion.simular()
            simulacion.imprimir_pasos()
            simulacion.imprimir_resumen()
            simulacion.generar_xml_salida(invernadero.nombre, plan_riego.nombre, "salida.xml")

        elif opcion == "3":
            print("Ejecucion finalizada")
            break
        else:
            print("opcion no válida")

if  __name__ == "__main__":
    main()