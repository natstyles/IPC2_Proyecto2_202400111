class PlanRiego:
    def __init__(self, nombre, secuencia_ubicacion_riego, tiempo_optimo=0, agua_requerida=0, fertilizante_requerido=0):
        self.nombre = nombre
        self.secuencia_ubicacion_riego = secuencia_ubicacion_riego
        self.tiempo_optimo = tiempo_optimo
        self.agua_requerida = agua_requerida
        self.fertilizante_requerido = fertilizante_requerido
