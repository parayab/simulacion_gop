import tasas
import produccion
import producto
from maquinas import Estanque, Camaras, MaquinaProductiva
import numpy as np

'''SUPUESTOS:
- Las camaras solo se cierran y comienzan a estabilizar si estan a maxima capacidad
- Las maquinas solo funcionan si es con cierta capacidad sobre un minimo
- El producto que no alcanza a procesar una maquina se pierde
- Productos tienen envasado y embolsado, a menos que se demuestre lo contrario >:(
- Cambiar la linea 75: self.fegama => self.pick cuando se cocina con pick
'''

# MEGA ATENCION CON LA NID, envasadora y embolsadora por las unidades!!!
TIEMPO_SIMULACION = 4500  # EN MINUTOS


class Simulacion:

    def __init__(self, tiempo_maximo):
        # Necesarios simulacion
        self.tiempo_maximo = tiempo_maximo
        self.tiempo_actual = 0

        # Estadisticas
        self.kilos_terminados = 0

        # Maquinas:
        self.coolmix = MaquinaProductiva(
            produccion_maxima=produccion.COOLMIX_MAX, produccion_minima=produccion.COOLMIX_MIN,
            cola_anterior=False, nombre="Coolmix",
            triangular_min=tasas.COOLMIX_TRIANGULAR_MIN, triangular_max=tasas.COOLMIX_TRIANGULAR_MAX, triangular_moda=tasas.COOLMIX_TRIANGULAR_MODA)

        self.estanque_pulmon_crudo = Estanque(
            capacidad_maxima=1500, tiempo_maximo=None)

        self.fegama = MaquinaProductiva(
            produccion_maxima=produccion.FEGAMA_MAX, produccion_minima=produccion.FEGAMA_MIN,
            cola_anterior=self.estanque_pulmon_crudo, nombre="Fegama",
            triangular_min=tasas.FEGAMA_TRIANGULAR_MIN, triangular_max=tasas.FEGAMA_TRIANGULAR_MAX, triangular_moda=tasas.FEGAMA_TRIANGULAR_MODA)

        self.pick = MaquinaProductiva(
            produccion_maxima=produccion.PICK_MAX, produccion_minima=produccion.PICK_MIN,
            cola_anterior=self.estanque_pulmon_crudo, nombre="Pick",
            triangular_min=tasas.PICK_TRIANGULAR_MIN, triangular_max=tasas.PICK_TRIANGULAR_MAX, triangular_moda=tasas.PICK_TRIANGULAR_MODA)

        self.estanque_pulmon_cocido = Estanque(
            capacidad_maxima=1200, tiempo_maximo=3)

        self.nid_1 = MaquinaProductiva(
            produccion_maxima=produccion.NID_1_MAX, produccion_minima=produccion.NID_1_MIN,
            cola_anterior=self.estanque_pulmon_cocido, nombre="Nid moldeado",
            triangular_min=tasas.NID_1_TRIANGULAR_MIN, triangular_max=tasas.NID_1_TRIANGULAR_MAX, triangular_moda=tasas.NID_1_TRIANGULAR_MODA)

        self.camaras = Camaras(cantidad_horas_producto=producto.HORAS_EN_CAMARA,
                               peso_por_carro_producto=producto.PESO_POR_CARRO,
                               triangular_min=tasas.CAMARAS_TRIANGULAR_MIN,
                               triangular_max=tasas.CAMARAS_TRIANGULAR_MAX,
                               triangular_moda=tasas.CAMARAS_TRIANGULAR_MODA
                               )

        self.nid_2 = MaquinaProductiva(
            produccion_maxima=produccion.NID_2_MAX, produccion_minima=produccion.NID_2_MIN,
            cola_anterior=self.camaras, nombre="Nid desbandejado",
            triangular_min=tasas.NID_2_TRIANGULAR_MIN, triangular_max=tasas.NID_2_TRIANGULAR_MAX, triangular_moda=tasas.NID_2_TRIANGULAR_MODA)

        self.estanque_envasado = Estanque(
            capacidad_maxima=float("inf"), tiempo_maximo=None)

        self.envasadora = MaquinaProductiva(
            produccion_maxima=produccion.NAGEMA_MAX, produccion_minima=produccion.NAGEMA_MIN,
            cola_anterior=self.estanque_envasado, nombre="Envasadora-Nagema",
            triangular_min=tasas.NAGEMA_TRIANGULAR_MIN, triangular_max=tasas.NAGEMA_TRIANGULAR_MAX, triangular_moda=tasas.NAGEMA_TRIANGULAR_MODA)

        self.estanque_embolsado = Estanque(
            capacidad_maxima=float("inf"), tiempo_maximo=None)

        self.embolsadora = MaquinaProductiva(
            produccion_maxima=produccion.EMBOLSADO_MAX, produccion_minima=produccion.EMBOLSADO_MIN,
            cola_anterior=self.estanque_embolsado, nombre="Embolsado",
            triangular_min=tasas.EMBOLSADO_TRIANGULAR_MIN, triangular_max=tasas.EMBOLSADO_TRIANGULAR_MAX, triangular_moda=tasas.EMBOLSADO_TRIANGULAR_MODA)

        self.estanque_finalizados = Estanque(
            capacidad_maxima=float("inf"), tiempo_maximo=None)

        self.coolmix.asignar_cola_siguiente(self.estanque_pulmon_crudo)
        self.fegama.asignar_cola_siguiente(self.estanque_pulmon_cocido)
        self.pick.asignar_cola_siguiente(self.estanque_pulmon_cocido)
        self.nid_1.asignar_cola_siguiente(self.camaras)
        self.nid_2.asignar_cola_siguiente(self.estanque_envasado)
        self.envasadora.asignar_cola_siguiente(self.estanque_embolsado)
        self.embolsadora.asignar_cola_siguiente(self.estanque_finalizados)

        self.maquinas = [self.coolmix, self.fegama, self.nid_1,
                         self.nid_2, self.envasadora, self.embolsadora]
        # set de maquinas para un producto que usa fegama, envasadora y embolsadora

    def buscar_proximo_termino_produccion(self):
        proximo_termino_produccion = float("inf")
        proxima_maquina = None
        for maquina in self.maquinas:
            if maquina.proximo_termino_produccion < proximo_termino_produccion:
                proximo_termino_produccion = maquina.proximo_termino_produccion
                proxima_maquina = maquina
        camara = self.camaras.camara_proxima_apertura()

        if camara and camara.tiempo_proxima_apertura < proximo_termino_produccion:
            return self.camaras
        else:
            return proxima_maquina

    def simular(self):
        self.coolmix.intentar_producir(self.tiempo_actual)  # produce al maximo

        # Mientras haya eventos en la lista y el tiempo de simulacion no termine
        while(self.tiempo_actual < self.tiempo_maximo):

            # Encontrar proximo evento
            maquina_lista = self.buscar_proximo_termino_produccion()
            nuevo_tiempo = maquina_lista.simular()

            # Avanzar el tiempo de simulacion al tiempo del evento
            self.tiempo_actual = nuevo_tiempo

            for maquina in self.maquinas:
                maquina.intentar_producir(self.tiempo_actual)

        # print("Estadísticas de la simulación:")
        # for maquina in self.maquinas:
        #     print(maquina.estadisticas())
        #     print(maquina.cola_siguiente.estadisticas())
        return self.estanque_finalizados.contenido_actual


produccion_total = []

for i in range(1000):
    simulacion = Simulacion(TIEMPO_SIMULACION)  # EN minutos
    produccion_i = simulacion.simular()
    produccion_total.append(produccion_i)

print("Estadisticas 1000 simulaciones")
print(np.mean(np.array(produccion_total)))
print(np.std(np.array(produccion_total)))
# print(produccion_total)