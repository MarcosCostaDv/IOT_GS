"""
validacao_manager.py
Gerencia o ciclo de validação por gestos.
"""

import time
from dataclasses import dataclass
from typing import Optional


TEMP_GESTO = {
    "QUENTE": 31.5,
    "NORMAL": 22.0,
    "FRIO": 15.5,
}

ICONE_GESTO = {
    "QUENTE": "INDICADOR ^",
    "NORMAL": "JOINHA",
    "FRIO": "PEACE/V",
}


@dataclass
class RegistroValidacao:
    gesto: str
    temperatura: float
    timestamp: float
    hora_fmt: str = ""

    def __post_init__(self):
        self.hora_fmt = time.strftime(
            "%H:%M:%S",
            time.localtime(self.timestamp),
        )


class ValidacaoManager:
    def __init__(self, intervalo_segundos: int = 1800):
        self.intervalo = intervalo_segundos
        self._proxima = time.time() + intervalo_segundos
        self._validando = False
        self._historico: list[RegistroValidacao] = []
        self._ultimo: Optional[RegistroValidacao] = None

    def deve_validar(self) -> bool:
        return time.time() >= self._proxima and not self._validando

    def segundos_para_proxima(self) -> float:
        return max(0.0, self._proxima - time.time())

    def formato_countdown(self) -> str:
        segundos = int(self.segundos_para_proxima())
        return f"{segundos // 60:02d}:{segundos % 60:02d}"

    @property
    def ultimo(self) -> Optional[RegistroValidacao]:
        return self._ultimo

    @property
    def historico(self) -> list[RegistroValidacao]:
        return list(self._historico)

    def iniciar_sessao(self):
        self._validando = True

    def registrar(self, gesto: str):
        temperatura = TEMP_GESTO.get(gesto, 22.0)

        registro = RegistroValidacao(
            gesto=gesto,
            temperatura=temperatura,
            timestamp=time.time(),
        )

        self._historico.append(registro)
        self._ultimo = registro
        self._proxima = time.time() + self.intervalo
        self._validando = False

        print(
            f"[VALIDACAO] Registrado: {gesto} | "
            f"{temperatura}°C | proxima em {self.intervalo // 60} min"
        )

    def cancelar_sessao(self):
        self._validando = False
        self._proxima = time.time() + 120

    def forcar_agora(self):
        self._proxima = time.time() + 1
        print("[VALIDACAO] Validacao forcada manualmente.")

    def resetar_timer(self, segundos: int | None = None):
        intervalo = segundos if segundos is not None else self.intervalo
        self._proxima = time.time() + intervalo
        self._validando = False