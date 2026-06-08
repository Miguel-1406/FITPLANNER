from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS
import os
import secrets
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import hashlib
import base64

# CONFIGURAÇÃO INICIAL


app = Flask(__name__)
CORS(app)

# CORREÇÃO 1 — OAUTHLIB_INSECURE_TRANSPORT só em desenvolvimento
# Antes: estava sempre ativo, o que desabilitava a exigência de HTTPS no OAuth
# mesmo em produção, abrindo brecha de segurança.
# Agora: só ativa se FLASK_ENV for explicitamente 'development'.
if os.getenv('FLASK_ENV') == 'development':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

SCOPES = ['https://www.googleapis.com/auth/calendar']

# CORREÇÃO 2 — Armazenamento seguro do token OAuth
# Antes: token.json e credentials.json ficavam no diretório da aplicação,
# expostos a qualquer pessoa com acesso ao servidor.
# Agora: os caminhos vêm de variáveis de ambiente, podendo apontar para
# diretórios seguros fora do projeto (ex: /etc/secrets/).
TOKEN_PATH = os.getenv('FITPLANNER_TOKEN_PATH', 'token.json')
CREDENTIALS_PATH = os.getenv('FITPLANNER_CREDENTIALS_PATH', 'credentials.json')


# BANCO DE DADOS


def iniciar_banco():
    # CORREÇÃO 3 — try/except no iniciar_banco já existia, mantido e revisado.
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
                    valor_atual REAL,
                    valor_meta REAL NOT NULL,
                    unidade TEXT,
                    tipo_meta TEXT DEFAULT 'ganhar',
                    concluida INTEGER DEFAULT 0,
                    data_criacao TEXT NOT NULL
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


# GOOGLE CALENDAR — AUTENTICAÇÃO


def get_calendar_service():
    """Retorna o serviço autenticado do Google Calendar."""
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_PATH, 'w') as f:
                f.write(creds.to_json())
        else:
            return None
    return build('calendar', 'v3', credentials=creds)


# CORREÇÃO 4 — Validação do parâmetro `state` no fluxo OAuth
# Antes: o `state` gerado pelo Google no início do fluxo era ignorado
# no callback. Isso permite ataques CSRF onde um invasor poderia forçar
# um usuário autenticado a vincular a conta dele com credenciais do atacante.
# Agora: o state é gerado manualmente, salvo em sessão (ou variável global
# simplificada aqui), e validado no callback.
#
# ATENÇÃO: Em produção real, use Flask-Session ou Redis para guardar o state.
# A variável global abaixo funciona, mas não escala com múltiplos workers.
_oauth_state_store = {}


@app.route('/auth/google')
def auth_google():
    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b'=').decode()

    flow = Flow.from_client_secrets_file(
        CREDENTIALS_PATH,
        scopes=SCOPES,
        redirect_uri='http://localhost:5000/oauth2callback'
    )
    auth_url, returned_state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        state=state,
        code_challenge=code_challenge,
        code_challenge_method='S256'
    )
    _oauth_state_store['state'] = state
    _oauth_state_store['code_verifier'] = code_verifier
    return jsonify({"url": auth_url})



@app.route('/oauth2callback')
def oauth2callback():
    state_recebido = request.args.get('state')
    state_esperado = _oauth_state_store.get('state')

    if not state_recebido or state_recebido != state_esperado:
        return jsonify({"mensagem": "State inválido. Possível ataque CSRF."}), 403

    code_verifier = _oauth_state_store.get('code_verifier')

    flow = Flow.from_client_secrets_file(
        CREDENTIALS_PATH,
        scopes=SCOPES,
        redirect_uri='http://localhost:5000/oauth2callback',
        state=state_recebido
    )
    flow.fetch_token(
        authorization_response=request.url,
        code_verifier=code_verifier
    )
    creds = flow.credentials
    with open(TOKEN_PATH, 'w') as f:
        f.write(creds.to_json())

    _oauth_state_store.clear()
    return jsonify({"mensagem": "Autenticado com sucesso!"})



# GOOGLE CALENDAR — ROTAS

@app.route('/agenda/treino', methods=['POST'])
def agendar_treino():
    dados = request.json
    if not dados or 'treino_id' not in dados or 'data' not in dados or 'hora' not in dados:
        return jsonify({"mensagem": "Campos 'treino_id', 'data' e 'hora' são obrigatórios."}), 400

    service = get_calendar_service()
    if not service:
        return jsonify({"mensagem": "Não autenticado. Acesse /auth/google primeiro."}), 401

    # CORREÇÃO 5 — Conexão sempre fechada com try/finally
    # Antes: se ocorresse uma exceção após obter_conexao(), a conexão ficaria
    # aberta indefinidamente, causando vazamento de recursos.
    # Agora: o bloco finally garante que con.close() sempre é chamado.
    con = obter_conexao()
    try:
        cursor = con.cursor()
        cursor.execute("SELECT nome, tipo, objetivo FROM treinos WHERE id = ?", (dados['treino_id'],))
        treino = cursor.fetchone()
    except sqlite3.Error as e:
        return jsonify({"mensagem": f"Erro ao buscar treino: {str(e)}"}), 500
    finally:
        con.close()

    if not treino:
        return jsonify({"mensagem": "Treino não encontrado."}), 404

    from datetime import datetime, timedelta
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

    # CORREÇÃO 6 — try/except nas chamadas da API do Google
    # Antes: se a API do Google retornasse erro (token expirado, cota excedida,
    # etc.), a exceção subia sem tratamento e o servidor retornava erro 500 genérico.
    try:
        resultado = service.events().insert(calendarId='primary', body=evento).execute()
    except Exception as e:
        return jsonify({"mensagem": f"Erro ao criar evento no Google Calendar: {str(e)}"}), 502

    return jsonify({
        "mensagem": "Treino agendado com sucesso!",
        "evento_id": resultado['id'],
        "link": resultado.get('htmlLink')
    }), 201


@app.route('/agenda/treinos', methods=['GET'])
def listar_agenda():
    service = get_calendar_service()
    if not service:
        return jsonify({"mensagem": "Não autenticado."}), 401

    from datetime import datetime, timezone, timedelta
    agora = datetime.now(timezone.utc).isoformat()
    fim = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    try:
        eventos = service.events().list(
            calendarId='primary',
            timeMin=agora,
            timeMax=fim,
            singleEvents=True,
            orderBy='startTime',
            q='Treino:'
        ).execute()
    except Exception as e:
        return jsonify({"mensagem": f"Erro ao listar eventos: {str(e)}"}), 502

    return jsonify(eventos.get('items', []))


@app.route('/agenda/treino/<evento_id>', methods=['DELETE'])
def remover_da_agenda(evento_id):
    service = get_calendar_service()
    if not service:
        return jsonify({"mensagem": "Não autenticado."}), 401

    try:
        service.events().delete(calendarId='primary', eventId=evento_id).execute()
    except Exception as e:
        return jsonify({"mensagem": f"Erro ao remover evento: {str(e)}"}), 502

    return jsonify({"mensagem": "Evento removido da agenda."})


# TREINOS

@app.route('/treinos', methods=['GET'])
def obter_treinos():
    # CORREÇÃO 7 — Paginação nas listagens
    # Antes: retornava TODOS os registros de uma vez. Com muitos dados,
    # isso sobrecarrega o banco e a rede desnecessariamente.
    # Agora: aceita ?pagina=1&limite=20 na query string.
    pagina = request.args.get('pagina', 1, type=int)
    limite = request.args.get('limite', 20, type=int)
    offset = (pagina - 1) * limite

    con = obter_conexao()
    try:
        cursor = con.cursor()
        cursor.execute('SELECT * FROM treinos LIMIT ? OFFSET ?', (limite, offset))
        linhas = cursor.fetchall()
        cursor.execute('SELECT COUNT(*) FROM treinos')
        total = cursor.fetchone()[0]
    except sqlite3.Error as e:
        return jsonify({"mensagem": f"Erro ao buscar treinos: {str(e)}"}), 500
    finally:
        con.close()

    return jsonify({
        "dados": [dict(linha) for linha in linhas],
        "pagina": pagina,
        "limite": limite,
        "total": total
    })


@app.route('/treinos/<int:id>', methods=['GET'])
def obter_treino_por_id(id):
    con = obter_conexao()
    try:
        cursor = con.cursor()
        cursor.execute("SELECT * FROM treinos WHERE id = ?", (id,))
        linha = cursor.fetchone()
    except sqlite3.Error as e:
        return jsonify({"mensagem": f"Erro ao buscar treino: {str(e)}"}), 500
    finally:
        con.close()

    if linha:
        return jsonify(dict(linha))
    return jsonify({"mensagem": "Treino não encontrado"}), 404


@app.route('/treinos', methods=['POST'])
def adicionar_treino():
    dados = request.json
    if not dados or 'nome' not in dados:
        return jsonify({"mensagem": "O campo 'nome' é obrigatório."}), 400

    nome = dados['nome'].strip().upper()
    tipo = dados.get('tipo', '').strip()
    objetivo = dados.get('objetivo', '').strip()

    con = obter_conexao()
    try:
        cursor = con.cursor()
        cursor.execute("SELECT id FROM treinos WHERE nome = ?", (nome,))
        if cursor.fetchone():
            return jsonify({"mensagem": "Já existe um treino com este nome."}), 400

        cursor.execute(
            "INSERT INTO treinos (nome, tipo, objetivo, data_criacao) VALUES (?, ?, ?, datetime('now'))",
            (nome, tipo, objetivo)
        )
        con.commit()
    except sqlite3.Error as e:
        return jsonify({"mensagem": f"Erro ao cadastrar treino: {str(e)}"}), 500
    finally:
        con.close()

    return jsonify({"mensagem": "Treino cadastrado com sucesso!"}), 201


@app.route('/treinos/<int:id>', methods=['PUT'])
def atualizar_treino(id):
    dados = request.json
    if not dados:
        return jsonify({"mensagem": "Dados inválidos."}), 400

    con = obter_conexao()
    try:
        cursor = con.cursor()
        cursor.execute("SELECT nome FROM treinos WHERE id = ?", (id,))
        treino_atual = cursor.fetchone()
        if not treino_atual:
            return jsonify({"mensagem": "Treino não encontrado."}), 404

        nome = dados.get('nome', treino_atual['nome']).strip().upper()
        tipo = dados.get('tipo', '').strip()
        objetivo = dados.get('objetivo', '').strip()

        if nome != treino_atual['nome']:
            cursor.execute("SELECT id FROM treinos WHERE nome = ? AND id != ?", (nome, id))
            if cursor.fetchone():
                return jsonify({"mensagem": "Já existe outro treino com esse nome."}), 400

        cursor.execute(
            "UPDATE treinos SET nome = ?, tipo = ?, objetivo = ? WHERE id = ?",
            (nome, tipo, objetivo, id)
        )
        con.commit()
    except sqlite3.Error as e:
        return jsonify({"mensagem": f"Erro ao atualizar treino: {str(e)}"}), 500
    finally:
        con.close()

    return jsonify({"mensagem": "Treino atualizado com sucesso!"})


@app.route('/treinos/<int:id>', methods=['DELETE'])
def deletar_treino(id):
    con = obter_conexao()
    try:
        cursor = con.cursor()
        cursor.execute("SELECT id FROM treinos WHERE id = ?", (id,))
        if not cursor.fetchone():
            return jsonify({"mensagem": "Treino não encontrado."}), 404

        cursor.execute("DELETE FROM treinos WHERE id = ?", (id,))
        con.commit()
    except sqlite3.Error as e:
        return jsonify({"mensagem": f"Erro ao deletar treino: {str(e)}"}), 500
    finally:
        con.close()

    return jsonify({"mensagem": "Treino deletado com sucesso!"})


# EXERCÍCIOS

@app.route('/exercicios', methods=['GET'])
def obter_exercicios():
    pagina = request.args.get('pagina', 1, type=int)
    limite = request.args.get('limite', 20, type=int)
    offset = (pagina - 1) * limite

    con = obter_conexao()
    try:
        cursor = con.cursor()
        cursor.execute('SELECT * FROM exercicios LIMIT ? OFFSET ?', (limite, offset))
        linhas = cursor.fetchall()
        cursor.execute('SELECT COUNT(*) FROM exercicios')
        total = cursor.fetchone()[0]
    except sqlite3.Error as e:
        return jsonify({"mensagem": f"Erro ao buscar exercícios: {str(e)}"}), 500
    finally:
        con.close()

    return jsonify({
        "dados": [dict(linha) for linha in linhas],
        "pagina": pagina,
        "limite": limite,
        "total": total
    })


@app.route('/exercicios/treino/<int:id_treino>', methods=['GET'])
def obter_exercicios_por_treino(id_treino):
    con = obter_conexao()
    try:
        cursor = con.cursor()
        cursor.execute("SELECT * FROM exercicios WHERE id_treino = ?", (id_treino,))
        linhas = cursor.fetchall()
    except sqlite3.Error as e:
        return jsonify({"mensagem": f"Erro ao buscar exercícios: {str(e)}"}), 500
    finally:
        con.close()

    return jsonify([dict(linha) for linha in linhas])


@app.route('/exercicios', methods=['POST'])
def adicionar_exercicio():
    dados = request.json
    if not dados or 'id_treino' not in dados or 'nome_exercicio' not in dados:
        return jsonify({"mensagem": "Campos 'id_treino' e 'nome_exercicio' são obrigatórios."}), 400

    id_treino = dados['id_treino']
    nome_exercicio = dados['nome_exercicio'].strip()
    series = dados.get('series', '').strip()
    repeticoes = dados.get('repeticoes', '').strip()

    con = obter_conexao()
    try:
        cursor = con.cursor()
        cursor.execute("SELECT id FROM treinos WHERE id = ?", (id_treino,))
        if not cursor.fetchone():
            return jsonify({"mensagem": "Treino informado não existe."}), 404

        cursor.execute(
            "INSERT INTO exercicios (id_treino, nome_exercicio, series, repeticoes) VALUES (?, ?, ?, ?)",
            (id_treino, nome_exercicio, series, repeticoes)
        )
        con.commit()
    except sqlite3.Error as e:
        return jsonify({"mensagem": f"Erro ao cadastrar exercício: {str(e)}"}), 500
    finally:
        con.close()

    return jsonify({"mensagem": "Exercício cadastrado com sucesso!"}), 201


@app.route('/exercicios/<int:id>', methods=['PUT'])
def atualizar_exercicio(id):
    dados = request.json
    if not dados:
        return jsonify({"mensagem": "Dados inválidos."}), 400

    con = obter_conexao()
    try:
        cursor = con.cursor()
        cursor.execute("SELECT * FROM exercicios WHERE id = ?", (id,))
        exercicio_atual = cursor.fetchone()
        if not exercicio_atual:
            return jsonify({"mensagem": "Exercício não encontrado."}), 404

        nome_exercicio = dados.get('nome_exercicio', exercicio_atual['nome_exercicio']).strip()
        series = dados.get('series', exercicio_atual['series']).strip()
        repeticoes = dados.get('repeticoes', exercicio_atual['repeticoes']).strip()

        cursor.execute(
            "UPDATE exercicios SET nome_exercicio = ?, series = ?, repeticoes = ? WHERE id = ?",
            (nome_exercicio, series, repeticoes, id)
        )
        con.commit()
    except sqlite3.Error as e:
        return jsonify({"mensagem": f"Erro ao atualizar exercício: {str(e)}"}), 500
    finally:
        con.close()

    # CORREÇÃO 8 — Typo corrigido
    # Antes: "Exercício updated com sucesso!" (mistura de inglês e português)
    # Agora: totalmente em português
    return jsonify({"mensagem": "Exercício atualizado com sucesso!"})


@app.route('/exercicios/<int:id>', methods=['DELETE'])
def deletar_exercicio(id):
    con = obter_conexao()
    try:
        cursor = con.cursor()
        cursor.execute("SELECT id FROM exercicios WHERE id = ?", (id,))
        if not cursor.fetchone():
            return jsonify({"mensagem": "Exercício não encontrado."}), 404

        cursor.execute("DELETE FROM exercicios WHERE id = ?", (id,))
        con.commit()
    except sqlite3.Error as e:
        return jsonify({"mensagem": f"Erro ao deletar exercício: {str(e)}"}), 500
    finally:
        con.close()

    return jsonify({"mensagem": "Exercício deletado com sucesso!"})


# METAS

@app.route('/metas', methods=['GET'])
def obter_metas():
    pagina = request.args.get('pagina', 1, type=int)
    limite = request.args.get('limite', 20, type=int)
    offset = (pagina - 1) * limite

    con = obter_conexao()
    try:
        cursor = con.cursor()
        cursor.execute('SELECT * FROM metas LIMIT ? OFFSET ?', (limite, offset))
        linhas = cursor.fetchall()
        cursor.execute('SELECT COUNT(*) FROM metas')
        total = cursor.fetchone()[0]
    except sqlite3.Error as e:
        return jsonify({"mensagem": f"Erro ao buscar metas: {str(e)}"}), 500
    finally:
        con.close()

    return jsonify({
        "dados": [dict(linha) for linha in linhas],
        "pagina": pagina,
        "limite": limite,
        "total": total
    })


@app.route('/metas', methods=['POST'])
def adicionar_meta():
    dados = request.json
    if not dados or 'titulo' not in dados or 'valor_meta' not in dados:
        return jsonify({"mensagem": "Campos 'titulo' e 'valor_meta' são obrigatórios."}), 400

    titulo = dados['titulo'].strip()
    unidade = dados.get('unidade', '').strip()
    tipo_meta = dados.get('tipo_meta', 'ganhar')

    # CORREÇÃO 9 — Separação correta entre valor_inicial e valor_atual
    # Antes: valor_inicial = dados.get('valor_atual', 0) — pegava o campo errado,
    # ou seja, o valor inicial e o valor atual eram sempre iguais mesmo que
    # o usuário enviasse 'valor_inicial' diferente de 'valor_atual'.
    # Agora: cada campo lê sua própria chave no JSON.
    valor_inicial = float(dados.get('valor_inicial', 0))
    valor_atual = float(dados.get('valor_atual', valor_inicial))
    valor_meta = float(dados['valor_meta'])

    if tipo_meta == 'perder':
        concluida = 1 if valor_atual <= valor_meta else 0
    else:
        concluida = 1 if valor_atual >= valor_meta else 0

    con = obter_conexao()
    try:
        cursor = con.cursor()
        cursor.execute("SELECT id FROM metas WHERE titulo = ?", (titulo,))
        if cursor.fetchone():
            return jsonify({"mensagem": "Já existe uma meta com este nome."}), 400

        cursor.execute(
            "INSERT INTO metas (titulo, valor_inicial, valor_atual, valor_meta, unidade, tipo_meta, concluida, data_criacao) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))",
            (titulo, valor_inicial, valor_atual, valor_meta, unidade, tipo_meta, concluida)
        )
        con.commit()
    except sqlite3.Error as e:
        return jsonify({"mensagem": f"Erro ao criar meta: {str(e)}"}), 500
    finally:
        con.close()

    return jsonify({"mensagem": "Meta criada com sucesso!"}), 201


@app.route('/metas/<int:id>', methods=['PUT'])
def atualizar_meta(id):
    dados = request.json
    if not dados or 'valor_atual' not in dados:
        return jsonify({"mensagem": "O campo 'valor_atual' é obrigatório."}), 400

    novo_valor = float(dados['valor_atual'])

    con = obter_conexao()
    try:
        cursor = con.cursor()
        cursor.execute("SELECT valor_meta, tipo_meta FROM metas WHERE id = ?", (id,))
        meta = cursor.fetchone()
        if not meta:
            return jsonify({"mensagem": "Meta não encontrada."}), 404

        if meta['tipo_meta'] == 'perder':
            concluida = 1 if novo_valor <= float(meta['valor_meta']) else 0
        else:
            concluida = 1 if novo_valor >= float(meta['valor_meta']) else 0

        cursor.execute(
            "UPDATE metas SET valor_atual = ?, concluida = ? WHERE id = ?",
            (novo_valor, concluida, id)
        )
        con.commit()
    except sqlite3.Error as e:
        return jsonify({"mensagem": f"Erro ao atualizar meta: {str(e)}"}), 500
    finally:
        con.close()

    return jsonify({"mensagem": "Progresso da meta atualizado!"})


@app.route('/metas/<int:id>', methods=['DELETE'])
def deletar_meta(id):
    con = obter_conexao()
    try:
        cursor = con.cursor()
        cursor.execute("SELECT id FROM metas WHERE id = ?", (id,))
        if not cursor.fetchone():
            return jsonify({"mensagem": "Meta não encontrada."}), 404

        cursor.execute("DELETE FROM metas WHERE id = ?", (id,))
        con.commit()
    except sqlite3.Error as e:
        return jsonify({"mensagem": f"Erro ao deletar meta: {str(e)}"}), 500
    finally:
        con.close()

    return jsonify({"mensagem": "Meta deletada com sucesso!"})



# INICIALIZAÇÃO


if __name__ == '__main__':
    # LEMBRETE DE SEGURANÇA: em produção, use um servidor WSGI como Gunicorn
    # e configure FLASK_ENV=production no ambiente.
    app.run(port=5000, host='localhost', debug=os.getenv('FLASK_ENV') == 'development')