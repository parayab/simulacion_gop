from random import expovariate


class Estanque:
    ID = 0

    def __init__(self, capacidad_maxima, tiempo_maximo):
        self.id = Estanque.ID
        Estanque.ID += 1
        self.contenido_actual = 0
        self.capacidad_maxima = capacidad_maxima
        self.tiempo_maximo = tiempo_maximo

        # Estadisticas, siempre deberian ser cero porque asi se construye:
        self.demanda_no_satisfecha = 0
        self.capacidad_faltante = 0

    def producto_disponible(self):
        return self.contenido_actual

    def capacidad_disponible(self):
        return self.capacidad_maxima - self.contenido_actual

    def agregar_contenido(self, cantidad, tiempo_ingreso=0):
        # retorna la cantidad que efectivamente fue recibida por el estanque
        if (self.contenido_actual + cantidad <= self.capacidad_maxima):
            self.contenido_actual += cantidad
            return cantidad
        else:
            self.capacidad_faltante += self.capacidad_disponible - cantidad
            capacidad_disponible = self.capacidad_maxima - self.contenido_actual
            self.contenido_actual = self.capacidad_maxima
            return capacidad_disponible

    def quitar_contenido(self, cantidad):
        # retorna el contenido que efectivamente se pudo sacar del estanque
        if (self.contenido_actual - cantidad > 0):
            self.contenido_actual -= cantidad
            return cantidad
        else:
            self.demanda_no_satisfecha = cantidad - self.contenido_actual
            disponible = self.contenido_actual
            self.contenido_actual = 0
            return disponible

    def estadisticas(self):
        return "Cola de id {0}\n\tDemanda no satisfecha: {1} kilos\n\tCapacidad faltante: {2} kilos\n\tContenido actual: {3}/{4}".format(self.id, self.demanda_no_satisfecha, self.capacidad_faltante, self.contenido_actual, self.capacidad_maxima)
        # return {"demanda_no_satisfecha": self.demanda_no_satisfecha, "capacidad_faltante": self.capacidad_faltante}

    def __str__(self):
        return "Soy la cola de id {0} y mi contenido actual es: {1}/{2}\n".format(self.id, self.contenido_actual, self.capacidad_maxima)


class MaquinaProductiva:
    ID = 0

    def __init__(self, tasa, produccion_maxima, produccion_minima, cola_anterior, nombre):
        """
        tasa: tiempo que puede demorar la maquina en hacer un lote 
        la producción de la máquina está entre producción mínima y producción máxima según cuando le pidan
        Aún no se incorpora variabilidad
        cola_anterior: estanque del cual la máquina saca 'materia prima'
        """
        self.id = MaquinaProductiva.ID
        self.nombre = nombre
        MaquinaProductiva.ID += 1
        self.tasa = tasa
        self.produccion_maxima = produccion_maxima
        self.produccion_minima = produccion_minima
        # cantidad producida en el ultimo lote
        self.cantidad_ultima_produccion = 0
        self.produccion_total = 0
        self.proximo_termino_produccion = float("inf")

        # al intentar producir se toma de cola anterior y al termino de la produccion se deposita en cola siguiente
        self.cola_anterior = cola_anterior
        self.cola_siguiente = False

        # estadisticas de una maquina:
        self.tiempo_trabajando = 0
        self.no_produce_por_falta_de_input = 0
        self.no_produce_por_falta_de_espacio_output = 0
        self.demanda_no_satisfecha = 0  # cantidad_a_producir > capacidad_maxima

    def asignar_cola_siguiente(self, cola_siguiente):
        self.cola_siguiente = cola_siguiente

    def quiebre_stock(self):
        # Agrega un quiebre de stock donde corresponda: por falta de input o por espacio para el output
        if not self.cola_anterior:
            self.no_produce_por_falta_de_espacio_output += 1
        else:
            if self.cola_anterior.producto_disponible() < self.cola_siguiente.capacidad_disponible():
                self.no_produce_por_falta_de_input += 1
            else:
                self.no_produce_por_falta_de_espacio_output += 1

    def producir(self, cantidad, tiempo_inicio):
        # retorna la cantidad efectivamente producida por la maquina
        if (self.proximo_termino_produccion != float("inf")):
            return 0  # maquina ocupada
        if (cantidad < self.produccion_minima):
            self.quiebre_stock()
            return 0  # no piden suficiente produccion
        elif (cantidad > self.produccion_maxima):
            # me piden mas que lo que puedo producir
            self.demanda_no_satisfecha += cantidad - self.produccion_maxima
            tiempo_produccion = expovariate(1/self.tasa)
            self.cantidad_ultima_produccion = self.produccion_maxima
            self.proximo_termino_produccion = tiempo_inicio + tiempo_produccion
            self.tiempo_trabajando += tiempo_produccion
            return self.cantidad_ultima_produccion  # solo produzco el maximo
        else:
            # me piden una cantidad entre mi minimo y mi maximo
            tiempo_produccion = expovariate(1/self.tasa)
            self.cantidad_ultima_produccion = cantidad
            self.proximo_termino_produccion = tiempo_inicio + tiempo_produccion
            self.tiempo_trabajando += tiempo_produccion
            return self.cantidad_ultima_produccion

    def intentar_producir(self, tiempo_inicio):
        # Este metodo retorna True si logra producir, False en otro caso.
        # tener cuidado al elegir dsitribucion para que no de cero la cantidad a producir.
        if self.cola_anterior:
            cantidad_a_pedir = min(self.cola_anterior.producto_disponible(
            ), self.cola_siguiente.capacidad_disponible())
            # pido el minimo entre lo que tengo de "materia prima" en la cola anterior
            # y la capacidad que le queda al estanque que debe recibir mi produccion

            produccion = self.producir(cantidad_a_pedir, tiempo_inicio)
            self.cola_anterior.quitar_contenido(produccion)
        else:
            cantidad_a_pedir = self.cola_siguiente.capacidad_disponible()
            # pido la capacidad que le queda al estanque que debe recibir mi produccion
            produccion = self.producir(cantidad_a_pedir, tiempo_inicio)

        return produccion > 0

    def terminar_produccion(self):
        self.cola_siguiente.agregar_contenido(
            self.cantidad_ultima_produccion, self.proximo_termino_produccion)
        self.proximo_termino_produccion = float("inf")
        self.produccion_total += self.cantidad_ultima_produccion

    def simular(self):
        tiempo_retorno = self.proximo_termino_produccion
        self.terminar_produccion()
        return tiempo_retorno

    def estadisticas(self):
        return "{0}) {5}\n\tTiempo trabajando: {1} minutos\n\tProducción total: {2} kilos\n\tNo produzco por falta de input: {3} veces\n\tNo produce porque la siguiente cola no tiene espacio: {4} veces".format(self.id, self.tiempo_trabajando, self.produccion_total, self.no_produce_por_falta_de_input, self.no_produce_por_falta_de_espacio_output, self.nombre)
        # return {"tiempo_trabajando": self.tiempo_trabajando, "produccion_total": self.produccion_total, "no_produce_por_falta_de_input": self.no_produce_por_falta_de_input, "no_produce_por_falta_de_espacio_output": self.no_produce_por_falta_de_espacio_output}

    def __str__(self):
        return "Soy la maquina de id {0} y acabo de terminar en el tiempo {1}\n".format(self.id, self.proximo_termino_produccion)


class Camara:
    def __init__(self, camara_id, cantidad_horas_producto, peso_por_carro_producto):
        # Supuesto: siempre trabaja a capacidad maxima
        self.id = camara_id
        self.cantidad_horas_producto = cantidad_horas_producto
        self.capacidad = 42 * peso_por_carro_producto
        # disponible inidica si la camara esta abierta o en proceso de estabilizacion
        self.disponible = True
        # estabilizado indica si el producto al interior ya fue estabilizado o no
        self.estabilizado = False
        self.contenido_actual = 0
        self.tiempo_proxima_apertura = float("inf")

        #Estadisticas:
        self.tiempo_trabajando = 0
        self.produccion_total = 0

    def agregar_contenido(self, cantidad, tiempo):
        # retorna la cantidad efectivamente añadida a la camara
        contenido_agregado = 0
        if (self.contenido_actual + cantidad <= self.capacidad):
            self.contenido_actual += cantidad
            contenido_agregado = cantidad
        else:
            contenido_agregado = self.capacidad_disponible()
            self.contenido_actual = self.capacidad
        if (self.capacidad_completa()):
            self.estabilizar_producto(tiempo)
        return contenido_agregado

    def estabilizar_producto(self, tiempo_inicio):
        self.tiempo_proxima_apertura = tiempo_inicio + self.cantidad_horas_producto
        self.disponible = False
        self.tiempo_trabajando = self.cantidad_horas_producto

    def finalizar_estabilizacion(self):
        self.produccion_total += self.contenido_actual
        self.tiempo_proxima_apertura = float("inf")
        self.estabilizado = True
        self.disponible = True

    def quitar_contenido(self, cantidad):
        # retorna cantidad de producto efectivamente quitado
        if (self.contenido_actual - cantidad > 0):
            self.contenido_actual -= cantidad
            return cantidad
        else:
            disponible = self.contenido_actual
            self.contenido_actual = 0
            # Si se queda con cero contenido => ya no hay producto estabilizado
            self.estabilizado = False
            return disponible

    def recibiendo_producto(self):
        return self.disponible and not self.estabilizado

    def producto_disponible(self):
        return self.disponible and self.estabilizado

    def capacidad_completa(self):
        return self.contenido_actual == self.capacidad

    def capacidad_disponible(self):
        return self.capacidad - self.contenido_actual

    def estadisticas(self):
        return {"tiempo_trabajando": self.tiempo_trabajando, "produccion_total": self.produccion_total}

    def __str__(self):
        return "Camaras{4}\n\tUsado: {0}/{1} \n\tDisponible: {2} \n\tEstabilizado: {3}\n".format(self.contenido_actual, self.capacidad, self.disponible, self.estabilizado, self.id)


class Camaras:
    # 6 camaras, 42 carros por camara, 90 bandejas por carro -> Kilos por carro
    def __init__(self, cantidad_horas_producto, peso_por_carro_producto):
        self.camaras = [Camara(i, cantidad_horas_producto,
                               peso_por_carro_producto) for i in range(6)]
        self.capacidad_faltante = 0
        self.demanda_no_satisfecha = 0

    def capacidad_disponible(self):
        # Cuanto producto pueden recibir las camaras
        # camaras funcionan a maxima capacidad, si hay espacio libre, entonces se puede ingresar mas producto
        capacidad = 0
        for camara in self.camaras:
            if (camara.recibiendo_producto()):
                capacidad += camara.capacidad_disponible()
        return capacidad

    def producto_disponible(self):
        producto = 0
        for camara in self.camaras:
            if (camara.producto_disponible()):
                producto += camara.contenido_actual
        return producto

    def camara_proxima_apertura(self):
        camara_por_abrir = None
        tiempo_proxima_apertura = float("inf")
        for camara in self.camaras:
            if (camara.tiempo_proxima_apertura < tiempo_proxima_apertura):
                camara_por_abrir = camara
                tiempo_proxima_apertura = camara.tiempo_proxima_apertura
        return camara_por_abrir

    def proxima_camara_disponible(self):
        # siguiente camara que puede recibir producto
        for camara in self.camaras:
            if camara.recibiendo_producto() and camara.capacidad_disponible() > 0:
                return camara
        return None

    def proxima_camara_con_producto_estabilizado(self):
        for camara in self.camaras:
            if camara.producto_disponible():
                return camara
        return None

    def agregar_contenido(self, cantidad, tiempo_ingreso):
        while (cantidad > 0 and self.capacidad_disponible() > 0):
            proxima_camara = self.proxima_camara_disponible()
            if not proxima_camara:
                break
            contenido_agregado = proxima_camara.agregar_contenido(
                cantidad, tiempo_ingreso)
            cantidad -= contenido_agregado
        # Si sale del while y cantidad > 0, se pierde 'cantidad'
        self.capacidad_faltante += cantidad

    def quitar_contenido(self, cantidad):
        while (cantidad > 0 and self.producto_disponible() > 0):
            proxima_camara = self.proxima_camara_con_producto_estabilizado()
            if not proxima_camara:
                break
            contenido_obtenido = proxima_camara.quitar_contenido(cantidad)
            cantidad -= contenido_obtenido
        # Si sale del while y cantidad > 0, no se pudo entregar todo lo solicitado
        self.demanda_no_satisfecha += cantidad

    def print_camaras(self):
        for camara in self.camaras:
            print(camara)

    def simular(self):
        proxima_camara = self.camara_proxima_apertura()
        tiempo_retorno = proxima_camara.tiempo_proxima_apertura
        proxima_camara.finalizar_estabilizacion()
        return tiempo_retorno  # tiempo que se debe agregar a la cola de eventos

    def estadisticas(self):
        total_horas_trabajando = 0
        produccion_total_camaras = 0
        for camara in self.camaras:
            estadisticas = camara.estadisticas()
            total_horas_trabajando += estadisticas["tiempo_trabajando"]
            produccion_total_camaras += estadisticas["produccion_total"]
        return "Cámaras:\n\tDemanda no satisfecha: {0} kilos\n\tCantidad que las cámaras no pudieron recibir: {1}kilos\n\tTiempo total trabajando (cámara cerrada): {2} minutos\n\tProducción total: {3} kilos".format(self.demanda_no_satisfecha, self.capacidad_faltante, total_horas_trabajando, produccion_total_camaras)
        # return {"demanda_no_satisfecha": self.demanda_no_satisfecha, "capacidad_faltante": self.capacidad_faltante, "tiempo_trabajando": total_horas_trabajando, "produccion_total": produccion_total_camaras}

    def __str__(self):
        s = ''
        for camara in self.camaras:
            s += camara.__str__()
        return s