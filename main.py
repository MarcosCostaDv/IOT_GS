"""
main.py
Space Capsule Monitoring System

Teclas:
V - forçar validação por câmera
F - simular falha do sensor
R - resetar sensor
Q - encerrar sistema
"""

import argparse
import threading
import time

import cv2

from api_server import atualizar_dados, iniciar_servidor
from monitor_hud import MonitorHUD
from sensor_simulator import SensorTemperatura
from validacao_camera import executar_validacao
from validacao_manager import TEMP_GESTO, ValidacaoManager


MONITORANDO = "MONITORANDO"
VALIDANDO = "VALIDANDO"

_ultimo_dado: dict = {}
_lock = threading.Lock()


def _loop_aquisicao(sensor: SensorTemperatura, intervalo: float = 1.0):
    global _ultimo_dado

    print("[AQUISICAO] Iniciando coleta de dados...")

    while True:
        dado = sensor.ler()

        atualizar_dados(dado)

        with _lock:
            _ultimo_dado = dado

        temperatura = dado.get("temperatura", "N/A")
        status = dado.get("status", "N/A")

        print(
            f"[SENSOR] #{dado.get('leitura_num', 0):04d} "
            f"{temperatura}°C | {status}"
        )

        time.sleep(intervalo)


def _ler_dado_atual() -> dict:
    with _lock:
        return dict(_ultimo_dado)


def _tela_transicao(hud: MonitorHUD, dado: dict, vm: ValidacaoManager, msg: str):
    t_inicio = time.time()

    while time.time() - t_inicio < 1.5:
        frame = hud.gerar_frame(dado, vm)
        altura, largura = frame.shape[:2]

        overlay = frame.copy()

        cv2.rectangle(
            overlay,
            (largura // 4, altura // 3),
            (largura * 3 // 4, altura * 2 // 3),
            (10, 10, 20),
            -1,
        )

        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

        cv2.rectangle(
            frame,
            (largura // 4, altura // 3),
            (largura * 3 // 4, altura * 2 // 3),
            (0, 200, 80),
            2,
        )

        cv2.putText(
            frame,
            msg,
            (largura // 4 + 20, altura // 2 + 12),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (0, 220, 80),
            2,
        )

        cv2.imshow("Space Capsule Monitoring", frame)
        cv2.waitKey(50)


def main():
    parser = argparse.ArgumentParser(
        description="Space Capsule Monitoring System"
    )

    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Indice da camera",
    )

    parser.add_argument(
        "--intervalo",
        type=int,
        default=1800,
        help="Intervalo de validacao em segundos",
    )

    parser.add_argument(
        "--porta",
        type=int,
        default=5000,
        help="Porta Flask",
    )

    parser.add_argument(
        "--sem-api",
        action="store_true",
        help="Nao inicia o servidor Flask",
    )

    args = parser.parse_args()

    print("=" * 65)
    print("SPACE CAPSULE MONITORING SYSTEM")
    print(f"Intervalo de validacao: {args.intervalo} segundos")
    print(f"Camera: {args.camera}")
    print(f"Porta API: {args.porta}")
    print("=" * 65)
    print("Teclas: V = validar agora | F = falha sensor | R = reset | Q = sair")
    print("=" * 65)

    sensor = SensorTemperatura(
        temp_base=22.0,
        ruido=0.3,
    )

    vm = ValidacaoManager(
        intervalo_segundos=args.intervalo,
    )

    hud = MonitorHUD(
        largura=1100,
        altura=650,
    )

    if not args.sem_api:
        threading.Thread(
            target=iniciar_servidor,
            kwargs={
                "host": "0.0.0.0",
                "porta": args.porta,
            },
            daemon=True,
        ).start()

    threading.Thread(
        target=_loop_aquisicao,
        args=(sensor, 1.0),
        daemon=True,
    ).start()

    time.sleep(1.2)

    estado = MONITORANDO

    while True:
        if estado == MONITORANDO:
            dado = _ler_dado_atual()
            frame = hud.gerar_frame(dado, vm)

            cv2.imshow("Space Capsule Monitoring", frame)

            tecla = cv2.waitKey(50) & 0xFF

            if tecla in (ord("v"), ord("V")):
                vm.forcar_agora()

            elif tecla in (ord("f"), ord("F")):
                sensor.simular_falha(True)
                sensor.temp_override = None
                print("[MAIN] Falha de sensor ativada.")

            elif tecla in (ord("r"), ord("R")):
                sensor.simular_falha(False)
                sensor.temp_override = None
                print("[MAIN] Sensor resetado.")

            elif tecla in (ord("q"), ord("Q")):
                break

            if vm.deve_validar():
                estado = VALIDANDO

        elif estado == VALIDANDO:
            vm.iniciar_sessao()

            dado = _ler_dado_atual()

            try:
                cv2.destroyWindow("Space Capsule Monitoring")
            except cv2.error:
                pass

            _tela_transicao(
                hud=hud,
                dado=dado,
                vm=vm,
                msg="Abrindo validacao por camera...",
            )

            gesto = executar_validacao(
                indice_camera=args.camera,
                timeout=None,
            )

            if gesto:
                vm.registrar(gesto)

                nova_temperatura = TEMP_GESTO.get(gesto, 22.0)
                sensor.temp_override = nova_temperatura

                print(
                    f"[MAIN] Gesto {gesto} aplicado. "
                    f"Temperatura simulada: {nova_temperatura}°C"
                )

            else:
                vm.cancelar_sessao()
                print("[MAIN] Validacao cancelada ou sem gesto.")

            estado = MONITORANDO

    cv2.destroyAllWindows()
    print("[MAIN] Sistema encerrado.")


if __name__ == "__main__":
    main()