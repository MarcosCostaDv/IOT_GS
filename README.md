# Space Capsule Monitoring System 🚀

Sistema Inteligente de Monitoramento para Cápsula Espacial  
**Engenharia de Software – Global Solution 2026.1 – FIAP**

---

## Visão Geral

Este projeto implementa um sistema de monitoramento em tempo real para cápsula espacial, integrando:

| Camada | Tecnologia |
|---|---|
| Simulação de sensor | Python (módulo `sensor_simulator`) |
| Visão computacional | Python + OpenCV |
| API REST | Python + Flask |
| Dashboard | Node-RED + node-red-dashboard |

---

## Estrutura do Projeto

```
space_capsule/
├── main.py               # Ponto de entrada principal
├── sensor_simulator.py   # Simulação do sensor de temperatura (Arduino)
├── vision_system.py      # Sistema de visão computacional (OpenCV)
├── api_server.py         # Servidor REST Flask (integração Node-RED)
├── node_red_flow.json    # Flow completo para importar no Node-RED
├── requirements.txt      # Dependências Python
└── README.md
```

---

## Instalação

### 1. Clonar e entrar no diretório
```bash
git clone <url-do-repositorio>
cd space_capsule
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

### 4. Instalar Node-RED (caso não tenha)
```bash
npm install -g --unsafe-perm node-red
```

### 5. Instalar pacotes Node-RED
```bash
cd ~/.node-red
npm install node-red-dashboard node-red-node-ui-led
```

---

## Execução

### Passo 1 – Iniciar o sistema Python
```bash
python main.py
```

Isso abre:
- A janela OpenCV (visão computacional)  
- O servidor REST em `http://localhost:5000`

Para rodar sem a janela OpenCV (apenas API):
```bash
python main.py --sem-visao
```

### Passo 2 – Iniciar o Node-RED
```bash
node-red
```
Acesse: `http://localhost:1880`

### Passo 3 – Importar o flow
1. Menu ☰ → **Import**
2. Cole o conteúdo de `node_red_flow.json` ou use "select a file to import"
3. Clique **Import** e depois **Deploy**

### Passo 4 – Visualizar o dashboard
Acesse: `http://localhost:1880/ui`

---

## API REST – Endpoints

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/temperatura` | Leitura mais recente |
| GET | `/api/historico?limite=60` | Histórico de leituras |
| GET | `/api/status` | Resumo do sistema |
| GET | `/api/alertas` | Últimas leituras em alerta |
| GET | `/api/health` | Health-check |

Exemplo de resposta de `/api/temperatura`:
```json
{
  "temperatura": 23.47,
  "status": "NORMAL",
  "timestamp": 1748400000.0,
  "leitura_num": 42,
  "timestamp_iso": "2026-05-28T14:00:00"
}
```

---

## Teclas da Janela OpenCV

| Tecla | Ação |
|---|---|
| `q` | Encerra o sistema |
| `f` | Simula falha do sensor |
| `r` | Reseta o sensor (cancela falha) |

---

## Limites de Temperatura

| Range | Status |
|---|---|
| > 28 °C | `ALERTA_ALTO` (borda vermelha piscando) |
| 25–28 °C | `AVISO` (gauge amarelo) |
| 18–25 °C | `NORMAL` (verde) |
| < 18 °C | `ALERTA_BAIXO` |
| Sensor offline | `FALHA` |

---

## Arquitetura do Sistema

```
[Sensor Simulado]
       │  1 leitura/s
       ▼
[Thread Aquisição] ──────────────► [Flask API REST :5000]
       │                                    │
       │                                    │ GET polling 1s
       ▼                                    ▼
[OpenCV Vision System]            [Node-RED Flow]
  - Mapa térmico                    - Gauge temperatura
  - Detecção de contornos           - Gráfico histórico
  - Gauge circular                  - LED de status
  - Gráfico histórico               - Texto de resumo
  - Alertas visuais                 ▼
                               [Dashboard Web :1880/ui]
```

---

## Melhorias Futuras

- Integração com MQTT para múltiplos sensores distribuídos
- Modelo de ML para previsão de anomalias de temperatura
- Exportação de histórico em CSV/JSON
- Notificações por e-mail/SMS em caso de alerta
- Simulação de outros sensores (pressão, umidade, CO₂)
- Deploy em Raspberry Pi com sensor real DHT22

---

## Tecnologias Utilizadas

- **Python 3.10+**
- **OpenCV 4.8+** – Visão computacional
- **NumPy** – Processamento de arrays
- **Flask + Flask-CORS** – API REST
- **Node-RED** – Orquestração e dashboard
- **node-red-dashboard** – Widgets visuais

---

## Autores

| Nome | RM |
|---|---|
| _[Preencher]_ | _[RM]_ |
| _[Preencher]_ | _[RM]_ |

**GitHub:** [link]  
**Vídeo YouTube:** [link]
