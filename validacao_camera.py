"""
validacao_camera.py
Validação de gestos usando OpenCV + MediaPipe Hands.

Versão leve:
- Não usa pasta models
- Não usa caffemodel pesado
- Não usa OpenPose/Caffe
- Usa MediaPipe Hands, que já possui o modelo embutido na biblioteca

Gestos:
- Indicador levantado -> QUENTE
- Joinha             -> NORMAL
- Paz / V            -> FRIO
"""

from __future__ import annotations

import time
from collections import Counter, deque

import cv2
import numpy as np
import mediapipe as mp


cv2.setUseOptimized(True)
cv2.setNumThreads(2)


TEMP_GESTO = {
    "QUENTE": 31.5,
    "NORMAL": 22.0,
    "FRIO": 15.5,
}

CORES = {
    "QUENTE": (0, 60, 230),
    "NORMAL": (0, 200, 80),
    "FRIO": (200, 100, 0),
    "AGUARDANDO": (120, 120, 120),
}

LABEL = {
    "QUENTE": "INDICADOR  ->  QUENTE  31.5 C",
    "NORMAL": "JOINHA     ->  NORMAL  22.0 C",
    "FRIO": "PEACE/V    ->  FRIO    15.5 C",
}


class DetectorMaoMediaPipe:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_styles = mp.solutions.drawing_styles

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            model_complexity=0,
            min_detection_confidence=0.55,
            min_tracking_confidence=0.55,
        )

    def processar(self, frame_bgr: np.ndarray) -> tuple[str | None, np.ndarray]:
        frame_saida = frame_bgr.copy()

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        resultado = self.hands.process(rgb)
        rgb.flags.writeable = True

        if not resultado.multi_hand_landmarks:
            return None, frame_saida

        hand_landmarks = resultado.multi_hand_landmarks[0]

        self.mp_draw.draw_landmarks(
            frame_saida,
            hand_landmarks,
            self.mp_hands.HAND_CONNECTIONS,
            self.mp_styles.get_default_hand_landmarks_style(),
            self.mp_styles.get_default_hand_connections_style(),
        )

        gesto = self._classificar(hand_landmarks)

        return gesto, frame_saida

    def _classificar(self, hand_landmarks) -> str | None:
        lm = hand_landmarks.landmark

        indicador = self._dedo_levantado(lm, ponta=8, pip=6, mcp=5)
        medio = self._dedo_levantado(lm, ponta=12, pip=10, mcp=9)
        anelar = self._dedo_levantado(lm, ponta=16, pip=14, mcp=13)
        minimo = self._dedo_levantado(lm, ponta=20, pip=18, mcp=17)
        polegar = self._polegar_para_cima(lm)

        # Joinha: polegar para cima e os outros dedos fechados
        if polegar and not indicador and not medio and not anelar and not minimo:
            return "NORMAL"

        # Indicador: somente indicador levantado
        if indicador and not medio and not anelar and not minimo:
            return "QUENTE"

        # Paz/V: indicador + médio levantados
        if indicador and medio and not anelar and not minimo:
            return "FRIO"

        return None

    @staticmethod
    def _dedo_levantado(lm, ponta: int, pip: int, mcp: int) -> bool:
        """
        Detecta se um dedo está levantado com base nos landmarks do MediaPipe.

        No OpenCV/imagem:
        - menor valor de Y = ponto mais alto
        """

        margem = 0.025

        ponta_acima_pip = lm[ponta].y < lm[pip].y - margem
        ponta_acima_mcp = lm[ponta].y < lm[mcp].y - margem

        dist_ponta_punho = np.linalg.norm(
            np.array([lm[ponta].x, lm[ponta].y]) -
            np.array([lm[0].x, lm[0].y])
        )

        dist_pip_punho = np.linalg.norm(
            np.array([lm[pip].x, lm[pip].y]) -
            np.array([lm[0].x, lm[0].y])
        )

        dedo_estendido = dist_ponta_punho > dist_pip_punho * 1.05

        return bool(ponta_acima_pip and ponta_acima_mcp and dedo_estendido)

    @staticmethod
    def _polegar_para_cima(lm) -> bool:
        ponta = lm[4]
        junta = lm[3]
        base = lm[1]

        ponta_acima = ponta.y < junta.y - 0.02

        deslocamento_vertical = abs(ponta.y - base.y)
        deslocamento_horizontal = abs(ponta.x - base.x)

        formato_vertical = deslocamento_vertical > deslocamento_horizontal * 0.65

        return bool(ponta_acima and formato_vertical)


def _desenhar_interface(
    frame: np.ndarray,
    gesto: str | None,
    validacao_iniciada: bool,
    votos: deque[str],
) -> np.ndarray:
    saida = frame.copy()
    altura, largura = saida.shape[:2]

    cor = CORES.get(gesto or "AGUARDANDO", CORES["AGUARDANDO"])

    cv2.rectangle(saida, (0, 0), (largura, 110), (10, 10, 20), -1)

    cv2.putText(
        saida,
        "VALIDACAO DE MAO - OpenCV + MediaPipe Hands",
        (15, 34),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.72,
        (0, 220, 80),
        2,
    )

    cv2.putText(
        saida,
        "Sem pasta models | Sem Caffe | Sem arquivo de 147 MB",
        (15, 68),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.52,
        (190, 190, 190),
        1,
    )

    cv2.putText(
        saida,
        "Indicador = QUENTE | Joinha = NORMAL | Paz/V = FRIO",
        (15, 95),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (140, 140, 140),
        1,
    )

    if not validacao_iniciada:
        msg = "POSICIONE A MAO E APERTE ESPACO"
        cor_msg = (0, 200, 220)
    else:
        msg = "VALIDANDO... MANTENHA O GESTO PARADO"
        cor_msg = cor

    cv2.rectangle(saida, (0, altura - 110), (largura, altura), (10, 10, 20), -1)

    cv2.putText(
        saida,
        msg,
        (25, altura - 68),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.72,
        cor_msg,
        2,
    )

    texto_gesto = gesto if gesto else "AGUARDANDO"
    texto_label = LABEL.get(gesto, "Nenhum gesto reconhecido")

    cv2.putText(
        saida,
        f"Gesto atual: {texto_gesto} | votos: {len(votos)}",
        (25, altura - 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.58,
        cor,
        2,
    )

    cv2.putText(
        saida,
        texto_label,
        (largura - 450, altura - 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        cor,
        1,
    )

    return saida


def _tela_confirmacao(frame: np.ndarray, gesto: str) -> np.ndarray:
    saida = frame.copy()
    altura, largura = saida.shape[:2]

    cor = CORES.get(gesto, CORES["NORMAL"])
    texto = LABEL.get(gesto, gesto)

    overlay = saida.copy()
    cv2.rectangle(overlay, (0, 0), (largura, altura), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.45, saida, 0.55, 0, saida)

    cv2.rectangle(
        saida,
        (largura // 2 - 310, altura // 2 - 105),
        (largura // 2 + 310, altura // 2 + 105),
        (20, 20, 30),
        -1,
    )

    cv2.rectangle(
        saida,
        (largura // 2 - 310, altura // 2 - 105),
        (largura // 2 + 310, altura // 2 + 105),
        cor,
        3,
    )

    cv2.putText(
        saida,
        "GESTO CONFIRMADO",
        (largura // 2 - 195, altura // 2 - 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.85,
        cor,
        2,
    )

    cv2.putText(
        saida,
        texto,
        (largura // 2 - 245, altura // 2 + 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        cor,
        2,
    )

    return saida


def executar_validacao(
    indice_camera: int = 0,
    timeout: int | None = None,
) -> str | None:
    """
    Função chamada pelo main.py.

    O parâmetro timeout foi mantido apenas para compatibilidade.
    A validação começa somente quando o usuário aperta ESPAÇO.
    """

    cap = cv2.VideoCapture(indice_camera)

    if not cap.isOpened():
        print(f"[CAMERA] Nao foi possivel abrir a camera {indice_camera}")
        return None

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 15)

    detector = DetectorMaoMediaPipe()

    votos: deque[str] = deque(maxlen=14)
    votos_minimos = 8

    validacao_iniciada = False
    confirmado = None
    tempo_confirmado = None

    print("[CAMERA] Validacao com MediaPipe Hands iniciada.")
    print("[CAMERA] Posicione a mao na camera.")
    print("[CAMERA] Aperte ESPACO para iniciar.")
    print("[CAMERA] Q/ESC cancela.")

    while True:
        ok, frame = cap.read()

        if not ok:
            print("[CAMERA] Falha ao ler frame.")
            break

        frame = cv2.flip(frame, 1)

        gesto, frame_processado = detector.processar(frame)

        if validacao_iniciada and gesto in TEMP_GESTO:
            votos.append(gesto)

        elif validacao_iniciada and len(votos) > 0:
            votos.popleft()

        if confirmado is None and validacao_iniciada and len(votos) >= votos_minimos:
            contagem = Counter(votos)
            gesto_mais_comum, total = contagem.most_common(1)[0]
            confianca = total / len(votos)

            if total >= votos_minimos and confianca >= 0.72:
                confirmado = gesto_mais_comum
                tempo_confirmado = time.time()
                print(f"[CAMERA] Gesto confirmado: {confirmado}")

        tela = _desenhar_interface(
            frame=frame_processado,
            gesto=gesto,
            validacao_iniciada=validacao_iniciada,
            votos=votos,
        )

        if confirmado is not None:
            tela = _tela_confirmacao(tela, confirmado)
            cv2.imshow("Validacao de Temperatura", tela)

            if time.time() - tempo_confirmado >= 1.8:
                break

        else:
            cv2.imshow("Validacao de Temperatura", tela)

        tecla = cv2.waitKey(1) & 0xFF

        if tecla in (ord("q"), ord("Q"), 27):
            confirmado = None
            break

        if tecla == 32:
            validacao_iniciada = True
            votos.clear()
            print("[CAMERA] Validacao iniciada. Mantenha o gesto parado.")

    cap.release()

    try:
        cv2.destroyWindow("Validacao de Temperatura")
    except cv2.error:
        pass

    return confirmado