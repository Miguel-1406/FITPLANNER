import sqlite3
import os
from datetime import datetime


def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')


def conectar():
    
    con = sqlite3.connect('fitplanner.db')
    con.execute("PRAGMA foreign_keys = ON")
    return con

def iniciar_banco():
    try:
        with conectar() as con:
            cur = con.cursor()

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
                    titulo TEXT NOT NULL,
                    valor_atual REAL,
                    valor_meta REAL NOT NULL,
                    unidade TEXT,
                    concluida INTEGER DEFAULT 0,
                    data_criacao TEXT NOT NULL
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS historico_metas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_meta INTEGER NOT NULL,
                    valor REAL NOT NULL,
                    data_registro TEXT NOT NULL,
                    FOREIGN KEY (id_meta) REFERENCES metas(id) ON DELETE CASCADE
                )
            ''')
            con.commit()
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

        escolha = input("\n-> ").strip()

        if escolha == '1':
            nome = input("Nome do Treino (ex: Treino A): ").strip().upper()
            tipo = input("Tipo (ex: Musculação/Cardio): ").strip()
            objetivo = input("Objetivo (ex: Ganhar Massa Muscular): ").strip()
            if not nome or not tipo or not objetivo:
             print("\n[!] Todos os campos são obrigatórios.")
             input("Pressione Enter...")
             continue
            data_criacao = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

            try:
                with conectar() as con:
                    cur = con.cursor()
                    cur.execute("SELECT id FROM treinos WHERE nome = ?", (nome,))
                    if cur.fetchone():
                        print("\n[!] Já existe um treino com este nome. Escolha um nome exclusivo.")
                    else:
                        cur.execute(
                            "INSERT INTO treinos (nome, tipo, objetivo, data_criacao) VALUES (?, ?, ?, ?)",
                            (nome, tipo, objetivo, data_criacao)
                        )
                        con.commit()
                        print("\nTreino cadastrado com sucesso!")
            except sqlite3.Error as e:
                print(f"\n[!] Erro ao cadastrar treino: {e}")
            input("Pressione Enter...")

        elif escolha == '2':
            try:
                with conectar() as con:
                    cur = con.cursor()
                    cur.execute("SELECT nome, tipo, objetivo, data_criacao FROM treinos")
                    dados = cur.fetchall()

                    print("\n--- SEUS TREINOS ---")
                    if not dados:
                        print("[!] Nenhum treino cadastrado ainda.")
                    else:
                        for linha in dados:
                            print(f"Nome: {linha[0]} | Tipo: {linha[1]} | Objetivo: {linha[2]} | Criado em: {linha[3]}")

                        ver = input("\nDigite o NOME de um treino para ver seus exercícios (ou Enter para voltar): ").strip().upper()
                        if ver:
                            cur.execute("SELECT id FROM treinos WHERE nome = ?", (ver,))
                            treino = cur.fetchone()

                            if not treino:
                                print("[!] Treino não encontrado.")
                            else:
                                treino_id = treino[0]
                                cur.execute(
                                    "SELECT nome_exercicio, series, repeticoes FROM exercicios WHERE id_treino = ?",
                                    (treino_id,)
                                )
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
                with conectar() as con:
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
        with conectar() as con:
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
            nome_exercicio = input("Nome do Exercício: ").strip().upper()
            if not nome_exercicio:
               print("[!] Informe o nome do exercício.")
               input("Pressione Enter...")
               return
            series = input("Séries (ex: 3/5): ").strip()
            repeticoes = input("Repetições (ex: 10/12): ").strip()
            if not series or not repeticoes:
               print("\n[!] Séries e repetições são obrigatórias.")
               input("Pressione Enter...")
               return
            cur.execute(
                 """
                 SELECT id
                 FROM exercicios
                 WHERE id_treino = ?
                 AND nome_exercicio = ?
                 """,
                (treino_id, nome_exercicio)
)

            if cur.fetchone():
               print("\n[!] Este exercício já existe neste treino.")
               input("Pressione Enter...")
               return

            cur.execute(
                "INSERT INTO exercicios (id_treino, nome_exercicio, series, repeticoes) VALUES (?, ?, ?, ?)",
                (treino_id, nome_exercicio, series, repeticoes)
            )
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

        escolha = input("\n-> ").strip()

        if escolha == '1':
            try:
                with conectar() as con:
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

                    nome_atual = input("\nDigite o NOME do treino que deseja editar: ").strip().upper()
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

                        cur.execute(
                            "UPDATE treinos SET nome = ?, tipo = ?, objetivo = ? WHERE id = ?",
                            (novo_nome, novo_tipo, novo_obj, treino_id)
                        )
                        con.commit()
                        print("\nTreino atualizado com sucesso!")
            except sqlite3.Error as e:
                print(f"\n[!] Erro ao editar treino: {e}")
            input("Pressione Enter...")

        elif escolha == '2':
            try:
                with conectar() as con:
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

                    nome_treino = input("\nDigite o NOME do treino dono do exercício: ").strip().upper()
                    cur.execute("SELECT id FROM treinos WHERE nome = ?", (nome_treino,))
                    treino = cur.fetchone()

                    if not treino:
                        print("[!] Treino não encontrado.")
                    else:
                        treino_id = treino[0]
                        cur.execute(
                            "SELECT id, nome_exercicio, series, repeticoes FROM exercicios WHERE id_treino = ?",
                            (treino_id,)
                        )
                        exercicios = cur.fetchall()

                        if not exercicios:
                            print("[!] Nenhum exercício associado a este treino.")
                        else:
                            print(f"\n--- EXERCÍCIOS DE {nome_treino} ---")
                            for ex in exercicios:
                                print(f"- {ex[1]} | Séries: {ex[2]} | Repetições: {ex[3]}")

                            nome_ex_atual = input("\nDigite o NOME do exercício que deseja editar: ").strip().upper()
                            cur.execute(
                                "SELECT id, series, repeticoes FROM exercicios WHERE id_treino = ? AND nome_exercicio = ?",
                                (treino_id, nome_ex_atual)
                            )
                            exercicio_dados = cur.fetchone()

                            if not exercicio_dados:
                                print("[!] Exercício não encontrado.")
                            else:
                                ex_id = exercicio_dados[0]
                                print("\n(Deixe em branco para manter o valor atual)")
                                novo_nome_ex = input(f"Novo Nome (Atual: {nome_ex_atual}): ").strip().upper() or nome_ex_atual
                                novas_series = input(f"Novas Séries (Atual: {exercicio_dados[1]}): ").strip() or exercicio_dados[1]
                                novas_rep = input(f"Novas Repetições (Atual: {exercicio_dados[2]}): ").strip() or exercicio_dados[2]

                                cur.execute(
                                    "UPDATE exercicios SET nome_exercicio = ?, series = ?, repeticoes = ? WHERE id = ?",
                                    (novo_nome_ex, novas_series, novas_rep, ex_id)
                                )
                                con.commit()
                                print("\nExercício atualizado com sucesso!")
            except sqlite3.Error as e:
                print(f"\n[!] Erro ao editar exercício: {e}")
            input("Pressione Enter...")

        elif escolha == '0':
            break


def menu_metas():
    while True:
        limpar_tela()
        print("=== CONTROLE DE METAS ===")
        print("1. Criar Meta")
        print("2. Listar Metas")
        print("3. Atualizar Progresso")
        print("4. Concluir Meta")
        print("5. Deletar Meta")
        print("0. Voltar")

        opcao = input("\n-> ").strip()

        if opcao == '1':
            criar_meta()
        elif opcao == '2':
            listar_metas()
        elif opcao == '3':
            atualizar_meta()
        elif opcao == '4':
            concluir_meta()
        elif opcao == '5':
            deletar_meta()
        elif opcao == '0':
            break


def criar_meta():
    limpar_tela()

    titulo = input("Nome da Meta: ").strip().upper()
    unidade = input("Unidade (kg/km/%): ").strip()
    if not titulo or not unidade:
       print("[!] Todos os campos são obrigatórios.")
       input("\nPressione Enter...")
       return

    try:
        valor_atual = float(input("Valor Atual: ").strip())
        valor_meta = float(input("Valor da Meta: ").strip())
        if valor_atual < 0 or valor_meta <= 0:
           print("[!] Valores inválidos.")
           input("\nPressione Enter...")
           return
    except ValueError:
        print("[!] Valor inválido. Use números (ex: 70.5)")
        input("\nPressione Enter...")
        return

    data = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    try:
        with conectar() as con:
            cur = con.cursor()

            cur.execute("SELECT id FROM metas WHERE titulo = ?", (titulo,))
            if cur.fetchone():
                print("\n[!] Já existe uma meta com este nome.")
                input("\nPressione Enter...")
                return

            cur.execute(
               "INSERT INTO metas (titulo, valor_atual, valor_meta, unidade, data_criacao) VALUES (?, ?, ?, ?, ?)",
               (titulo, valor_atual, valor_meta, unidade, data)
)

            meta_id = cur.lastrowid

            cur.execute(
               "INSERT INTO historico_metas (id_meta, valor, data_registro) VALUES (?, ?, ?)",
               (meta_id, valor_atual, data)
)
            
            con.commit()
            print("\nMeta criada com sucesso!")
    except sqlite3.Error as e:
        print(f"\nErro: {e}")

    input("\nPressione Enter...")


def listar_metas(pausar=True):
    limpar_tela()

    try:
        with conectar() as con:
            cur = con.cursor()
            cur.execute("SELECT titulo, valor_atual, valor_meta, unidade, concluida FROM metas")
            metas = cur.fetchall()

            print("\n=== SUAS METAS ===")

            if not metas:
                print("Nenhuma meta cadastrada.")
            else:
                for meta in metas:
                    porcentagem = max(0, min((meta[1] / meta[2]) * 100, 100))
                    if porcentagem > 100:
                        porcentagem = 100
                    status = "✅ Concluída" if meta[4] else "⏳ Em andamento"

                    print(f"""
Meta: {meta[0]}
Progresso: {meta[1]} / {meta[2]} {meta[3]}
Conclusão: {porcentagem:.1f}%
Status: {status}
------------------------""")

    except sqlite3.Error as e:
        print(f"\nErro: {e}")

    if pausar:
        input("\nPressione Enter...")


def atualizar_meta():
    listar_metas()

    try:
        titulo = input("\nNome da meta a atualizar: ").strip().upper()
        if not titulo:
           print("[!] Digite um nome válido.")
           input("\nPressione Enter...")
           return
        novo_valor = float(input("Novo valor atual: "))
        if novo_valor < 0:
           print("[!] O valor não pode ser negativo.")
           input("\nPressione Enter...")
           return

        with conectar() as con:
            cur = con.cursor()

            cur.execute(
                 "SELECT id, concluida FROM metas WHERE titulo = ?",
                 (titulo,)
)

            meta = cur.fetchone()
            if not meta:
                print("[!] Meta não encontrada.")
                input("\nPressione Enter...")
                return
            if meta[1] == 1:
               print("[!] Esta meta já foi concluída.")
               input("\nPressione Enter...")
               return

            meta_id = meta[0]
            data = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

            cur.execute("UPDATE metas SET valor_atual = ? WHERE titulo = ?", (novo_valor, titulo))
            cur.execute("INSERT INTO historico_metas (id_meta, valor, data_registro) VALUES (?, ?, ?)",
                        (meta_id, novo_valor, data))
            con.commit()
            print("\nMeta atualizada!")

    except Exception as e:
        print(f"\nErro: {e}")

    input("\nPressione Enter...")

def concluir_meta():
    listar_metas(pausar=False)

    try:
        titulo = input("\nNome da meta concluída: ").strip().upper()

        with conectar() as con:
            cur = con.cursor()

            cur.execute("SELECT id FROM metas WHERE titulo = ?", (titulo,))
            if not cur.fetchone():
                print("[!] Meta não encontrada.")
                input("\nPressione Enter...")
                return

            cur.execute("UPDATE metas SET concluida = 1 WHERE titulo = ?", (titulo,))
            con.commit()
            print("\n🏆 Meta concluída!")
    except sqlite3.Error as e:
        print(f"\nErro: {e}")

    input("\nPressione Enter...")


def deletar_meta():
    listar_metas(pausar=False)

    try:
        titulo = input("\nNome da meta para deletar: ").strip().upper()

        with conectar() as con:
            cur = con.cursor()

            cur.execute("SELECT id FROM metas WHERE titulo = ?", (titulo,))
            if not cur.fetchone():
                print("[!] Meta não encontrada.")
                input("\nPressione Enter...")
                return

            cur.execute("DELETE FROM metas WHERE titulo = ?", (titulo,))
            con.commit()
            print("\nMeta deletada!")
    except sqlite3.Error as e:
        print(f"\nErro: {e}")

    input("\nPressione Enter...")

def acompanhar_evolucao():
    listar_metas()

    try:
        titulo = input("\nNome da meta para ver evolução: ").strip().upper()

        with conectar() as con:
            cur = con.cursor()

            cur.execute("""
                SELECT id, valor_atual, valor_meta, unidade, data_criacao
                FROM metas WHERE titulo = ?
            """, (titulo,))
            meta = cur.fetchone()

            if not meta:
                print("[!] Meta não encontrada.")
                input("\nPressione Enter...")
                return

            meta_id, valor_atual, valor_meta, unidade, data_criacao = meta

            cur.execute("""
                SELECT valor, data_registro FROM historico_metas
                WHERE id_meta = ? ORDER BY id ASC
            """, (meta_id,))
            historico = cur.fetchall()

            limpar_tela()
            print(f"=== EVOLUÇÃO: {titulo} ===")
            print(f"Meta: {valor_meta} {unidade} | Criada em: {data_criacao}")

            # Dias desde a criação
            try:
                data_dt = datetime.strptime(data_criacao, "%d-%m-%Y %H:%M:%S")
                dias = (datetime.now() - data_dt).days
                print(f"Dias em andamento: {dias}")
            except:
                pass

            print("\n--- HISTÓRICO ---")
            if not historico:
                print("Nenhuma atualização registrada ainda.")
            else:
                valor_inicial = historico[0][0]
                valores = [h[0] for h in historico]

                for i, (valor, data) in enumerate(historico):
                    if i == 0:
                        variacao = ""
                    else:
                        diff = valor - historico[i - 1][0]
                        sinal = "+" if diff >= 0 else ""
                        variacao = f"  ({sinal}{diff:.2f} {unidade})"
                    print(f"{data}  →  {valor} {unidade}{variacao}")

                variacao_total = valor_atual - valor_inicial
                sinal = "+" if variacao_total >= 0 else ""
                print(f"\nVariação total:   {sinal}{variacao_total:.2f} {unidade}")
                print(f"Maior valor:      {max(valores)} {unidade}")
                print(f"Menor valor:      {min(valores)} {unidade}")
                print(f"Valor atual:      {valor_atual} {unidade}")

                porcentagem = max(0, min((valor_atual / valor_meta) * 100, 100))
                print(f"Progresso:        {porcentagem:.1f}%")

    except Exception as e:
        print(f"\nErro: {e}")

    input("\nPressione Enter...")
def sugestoes_personalizadas():
    while True:
        limpar_tela()
        print("=== SUGESTÕES PERSONALIZADAS ===")
        print("Selecione um plano de treino recomendado:")
        print("1. Recomendação: Peito e Tríceps")
        print("2. Recomendação: Costas e Bíceps")
        print("3. Recomendação: Pernas Completo")
        print("0. Voltar")

        escolha = input("\n-> ")

        if escolha == '1':
            limpar_tela()
            print("=== TREINO RECOMENDADO: PEITO E TRÍCEPS ===")
            print("Objetivo: Hipertrofia / Fortalecimento")
            print("-" * 50)
            print("Exercício 1: Supino Reto com Barra       | Séries: 4 | Repetições: 10")
            print("Exercício 2: Supino Inclinado c/ Halter  | Séries: 4 | Repetições: 12")
            print("Exercício 3: Crossover na Polia          | Séries: 3 | Repetições: 15")
            print("Exercício 4: Tríceps Pulley (Corda)      | Séries: 4 | Repetições: 12")
            print("Exercício 5: Tríceps Testa na Barra W    | Séries: 3 | Repetições: 10")
            print("-" * 50)
            input("\nPressione Enter para voltar às sugestões...")

        elif escolha == '2':
            limpar_tela()
            print("=== TREINO RECOMENDADO: COSTAS E BÍCEPS ===")
            print("Objetivo: Hipertrofia / Fortalecimento")
            print("-" * 50)
            print("Exercício 1: Puxada Alta (Pulldown)      | Séries: 4 | Repetições: 10")
            print("Exercício 2: Remada Curvada com Barra    | Séries: 4 | Repetições: 10")
            print("Exercício 3: Remada Baixa (Triângulo)    | Séries: 3 | Repetições: 12")
            print("Exercício 4: Rosca Direta com Barra      | Séries: 4 | Repetições: 10")
            print("Exercício 5: Rosca Alternada c/ Halter   | Séries: 3 | Repetições: 12")
            print("-" * 50)
            input("\nPressione Enter para voltar às sugestões...")

        elif escolha == '3':
            limpar_tela()
            print("=== TREINO RECOMENDADO: PERNAS ===")
            print("Objetivo: Hipertrofia / Fortalecimento")
            print("-" * 50)
            print("Exercício 1: Agachamento Livre           | Séries: 4 | Repetições: 10")
            print("Exercício 2: Leg Press 45°               | Séries: 4 | Repetições: 12")
            print("Exercício 3: Cadeira Extensora           | Séries: 3 | Repetições: 15")
            print("Exercício 4: Mesa Flexora                | Séries: 4 | Repetições: 12")
            print("Exercício 5: Gêmeos Sentado (Panturrilha)| Séries: 4 | Repetições: 15")
            print("-" * 50)
            input("\nPressione Enter para voltar às sugestões...")

        elif escolha == '0':
            break
        else:
            print("[!] Opção inválida! Tente novamente.")
            input("Pressione Enter...")

iniciar_banco()

while True:
    limpar_tela()
    print("╔══════════════════════╗")
    print("║      FITPLANNER      ║")
    print("╚══════════════════════╝")
    print("Escolha o que deseja realizar:")
    print(" 1 - Gerenciar Planos de Treino")
    print(" 2 - Cadastrar Exercícios")
    print(" 3 - Editar")
    print(" 4 - Controle de Metas")
    print(" 5 - Acompanhar Evolução")
    print(" 6 - Sugestões Personalizadas")
    print(" 7 - Extra")
    print(" 8 - Sair")
    opcao = input("\n -> ").strip()

    if opcao == '1':
        menu_gerenciar_treinos()
    elif opcao == '2':
        print("\n--- Cadastrar Exercícios ---")
        cadastrar_exercicio()
    elif opcao == '3':
        menu_editar()
    elif opcao == '4':
        menu_metas()
    elif opcao == '5':
        acompanhar_evolucao()
    elif opcao == '6':
        sugestoes_personalizadas()
    elif opcao == '7':
        print("\n--- Funcionalidade Extra ---")
        print("[!] Funcionalidade em desenvolvimento.")
        input("\nPressione Enter para voltar...")
    elif opcao == '8':
        print("\nSaindo do sistema... Bom treino! 💪")
        break
    else:
        print("[!] Opção inválida! Tente novamente.")
        input("Pressione Enter...")
