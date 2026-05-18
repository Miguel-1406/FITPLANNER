import sqlite3
import os
from datetime import datetime
def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')
def iniciar_banco():
    conexao = sqlite3.connect('fitplanner.db')
    cursor = conexao.cursor()
    
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS treinos (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   nome TEXT NOT NULL,
                   tipo TEXT,
                   objetivo TEXT,
                   data_criacao TEXT NOT NULL
                   )
               ''')
    conexao.commit()
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS exercicios (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   id_treino INTEGER NOT NULL,
                   nome_exercicio TEXT NOT NULL,
                   series TEXT,
                   repeticoes TEXT
                   )
               ''')
    conexao.commit()
    conexao.close()
def menu_gerenciar_treinos():
    while True:
        limpar_tela()
        print("=== GERENCIAR TREINOS ===")
        print("1. Cadastrar Novo Treino")
        print("2. Listar Meus Treinos")
        print("3. Deletar Treino")
        print("0. Voltar")
        
        escolha = input("\n-> ")
        if escolha == '1':
            nome = input("Nome do Treino (ex: Treino A): ")
            tipo = input("Tipo (ex: Musculação/Cardio): ")
            objetivo = input("Objetivo (ex: Ganhar Massa Muscular): ")
            data_criacao = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            con = sqlite3.connect('fitplanner.db')

            cur = con.cursor()
            cur.execute("INSERT INTO treinos (nome, tipo, objetivo, data_criacao) VALUES (?, ?, ?, ?)", (nome, tipo, objetivo, data_criacao))
            con.commit()
            con.close()
            print("\nTreino cadastrado com sucesso!")
            input("Pressione Enter...")
        elif escolha == '2':
            con = sqlite3.connect('fitplanner.db')
            cur = con.cursor()
            cur.execute("SELECT id, nome, tipo, data_criacao FROM treinos")
            dados = cur.fetchall()
            con.close()
            
            print("\n--- SEUS TREINOS ---")
            for linha in dados:
                print(f"ID: {linha[0]} | Nome: {linha[1]} | Tipo: {linha[2]} | Data de Criação: {linha[3]}")
            input("\nPressione Enter para voltar...")
        elif escolha == '3':
            id_treino = input("Digite o ID do treino que deseja deletar: ")
            con = sqlite3.connect('fitplanner.db')
            cur = con.cursor()
            cur.execute("DELETE FROM treinos WHERE id = ?", (id_treino,))
            con.commit()
            con.close()
            print("\nTreino deletado com sucesso!")
            input("Pressione Enter...")
        elif escolha == '0':
            break
def cadastrar_exercicio():
    nome_exercicio = input("Nome do Exercício: ")
    series = input("Series (ex: 3/5): ")
    repeticoes = input("Repetições (ex: 10/12): ")
    id_treino = input("A qual treino este exercício pertence? (Digite o ID do treino): ")
    con = sqlite3.connect('fitplanner.db')
    cur = con.cursor()
    cur.execute("INSERT INTO exercicios (id_treino, nome_exercicio, series, repeticoes) VALUES (?, ?, ?, ?)", (id_treino, nome_exercicio, series, repeticoes))
    con.commit()
    con.close()
    print("\nExercício cadastrado com sucesso!")
    input("Pressione Enter...")
iniciar_banco()
while True:
    limpar_tela()
    print("FITPLANNER")
    print("Escolha o que deseja realizar: ")
    print(" 1-Gerenciar Planos de treino\n 2-Cadastrar Exercicios\n 3-Controle de Metas\n 4-Acompanhar \n 5-Sugestões Personalizadas\n 6-Extra")
    opcao = input(" ->")
    # Lógica de Navegação
    if opcao == '1':
        menu_gerenciar_treinos()
    elif opcao == '2':
        print("\n--- Cadastrar Exercícios ---")
        cadastrar_exercicio()
        input("\nPressione Enter para voltar...")

    elif opcao == '3':
        print("\n--- Controle de Metas ---")
        # Espaço para o Membro 4 trabalhar
        input("\nPressione Enter para voltar...")

    elif opcao == '4':
        print("\n--- Acompanhamento de Evolução ---")
        # Espaço para o Membro 4 trabalhar
        input("\nPressione Enter para voltar...")

    elif opcao == '5':
        print("\n--- Sugestões Personalizadas ---")
        # Espaço para o Membro 5 trabalhar
        input("\nPressione Enter para voltar...")

    elif opcao == '6':
        print("\n--- Funcionalidade Extra ---")
        input("\nPressione Enter para voltar...")

    elif opcao == '0':
        print("Saindo do sistema... Bom treino!")
        break # Este é o comando que encerra o programa

    else:
        print("Opção inválida! Tente novamente.")
        input("Pressione Enter...")
