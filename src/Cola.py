class Nodo:
    def __init__(self, valor):
        self.valor = valor
        self.siguiente = None

class Cola:
    def __init__(self):
        self.frente = None
        self.final = None
        self.tamanio = 0

    def esta_vacia(self):
        return self.frente is None

    def encolar(self, valor):
        #Agrega un nuevo elemento al final de la cola
        nuevo = Nodo(valor)
        if self.esta_vacia():
            self.frente = nuevo
            self.final = nuevo
        else:
            self.final.siguiente = nuevo
            self.final = nuevo
        self.tamanio += 1

    def desencolar(self):
        #Saca el elemento al frente de la cola y lo retorna
        if self.esta_vacia():
            return None
        valor = self.frente.valor
        self.frente = self.frente.siguiente
        if self.frente is None:  #si la cola queda vacía
            self.final = None
        self.tamanio -= 1
        return valor

    def ver_frente(self):
        #Muestra el valor al frente de la cola sin quitarlo"""
        if self.esta_vacia():
            return None
        return self.frente.valor

    def __len__(self):
        return self.tamanio

    def __str__(self):
        valores = []
        actual = self.frente
        while actual:
            valores.append(str(actual.valor))
            actual = actual.siguiente
        return " <- ".join(valores) if valores else "Cola vacía"
class Nodo:
    def __init__(self, valor):
        self.valor = valor
        self.siguiente = None


class Cola:
    def __init__(self):
        self.frente = None
        self.final = None
        self.tamanio = 0

    def esta_vacia(self):
        return self.frente is None

    def encolar(self, valor):
        """Agrega un nuevo elemento al final de la cola"""
        nuevo = Nodo(valor)
        if self.esta_vacia():
            self.frente = nuevo
            self.final = nuevo
        else:
            self.final.siguiente = nuevo
            self.final = nuevo
        self.tamanio += 1

    def desencolar(self):
        """Saca el elemento al frente de la cola y lo retorna"""
        if self.esta_vacia():
            return None
        valor = self.frente.valor
        self.frente = self.frente.siguiente
        if self.frente is None:  #si la cola queda vacía
            self.final = None
        self.tamanio -= 1
        return valor

    def ver_frente(self):
        """Muestra el valor al frente de la cola sin quitarlo"""
        if self.esta_vacia():
            return None
        return self.frente.valor

    def __len__(self):
        return self.tamanio

    def __str__(self):
        valores = []
        actual = self.frente
        while actual:
            valores.append(str(actual.valor))
            actual = actual.siguiente
        return " <- ".join(valores) if valores else "Cola vacía"
