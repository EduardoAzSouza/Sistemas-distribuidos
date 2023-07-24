####  Trabalho de MA2

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy

import datetime
import asyncio
import logHelper

servidor = Flask(__name__)
servidor.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db-orm.db"
orm = SQLAlchemy()

aluno_x_disciplina = orm.Table('aluno_x_disciplina',
    orm.Column('aluno_id', orm.Integer, orm.ForeignKey('aluno.id'), primary_key=True),                
    orm.Column('disciplina_id', orm.Integer, orm.ForeignKey('disciplina.id'), primary_key=True)              
    )

class Aluno(orm.Model):
    id = orm.Column(orm.Integer, primary_key = True, autoincrement = True)
    nome = orm.Column(orm.String, nullable = False)
    email = orm.Column(orm.String)
    ra = orm.Column(orm.Integer, nullable = False)
    data_criacao = orm.Column(orm.DateTime, nullable = False)
    data_atualizacao = orm.Column(orm.DateTime, nullable = False)
    endereco = orm.relationship('Endereco', backref = 'aluno', lazy = True)
    disciplinas = orm.relationship('Disciplina', secondary= aluno_x_disciplina, lazy='subquery',
                                  backref = orm.backref('aluno', lazy=True))

class Disciplina(orm.Model):
    id = orm.Column(orm.Integer, primary_key = True, autoincrement = True)
    nome = orm.Column(orm.String, nullable = False)
    carga_horaria = orm.Column(orm.Integer)
    data_criacao = orm.Column(orm.DateTime, nullable = False)
    data_atualizacao = orm.Column(orm.DateTime, nullable = False)
    alunos = orm.relationship('Aluno', secondary= aluno_x_disciplina, lazy='subquery',
                                  backref = orm.backref('disciplina', lazy=True))

class Endereco(orm.Model):
    id = orm.Column(orm.Integer, primary_key = True, autoincrement = True)
    logradouro = orm.Column(orm.String, nullable = False)
    cep = orm.Column(orm.String)
    cidade = orm.Column(orm.String, nullable = False)
    aluno_id = orm.Column(orm.Integer, orm.ForeignKey('aluno.id'), nullable = False)

orm.init_app(servidor)

@servidor.route("/")
def home():
    return "Servidor executado com Flask SQLAlchemy ORM", 200

@servidor.route("/aluno", methods=["POST"])
async def cadastrar_aluno():
    dados = request.get_json()

    aluno = Aluno (
        nome = dados['nome'],
        email = dados['email'],
        ra = dados['ra'],
        data_criacao = datetime.datetime.now(),
        data_atualizacao = datetime.datetime.now()
    )
    endereco = Endereco (
        logradouro = dados['logradouro'],
        cep = dados['cep'],
        cidade = dados['cidade'],
    )
    aluno.endereco.append(endereco)

    try:
        orm.session.add(aluno)
        orm.session.commit()
        orm.session.refresh(aluno)

        response = {"aluno.id": aluno.id }, 201
    except:
        response = {"mensagem": "error"}, 500
    
    await asyncio.create_task(logHelper.gravar_log(request, response))

    return response

@servidor.route("/disciplina", methods=["POST"])
async def cadastrar_diciplina():
    #resgatamos os dados do corpo do req
    dados = request.get_json()

    disciplina = Disciplina (
       
        nome = dados['nome'],
        carga_horaria = dados['carga_horaria'],
        data_criacao = datetime.datetime.now(),
        data_atualizacao = datetime.datetime.now()
    )
    try:
        orm.session.add(disciplina)
        orm.session.commit()
        orm.session.refresh(disciplina)
        response = {"disciplina.id": disciplina.id }, 201
    except:
        response = {"mensagem": "error"}, 500

    await asyncio.create_task(logHelper.gravar_log(request, response))
    
    return response

@servidor.route("/matricula", methods=["POST"])
async def cadastrar_matricula():
    #resgatamos os dados do corpo do req
    dados = request.get_json()

    aluno = Aluno.query.get(dados['aluno_id'])
    disciplina = Disciplina.query.get(dados['disciplina_id'])

    aluno.disciplinas.append(disciplina)
    try:
        orm.session.commit()
        response = {"Aluno matriculado com sucesso" }, 201
    except:
        response = {"mensagem": "error"}, 500

    await asyncio.create_task(logHelper.gravar_log(request, response))
    
    return response

@servidor.route("/aluno/<int:id>")
async def consultar_aluno(id):
    aluno = Aluno.query.get(id)

    if aluno:
        endereco = Endereco.query.filter_by(aluno_id=id).first()
    response = {
            "id": aluno.id,
            "nome": aluno.nome,
            "email": aluno.email,
            "ra": aluno.ra,
            "data_criacao": aluno.data_criacao,
            "data_atualizacao": aluno.data_atualizacao,
            "endereco": {
                "logradouro": endereco.logradouro,
                "cep": endereco.cep,
                "cidade": endereco.cidade
            }
        }, 200

    await asyncio.create_task(logHelper.gravar_log(request, response))

    return response

@servidor.route("/alunos")
async def listar_todos_alunos() :
    alunos = Aluno.query.all()

    response = []

    for aluno in alunos:
        endereco = Endereco.query.filter_by(aluno_id=aluno.id).first()

        aluno_data = {
            "id": aluno.id,
            "nome": aluno.nome,
            "email": aluno.email,
            "ra": aluno.ra,
            "data_criacao": aluno.data_criacao,
            "data_atualizacao": aluno.data_atualizacao,
            "endereco": {
                "logradouro": endereco.logradouro,
                "cep": endereco.cep,
                "cidade": endereco.cidade
            }
        }

        response.append(aluno_data)
    await asyncio.create_task(logHelper.gravar_log(request, response))
    return response, 200

@servidor.route("/aluno", methods=['PUT'])
async def atualizar_aluno():
    dados = request.get_json()
    try:
        aluno = Aluno.query.get(dados['id'])
        endereco = Endereco.query.filter(Endereco.aluno_id.like(dados['id'])).all()
        if aluno:
            aluno.nome = dados['nome']
            aluno.email = dados['email']
            aluno.ra = dados['ra']
            aluno.data_atualizacao = datetime.datetime.now()
            endereco[0].logradouro = dados['logradouro']
            endereco[0].cep = dados['cep']
            endereco[0].cidade = dados['cidade']

            orm.session.commit()
            response = {"mensagem": "aluno atualizado"}, 200
        else:
            response = {"mensagem": "aluno não encontrado"}, 200    
    except:
        response = {"mensagem": "erro ao atualizar"}, 500

    await asyncio.create_task(logHelper.gravar_log(request, response))
   
    return response

@servidor.route("/aluno/<int:id>", methods=['DELETE'])
async def deletar_aluno(id):
    try:
        aluno = Aluno.query.get(id)
        endereco = Endereco.query.filter(Endereco.aluno_id.like(id)).all()

        orm.session.delete(endereco[0])
        orm.session.delete(aluno)
        orm.session.commit()
        response = {"mensagem": "Aluno deletado com sucesso"}, 200
        
    except:
        response = {"mensagem": "Erro ao deletar o aluno"}, 500

    await asyncio.create_task(logHelper.gravar_log(request, response))
    return response  

@servidor.route("/disciplinas")
async def listar_todas_disciplinas() :
    disciplinas = Disciplina.query.all() #resgata dos os registros da tabela

    response = [{
        "disciplina_id" : disciplina.id,
        "nome" : disciplina.nome,
        "carga_horaria" : disciplina.carga_horaria    
    }for disciplina in disciplinas ]

    await asyncio.create_task(logHelper.gravar_log(request, response))
    return response, 200

@servidor.route("/disciplina/<int:id>", methods=['DELETE'])
async def deletar_disciplina(id):
    try:
        disciplinas = Disciplina.query.get(id)

        orm.session.delete(disciplinas)
        orm.session.commit()
       
        response = {"mensagem": "Diciplina deletada"},200
    except:
        response={"mensagem":"erro ao atualizar"},500

    await asyncio.create_task(logHelper.gravar_log(request, response))
    return response  

@servidor.route("/endereco", methods=['PUT'])
async def atualizar_endeco():
    dados = request.get_json()
    try:
        endereco = Endereco.query.get(dados['id'])
        if endereco:
            endereco.logradouro = dados['logradouro']
            endereco.cep = dados['cep']
            endereco.cidade = dados['cidade']
            endereco.data_atualizacao = datetime.datetime.now()

            orm.session.commit()
            response = {"mensagem": "Endereço atualizado"}, 200
        else:
            response = {"mensagem": "endereço não encontrado"}, 200    
    except:
        response = {"mensagem": "erro ao atualizar"}, 500
    await asyncio.create_task(logHelper.gravar_log(request, response))
    return response

with servidor.app_context():
    orm.create_all() #vai verificar quais classes não
                     #possuem tabelas e criá-las
