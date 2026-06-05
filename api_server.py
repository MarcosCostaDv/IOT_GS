"""
api_server.py
Servidor Flask REST para integração com Node-RED.
"""

import threading
import time
from collections import deque

from flask import Flask, jsonify, request
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

_lock = threading.Lock()
_historico = deque(maxlen=200)
_ultimo_dado = {}


def atualizar_dados(dado: dict):
    global _ultimo_dado

    with _lock:
        enriquecido = {
            **dado,
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }

        _historico.append(enriquecido)
        _ultimo_dado = enriquecido


@app.route("/api/temperatura")
def get_temperatura():
    with _lock:
        if not _ultimo_dado:
            return jsonify({"erro": "sem dados"}), 404

        return jsonify(_ultimo_dado)


@app.route("/api/historico")
def get_historico():
    limite = request.args.get("limite", 60, type=int)

    with _lock:
        dados = list(_historico)[-limite:]

    return jsonify(
        {
            "historico": dados,
            "total": len(dados),
        }
    )


@app.route("/api/status")
def get_status():
    with _lock:
        temperatura = _ultimo_dado.get("temperatura")
        status = _ultimo_dado.get("status", "SEM_DADOS")
        total = len(_historico)

    return jsonify(
        {
            "sistema": "online",
            "temperatura_atual": temperatura,
            "status_sensor": status,
            "total": total,
            "total_leituras": total,
        }
    )


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


def iniciar_servidor(host="0.0.0.0", porta=5000):
    print(f"[API] Flask em http://{host}:{porta}")

    app.run(
        host=host,
        port=porta,
        debug=False,
        use_reloader=False,
    )