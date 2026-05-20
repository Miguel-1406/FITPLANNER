import sqlite3
import os
from datetime import datetime

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def input_numero(mensagem):
    while True:
        try:
            return int(input(mensagem).strip())
        except ValueError:
            print("[!] Digite apenas números inteiros.")

def iniciar_banco():
    try:
        with sqlite3.connect('fitplanner.db') as conexao:
            cursor = conexao.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS treinos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE,
                    tipo TEXT,
                    objetivo TEXT,
                    data_criacao TEXT NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exercicios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_treino INTEGER NOT NULL,
                    nome_exercicio TEXT NOT NULL,
                    series TEXT,
                    repeticoes TEXT,
                    FOREIGN KEY (id_treino) REFERENCES treinos(id) ON DELETE CASCADE ON UPDATE CASCADE
                )
            ''')
            conexao.commit()
    except sqlite3.Error as e:
        print(f"[!] Erro crítico ao inicializar o banco de dados: {e}")
        print("[Dica] Se você modificou a estrutura das tabelas, apague o arquivo 'fitplanner.db' e tente novamente.")
        input("Pressione Enter para sair...")
        exit()

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
            nome = input("Nome do Treino (ex: Treino A): ").strip().upper()
            tipo = input("Tipo (ex: Musculação/Cardio): ").strip()
            objetivo = input("Objetivo (ex: Ganhar Massa Muscular): ").strip()
            data_criacao = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            
            try:
                with sqlite3.connect('fitplanner.db') as con:
                    cur = con.cursor()
                    cur.execute("SELECT id FROM treinos WHERE nome = ?", (nome,))
                    if cur.fetchone():
                        print("\n[!] Já existe um treino com este nome. Escolha um nome exclusivo.")
                    else:
                        cur.execute("INSERT INTO treinos (nome, tipo, objetivo, data_criacao) VALUES (?, ?, ?, ?)", 
                                    (nome, tipo, objetivo, data_criacao))
                        con.commit()
                        print("\nTreino cadastrado com sucesso!")
            except sqlite3.Error as e:
                print(f"\n[!] Erro ao cadastrar treino: {e}")
            input("Pressione Enter...")

        elif escolha == '2':
            try:
                with sqlite3.connect('fitplanner.db') as con:
                    cur = con.cursor()
                    cur.execute("SELECT nome, tipo, objetivo, data_criacao FROM treinos")
                    dados = cur.fetchall()
                    
                    print("\n--- SEUS TREINOS ---")
                    if not dados:
                        print("[!] Nenhum treino cadastrado ainda.")
                    else:
                        for linha in dados:
                            print(f"Nome: {linha[0]} | Tipo: {linha[1]} | Objetivo: {linha[2]} | Criado em: {linha[3]}")

                        ver = input("\nDigite o NOME de um treino para ver seus exercícios (ou Enter para voltar): ").strip()
                        if ver:
                            cur.execute("SELECT id FROM treinos WHERE nome = ?", (ver,))
                            treino = cur.fetchone()

                            if not treino:
                                print("[!] Treino não encontrado.")
                            else:
                                treino_id = treino[0]
                                cur.execute("SELECT nome_exercicio, series, repeticoes FROM exercicios WHERE id_treino = ?", (treino_id,))
                                exercicios = cur.fetchall()

                                print(f"\n--- EXERCÍCIOS DO TREINO: {ver} ---")
                                if not exercicios:
                                    print("[!] Nenhum exercício cadastrado para este treino.")
                                else:
                                    for ex in exercicios:
                                        print(f"Exercício: {ex[0]} | Séries: {ex[1]} | Repetições: {ex[2]}")
            except sqlite3.Error as e:
                print(f"\n[!] Erro ao listar treinos: {e}")
            input("\nPressione Enter para voltar...")

        elif escolha == '3':
            try:
                with sqlite3.connect('fitplanner.db') as con:
                    con.execute("PRAGMA foreign_keys = ON")
                    cur = con.cursor()
                    
                    cur.execute("SELECT nome FROM treinos")
                    treinos = cur.fetchall()
                    
                    print("\n--- SEUS TREINOS ---")
                    if not treinos:
                        print("[!] Nenhum treino cadastrado para deletar.")
                    else:
                        for t in treinos:
                            print(f"- {t[0]}")
                            
                        nome_treino = input("\nDigite o NOME do treino que deseja deletar: ").strip().upper()
                        
                        cur.execute("SELECT id FROM treinos WHERE nome = ?", (nome_treino,))
                        if not cur.fetchone():
                            print("[!] Treino não encontrado.")
                        else:
                            cur.execute("DELETE FROM treinos WHERE nome = ?", (nome_treino,))
                            con.commit()
                            print("\nTreino e seus exercícios foram deletados com sucesso!")
            except sqlite3.Error as e:
                   print(f"\n[!] Erro ao deletar treino: {e}")
            input("Pressione Enter...")
            

        elif escolha == '0':
            break

def cadastrar_exercicio():
    try:
        with sqlite3.connect('fitplanner.db') as con:
            cur = con.cursor()
            cur.execute("SELECT nome FROM treinos")
            treinos = cur.fetchall()

            if not treinos:
                print("[!] Nenhum treino cadastrado. Cadastre um treino primeiro.")
                input("Pressione Enter...")
                return

            print("\n--- TREINOS DISPONÍVEIS ---")
            for t in treinos:
                print(f"- {t[0]}")

            nome_treino = input("\nDigite o NOME do treino: ").strip().upper()

            cur.execute("SELECT id FROM treinos WHERE nome = ?", (nome_treino,))
            treino = cur.fetchone()

            if not treino:
                print(f"\n[!] Treino '{nome_treino}' não encontrado.")
                input("Pressione Enter...")
                return

            treino_id = treino[0]
            print(f"\nAdicionando exercício ao treino: {nome_treino}")
            nome_exercicio = input("Nome do Exercício: ").strip()
            series = input("Séries (ex: 3/5): ").strip()
            repeticoes = input("Repetições (ex: 10/12): ").strip()

            cur.execute("INSERT INTO exercicios (id_treino, nome_exercicio, series, repeticoes) VALUES (?, ?, ?, ?)", 
                        (treino_id, nome_exercicio, series, repeticoes))
            con.commit()
            print("\nExercício cadastrado com sucesso!")
    except sqlite3.Error as e:
        print(f"\n[!] Erro ao cadastrar exercício: {e}")
    input("Pressione Enter...")

def menu_editar():
    while True:
        limpar_tela()
        print("=== MENU EDITAR ===")
        print("1. Editar Dados de um Treino")
        print("2. Editar Dados de um Exercício")
        print("0. Voltar")
        
        escolha = input("\n-> ")
        
        if escolha == '1':
            try:
                with sqlite3.connect('fitplanner.db') as con:
                    cur = con.cursor()
                    cur.execute("SELECT nome FROM treinos")
                    treinos = cur.fetchall()
                    
                    if not treinos:
                        print("[!] Nenhum treino cadastrado.")
                        input("Pressione Enter...")
                        continue
                    
                    print("\n--- TREINOS DISPONÍVEIS ---")
                    for t in treinos:
                        print(f"- {t[0]}")
                        
                    nome_atual = input("\nDigite o NOME do treino que deseja editar: ").strip()
                    cur.execute("SELECT id, tipo, objetivo FROM treinos WHERE nome = ?", (nome_atual,))
                    treino = cur.fetchone()
                    
                    if not treino:
                        print("[!] Treino não encontrado.")
                    else:
                        treino_id = treino[0]
                        print("\n(Deixe em branco para manter o valor atual)")
                        novo_nome = input(f"Novo Nome (Atual: {nome_atual}): ").strip().upper() or nome_atual
                        novo_tipo = input(f"Novo Tipo (Atual: {treino[1]}): ").strip() or treino[1]
                        novo_obj = input(f"Novo Objetivo (Atual: {treino[2]}): ").strip() or treino[2]
                        
                        if novo_nome != nome_atual:
                            cur.execute("SELECT id FROM treinos WHERE nome = ?", (novo_nome,))
                            if cur.fetchone():
                                print("[!] Já existe um treino com esse novo nome.")
                                input("Pressione Enter...")
                                continue
                        
                        cur.execute("UPDATE treinos SET nome = ?, tipo = ?, objetivo = ? WHERE id = ?", 
                                    (novo_nome, novo_tipo, novo_obj, treino_id))
                        con.commit()
                        print("\nTreino atualizado com sucesso!")
            except sqlite3.Error as e:
                print(f"\n[!] Erro ao editar treino: {e}")
            input("Pressione Enter...")
            
        elif escolha == '2':
            try:
                with sqlite3.connect('fitplanner.db') as con:
                    cur = con.cursor()
                    cur.execute("SELECT nome FROM treinos")
                    treinos = cur.fetchall()
                    
                    if not treinos:
                        print("[!] Nenhum treino cadastrado.")
                        input("Pressione Enter...")
                        continue
                    
                    print("\n--- TREINOS DISPONÍVEIS ---")
                    for t in treinos:
                        print(f"- {t[0]}")
                        
                    nome_treino = input("\nDigite o NOME do treino dono do exercício: ").strip()
                    cur.execute("SELECT id FROM treinos WHERE nome = ?", (nome_treino,))
                    treino = cur.fetchone()
                    
                    if not treino:
                        print("[!] Treino não encontrado.")
                    else:
                        treino_id = treino[0]
                        cur.execute("SELECT id, nome_exercicio, series, repeticoes FROM exercicios WHERE id_treino = ?", (treino_id,))
                        exercicios = cur.fetchall()
                        
                        if not exercicios:
                            print("[!] Nenhum exercício associado a este treino.")
                        else:
                            print(f"\n--- EXERCÍCIOS DE {nome_treino} ---")
                            for ex in exercicios:
                                print(f"- {ex[1]} | Séries: {ex[2]} | Repetições: {ex[3]}")
                                
                            nome_ex_atual = input("\nDigite o NOME do exercício que deseja editar: ").strip()
                            cur.execute("SELECT id, series, repeticoes FROM exercicios WHERE id_treino = ? AND nome_exercicio = ?", 
                                        (treino_id, nome_ex_atual))
                            exercicio_dados = cur.fetchone()
                            
                            if not exercicio_dados:
                                print("[!] Exercício não encontrado.")
                            else:
                                ex_id = exercicio_dados[0]
                                print("\n(Deixe em branco para manter o valor atual)")
                                novo_nome_ex = input(f"Novo Nome (Atual: {nome_ex_atual}): ").strip().upper() or nome_ex_atual
                                novas_series = input(f"Novas Séries (Atual: {exercicio_dados[1]}): ").strip() or exercicio_dados[1]
                                novas_rep = input(f"Novas Repetições (Atual: {exercicio_dados[2]}): ").strip() or exercicio_dados[2]
                                
                                cur.execute("UPDATE exercicios SET nome_exercicio = ?, series = ?, repeticoes = ? WHERE id = ?", 
                                            (novo_nome_ex, novas_series, novas_rep, ex_id))
                                con.commit()
                                print("\nExercício atualizado com sucesso!")
            except sqlite3.Error as e:
                print(f"\n[!] Erro ao editar exercício: {e}")
            input("Pressione Enter...")
            
        elif escolha == '0':
            break

iniciar_banco()

while True:
    limpar_tela()
    print("FITPLANNER")
    print("Escolha o que deseja realizar: ")
    print(" 1-Gerenciar Planos de treino")
    print(" 2-Cadastrar Exercicios")
    print(" 3-Editar")
    print(" 4-Controle de Metas")
    print(" 5-Acompanhar")
    print(" 6-Sugestões Personalizadas")
    print(" 7-Extra")
    print(" 8-Sair")
    opcao = input(" -> ")

    if opcao == '1':
        menu_gerenciar_treinos()
    elif opcao == '2':
        print("\n--- Cadastrar Exercícios ---")
        cadastrar_exercicio()
    elif opcao == '3':
        menu_editar()
    elif opcao == '4':
        print("\n--- Controle de Metas ---")
        input("\nPressione Enter para voltar...")
    elif opcao == '5':
        print("\n--- Acompanhamento de Evolução ---")
        input("\nPressione Enter para voltar...")
    elif opcao == '6':
        print("\n--- Sugestões Personalizadas ---")
        input("\nPressione Enter para voltar...")
    elif opcao == '7':
        print("\n--- Funcionalidade Extra ---")
        input("\nPressione Enter para voltar...")
    elif opcao == '8':
        print("Saindo do sistema... Bom treino!")
        break
    else:
        print("Opção inválida! Tente novamente.")
        input("Pressione Enter...")
