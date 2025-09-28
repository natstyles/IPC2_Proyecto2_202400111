from ListaSimpleEnlazada import ListaEnlazada
from Planta import Planta

class Matriz:
    def __init__(self, num_filas, num_columnas):
        self.num_filas = num_filas
        self.num_columnas = num_columnas
        self.matriz = ListaEnlazada()

        # Crear matriz con valores nulos (se llenará con plantas reales después)
        for i in range(1, num_filas + 1):
            fila = ListaEnlazada()
            for j in range(1, num_columnas + 1):
                planta = Planta(i, j, 0, 0, "")
                fila.insertar(planta)
            self.matriz.insertar(fila)
    
    def establecer(self, num_fila, num_columna, planta):
        #Establece un valor en la posición fila x columna
        fila = self.matriz.obtener(num_fila - 1) 
        if fila:
            columna = fila.primero
            for _ in range(num_columna - 1):
                if columna:
                    columna = columna.siguiente
            if columna:
                columna.dato = planta

    def obtener(self, num_fila, num_columna):
        #Obtiene el valor en la posición fila x columna
        fila = self.matriz.obtener(num_fila - 1)
        if fila:
            return fila.obtener(num_columna - 1)
        return None

    def mostrar(self, titulo="Matriz"):
        #Imprime la matriz de forma tabular (opcional, para depuración)
        print(titulo)
        actual_fila = self.matriz.primero
        while actual_fila:
            fila = actual_fila.dato
            valores = []
            actual_col = fila.primero
            while actual_col:
                planta = actual_col.dato
                if planta:
                    valores.append(f"{planta.tipo_planta or '-'}")
                else:
                    valores.append("None")
                actual_col = actual_col.siguiente
            print(" | ".join(valores))
            actual_fila = actual_fila.siguiente
