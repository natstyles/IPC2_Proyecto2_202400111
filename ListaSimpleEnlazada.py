class Nodo:
    def __init__(self, valor):
        self.valor = valor
        self.siguiente = None


class ListaEnlazada:
    def __init__(self):
        self.primero = None
        self.tamanio = 0

    def esta_vacia(self):
        return self.primero is None

    def agregar_al_final(self, valor):
        #Agrega un nuevo nodo al final de la lista
        nuevo = Nodo(valor)
        if self.esta_vacia():
            self.primero = nuevo
        else:
            actual = self.primero
            while actual.siguiente:
                actual = actual.siguiente
            actual.siguiente = nuevo
        self.tamanio += 1

    def agregar_al_inicio(self, valor):
        #Agrega un nuevo nodo al inicio de la lista
        nuevo = Nodo(valor)
        nuevo.siguiente = self.primero
        self.primero = nuevo
        self.tamanio += 1

    def obtener(self, indice):
        #Obtiene el valor en la posición indicada (0-based)
        if indice < 0 or indice >= self.tamanio:
            return None
        actual = self.primero
        for _ in range(indice):
            actual = actual.siguiente
        return actual.valor

    def eliminar(self, indice):
        #Elimina un nodo en la posición indicada (0-based)
        if indice < 0 or indice >= self.tamanio:
            return None
        if indice == 0:
            valor = self.primero.valor
            self.primero = self.primero.siguiente
        else:
            actual = self.primero
            for _ in range(indice - 1):
                actual = actual.siguiente
            valor = actual.siguiente.valor
            actual.siguiente = actual.siguiente.siguiente
        self.tamanio -= 1
        return valor

    def __len__(self):
        return self.tamanio

    def __iter__(self):
        #Permite recorrer la lista con un for-in
        actual = self.primero
        while actual:
            yield actual.valor
            actual = actual.siguiente

    def __str__(self):
        valores = []
        actual = self.primero
        while actual:
            valores.append(str(actual.valor))
            actual = actual.siguiente
        return " -> ".join(valores) if valores else "Lista vacía"
