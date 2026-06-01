from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

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

@app.route('/treinos', methods=['GET'])
def obter_treinos():
    con = obter_conexao()
    cursor = con.cursor()
    cursor.execute('SELECT * FROM treinos')
    linhas = cursor.fetchall()
    con.close()
    return jsonify([dict(linha) for linha in linhas])

@app.route('/treinos/<int:id>', methods=['GET'])
def obter_treino_por_id(id):
    con = obter_conexao()
    cursor = con.cursor()
    cursor.execute("SELECT * FROM treinos WHERE id = ?", (id,))
    linha = cursor.fetchone()
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
    cursor = con.cursor()
    
    cursor.execute("SELECT id FROM treinos WHERE nome = ?", (nome,))
    if cursor.fetchone():
        con.close()
        return jsonify({"mensagem": "Já existe um treino com este nome."}), 400
        
    cursor.execute("INSERT INTO treinos (nome, tipo, objetivo, data_criacao) VALUES (?, ?, ?, datetime('now'))", (nome, tipo, objetivo))
    con.commit()
    con.close()
    return jsonify({"mensagem": "Treino cadastrado com sucesso!"}), 201

@app.route('/treinos/<int:id>', methods=['PUT'])
def atualizar_treino(id):
    dados = request.json
    if not dados:
        return jsonify({"mensagem": "Dados inválidos."}), 400
        
    con = obter_conexao()
    cursor = con.cursor()
    
    cursor.execute("SELECT nome FROM treinos WHERE id = ?", (id,))
    treino_atual = cursor.fetchone()
    if not treino_atual:
        con.close()
        return jsonify({"mensagem": "Treino não encontrado."}), 404
        
    nome = dados.get('nome', treino_atual['nome']).strip().upper()
    tipo = dados.get('tipo', '').strip()
    objetivo = dados.get('objetivo', '').strip()
    
    if nome != treino_atual['nome']:
        cursor.execute("SELECT id FROM treinos WHERE nome = ? AND id != ?", (nome, id))
        if cursor.fetchone():
            con.close()
            return jsonify({"mensagem": "Já existe outro treino com esse nome."}), 400
            
    cursor.execute("UPDATE treinos SET nome = ?, tipo = ?, objetivo = ? WHERE id = ?", (nome, tipo, objetivo, id))
    con.commit()
    con.close()
    return jsonify({"mensagem": "Treino atualizado com sucesso!"})

@app.route('/treinos/<int:id>', methods=['DELETE'])
def deletar_treino(id):
    con = obter_conexao()
    cursor = con.cursor()
    cursor.execute("SELECT id FROM treinos WHERE id = ?", (id,))
    if not cursor.fetchone():
        con.close()
        return jsonify({"mensagem": "Treino não encontrado."}), 404
        
    cursor.execute("DELETE FROM treinos WHERE id = ?", (id,))
    con.commit()
    con.close()
    return jsonify({"mensagem": "Treino deletado com sucesso!"})

@app.route('/exercicios', methods=['GET'])
def obter_exercicios():
    con = obter_conexao()
    cursor = con.cursor()
    cursor.execute('SELECT * FROM exercicios')
    linhas = cursor.fetchall()
    con.close()
    return jsonify([dict(linha) for linha in linhas])

@app.route('/exercicios/treino/<int:id_treino>', methods=['GET'])
def obter_exercicios_por_treino(id_treino):
    con = obter_conexao()
    cursor = con.cursor()
    cursor.execute("SELECT * FROM exercicios WHERE id_treino = ?", (id_treino,))
    linhas = cursor.fetchall()
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
    cursor = con.cursor()
    
    cursor.execute("SELECT id FROM treinos WHERE id = ?", (id_treino,))
    if not cursor.fetchone():
        con.close()
        return jsonify({"mensagem": "Treino informado não existe."}), 404
        
    cursor.execute("INSERT INTO exercicios (id_treino, nome_exercicio, series, repeticoes) VALUES (?, ?, ?, ?)",
                   (id_treino, nome_exercicio, series, repeticoes))
    con.commit()
    con.close()
    return jsonify({"mensagem": "Exercício cadastrado com sucesso!"}), 201

@app.route('/exercicios/<int:id>', methods=['PUT'])
def atualizar_exercicio(id):
    dados = request.json
    if not dados:
        return jsonify({"mensagem": "Dados inválidos."}), 400
        
    con = obter_conexao()
    cursor = con.cursor()
    
    cursor.execute("SELECT * FROM exercicios WHERE id = ?", (id,))
    exercicio_atual = cursor.fetchone()
    if not exercicio_atual:
        con.close()
        return jsonify({"mensagem": "Exercício não encontrado."}), 404
        
    nome_exercicio = dados.get('nome_exercicio', exercicio_atual['nome_exercicio']).strip()
    series = dados.get('series', exercicio_atual['series']).strip()
    repeticoes = dados.get('repeticoes', exercicio_atual['repeticoes']).strip()
    
    cursor.execute("UPDATE exercicios SET nome_exercicio = ?, series = ?, repeticoes = ? WHERE id = ?", 
                   (nome_exercicio, series, repeticoes, id))
    con.commit()
    con.close()
    return jsonify({"mensagem": "Exercício updated com sucesso!"})

@app.route('/exercicios/<int:id>', methods=['DELETE'])
def deletar_exercicio(id):
    con = obter_conexao()
    cursor = con.cursor()
    cursor.execute("SELECT id FROM exercicios WHERE id = ?", (id,))
    if not cursor.fetchone():
        con.close()
        return jsonify({"mensagem": "Exercício não encontrado."}), 404
        
    cursor.execute("DELETE FROM exercicios WHERE id = ?", (id,))
    con.commit()
    con.close()
    return jsonify({"mensagem": "Exercício deletado com sucesso!"})

@app.route('/metas', methods=['GET'])
def obter_metas():
    con = obter_conexao()
    cursor = con.cursor()
    cursor.execute('SELECT * FROM metas')
    linhas = cursor.fetchall()
    con.close()
    return jsonify([dict(linha) for linha in linhas])

@app.route('/metas', methods=['POST'])
def adicionar_meta():
    dados = request.json
    if not dados or 'titulo' not in dados or 'valor_meta' not in dados:
        return jsonify({"mensagem": "Campos 'titulo' e 'valor_meta' são obrigatórios."}), 400
        
    titulo = dados['titulo'].strip()
    unidade = dados.get('unidade', '').strip()
    valor_inicial = float(dados.get('valor_atual', 0))
    valor_atual = valor_inicial
    valor_meta = float(dados['valor_meta'])
    tipo_meta = dados.get('tipo_meta', 'ganhar')
    
    if tipo_meta == 'perder':
        concluida = 1 if valor_atual <= valor_meta else 0
    else:
        concluida = 1 if valor_atual >= valor_meta else 0
    
    con = obter_conexao()
    cursor = con.cursor()
    
    cursor.execute("SELECT id FROM metas WHERE titulo = ?", (titulo,))
    if cursor.fetchone():
        con.close()
        return jsonify({"mensagem": "Já existe uma meta com este nome."}), 400
        
    cursor.execute("INSERT INTO metas (titulo, valor_inicial, valor_atual, valor_meta, unidade, tipo_meta, concluida, data_criacao) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))",
                   (titulo, valor_inicial, valor_atual, valor_meta, unidade, tipo_meta, concluida))
    con.commit()
    con.close()
    return jsonify({"mensagem": "Meta criada com sucesso!"}), 201

@app.route('/metas/<int:id>', methods=['PUT'])
def atualizar_meta(id):
    dados = request.json
    if not dados or 'valor_atual' not in dados:
        return jsonify({"mensagem": "O campo 'valor_atual' é obrigatório."}), 400
        
    novo_valor = float(dados['valor_atual'])
    
    con = obter_conexao()
    cursor = con.cursor()
    
    cursor.execute("SELECT valor_meta, tipo_meta FROM metas WHERE id = ?", (id,))
    meta = cursor.fetchone()
    if not meta:
        con.close()
        return jsonify({"mensagem": "Meta não encontrada."}), 404
        
    if meta['tipo_meta'] == 'perder':
        concluida = 1 if novo_valor <= float(meta['valor_meta']) else 0
    else:
        concluida = 1 if novo_valor >= float(meta['valor_meta']) else 0
    
    cursor.execute("UPDATE metas SET valor_atual = ?, concluida = ? WHERE id = ?", (novo_valor, concluida, id))
    con.commit()
    con.close()
    return jsonify({"mensagem": "Progresso da meta atualizado!"})

@app.route('/metas/<int:id>', methods=['DELETE'])
def deletar_meta(id):
    con = obter_conexao()
    cursor = con.cursor()
    cursor.execute("SELECT id FROM metas WHERE id = ?", (id,))
    if not cursor.fetchone():
        con.close()
        return jsonify({"mensagem": "Meta não encontrada."}), 404
        
    cursor.execute("DELETE FROM metas WHERE id = ?", (id,))
    con.commit()
    con.close()
    return jsonify({"mensagem": "Meta deletada com sucesso!"})

if __name__ == '__main__':
    app.run(port=5000, host='localhost', debug=True)