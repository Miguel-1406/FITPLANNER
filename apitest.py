from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

SCOPES = ['https://www.googleapis.com/auth/calendar']
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

def get_calendar_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open('token.json', 'w') as f:
                f.write(creds.to_json())
        else:
            return None
    return build('calendar', 'v3', credentials=creds)

@app.route('/auth/google')
def auth_google():
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES,
        redirect_uri='http://localhost:5000/oauth2callback'
    )
    auth_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    return jsonify({"url": auth_url})

@app.route('/oauth2callback')
def oauth2callback():
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES,
        redirect_uri='http://localhost:5000/oauth2callback'
    )
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    with open('token.json', 'w') as f:
        f.write(creds.to_json())
    return jsonify({"mensagem": "Autenticado com sucesso!"})

@app.route('/agenda/treino', methods=['POST'])
def agendar_treino():
    dados = request.json
    if not dados or 'treino_id' not in dados or 'data' not in dados or 'hora' not in dados:
        return jsonify({"mensagem": "Campos 'treino_id', 'data' e 'hora' são obrigatórios."}), 400

    service = get_calendar_service()
    if not service:
        return jsonify({"mensagem": "Não autenticado. Acesse /auth/google primeiro."}), 401

    con = obter_conexao()
    cursor = con.cursor()
    cursor.execute("SELECT nome, tipo, objetivo FROM treinos WHERE id = ?", (dados['treino_id'],))
    treino = cursor.fetchone()
    con.close()

    if not treino:
        return jsonify({"mensagem": "Treino não encontrado."}), 404

    duracao = dados.get('duracao_min', 60)
    inicio = datetime.fromisoformat(f"{dados['data']}T{dados['hora']}:00")
    fim = inicio + timedelta(minutes=duracao)

    evento = {
        'summary': f'🏋️ Treino: {treino["nome"]}',
        'description': f'Tipo: {treino["tipo"]}\nObjetivo: {treino["objetivo"]}',
        'start': {'dateTime': inicio.isoformat(), 'timeZone': 'America/Recife'},
        'end':   {'dateTime': fim.isoformat(),   'timeZone': 'America/Recife'},
        'reminders': {
            'useDefault': False,
            'overrides': [{'method': 'popup', 'minutes': 30}]
        }
    }

    resultado = service.events().insert(calendarId='primary', body=evento).execute()
    return jsonify({
        "mensagem": "Treino agendado com sucesso!",
        "evento_id": resultado['id'],
        "link": resultado.get('htmlLink')
    }), 201

def iniciar_banco():
    try:
        with sqlite3.connect('fitplanner.db') as con:
            cur = con.cursor()
            cur.execute("PRAGMA foreign_keys = ON")
            cur.execute('''
                CREATE TABLE IF NOT EXISTS treinos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE,
                    tipo TEXT,
                    objetivo TEXT,
                    data_criacao TEXT NOT NULL
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS exercicios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_treino INTEGER NOT NULL,
                    nome_exercicio TEXT NOT NULL,
                    series TEXT,
                    repeticoes TEXT,
                    FOREIGN KEY (id_treino) REFERENCES treinos(id) ON DELETE CASCADE ON UPDATE CASCADE
                )
            ''')
            cur.execute('''
                 CREATE TABLE IF NOT EXISTS metas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT NOT NULL UNIQUE,
                    valor_inicial REAL DEFAULT 0,
                    valor_atual REAL DEFAULT 0,
                    valor_meta REAL NOT NULL,
                    unidade TEXT,
                    tipo_meta TEXT DEFAULT 'ganhar',
                    concluid INTEGER DEFAULT 0,
                    data_criacao TEXT NOT NULL
                 )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS historico_treinos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_treino INTEGER NOT NULL,
                    data_realizacao TEXT NOT NULL,
                    FOREIGN KEY (id_treino) REFERENCES treinos(id) ON DELETE CASCADE
                )
            ''')
            con.commit()
    except sqlite3.Error as e:
        print(f"Erro ao iniciar banco: {e}")

iniciar_banco()

def obter_conexao():
    conn = sqlite3.connect('fitplanner.db')
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

# BUG CORRIGIDO 1: list comprehension com variável fantasma "login" removida.
# Era: [dict(linha) for login in [0] for linha in linhas]  → iterava duas vezes de forma errada
@app.route('/treinos', methods=['GET'])
def obter_treinos():
    con = obter_conexao()
    cursor = con.cursor()
    cursor.execute('SELECT * FROM treinos')
    linhas = cursor.fetchall()
    con.close()
    return jsonify([dict(linha) for linha in linhas])

@app.route('/treinos', methods=['POST'])
def adicionar_treino():
    dados = request.json
    if not dados or 'nome' not in dados:
        return jsonify({"mensagem": "O campo 'nome' é obrigatório."}), 400

    nome = dados['nome'].strip().upper()
    tipo = dados.get('tipo', 'Musculação').strip()
    objetivo = dados.get('objetivo', 'Condicionamento').strip()

    con = obter_conexao()
    cursor = con.cursor()

    cursor.execute("SELECT id FROM treinos WHERE nome = ?", (nome,))
    if cursor.fetchone():
        con.close()
        return jsonify({"mensagem": "Já existe um treino com este nome."}), 400

    cursor.execute("INSERT INTO treinos (nome, tipo, objetivo, data_criacao) VALUES (?, ?, ?, datetime('now', 'localtime'))", (nome, tipo, objetivo))
    con.commit()
    con.close()
    return jsonify({"mensagem": "Treino cadastrado com sucesso!"}), 201

@app.route('/treinos/<int:id>', methods=['DELETE'])
def deletar_treino(id):
    con = obter_conexao()
    cursor = con.cursor()
    cursor.execute("DELETE FROM treinos WHERE id = ?", (id,))
    con.commit()
    con.close()
    return jsonify({"mensagem": "Treino deletado!"})

@app.route('/exercicios', methods=['GET'])
def obter_exercicios():
    con = obter_conexao()
    cursor = con.cursor()
    cursor.execute('SELECT exercicios.*, treinos.nome as nome_treino FROM exercicios JOIN treinos ON exercicios.id_treino = treinos.id')
    linhas = cursor.fetchall()
    con.close()
    return jsonify([dict(linha) for linha in linhas])

@app.route('/exercicios', methods=['POST'])
def adicionar_exercicio():
    dados = request.json
    if not dados or 'id_treino' not in dados or 'nome_exercicio' not in dados:
        return jsonify({"mensagem": "Campos obrigatórios ausentes."}), 400
    con = obter_conexao()
    cursor = con.cursor()
    cursor.execute("INSERT INTO exercicios (id_treino, nome_exercicio, series, repeticoes) VALUES (?, ?, ?, ?)",
                   (dados['id_treino'], dados['nome_exercicio'], dados.get('series',''), dados.get('repeticoes','')))
    con.commit()
    con.close()
    return jsonify({"mensagem": "Exercício cadastrado com sucesso!"}), 201

@app.route('/metas', methods=['GET'])
def obter_metas():
    con = obter_conexao()
    cursor = con.cursor()
    cursor.execute('SELECT * FROM metas')
    linhas = cursor.fetchall()
    con.close()
    return jsonify([dict(linha) for linha in linhas])

# BUG CORRIGIDO 2: valor_inicial agora é gravado separadamente do valor_atual,
# permitindo que /evolucao calcule o progresso real ao longo do tempo.
# Antes, valor_inicial e valor_atual recebiam o mesmo valor (valor_atual do request),
# fazendo a barra de progresso ficar sempre em 0% (tot_esperado = 0).
@app.route('/metas', methods=['POST'])
def adicionar_meta():
    dados = request.json
    if not dados or 'titulo' not in dados or 'valor_meta' not in dados:
        return jsonify({"mensagem": "Campos 'titulo' e 'valor_meta' são obrigatórios."}), 400

    titulo = dados['titulo'].strip()
    unidade = dados.get('unidade', 'Kg').strip()
    valor_atual = float(dados.get('valor_atual', 0))
    valor_meta = float(dados['valor_meta'])
    # BUG CORRIGIDO: valor_inicial vem do campo 'valor_inicial' do request.
    # Se não enviado, usa valor_atual como ponto de partida (comportamento anterior).
    valor_inicial = float(dados.get('valor_inicial', valor_atual))
    tipo_meta = dados.get('tipo_meta', 'ganhar')

    concluid = 1 if (tipo_meta == 'perder' and valor_atual <= valor_meta) or (tipo_meta == 'ganhar' and valor_atual >= valor_meta) else 0

    con = obter_conexao()
    cursor = con.cursor()

    cursor.execute("DELETE FROM metas WHERE titulo = ?", (titulo,))
    cursor.execute(
        "INSERT INTO metas (titulo, valor_inicial, valor_atual, valor_meta, unidade, tipo_meta, concluid, data_criacao) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))",
        (titulo, valor_inicial, valor_atual, valor_meta, unidade, tipo_meta, concluid)
    )
    con.commit()
    con.close()
    return jsonify({"mensagem": "Meta criada com sucesso!"}), 201

# BUG CORRIGIDO 3: conversão segura de id_treino com tratamento de ValueError.
# Antes, int() sem try/except causava exceção 500 se recebesse valor não numérico.
@app.route('/historico', methods=['POST'])
def registrar_treino_feito():
    dados = request.json
    if not dados or 'id_treino' not in dados:
        return jsonify({"mensagem": "O campo 'id_treino' é obrigatório."}), 400

    try:
        id_treino = int(dados['id_treino'])
    except (ValueError, TypeError):
        return jsonify({"mensagem": "O campo 'id_treino' deve ser um número inteiro válido."}), 400

    con = obter_conexao()
    cursor = con.cursor()

    cursor.execute("SELECT id FROM treinos WHERE id = ?", (id_treino,))
    if not cursor.fetchone():
        con.close()
        return jsonify({"mensagem": "Treino não encontrado."}), 404

    cursor.execute("INSERT INTO historico_treinos (id_treino, data_realizacao) VALUES (?, datetime('now', 'localtime'))", (id_treino,))
    con.commit()
    con.close()
    return jsonify({"mensagem": "Treino concluído registrado!"}), 201

@app.route('/evolucao', methods=['GET'])
def obter_evolucao():
    con = obter_conexao()
    cursor = con.cursor()

    cursor.execute("SELECT COUNT(*) FROM historico_treinos")
    total_treinos = cursor.fetchone()[0]

    sete_dias_atras = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("SELECT COUNT(*) FROM historico_treinos WHERE data_realizacao >= ?", (sete_dias_atras,))
    frequencia_semanal = cursor.fetchone()[0]

    cursor.execute("SELECT titulo, valor_atual, valor_meta, unidade, concluid, valor_inicial FROM metas")
    metas_banco = cursor.fetchall()

    progresso_metas = []
    for meta in metas_banco:
        v_inicial = meta['valor_inicial'] if meta['valor_inicial'] is not None else 0.0
        v_atual = meta['valor_atual'] if meta['valor_atual'] is not None else 0.0
        v_meta = meta['valor_meta'] if meta['valor_meta'] is not None else 0.0
        is_concluida = int(meta['concluid'])

        if is_concluida == 1:
            progresso_porcentagem = 100.0
        else:
            try:
                tot_esperado = abs(v_meta - v_inicial)
                tot_atual = abs(v_atual - v_inicial)
                progresso_porcentagem = round((tot_atual / tot_esperado) * 100, 2) if tot_esperado > 0 else 0.0
            except:
                progresso_porcentagem = 0.0

        progresso_metas.append({
            "meta": meta['titulo'],
            "atual": v_atual,
            "objetivo": v_meta,
            "unidade": meta['unidade'] if meta['unidade'] else '',
            "porcentagem_conclusao": min(max(progresso_porcentagem, 0.0), 100.0),
            "concluida": is_concluida == 1
        })

    con.close()
    return jsonify({
        "quantidade_de_treinos_realizados": int(total_treinos),
        "frequencia_semanal_ultimos_7_dias": int(frequencia_semanal),
        "progresso_em_relacao_as_metas": progresso_metas
    })

if __name__ == '__main__':
    app.run(port=5000, host='localhost', debug=True)