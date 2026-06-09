# 🚀 NextSpace — Space Capsule Monitoring System

> Sistema de monitoramento em tempo real para cápsulas espaciais, combinando visão computacional, IoT e dashboards interativos.

---

## 👥 Equipe

| Nome | RM |
|---|---|
| Andre Queiroz | RM554503 |
| Marcos Vinicius Costa | RM555490 |
| Paulo Poças | RM556080 |
| Rafael Bocchi | RM557603 |
| Rafael Oliveira | RM554736 |

**Curso:** Engenharia de Software — FIAP  
**Global Solution 2026.1 — IoT**

---

## 📋 Sobre o Projeto

O **NextSpace** é um sistema de monitoramento de cápsulas espaciais que simula a leitura de sensores de temperatura e permite o controle de parâmetros via gestos das mãos, processados por visão computacional. Os dados são expostos por uma API REST e visualizados em um dashboard Node-RED em tempo real.

---

## 🛠️ Tecnologias

| Camada | Tecnologia |
|---|---|
| Visão Computacional | OpenCV + MediaPipe Hands |
| Simulação de Sensor | Python (NumPy, seno + ruído gaussiano) |
| API REST | Flask |
| Dashboard | Node-RED |
| Geração de Relatórios | ReportLab (PDF) |

---

## 🏗️ Arquitetura

```
Câmera (Webcam)
      │
      ▼
MediaPipe Hands ──► Reconhecimento de Gestos
      │                      │
      │              ┌───────┴──────────┐
      │              │  Gesto → Temp.   │
      │              │  ☝ QUENTE 31.5°C │
      │              │  👍 NORMAL 22.0°C│
      │              │  ✌ FRIO   15.5°C │
      │              └───────┬──────────┘
      │                      │
      ▼                      ▼
SensorTemperatura ◄──── Setpoint Externo
(simulação senoidal + ruído gaussiano)
      │
      ▼
Flask REST API
      │
      ├── GET /api/temperatura  → leitura atual
      ├── GET /api/historico    → histórico JSON
      ├── GET /api/status       → classificação
      └── GET /api/health       → saúde da API
      │
      ▼
Node-RED Dashboard
(gauge, chart, LED de status, texto)
```

---

## 🤚 Gestos Suportados

| Gesto | Ação | Temperatura Alvo |
|---|---|---|
| ☝️ Indicador | QUENTE | 31.5 °C |
| 👍 Joinha | NORMAL | 22.0 °C |
| ✌️ Paz | FRIO | 15.5 °C |

> O sistema usa um sistema de votação por deque com confiança mínima de 72% antes de aplicar o gesto.

---

## ⚠️ Classificação de Status

| Status | Faixa |
|---|---|
| `NORMAL` | 18 °C – 26 °C |
| `AVISO` | 26 °C – 30 °C ou 15 °C – 18 °C |
| `ALERTA_ALTO` | > 30 °C |
| `ALERTA_BAIXO` | < 15 °C |
| `FALHA` | Sensor sem leitura |

---

## ⚙️ Instalação e Execução

### Pré-requisitos

- Python 3.9+
- Node-RED instalado globalmente (`npm install -g node-red`)
- Webcam conectada

### 1. Clonar o repositório

```bash
git clone https://github.com/MarcosCostaDv/IOT_GS.git
cd IOT_GS
```

### 2. Criar ambiente virtual (recomendado)

```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Instalar dependências Python

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
flask
opencv-python
mediapipe
numpy
reportlab
```

### 4. Iniciar a API Flask

```bash
python app.py
```

A API ficará disponível em `http://localhost:5000`.

### 5. Iniciar o Node-RED

```bash
node-red
```

Acesse `http://localhost:1880`, importe o flow do arquivo `flows.json` e faça o deploy.

### 6. Dashboard

Acesse o dashboard em `http://localhost:1880/ui`.

---

## 📡 Endpoints da API

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/temperatura` | Temperatura atual + status |
| GET | `/api/historico` | Histórico de leituras (JSON) |
| GET | `/api/status` | Classificação atual |
| GET | `/api/health` | Saúde da API |

**Exemplo de resposta `/api/temperatura`:**
```json
{
  "temperatura": 22.4,
  "status": "NORMAL",
  "timestamp": "2026-06-08T10:32:00"
}
```

---

## 📁 Estrutura do Projeto

```
IOT_GS/
├── app.py                  # Aplicação principal Flask
├── sensor_temperatura.py   # Simulação do sensor (senoidal + ruído)
├── gesture_control.py      # Reconhecimento de gestos MediaPipe
├── flows.json              # Flow Node-RED
├── requirements.txt        # Dependências Python
├── gerar_relatorio.py      # Geração de relatório PDF
└── README.md
```

---

## 📄 Documentação

Os entregáveis completos do projeto estão disponíveis na pasta `/docs`:

- **Relatório Técnico** (Entregável 2)
- **Roteiro do Vídeo** (Entregável 3)
- **Arquivo de Entrega** (Entregável 4)

---

## 🔗 Links

- 🎥 **Vídeo de Demonstração:** `[inserir link YouTube]`
- 📦 **Repositório:** https://github.com/MarcosCostaDv/IOT_GS

---

## 📜 Licença

Projeto acadêmico desenvolvido para a Global Solution 2026.1 — FIAP. Todos os direitos reservados à equipe NextSpace.
