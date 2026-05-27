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

if __name__ == '__main__':
    app.run(port=5000, host='localhost', debug=True)