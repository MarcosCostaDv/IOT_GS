"""
vision_system.py
----------------
Sistema de Visão Computacional para monitoramento da cápsula espacial.
Utiliza OpenCV para:
  - Gerar mapa térmico simulado (câmera térmica)
  - Detectar contornos de regiões quentes (visão computacional)
  - Exibir gauge de temperatura, gráfico histórico e alertas visuais
"""

import cv2
import numpy as np
import time
from typing import Optional


class SistemaVisaoComputacional:
    """
    Exibe janela OpenCV com visualização em tempo real da cápsula.

    Parâmetros
    ----------
    largura, altura : int
        Dimensões da janela em pixels.
    """

    def __init__(self, largura: int = 960, altura: int = 600):
        self.largura   = largura
        self.altura    = altura
        self.historico = []          # histórico de temperaturas
        self.max_hist  = 120
        self._t0       = time.time()
        self._frames   = 0

    # ==================================================================
    # Loop principal
    # ==================================================================

    def executar(self, sensor):
        """
        Loop de captura / processamento / exibição.
        Pressione 'q' para sair, 'f' para simular falha, 'r' para resetar.
        """
        print("[VISAO] Sistema iniciado – pressione 'q' para sair, "
              "'f' falha, 'r' reset")

        while True:
            dados = sensor.ler()
            frame = self._processar_frame(dados)
            cv2.imshow("Space Capsule Vision System", frame)

            tecla = cv2.waitKey(100) & 0xFF
            if tecla == ord('q'):
                break
            elif tecla == ord('f'):
                sensor.simular_falha(True)
                print("[VISAO] Falha de sensor ativada!")
            elif tecla == ord('r'):
                sensor.simular_falha(False)
                print("[VISAO] Sensor resetado!")

        cv2.destroyAllWindows()
        print("[VISAO] Sistema encerrado.")

    # ==================================================================
    # Montagem do frame
    # ==================================================================

    def _processar_frame(self, dados: dict) -> np.ndarray:
        """Gera o frame completo a partir dos dados do sensor."""
        self._frames += 1
        temp   = dados.get("temperatura")
        status = dados.get("status", "NORMAL")

        # Atualiza histórico
        if temp is not None:
            self.historico.append(temp)
            if len(self.historico) > self.max_hist:
                self.historico.pop(0)

        # Base escura (estilo espacial)
        frame = np.zeros((self.altura, self.largura, 3), dtype=np.uint8)
        for i in range(self.altura):
            v = int(8 + 12 * i / self.altura)
            frame[i] = (v, v, v + 6)

        # --- Câmera térmica (quadrante superior esquerdo) ---
        self._inserir_termico(frame, temp or 22.0)

        # --- Painel de status (lado direito) ---
        self._painel_status(frame, dados)

        # --- Gauge circular de temperatura ---
        self._gauge_circular(frame, temp, status)

        # --- Gráfico histórico (rodapé esquerdo) ---
        self._grafico_historico(frame)

        # --- Alertas visuais ---
        self._alerta(frame, status)

        # --- Barra de titulo ---
        elapsed = time.time() - self._t0
        h, m, s = int(elapsed // 3600), int((elapsed % 3600) // 60), int(elapsed % 60)
        cv2.rectangle(frame, (0, 0), (self.largura, 28), (0, 50, 30), -1)
        cv2.putText(frame, "SPACE CAPSULE MONITORING SYSTEM v1.0",
                    (10, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 100), 1)
        cv2.putText(frame, f"MISSION  {h:02d}:{m:02d}:{s:02d}   FRAME {self._frames:05d}",
                    (self.largura - 310, 19),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 180, 80), 1)

        return frame

    # ==================================================================
    # Câmera térmica
    # ==================================================================

    def _inserir_termico(self, frame: np.ndarray, temp: float):
        """Gera e insere o mapa térmico simulado no frame."""
        W, H = self.largura // 2 - 15, self.altura // 2 - 45

        # Cria canvas com fontes de calor animadas
        canvas = np.zeros((H, W, 3), dtype=np.uint8)
        t = time.time() - self._t0
        temp_norm = float(np.clip((temp - 18) / 14, 0, 1))

        for i in range(10):
            cx = int(W // 2 + np.sin(t * 0.25 + i * 0.9) * W * 0.38)
            cy = int(H // 2 + np.cos(t * 0.18 + i * 0.7) * H * 0.35)
            inten = 0.4 + 0.6 * abs(np.sin(t * 0.4 + i))
            raio  = int((20 + 18 * inten) * (0.7 + 0.3 * temp_norm))
            r = int(255 * temp_norm * inten)
            b = int(255 * (1 - temp_norm) * inten)
            cv2.circle(canvas, (cx, cy), raio, (b, int(80 * inten), r), -1)

        canvas = cv2.GaussianBlur(canvas, (23, 23), 0)
        gray   = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
        termico = cv2.applyColorMap(gray, cv2.COLORMAP_JET)

        # ---- Visão computacional: detecção de contornos ----
        _, thresh = cv2.threshold(gray, 130, 255, cv2.THRESH_BINARY)
        contornos, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        regioes = [c for c in contornos if cv2.contourArea(c) > 80]
        cv2.drawContours(termico, regioes, -1, (0, 255, 255), 1)

        # Bounding boxes das regiões quentes
        for cnt in regioes[:4]:
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(termico, (x, y), (x + w, y + h), (255, 255, 0), 1)

        # Cola no frame
        frame[32:32 + H, 8:8 + W] = termico

        # Bordas e labels
        cv2.rectangle(frame, (8, 32), (8 + W, 32 + H), (0, 200, 100), 2)
        cv2.putText(frame, "THERMAL CAM  [SIMULADO]",
                    (12, 47), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 100), 1)
        cv2.putText(frame, f"Regioes quentes: {len(regioes)}",
                    (12, 32 + H - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 255, 255), 1)

    # ==================================================================
    # Painel de status (texto)
    # ==================================================================

    def _painel_status(self, frame: np.ndarray, dados: dict):
        """Painel de texto com informações de status."""
        xp  = self.largura // 2 + 10
        yp  = 38
        esp = 30          # espaçamento entre linhas

        temp   = dados.get("temperatura")
        status = dados.get("status", "N/A")
        leitura = dados.get("leitura_num", 0)

        # Título
        cv2.putText(frame, "CAPSULE STATUS",
                    (xp, yp + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 100), 2)
        cv2.line(frame, (xp, yp + 28), (self.largura - 10, yp + 28), (0, 200, 80), 1)

        # Temperatura
        cor = self._cor_status(status)
        cv2.putText(frame, "TEMPERATURA",
                    (xp, yp + 55), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)
        texto_temp = f"{temp:.1f} C" if temp is not None else "FALHA"
        cv2.putText(frame, texto_temp,
                    (xp, yp + 85), cv2.FONT_HERSHEY_SIMPLEX, 1.3, cor, 2)

        # Barra linear
        if temp is not None:
            self._barra_linear(frame, xp, yp + 95, temp, 15, 35, cor)

        # Status badge
        cv2.putText(frame, f"STATUS : {status}",
                    (xp, yp + 145), cv2.FONT_HERSHEY_SIMPLEX, 0.5, cor, 1)

        # Leituras
        cv2.putText(frame, f"LEITURA: #{leitura}",
                    (xp, yp + 175), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 150, 150), 1)

        # Limites de referência
        linhas_ref = [
            ("ALERTA ALTO  > 28 C", (0, 80, 200)),
            ("AVISO        > 25 C", (0, 200, 200)),
            ("IDEAL        22 C",   (0, 200, 80)),
            ("ALERTA BAIXO < 18 C", (80, 120, 255)),
        ]
        cv2.putText(frame, "LIMITES DE REFERENCIA",
                    (xp, yp + 215), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (120, 120, 120), 1)
        for idx, (txt, c) in enumerate(linhas_ref):
            cv2.putText(frame, txt,
                        (xp + 5, yp + 235 + idx * 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, c, 1)

    # ==================================================================
    # Gauge circular
    # ==================================================================

    def _gauge_circular(self, frame: np.ndarray,
                         temp: Optional[float], status: str):
        """Gauge circular de temperatura posicionado no centro inferior direito."""
        cx = int(self.largura * 0.78)
        cy = int(self.altura * 0.72)
        raio = 65

        angulo_ini = 210        # graus (OpenCV: sentido horário)
        angulo_fim = -30
        span = 240              # amplitude total do arco

        # Fundo do arco
        for a in range(int(angulo_ini), int(angulo_ini - span), -1):
            rad = math.radians(a)
            x1 = int(cx + raio * math.cos(rad))
            y1 = int(cy - raio * math.sin(rad))
            cv2.circle(frame, (x1, y1), 2, (40, 40, 40), -1)

        # Arco preenchido baseado na temperatura
        if temp is not None:
            prop  = np.clip((temp - 15) / (35 - 15), 0, 1)
            graus = int(span * prop)
            cor   = self._cor_status(status)
            for a in range(int(angulo_ini), int(angulo_ini - graus), -1):
                rad = math.radians(a)
                x1 = int(cx + raio * math.cos(rad))
                y1 = int(cy - raio * math.sin(rad))
                cv2.circle(frame, (x1, y1), 3, cor, -1)

        # Centro
        cv2.circle(frame, (cx, cy), raio - 15, (20, 20, 25), -1)
        cv2.circle(frame, (cx, cy), raio - 15, (40, 40, 50), 1)

        texto_c = f"{temp:.1f}" if temp is not None else "--"
        cv2.putText(frame, texto_c,
                    (cx - 28, cy + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.75,
                    self._cor_status(status), 2)
        cv2.putText(frame, "TEMP °C",
                    (cx - 28, cy + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.35,
                    (150, 150, 150), 1)

    # ==================================================================
    # Gráfico histórico
    # ==================================================================

    def _grafico_historico(self, frame: np.ndarray):
        if len(self.historico) < 2:
            return

        xg, yg  = 10, self.altura - 155
        wg, hg  = self.largura // 2 - 20, 120
        min_t, max_t = 15.0, 35.0

        # Fundo
        cv2.rectangle(frame, (xg, yg), (xg + wg, yg + hg), (15, 15, 22), -1)
        cv2.rectangle(frame, (xg, yg), (xg + wg, yg + hg), (0, 180, 80), 1)
        cv2.putText(frame, "HISTORICO DE TEMPERATURA",
                    (xg + 4, yg - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 180, 80), 1)

        # Grade
        for i in range(1, 4):
            y_gr = yg + int(hg * i / 4)
            cv2.line(frame, (xg, y_gr), (xg + wg, y_gr), (35, 35, 50), 1)
            val  = max_t - (max_t - min_t) * i / 4
            cv2.putText(frame, f"{val:.0f}", (xg - 18, y_gr + 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.3, (100, 100, 100), 1)

        # Linha ideal
        y_ideal = yg + hg - int((22 - min_t) / (max_t - min_t) * hg)
        cv2.line(frame, (xg, y_ideal), (xg + wg, y_ideal), (0, 200, 80), 1)

        # Curva
        dados = self.historico[-wg:]
        n     = len(dados)
        for i in range(1, n):
            x1 = xg + int((i - 1) * wg / n)
            x2 = xg + int(i * wg / n)
            y1 = yg + hg - int(np.clip((dados[i-1] - min_t) / (max_t - min_t), 0, 1) * hg)
            y2 = yg + hg - int(np.clip((dados[i]   - min_t) / (max_t - min_t), 0, 1) * hg)
            tn = np.clip((dados[i] - min_t) / (max_t - min_t), 0, 1)
            r  = int(255 * tn)
            b  = int(255 * (1 - tn))
            cv2.line(frame, (x1, y1), (x2, y2), (b, 100, r), 2)

    # ==================================================================
    # Alertas
    # ==================================================================

    def _alerta(self, frame: np.ndarray, status: str):
        if status not in ("ALERTA_ALTO", "ALERTA_BAIXO"):
            return
        t = time.time() - self._t0
        if int(t * 2) % 2 == 0:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (self.largura, self.altura),
                          (0, 0, 150), 18)
            cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)
        msg = ("!! ALERTA: TEMPERATURA ALTA !!"
               if status == "ALERTA_ALTO"
               else "!! ALERTA: TEMPERATURA BAIXA !!")
        cv2.putText(frame, msg,
                    (self.largura // 2 - 215, self.altura - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)

    # ==================================================================
    # Helpers
    # ==================================================================

    @staticmethod
    def _cor_status(status: str) -> tuple:
        return {
            "ALERTA_ALTO":  (0, 60, 230),
            "ALERTA_BAIXO": (180, 100, 0),
            "AVISO":        (0, 220, 220),
            "FALHA":        (0, 0, 200),
        }.get(status, (0, 220, 80))

    @staticmethod
    def _barra_linear(frame: np.ndarray, x: int, y: int,
                       valor: float, vmin: float, vmax: float, cor: tuple):
        W, H = 160, 18
        prop = float(np.clip((valor - vmin) / (vmax - vmin), 0, 1))
        cv2.rectangle(frame, (x, y), (x + W, y + H), (45, 45, 45), -1)
        cv2.rectangle(frame, (x, y), (x + W, y + H), (80, 80, 80), 1)
        if prop > 0:
            cv2.rectangle(frame, (x, y), (x + int(W * prop), y + H), cor, -1)
        cv2.putText(frame, f"{vmin:.0f}C",
                    (x, y + H + 13), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (120, 120, 120), 1)
        cv2.putText(frame, f"{vmax:.0f}C",
                    (x + W - 22, y + H + 13), cv2.FONT_HERSHEY_SIMPLEX, 0.32,
                    (120, 120, 120), 1)


# Importação local para usar math no gauge circular
import math
