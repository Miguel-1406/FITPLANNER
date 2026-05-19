from flask import Flask, request, jsonify
import sqlite3
app = Flask(__name__)

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
def adicionar_treino(nome, tipo, objetivo):
    con = obter_conexao()
    cursor = con.cursor()
    cursor.execute("INSERT INTO treinos (nome, tipo, objetivo, data_criacao) VALUES (?, ?, ?, datetime('now'))", (nome, tipo, objetivo))
    con.commit()
    obter_exercicios_por_treino()

if __name__ == '__main__':
    app.run(port=5000, host='localhost', debug=True)        