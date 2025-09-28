class Nodo:
    def __init__(self, dato):
        self.dato = dato
        self.siguiente = None


class ListaEnlazada:
    def __init__(self):
        self.primero = None
        self.tamanio = 0

    def esta_vacia(self):
        return self.primero is None

    def agregar_al_final(self, dato):
        #Agrega un nuevo nodo al final de la lista
        nuevo = Nodo(dato)
        if self.esta_vacia():
            self.primero = nuevo
        else:
            actual = self.primero
            while actual.siguiente:
                actual = actual.siguiente
            actual.siguiente = nuevo
        self.tamanio += 1

    def agregar_al_inicio(self, dato):
        #Agrega un nuevo nodo al inicio de la lista
        nuevo = Nodo(dato)
        nuevo.siguiente = self.primero
        self.primero = nuevo
        self.tamanio += 1

    def insertar(self, dato):
        # Alias de agregar_al_final (para compatibilidad con Sistema.py)
        self.agregar_al_final(dato)

    def obtener(self, indice):
        #Obtiene el valor en la posición indicada (0-based)
        if indice < 0 or indice >= self.tamanio:
            return None
        actual = self.primero
        for _ in range(indice):
            actual = actual.siguiente
        return actual.dato

    def eliminar(self, indice):
        #Elimina un nodo en la posición indicada (0-based)
        if indice < 0 or indice >= self.tamanio:
            return None
        if indice == 0:
            dato = self.primero.dato
            self.primero = self.primero.siguiente
        else:
            actual = self.primero
            for _ in range(indice - 1):
                actual = actual.siguiente
            dato = actual.siguiente.dato
            actual.siguiente = actual.siguiente.siguiente
        self.tamanio -= 1
        return dato

    def buscar_indice(self, id_dron):
        # Busca un dron por su id y devuelve el índice, o -1 si no lo encuentra
        actual = self.primero
        indice = 0
        while actual:
            if hasattr(actual.dato, "id") and actual.dato.id == id_dron:
                return indice
            indice += 1
            actual = actual.siguiente
        return -1

    def __len__(self):
        return self.tamanio

    def __iter__(self):
        #Permite recorrer la lista con un for-in
        actual = self.primero
        while actual:
            yield actual.dato
            actual = actual.siguiente

    def __str__(self):
        valores = []
        actual = self.primero
        while actual:
            valores.append(str(actual.dato))
            actual = actual.siguiente
        return " -> ".join(valores) if valores else "Lista vacía"
