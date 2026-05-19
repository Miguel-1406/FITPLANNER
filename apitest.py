from flask import Flask, request, jsonify
import sqlite3
app = Flask(__name__)
from flask_cors import CORS
CORS(app)

# iniciação do banco de dados 
def iniciar_banco():
    con = sqlite3.connect('fitplanner.db')
    cur = con.cursor()
    cur.execute("PRAGMA foreign_keys = ON")
    cur.execute('''
        CREATE TABLE IF NOT EXISTS treinos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
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
    con.close()

iniciar_banco()

def obter_conexao():
    conn = sqlite3.connect('fitplanner.db')
    conn.row_factory = sqlite3.Row
    return conn    

@app.route('/treinos', methods=['GET'])
def obter_treinos():
    con = obter_conexao()
    cursor = con.cursor()
    cursor.execute('SELECT * FROM treinos')
    linhas = cursor.fetchall()
    con.close()
    lista_treinos = [dict(linha) for linha in linhas]
    return jsonify(lista_treinos)

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

@app.route('/exercicios', methods=['GET'])
def obter_exercicios():
    con = obter_conexao()
    cursor = con.cursor()
    cursor.execute('SELECT * FROM exercicios')
    linhas = cursor.fetchall()
    con.close()
    lista_exercicios = [dict(linha) for linha in linhas]
    return jsonify(lista_exercicios)

@app.route('/exercicios/treino/<int:id_treino>', methods=['GET'])
def obter_exercicios_por_treino(id_treino):
    con = obter_conexao()
    cursor = con.cursor()
    cursor.execute("SELECT * FROM exercicios WHERE id_treino = ?", (id_treino,))
    linhas = cursor.fetchall()
    con.close()
    lista_exercicios = [dict(linha) for linha in linhas]
    return jsonify(lista_exercicios)

@app.route('/treinos', methods=['POST'])
def adicionar_treino():
    dados = request.json
    nome = dados['nome']
    tipo = dados['tipo']
    objetivo = dados['objetivo']
    con = obter_conexao()
    cursor = con.cursor()
    cursor.execute("INSERT INTO treinos (nome, tipo, objetivo, data_criacao) VALUES (?, ?, ?, datetime('now'))", (nome, tipo, objetivo))
    con.commit()
    con.close()
    return jsonify({"mensagem": "Treino cadastrado com sucesso!"})


# NOVAS FUNÇÕES

# excluir exercicio
@app.route('/treinos/<int:id>', methods=['DELETE'])
def deletar_treino(id):
    con = obter_conexao()
    cursor = con.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("DELETE FROM treinos WHERE id = ?", (id,))
    con.commit()
    con.close()
    return jsonify({"mensagem": "Treino deletado com sucesso!"})

# adicionar exercicio
@app.route('/exercicios', methods=['POST'])
def adicionar_exercicio():
    dados = request.json
    id_treino = dados['id_treino']
    nome_exercicio = dados['nome_exercicio']
    series = dados['series']
    repeticoes = dados['repeticoes']
    con = obter_conexao()
    cursor = con.cursor()
    cursor.execute("INSERT INTO exercicios (id_treino, nome_exercicio, series, repeticoes) VALUES (?, ?, ?, ?)",
                   (id_treino, nome_exercicio, series, repeticoes))
    con.commit()
    con.close()
    return jsonify({"mensagem": "Exercício cadastrado com sucesso!"})

if __name__ == '__main__':
    app.run(port=5000, host='localhost', debug=True)