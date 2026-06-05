"""
sensor_simulator.py
Simula leituras de temperatura da cápsula.
"""

import random
import time
import math


class SensorTemperatura:
    LIMITE_ALTO_ALERTA = 28.0
    LIMITE_ALTO_AVISO = 25.0
    LIMITE_BAIXO_ALERTA = 18.0

    def __init__(self, temp_base: float = 22.0, ruido: float = 0.3):
        self.temp_base = temp_base
        self.ruido = ruido
        self._t0 = time.time()
        self._falha = False
        self._contador = 0
        self.temp_override: float | None = None

    def ler(self) -> dict:
        self._contador += 1

        if self._falha:
            return {
                "temperatura": None,
                "status": "FALHA",
                "timestamp": time.time(),
                "leitura_num": self._contador,
            }

        if self.temp_override is not None:
            temperatura = round(self.temp_override + random.gauss(0, 0.1), 2)
        else:
            t = time.time() - self._t0

            temperatura = round(
                self.temp_base
                + math.sin(t * 0.05) * 3.0
                + math.sin(t * 0.01) * 1.5
                + random.gauss(0, self.ruido),
                2,
            )

        return {
            "temperatura": temperatura,
            "status": self._status(temperatura),
            "timestamp": time.time(),
            "leitura_num": self._contador,
        }

    def simular_falha(self, ativar=True):
        self._falha = ativar

    def _status(self, temperatura):
        if temperatura > self.LIMITE_ALTO_ALERTA:
            return "ALERTA_ALTO"

        if temperatura < self.LIMITE_BAIXO_ALERTA:
            return "ALERTA_BAIXO"

        if temperatura > self.LIMITE_ALTO_AVISO:
            return "AVISO"

        return "NORMAL"