"""
monitor_hud.py
HUD de monitoramento contínuo da cápsula espacial.
Exibe sensor, histórico, status de validação e countdown.
"""

import cv2
import numpy as np
import time
import math
from collections import deque


CORES_STATUS = {
    "ALERTA_ALTO":  (0,  50, 220),
    "ALERTA_BAIXO": (180, 80,  0),
    "AVISO":        (0, 200, 200),
    "NORMAL":       (0, 200,  80),
    "FALHA":        (0,   0, 200),
    "QUENTE":       (0,  50, 220),
    "FRIO":         (180, 80,  0),
    "AGUARDANDO":   (120,120,120),
}


class MonitorHUD:
    """Gera frames do painel de monitoramento principal."""

    def __init__(self, largura=1100, altura=650):
        self.W  = largura
        self.H  = altura
        self._t0 = time.time()
        self._frames = 0
        self._hist_temp: deque = deque(maxlen=200)

    def gerar_frame(self, dado_sensor: dict, validacao_mgr) -> np.ndarray:
        """
        Parâmetros
        ----------
        dado_sensor   : dict com 'temperatura', 'status', 'leitura_num'
        validacao_mgr : instância de ValidacaoManager
        """
        self._frames += 1
        temp   = dado_sensor.get("temperatura")
        status = dado_sensor.get("status", "NORMAL")

        if temp is not None:
            self._hist_temp.append(temp)

        # Base escura
        frame = np.zeros((self.H, self.W, 3), dtype=np.uint8)
        for i in range(self.H):
            v = int(6 + 10 * i / self.H)
            frame[i] = (v, v, v + 5)

        # Componentes
        self._header(frame, validacao_mgr)
        self._termico(frame, temp or 22.0, status)
        self._painel_status(frame, temp, status, dado_sensor)
        self._countdown(frame, validacao_mgr)
        self._historico_validacoes(frame, validacao_mgr)
        self._grafico(frame)
        self._alertas(frame, status)
        self._rodape(frame)

        return frame

    # ── Header ───────────────────────────────────────────────────────
    def _header(self, f, vm):
        cv2.rectangle(f, (0, 0), (self.W, 32), (8, 20, 12), -1)
        t = time.time() - self._t0
        h, m, s = int(t//3600), int((t%3600)//60), int(t%60)
        cv2.putText(f, "SPACE CAPSULE MONITORING SYSTEM  v2.0",
                    (12, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0,220,90), 1)
        cv2.putText(f, f"MISSION  {h:02d}:{m:02d}:{s:02d}   FRAME {self._frames:05d}",
                    (self.W - 340, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0,160,60), 1)

    # ── Câmera térmica simulada ────────────────────────────────────
    def _termico(self, f, temp, status):
        W2, H2 = self.W // 2 - 12, self.H // 2 - 44
        canvas = np.zeros((H2, W2, 3), dtype=np.uint8)
        t  = time.time() - self._t0
        tn = float(np.clip((temp - 18) / 14, 0, 1))

        for i in range(10):
            cx = int(W2//2 + np.sin(t*0.25+i*0.9)*W2*0.38)
            cy = int(H2//2 + np.cos(t*0.18+i*0.7)*H2*0.35)
            inten = 0.4 + 0.6*abs(np.sin(t*0.4+i))
            raio  = int((18+16*inten)*(0.7+0.3*tn))
            r = int(255*tn*inten); b = int(255*(1-tn)*inten)
            cv2.circle(canvas, (cx, cy), raio, (b, int(80*inten), r), -1)

        canvas = cv2.GaussianBlur(canvas, (23,23), 0)
        gray   = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
        termi  = cv2.applyColorMap(gray, cv2.COLORMAP_JET)

        # Detecção de contornos
        _, thresh = cv2.threshold(gray, 130, 255, cv2.THRESH_BINARY)
        cnts, _   = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        regioes   = [c for c in cnts if cv2.contourArea(c) > 80]
        cv2.drawContours(termi, regioes, -1, (0,255,255), 1)
        for c in regioes[:4]:
            x,y,w,h = cv2.boundingRect(c)
            cv2.rectangle(termi, (x,y),(x+w,y+h),(255,255,0),1)

        f[36:36+H2, 8:8+W2] = termi
        cv2.rectangle(f, (8,36), (8+W2,36+H2), (0,180,90), 2)
        cv2.putText(f, "THERMAL CAM [SIM]", (12,52),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0,220,80), 1)
        cv2.putText(f, f"Regioes: {len(regioes)}", (12,36+H2-8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0,220,220), 1)

    # ── Painel de status ─────────────────────────────────────────────
    def _painel_status(self, f, temp, status, dado):
        xp, yp = self.W//2+10, 40
        cor = CORES_STATUS.get(status, (0,200,80))

        cv2.putText(f, "CAPSULE STATUS",
                    (xp, yp+22), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0,220,80), 2)
        cv2.line(f, (xp, yp+30), (self.W-8, yp+30), (0,160,60), 1)

        cv2.putText(f, "TEMPERATURA",
                    (xp, yp+58), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (160,160,160), 1)
        txt = f"{temp:.1f} C" if temp is not None else "FALHA"
        cv2.putText(f, txt,
                    (xp, yp+92), cv2.FONT_HERSHEY_SIMPLEX, 1.3, cor, 2)

        if temp:
            self._barra(f, xp, yp+102, temp, 15, 35, cor)

        cv2.putText(f, f"STATUS: {status}",
                    (xp, yp+148), cv2.FONT_HERSHEY_SIMPLEX, 0.5, cor, 1)
        cv2.putText(f, f"LEITURA #{dado.get('leitura_num',0):04d}",
                    (xp, yp+172), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (120,120,120), 1)

        # Gauge circular
        self._gauge(f, self.W-110, 130, 70, temp, status)

    # ── Countdown para próxima validação ────────────────────────────
    def _countdown(self, f, vm):
        xp, yp = self.W//2+10, 240
        cv2.line(f, (xp, yp), (self.W-8, yp), (30,60,40), 1)

        prox = vm.formato_countdown()
        seg  = vm.segundos_para_proxima()
        cor_cd = (0,220,80) if seg > 120 else (0,60,220) if seg > 30 else (0,30,180)

        cv2.putText(f, "PROXIMA VALIDACAO",
                    (xp, yp+24), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (140,140,140), 1)
        cv2.putText(f, prox,
                    (xp, yp+68), cv2.FONT_HERSHEY_DUPLEX, 1.6, cor_cd, 2)

        # Barra de progresso do intervalo
        total = vm.intervalo
        prop  = 1.0 - min(seg / total, 1.0)
        bw    = self.W - xp - 10
        cv2.rectangle(f, (xp, yp+80), (xp+bw, yp+96), (30,30,40), -1)
        cv2.rectangle(f, (xp, yp+80), (xp+int(bw*prop), yp+96), cor_cd, -1)
        cv2.rectangle(f, (xp, yp+80), (xp+bw, yp+96), (60,60,70), 1)

        # Tecla de atalho
        cv2.putText(f, "[V] Validar agora   [F] Simular falha   [Q] Sair",
                    (xp, yp+116), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (80,160,80), 1)

    # ── Histórico de validações ──────────────────────────────────────
    def _historico_validacoes(self, f, vm):
        xp, yp = self.W//2+10, 380
        cv2.line(f, (xp, yp), (self.W-8, yp), (30,60,40), 1)
        cv2.putText(f, "HISTORICO DE VALIDACOES",
                    (xp, yp+20), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (140,140,140), 1)

        hist = vm.historico[-5:][::-1]   # últimas 5, mais recente primeiro
        if not hist:
            cv2.putText(f, "Nenhuma validacao registrada",
                        (xp+4, yp+46), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (80,80,80), 1)
            return

        for i, reg in enumerate(hist):
            y = yp + 46 + i * 26
            cor = CORES_STATUS.get(reg.gesto, (120,120,120))
            cv2.putText(f, f"{reg.hora_fmt}  {reg.gesto:<8}  {reg.temperatura:.1f}C",
                        (xp+4, y), cv2.FONT_HERSHEY_SIMPLEX, 0.42, cor, 1)

    # ── Gráfico histórico de temperatura ────────────────────────────
    def _grafico(self):
        pass  # chamado externamente

    def _grafico(self, f):
        dados = list(self._hist_temp)
        if len(dados) < 2:
            return
        xg, yg = 8, self.H - 158
        wg, hg = self.W//2 - 16, 118
        mn, mx  = 15.0, 35.0

        cv2.rectangle(f,(xg,yg),(xg+wg,yg+hg),(12,12,20),-1)
        cv2.rectangle(f,(xg,yg),(xg+wg,yg+hg),(0,160,70),1)
        cv2.putText(f,"HISTORICO DE TEMPERATURA",(xg+4,yg-6),
                    cv2.FONT_HERSHEY_SIMPLEX,0.38,(0,160,70),1)

        dados = dados[-wg:]
        n = len(dados)
        for i in range(1, n):
            x1 = xg+int((i-1)*wg/n); x2 = xg+int(i*wg/n)
            y1 = yg+hg-int(np.clip((dados[i-1]-mn)/(mx-mn),0,1)*hg)
            y2 = yg+hg-int(np.clip((dados[i]  -mn)/(mx-mn),0,1)*hg)
            tn = np.clip((dados[i]-mn)/(mx-mn),0,1)
            cv2.line(f,(x1,y1),(x2,y2),(int(255*(1-tn)),100,int(255*tn)),2)

        # Linha ideal
        yi = yg+hg-int((22-mn)/(mx-mn)*hg)
        cv2.line(f,(xg,yi),(xg+wg,yi),(0,180,60),1)

    # ── Alertas ──────────────────────────────────────────────────────
    def _alertas(self, f, status):
        if status not in ("ALERTA_ALTO","ALERTA_BAIXO"):
            return
        t = time.time()-self._t0
        if int(t*2)%2==0:
            ov = f.copy()
            cv2.rectangle(ov,(0,0),(self.W,self.H),(0,0,160),16)
            cv2.addWeighted(ov,0.4,f,0.6,0,f)
        msg = ("!! ALERTA: TEMPERATURA ALTA !!" if status=="ALERTA_ALTO"
               else "!! ALERTA: TEMPERATURA BAIXA !!")
        cv2.putText(f, msg, (self.W//2-210, self.H-16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0,0,240), 2)

    # ── Rodapé ───────────────────────────────────────────────────────
    def _rodape(self, f):
        cv2.rectangle(f,(0,self.H-20),(self.W,self.H),(8,20,12),-1)
        cv2.putText(f,"FIAP | Engenharia de Software | Global Solution 2026",
                    (self.W//2-240,self.H-6),cv2.FONT_HERSHEY_SIMPLEX,
                    0.38,(0,100,50),1)

    # ── Helpers ──────────────────────────────────────────────────────
    @staticmethod
    def _barra(f,x,y,val,vmin,vmax,cor,w=180,h=16):
        p = float(np.clip((val-vmin)/(vmax-vmin),0,1))
        cv2.rectangle(f,(x,y),(x+w,y+h),(40,40,50),-1)
        cv2.rectangle(f,(x,y),(x+w,y+h),(70,70,80),1)
        if p>0: cv2.rectangle(f,(x,y),(x+int(w*p),y+h),cor,-1)
        cv2.putText(f,f"{vmin}C",(x,y+h+12),cv2.FONT_HERSHEY_SIMPLEX,0.3,(90,90,90),1)
        cv2.putText(f,f"{vmax}C",(x+w-20,y+h+12),cv2.FONT_HERSHEY_SIMPLEX,0.3,(90,90,90),1)

    @staticmethod
    def _gauge(f,cx,cy,r,temp,status):
        cor = CORES_STATUS.get(status,(0,200,80))
        span = 240
        ini  = 210
        for a in range(ini,ini-span,-1):
            rad=math.radians(a)
            x=int(cx+r*math.cos(rad)); y=int(cy-r*math.sin(rad))
            cv2.circle(f,(x,y),2,(35,35,35),-1)
        if temp:
            prop  = float(np.clip((temp-15)/(35-15),0,1))
            graus = int(span*prop)
            for a in range(ini,ini-graus,-1):
                rad=math.radians(a)
                x=int(cx+r*math.cos(rad)); y=int(cy-r*math.sin(rad))
                cv2.circle(f,(x,y),3,cor,-1)
        cv2.circle(f,(cx,cy),r-16,(18,18,24),-1)
        cv2.circle(f,(cx,cy),r-16,(40,40,50),1)
        txt=f"{temp:.1f}" if temp else "--"
        cv2.putText(f,txt,(cx-26,cy+8),cv2.FONT_HERSHEY_SIMPLEX,0.72,cor,2)
        cv2.putText(f,"C",(cx+22,cy+8),cv2.FONT_HERSHEY_SIMPLEX,0.42,(120,120,120),1)
