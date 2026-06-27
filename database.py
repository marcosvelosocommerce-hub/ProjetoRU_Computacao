"""
database.py — módulo compartilhado entre app_aluno.py e app_ru.py
Cria e gerencia o banco SQLite utfpr.db automaticamente com segurança SHA-256 e carga de CSV.
"""
import sqlite3
import os
import csv
import hashlib
from datetime import datetime

# Caminho do banco — sempre na pasta db/ relativa a este arquivo
DB_PATH = os.path.join(os.path.dirname(__file__), "utfpr.db")


def get_conn():
    """Retorna uma conexão com o banco, com suporte a dicionários."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # permite leitura simultânea
    return conn


# ─── FUNÇÃO AUXILIAR DE CRIPTOGRAFIA ──────────────────
def gerar_hash_senha(senha_pura: str) -> str:
    """Transforma uma senha comum em um hash SHA-256 seguro e irreversível."""
    return hashlib.sha256(senha_pura.strip().encode('utf-8')).hexdigest()


# ─── CRIAÇÃO DAS TABELAS ──────────
def criar_tabelas():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS alunos (
            ra_num      TEXT PRIMARY KEY,
            ra          TEXT NOT NULL,
            nome        TEXT NOT NULL,
            nome_curto  TEXT NOT NULL,
            curso       TEXT NOT NULL,
            periodo     TEXT NOT NULL,
            campus      TEXT NOT NULL,
            senha_hash  TEXT NOT NULL,
            ativo       INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS fichas (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ra_num      TEXT NOT NULL,
            tipo        TEXT NOT NULL CHECK(tipo IN ('Almoço','Jantar')),
            saldo       INTEGER NOT NULL DEFAULT 0,
            UNIQUE(ra_num, tipo),
            FOREIGN KEY(ra_num) REFERENCES alunos(ra_num)
        );

        CREATE TABLE IF NOT EXISTS transacoes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ra_num      TEXT NOT NULL,
            tipo        TEXT NOT NULL CHECK(tipo IN ('Compra','Uso')),
            refeicao    TEXT NOT NULL,
            qtd         INTEGER NOT NULL,
            valor       REAL,
            status      TEXT NOT NULL DEFAULT 'ok',
            criado_em   TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            FOREIGN KEY(ra_num) REFERENCES alunos(ra_num)
        );

        CREATE TABLE IF NOT EXISTS acessos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ra_num      TEXT NOT NULL,
            nome_curto  TEXT NOT NULL,
            turno       TEXT NOT NULL,
            status      TEXT NOT NULL,
            criado_em   TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS cardapio (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            dia_semana  TEXT NOT NULL CHECK(dia_semana IN ('Seg','Ter','Qua','Qui','Sex')),
            turno       TEXT NOT NULL CHECK(turno IN ('almoco','jantar')),
            prato_principal TEXT NOT NULL,
            guarnicao   TEXT NOT NULL,
            salada      TEXT NOT NULL,
            sobremesa   TEXT NOT NULL,
            UNIQUE(dia_semana, turno)
        );

        CREATE TABLE IF NOT EXISTS avaliacoes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            ra_num          TEXT NOT NULL,
            qualidade       INTEGER,
            atendimento     INTEGER,
            higiene         INTEGER,
            variedade       INTEGER,
            comentario      TEXT,
            criado_em       TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );
        """)


# ─── SEED: DADOS INICIAIS (ATUALIZADO COM CARGA DE CSV E HASH) ──────────────
def popular_banco():
    """Insere dados do CSV (com criptografia) e dados de demonstração se o banco estiver vazio."""
    with get_conn() as conn:
        # Verificação se a tabela alunos está vazia para realizar a carga inicial
        if conn.execute("SELECT COUNT(*) FROM alunos").fetchone()[0] == 0:
            csv_carregado = False
            
            # Lista de caminhos prováveis para encontrar o seu arquivo alunos.csv
            caminhos_csv = [
                os.path.join(os.path.dirname(__file__), "alunos.csv"),
                os.path.join(os.path.dirname(__file__), "..", "alunos.csv"),
                "alunos.csv"
            ]
            
            for caminho in caminhos_csv:
                if os.path.exists(caminho):
                    try:
                        with open(caminho, mode='r', encoding='utf-8') as f:
                            leitor = csv.DictReader(f)
                            for linha in leitor:
                                ra_num = linha['ra_num'].strip().zfill(8)
                                ra = linha['ra'].strip().lower()
                                # Segurança: Transforma a senha limpa do CSV em Hash SHA-256
                                senha_segura = gerar_hash_senha(linha['senha_hash'])
                                
                                # Insere o aluno de forma protegida
                                conn.execute("""
                                    INSERT OR IGNORE INTO alunos (ra_num, ra, nome, nome_curto, curso, periodo, campus, senha_hash, ativo)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    ra_num, ra, linha['nome'].strip(), linha['nome_curto'].strip(),
                                    linha['curso'].strip(), linha['periodo'].strip(), linha['campus'].strip(),
                                    senha_segura, int(linha['ativo'])
                                ))
                                
                                # Carrega os saldos iniciais de fichas contidos no CSV
                                conn.execute("""
                                    INSERT OR IGNORE INTO fichas (ra_num, tipo, saldo)
                                    VALUES (?, 'Almoço', ?)
                                """, (ra_num, int(linha.get('fichas_almoco', 0))))
                                
                                conn.execute("""
                                    INSERT OR IGNORE INTO fichas (ra_num, tipo, saldo)
                                    VALUES (?, 'Jantar', ?)
                                """, (ra_num, int(linha.get('fichas_jantar', 0))))
                                
                        csv_carregado = True
                        break
                    except Exception as e:
                        print(f"Aviso na carga do CSV ({caminho}): {e}")

        # Cardápio
        if conn.execute("SELECT COUNT(*) FROM cardapio").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO cardapio (dia_semana,turno,prato_principal,guarnicao,salada,sobremesa) VALUES (?,?,?,?,?,?)",
                [
                    ("Seg","almoco","Frango grelhado com ervas","Arroz integral e feijão carioca","Alface americana com tomate cereja","Banana"),
                    ("Seg","jantar","Macarrão ao molho bolonhesa","Arroz branco e feijão preto","Repolho roxo ralado","Laranja"),
                    ("Ter","almoco","Peixe assado com limão","Purê de batata e arroz","Rúcula com beterraba","Melão"),
                    ("Ter","jantar","Carne moída refogada","Arroz com brócolis e feijão","Pepino com cenoura","Pêssego"),
                    ("Qua","almoco","Fraldinha ao molho madeira","Arroz branco e feijão carioca","Mix de folhas verdes","Goiaba"),
                    ("Qua","jantar","Omelete de legumes","Arroz integral e lentilha","Alface com tomate","Maçã"),
                    ("Qui","almoco","Frango ao molho pardo","Polenta cremosa e arroz","Couve refogada com alho","Abacaxi"),
                    ("Qui","jantar","Peixe grelhado com ervas","Arroz e feijão preto","Tomate com cebola roxa","Manga"),
                    ("Sex","almoco","Costela suína assada","Arroz com pequi e feijão","Salada caesar","Uva"),
                    ("Sex","jantar","Frango xadrez","Arroz branco e feijão carioca","Acelga com cenoura","Pera"),
                ]
            )


# ─── FUNÇÕES: ALUNO (ATUALIZADA COM COMPARAÇÃO DE HASH) ──────────
def login_aluno(ra: str, senha: str):
    """Autentica o aluno convertendo a senha digitada em Hash SHA-256 para checagem."""
    senha_hash_digitada = gerar_hash_senha(senha)
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM alunos WHERE (ra=? OR ra_num=?) AND senha_hash=?",
            (ra.lower().strip(), ra.strip().zfill(8), senha_hash_digitada)
        ).fetchone()
        return dict(row) if row else None


def get_aluno(ra_num: str):
    """Retorna dados do aluno pelo RA numérico."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM alunos WHERE ra_num=?", (ra_num.zfill(8),)
        ).fetchone()
        return dict(row) if row else None


def get_saldo(ra_num: str, tipo: str) -> int:
    """Retorna saldo de fichas do tipo informado."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT saldo FROM fichas WHERE ra_num=? AND tipo=?",
            (ra_num.zfill(8), tipo)
        ).fetchone()
        return row["saldo"] if row else 0


def get_historico_fichas(ra_num: str, limit: int = 15):
    """Retorna histórico de transações do aluno."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM transacoes WHERE ra_num=? ORDER BY criado_em DESC LIMIT ?",
            (ra_num.zfill(8), limit)
        ).fetchall()
        return [dict(r) for r in rows]


def get_historico_refeicoes(ra_num: str, limit: int = 20):
    """Retorna acessos liberados do aluno (histórico de refeições)."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM acessos WHERE ra_num=? AND status LIKE '%Liberado%' ORDER BY criado_em DESC LIMIT ?",
            (ra_num.zfill(8), limit)
        ).fetchall()
        return [dict(r) for r in rows]


def comprar_fichas(ra_num: str, tipo: str, qtd: int, valor: float):
    """Credita fichas após pagamento confirmado."""
    ra_num = ra_num.zfill(8)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO fichas (ra_num,tipo,saldo) VALUES (?,?,?) ON CONFLICT(ra_num,tipo) DO UPDATE SET saldo=saldo+?",
            (ra_num, tipo, qtd, qtd)
        )
        conn.execute(
            "INSERT INTO transacoes (ra_num,tipo,refeicao,qtd,valor,status) VALUES (?,?,?,?,?,?)",
            (ra_num, "Compra", tipo, qtd, valor, "ok")
        )


def salvar_avaliacao(ra_num: str, notas: dict, comentario: str):
    """Registra avaliação do restaurante."""
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO avaliacoes (ra_num,qualidade,atendimento,higiene,variedade,comentario) VALUES (?,?,?,?,?,?)",
            (ra_num.zfill(8), notas.get("qualidade"), notas.get("atendimento"),
             notas.get("higiene"), notas.get("variedade"), comentario)
        )


# ─── FUNÇÕES: CATRACA / RU ──────────────────────────
def buscar_aluno_catraca(ra_input: str):
    """Busca aluno por RA numérico ou textual."""
    ra_input = ra_input.strip()
    ra_norm  = ra_input.lstrip("0").zfill(8) if ra_input.isdigit() else ra_input
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM alunos WHERE ra_num=? OR ra=?",
            (ra_norm, ra_input.lower())
        ).fetchone()
        return dict(row) if row else None


def processar_acesso(ra_num: str, turno: str):
    """Tenta liberar acesso com base nas regras de negócio e saldo do estudante."""
    aluno = get_aluno(ra_num)
    if not aluno:
        return {"status": "nao_encontrado", "aluno": None, "saldo_restante": 0}

    if not aluno["ativo"]:
        return {"status": "inativo", "aluno": aluno, "saldo_restante": 0}

    saldo = get_saldo(ra_num, turno)
    if saldo <= 0:
        _registrar_acesso(ra_num, aluno["nome_curto"], turno, "⚠️ Sem ficha")
        return {"status": "sem_ficha", "aluno": aluno, "saldo_restante": 0}

    # Debita
    with get_conn() as conn:
        conn.execute(
            "UPDATE fichas SET saldo=saldo-1 WHERE ra_num=? AND tipo=?",
            (ra_num.zfill(8), turno)
        )
        conn.execute(
            "INSERT INTO transacoes (ra_num,tipo,refeicao,qtd,valor,status) VALUES (?,?,?,?,?,?)",
            (ra_num.zfill(8), "Uso", turno, -1, None, "ok")
        )

    saldo_restante = get_saldo(ra_num, turno)
    _registrar_acesso(ra_num, aluno["nome_curto"], turno, "✅ Liberado")
    return {"status": "ok", "aluno": aluno, "saldo_restante": saldo_restante}


def _registrar_acesso(ra_num: str, nome_curto: str, turno: str, status: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO acessos (ra_num,nome_curto,turno,status) VALUES (?,?,?,?)",
            (ra_num.zfill(8), nome_curto, turno, status)
        )


def get_log_acessos(limit: int = 50):
    """Retorna log de acessos do dia atual."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM acessos WHERE date(criado_em)=date('now','localtime') ORDER BY criado_em DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_stats_dia():
    """Retorna métricas consolidadas do dia para o painel de monitoramento do RU."""
    with get_conn() as conn:
        total     = conn.execute("SELECT COUNT(*) FROM acessos WHERE date(criado_em)=date('now','localtime')").fetchone()[0]
        liberados = conn.execute("SELECT COUNT(*) FROM acessos WHERE date(criado_em)=date('now','localtime') AND status LIKE '%Liberado%'").fetchone()[0]
        almoco    = conn.execute("SELECT COUNT(*) FROM acessos WHERE date(criado_em)=date('now','localtime') AND turno='Almoço' AND status LIKE '%Liberado%'").fetchone()[0]
        jantar    = conn.execute("SELECT COUNT(*) FROM acessos WHERE date(criado_em)=date('now','localtime') AND turno='Jantar' AND status LIKE '%Liberado%'").fetchone()[0]
        sem_ficha = conn.execute("SELECT COUNT(*) FROM acessos WHERE date(criado_em)=date('now','localtime') AND status LIKE '%Sem ficha%'").fetchone()[0]
    return {
        "total": total, "liberados": liberados, "negados": total - liberados,
        "almoco": almoco, "jantar": jantar,
        "sem_ficha": sem_ficha, "invalido": 0,
        "receita": liberados * 3.50, "subsidio": liberados * 8.38,
    }


def get_todos_alunos(busca: str = ""):
    """Lista todos os alunos com saldo de fichas para o painel administrativo."""
    with get_conn() as conn:
        if busca:
            rows = conn.execute(
                "SELECT * FROM alunos WHERE nome LIKE ? OR ra_num LIKE ? OR ra LIKE ?",
                (f"%{busca}%", f"%{busca}%", f"%{busca}%")
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM alunos ORDER BY nome").fetchall()

        alunos = []
        for r in rows:
            a = dict(r)
            a["fichas_almoco"] = get_saldo(a["ra_num"], "Almoço")
            a["fichas_jantar"] = get_saldo(a["ra_num"], "Jantar")
            alunos.append(a)
        return alunos


def get_cardapio(dia: str = None):
    """Retorna cardápio do dia informado (ou de todos os dias)."""
    with get_conn() as conn:
        if dia:
            rows = conn.execute("SELECT * FROM cardapio WHERE dia_semana=?", (dia,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM cardapio ORDER BY dia_semana, turno").fetchall()
        return [dict(r) for r in rows]


def atualizar_cardapio(dia: str, turno: str, dados: dict):
    """Atualiza ou insere um item do cardápio."""
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO cardapio (dia_semana,turno,prato_principal,guarnicao,salada,sobremesa)
            VALUES (?,?,?,?,?,?)
            ON CONFLICT(dia_semana,turno) DO UPDATE SET
                prato_principal=excluded.prato_principal,
                guarnicao=excluded.guarnicao,
                salada=excluded.salada,
                sobremesa=excluded.sobremesa
        """, (dia, turno, dados["prato_principal"], dados["guarnicao"], dados["salada"], dados["sobremesa"]))


# ─── INICIALIZAÇÃO AUTOMÁTICA ────────
criar_tabelas()
popular_banco()