from flask import Flask, request, json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

servidor = Flask(__name__)
servidor.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///log-db.db"

contexto = SQLAlchemy()

class Log (contexto.Model) :
    id = contexto.Column(contexto.Integer, primary_key=True)
    method = contexto.Column(contexto.String, nullable=False)
    url = contexto.Column(contexto.String, nullable=False)
    response = contexto.Column(contexto.String)
    data = contexto.Column(contexto.DateTime, nullable=False)

contexto.init_app(servidor)

@servidor.route("/log", methods=["POST"])
async def gravar_log() :

    dados = request.get_json()

    log = Log(
        method = dados['method'],
        url = dados['url'],
        response = dados['response'],
        data = datetime.now()
    )
    try:
        contexto.session.add(log)
        contexto.session.commit()

        response = {"mensagem": "Log criado com sucesso" }, 201
    except:
        response = {"mensagem": "error"}, 500
    return response


@servidor.route("/logs")
async def listar_logs() :

    logs = Log.query.all()

    response = [{
        "id" : log.id,
        "mensagem" : log.mensagem,
        "data" : log.data
    }for log in logs ]
    return response, 200

with servidor.app_context() :
    contexto.create_all()