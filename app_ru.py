import streamlit as st
from datetime import datetime
import sys, os, html
sys.path.insert(0, os.path.dirname(__file__))
from db.database import (
    buscar_aluno_catraca, processar_acesso,
    get_log_acessos, get_stats_dia, get_todos_alunos,
    get_cardapio, atualizar_cardapio,
    get_avaliacoes, get_media_por_prato
)

def esc(texto):
    return html.escape(str(texto)) if texto else ""

st.set_page_config(page_title="RU UTFPR — Terminal", page_icon="🏪", layout="wide", initial_sidebar_state="expanded")

FUNCIONARIO = {"usuario":"ru","senha":"ru123","nome":"José da Silva"}

def init_state():
    defaults = {"logado":False,"aba":"catraca","ultimo_resultado":None}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
* { font-family: 'Roboto', sans-serif !important; }
[data-testid="stHeader"],footer,#MainMenu,.stDeployButton{display:none!important}
[data-testid="stSidebar"]{background:#1E1E2E!important}
[data-testid="stSidebar"] *{color:#ccc!important}
[data-testid="stSidebar"] .stButton>button{background:transparent!important;color:#ccc!important;border:none!important;text-align:left!important;width:100%!important;padding:10px 16px!important;font-size:14px!important;border-radius:6px!important}
[data-testid="stSidebar"] .stButton>button:hover{background:rgba(255,255,255,.08)!important;color:#fff!important}
.sidebar-ativo>div>button{background:rgba(107,63,160,.4)!important;color:#D4BFFF!important;border-left:3px solid #6B3FA0!important}
.metrica-card{background:#fff;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,.08);text-align:center;border-top:4px solid #6B3FA0}
.metrica-num{font-size:36px;font-weight:700;color:#1E1E2E;line-height:1}
.metrica-label{font-size:13px;color:#888;margin-top:6px}
.metrica-card.verde{border-top-color:#2e7d32}
.metrica-card.amarelo{border-top-color:#F4A100}
.metrica-card.vermelho{border-top-color:#c62828}
.resultado-ok{background:#e8f5e9;border-radius:12px;padding:24px;border-left:6px solid #2e7d32;text-align:center}
.resultado-sem-ficha{background:#fff8e1;border-radius:12px;padding:24px;border-left:6px solid #F4A100;text-align:center}
.resultado-erro{background:#fce4e4;border-radius:12px;padding:24px;border-left:6px solid #c62828;text-align:center}
.log-item{display:flex;justify-content:space-between;align-items:center;padding:10px 14px;border-radius:8px;margin-bottom:6px;font-size:13px}
.log-ok{background:#e8f5e9}.log-warn{background:#fff8e1}.log-err{background:#fce4e4}
.badge-ativo{background:#e8f5e9;color:#2e7d32;border-radius:20px;padding:2px 10px;font-size:11px;font-weight:500}
.badge-inativo{background:#fce4e4;color:#c62828;border-radius:20px;padding:2px 10px;font-size:11px;font-weight:500}
.badge-ficha{background:#F3EEFF;color:#6B3FA0;border-radius:20px;padding:2px 10px;font-size:11px;font-weight:500}
.stButton>button{border-radius:8px!important;font-weight:500!important}
.btn-primary .stButton>button{background:#6B3FA0!important;color:#fff!important;border:none!important}
.btn-success .stButton>button{background:#2e7d32!important;color:#fff!important;border:none!important}
.btn-danger  .stButton>button{background:#f5f5f5!important;color:#c62828!important;border:1px solid #ddd!important}
.btn-amarelo .stButton>button{background:#F4A100!important;color:#412402!important;border:none!important}
div[data-testid="stTextInput"] input{border-radius:8px!important;border:1.5px solid #ddd!important;padding:10px 12px!important;font-size:15px!important}
div[data-testid="stTextInput"] input:focus{border-color:#6B3FA0!important;box-shadow:0 0 0 3px rgba(107,63,160,.15)!important}
</style>
""", unsafe_allow_html=True)

# ── LOGIN ─────────────────────────────────────────────────────────────────────
def page_login():
    col_l, col_c, col_r = st.columns([1,1.2,1])
    with col_c:
        st.markdown('<div style="text-align:center;padding:40px 0 32px"><div style="font-size:48px;font-weight:700;color:#1E1E2E;letter-spacing:-2px">UT<span style="color:#6B3FA0">F</span>PR</div><div style="font-size:16px;color:#888;margin-top:4px">Sistema de Gestão — Restaurante Universitário</div></div>', unsafe_allow_html=True)
        st.markdown('<div style="background:#fff;border-radius:16px;padding:32px;box-shadow:0 4px 24px rgba(0,0,0,.10)">', unsafe_allow_html=True)
        st.markdown('<p style="font-size:16px;font-weight:600;color:#222;margin-bottom:20px">Acesso restrito — funcionários</p>', unsafe_allow_html=True)
        usuario = st.text_input("Usuário", placeholder="usuário", key="fu")
        senha   = st.text_input("Senha", type="password", key="fs")
        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
        if st.button("Entrar no sistema", key="btn_login_ru", use_container_width=True):
            if usuario == FUNCIONARIO["usuario"] and senha == FUNCIONARIO["senha"]:
                st.session_state.logado = True; st.rerun()
            else:
                st.error("Credenciais inválidas. Use: ru / ru123")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ── SIDEBAR ─────────────────────
def sidebar():
    with st.sidebar:
        st.markdown(f'<div style="padding:20px 16px 16px"><div style="font-size:24px;font-weight:700;color:#fff;letter-spacing:-1px">UT<span style="color:#9B6FD0">F</span>PR</div><div style="font-size:12px;color:#888;margin-top:2px">RU · Ponta Grossa</div><div style="margin-top:16px;padding-top:16px;border-top:1px solid #333"><div style="font-size:13px;color:#aaa">Funcionário</div><div style="font-size:14px;color:#ddd;font-weight:500">{FUNCIONARIO["nome"]}</div></div></div>', unsafe_allow_html=True)
        st.markdown('<div style="padding:0 8px">', unsafe_allow_html=True)
        for aba, label in [("catraca","🚪  Terminal da Catraca"),("relatorio","📊  Relatório do Dia"),("alunos","👥  Gerenciar Alunos"),("cardapio","🍽️  Cardápio")]:
            ativo = "sidebar-ativo" if st.session_state.aba == aba else ""
            st.markdown(f'<div class="{ativo}">', unsafe_allow_html=True)
            if st.button(label, key=f"sb_{aba}", use_container_width=True):
                st.session_state.aba = aba; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
        if st.button("Sair do sistema", key="btn_sair_ru", use_container_width=True):
            st.session_state.logado = False; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ── ABA: CATRACA ─────────────────────────
def aba_catraca():
    st.markdown(f"## 🚪 Terminal da Catraca")
    st.markdown(f"<p style='color:#888;margin-top:-12px'>🕐 {datetime.now().strftime('%d/%m/%Y  %H:%M')} &nbsp;·&nbsp; Campus Ponta Grossa</p>", unsafe_allow_html=True)

    col_esq, col_dir = st.columns([1.2,1], gap="large")
    with col_esq:
        st.markdown("### Leitura do código de barras")
        st.markdown('<p style="font-size:13px;color:#888;margin-top:-8px">Digite o RA ou use o leitor USB — ele preenche o campo automaticamente</p>', unsafe_allow_html=True)
        ra_input = st.text_input("📷  RA / Código de barras", placeholder="Aguardando leitura...", key="ra_catraca")
        turno    = st.radio("Refeição", ["Almoço","Jantar"], horizontal=True, key="turno_catraca")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
            processar = st.button("✅  Processar entrada", key="btn_proc", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with col_b:
            st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
            if st.button("🔄  Limpar", key="btn_limpar", use_container_width=True):
                st.session_state.ultimo_resultado = None; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        if processar and ra_input.strip():
            aluno = buscar_aluno_catraca(ra_input.strip())
            if not aluno:
                resultado = {"status":"nao_encontrado","aluno":None}
            elif not aluno["ativo"]:
                resultado = {"status":"inativo","aluno":aluno}
            else:
                resultado = processar_acesso(aluno["ra_num"], turno)
            st.session_state.ultimo_resultado = resultado
            st.rerun()

        res = st.session_state.ultimo_resultado
        if res:
            st.markdown("<br>", unsafe_allow_html=True)
            if res["status"] == "ok":
                a = res["aluno"]
                st.markdown(f'<div class="resultado-ok"><div style="font-size:40px;margin-bottom:8px">✅</div><div style="font-size:22px;font-weight:700;color:#1b5e20">ACESSO LIBERADO</div><div style="font-size:16px;color:#2e7d32;margin-top:8px;font-weight:500">{a["nome"]}</div><div style="font-size:13px;color:#555;margin-top:4px">{a["curso"]} · {a["periodo"]} · RA {a["ra_num"]}</div><div style="background:#fff;border-radius:8px;padding:10px;margin-top:12px;display:inline-block;min-width:200px">🎟️ <b>{turno}</b> &nbsp;·&nbsp; Saldo restante: <b>{res["saldo_restante"]} ficha{"s" if res["saldo_restante"]!=1 else ""}</b></div></div>', unsafe_allow_html=True)
            elif res["status"] == "sem_ficha":
                a = res["aluno"]
                st.markdown(f'<div class="resultado-sem-ficha"><div style="font-size:40px;margin-bottom:8px">⚠️</div><div style="font-size:20px;font-weight:700;color:#e65100">SEM FICHAS DE {turno.upper()}</div><div style="font-size:16px;color:#333;margin-top:8px;font-weight:500">{a["nome"]}</div><div style="font-size:13px;color:#555;margin-top:4px">{a["curso"]} · RA {a["ra_num"]}</div><div style="font-size:13px;color:#e65100;margin-top:10px">Oriente o aluno a comprar fichas no app UTFPR.</div></div>', unsafe_allow_html=True)
            elif res["status"] == "inativo":
                a = res["aluno"]
                st.markdown(f'<div class="resultado-erro"><div style="font-size:40px;margin-bottom:8px">🚫</div><div style="font-size:20px;font-weight:700;color:#b71c1c">CADASTRO INATIVO</div><div style="font-size:14px;color:#555;margin-top:10px">{a["nome"]} — Oriente o aluno a procurar a secretaria.</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="resultado-erro"><div style="font-size:40px;margin-bottom:8px">❌</div><div style="font-size:20px;font-weight:700;color:#b71c1c">RA NÃO ENCONTRADO</div><div style="font-size:14px;color:#555;margin-top:10px">RA <code>{ra_input}</code> não está cadastrado no sistema.</div></div>', unsafe_allow_html=True)

    with col_dir:
        st.markdown("### Registro de hoje")
        stats = get_stats_dia()
        col_m1, col_m2 = st.columns(2)
        with col_m1: st.markdown(f'<div class="metrica-card verde"><div class="metrica-num">{stats["liberados"]}</div><div class="metrica-label">Liberados</div></div>', unsafe_allow_html=True)
        with col_m2: st.markdown(f'<div class="metrica-card vermelho"><div class="metrica-num">{stats["negados"]}</div><div class="metrica-label">Negados</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        log = get_log_acessos(12)
        if not log:
            st.markdown('<p style="color:#aaa;text-align:center;padding:20px">Nenhum acesso ainda</p>', unsafe_allow_html=True)
        for e in log:
            css = "log-ok" if "Liberado" in e["status"] else ("log-warn" if "Sem" in e["status"] else "log-err")
            hora = e["criado_em"][11:19]
            st.markdown(f'<div class="log-item {css}"><div><span style="font-weight:500;color:#222">{e["nome_curto"]}</span><span style="color:#777;font-size:12px;margin-left:6px">RA {e["ra_num"]}</span><br><span style="font-size:12px;color:#555">{e["turno"]} · {hora}</span></div><span style="font-size:13px">{e["status"]}</span></div>', unsafe_allow_html=True)

# ── ABA: RELATÓRIO ─────────
def aba_relatorio():
    st.markdown("## 📊 Relatório do Dia")
    st.markdown(f"<p style='color:#888;margin-top:-12px'>{datetime.now().strftime('%d/%m/%Y')} · Campus Ponta Grossa</p>", unsafe_allow_html=True)
    s = get_stats_dia()
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f'<div class="metrica-card"><div class="metrica-num">{s["total"]}</div><div class="metrica-label">Total de acessos</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metrica-card verde"><div class="metrica-num">{s["liberados"]}</div><div class="metrica-label">Refeições servidas</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metrica-card amarelo"><div class="metrica-num">R$ {s["receita"]:.0f}</div><div class="metrica-label">Arrecadação</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="metrica-card vermelho"><div class="metrica-num">R$ {s["subsidio"]:.0f}</div><div class="metrica-label">Subsídio aplicado</div></div>', unsafe_allow_html=True)
    st.markdown('<br>', unsafe_allow_html=True)
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("#### Por turno")
        st.markdown(f'<div style="background:#F3EEFF;border-radius:10px;padding:16px;margin-bottom:8px;display:flex;justify-content:space-between"><span style="font-weight:500">☀️ Almoço</span><span style="font-weight:700;color:#6B3FA0">{s["almoco"]} refeições</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="background:#F3EEFF;border-radius:10px;padding:16px;display:flex;justify-content:space-between"><span style="font-weight:500">🌙 Jantar</span><span style="font-weight:700;color:#6B3FA0">{s["jantar"]} refeições</span></div>', unsafe_allow_html=True)
    with col_r:
        st.markdown("#### Acessos negados")
        st.markdown(f'<div style="background:#fff8e1;border-radius:10px;padding:16px;margin-bottom:8px;display:flex;justify-content:space-between"><span>⚠️ Sem fichas</span><span style="font-weight:700;color:#e65100">{s["sem_ficha"]}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="background:#fce4e4;border-radius:10px;padding:16px;display:flex;justify-content:space-between"><span>❌ RA inválido</span><span style="font-weight:700;color:#c62828">{s["invalido"]}</span></div>', unsafe_allow_html=True)
    st.markdown('<br>', unsafe_allow_html=True)
    st.markdown("#### Histórico completo")
    for e in get_log_acessos(100):
        css = "log-ok" if "Liberado" in e["status"] else ("log-warn" if "Sem" in e["status"] else "log-err")
        hora = e["criado_em"][11:19]
        st.markdown(f'<div class="log-item {css}" style="margin-bottom:4px"><span><b>{e["nome_curto"]}</b> <span style="color:#888;font-size:12px">RA {e["ra_num"]}</span></span><span style="color:#555;font-size:13px">{e["turno"]} · {hora}</span><span>{e["status"]}</span></div>', unsafe_allow_html=True)

    # ── Avaliações dos alunos ──
    st.markdown('<br><br>', unsafe_allow_html=True)
    st.markdown("#### ⭐ Avaliações dos Alunos")
    avaliacoes = get_avaliacoes(200)
    if not avaliacoes:
        st.markdown('<p style="color:#aaa;text-align:center;padding:20px">Nenhuma avaliação registrada ainda.</p>', unsafe_allow_html=True)
    else:
        n = len(avaliacoes)
        medias = {
            "Qualidade":    sum(a["qualidade"]   or 0 for a in avaliacoes) / n,
            "Atendimento":  sum(a["atendimento"] or 0 for a in avaliacoes) / n,
            "Higiene":      sum(a["higiene"]     or 0 for a in avaliacoes) / n,
            "Variedade":    sum(a["variedade"]   or 0 for a in avaliacoes) / n,
        }
        cm1, cm2, cm3, cm4 = st.columns(4)
        for col, (label, val) in zip([cm1, cm2, cm3, cm4], medias.items()):
            with col:
                st.markdown(f'<div class="metrica-card"><div class="metrica-num">{val:.1f}⭐</div><div class="metrica-label">{label}</div></div>', unsafe_allow_html=True)

        st.markdown('<br>', unsafe_allow_html=True)
        st.markdown("##### 🍽️ Nota média por prato")
        ranking = get_media_por_prato()
        if ranking:
            import pandas as pd
            df = pd.DataFrame(ranking).set_index("prato")
            st.bar_chart(df["media"], color="#6B3FA0")

            melhor, pior = ranking[0], ranking[-1]
            cb1, cb2 = st.columns(2)
            with cb1:
                st.success(f"🏆 Melhor avaliado: **{esc(melhor['prato'])}** — {melhor['media']}⭐ ({melhor['qtd']} avaliações)")
            with cb2:
                st.error(f"⚠️ Pior avaliado: **{esc(pior['prato'])}** — {pior['media']}⭐ ({pior['qtd']} avaliações)")
        else:
            st.markdown('<p style="color:#aaa;font-size:13px">Sem dados de prato suficientes ainda.</p>', unsafe_allow_html=True)

        st.markdown('<br>', unsafe_allow_html=True)
        st.markdown("##### 💬 Comentários recentes")
        comentarios = [a for a in avaliacoes if a.get("comentario")]
        if not comentarios:
            st.markdown('<p style="color:#aaa;font-size:13px">Nenhum comentário escrito ainda.</p>', unsafe_allow_html=True)
        for a in comentarios[:15]:
            hora = a["criado_em"][11:16]
            data = a["criado_em"][:10]
            st.markdown(
                f'<div class="log-item" style="margin-bottom:4px;flex-direction:column;align-items:flex-start;gap:2px">'
                f'<span style="font-size:13px;color:#222">{esc(a["comentario"])}</span>'
                f'<span style="color:#888;font-size:11px">{esc(a.get("turno") or "")} · {esc(a.get("prato") or "")} · {data} {hora}</span>'
                f'</div>', unsafe_allow_html=True
            )

# ── ABA: ALUNOS ───────────────────
def aba_alunos():
    st.markdown("## 👥 Gerenciar Alunos")
    busca   = st.text_input("🔍  Buscar por nome ou RA", placeholder="Ex: Marcos ou 02828227", key="busca_aluno")
    alunos  = get_todos_alunos(busca)
    st.markdown(f'<p style="color:#888;font-size:13px">{len(alunos)} aluno{"s" if len(alunos)!=1 else ""} encontrado{"s" if len(alunos)!=1 else ""}</p>', unsafe_allow_html=True)
    st.markdown('<div style="background:#fff;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,.08);overflow:hidden">', unsafe_allow_html=True)
    st.markdown('<div style="display:grid;grid-template-columns:2fr 2fr 1fr 1fr 1fr;padding:10px 16px;background:#f5f5f5;font-size:12px;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:.5px"><span>Aluno</span><span>Curso</span><span>Status</span><span>Almoço</span><span>Jantar</span></div>', unsafe_allow_html=True)
    for a in alunos:
        badge = '<span class="badge-ativo">Ativo</span>' if a["ativo"] else '<span class="badge-inativo">Inativo</span>'
        st.markdown(f'<div style="display:grid;grid-template-columns:2fr 2fr 1fr 1fr 1fr;padding:12px 16px;border-top:1px solid #f0f0f0;align-items:center"><div><div style="font-weight:500;color:#222;font-size:14px">{a["nome_curto"]}</div><div style="font-size:12px;color:#888">RA {a["ra_num"]}</div></div><div style="font-size:13px;color:#555">{a["curso"]}<br><span style="color:#aaa;font-size:12px">{a["periodo"]}</span></div><div>{badge}</div><div><span class="badge-ficha">{a["fichas_almoco"]} 🎟️</span></div><div><span class="badge-ficha">{a["fichas_jantar"]} 🎟️</span></div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── ABA: CARDÁPIO ───────────────
def aba_cardapio():
    st.markdown("## 🍽️ Cardápio da Semana")
    dias_nome = {"Seg":"Segunda","Ter":"Terça","Qua":"Quarta","Qui":"Quinta","Sex":"Sexta"}
    dia_hoje  = ["Seg","Ter","Qua","Qui","Sex","Sáb","Dom"][datetime.now().weekday()]

    tab_vis, tab_edit = st.tabs(["📋 Visualizar", "✏️ Editar"])

    with tab_vis:
        for dia in ["Seg","Ter","Qua","Qui","Sex"]:
            rows = get_cardapio(dia)
            cardapio = {r["turno"]: r for r in rows}
            destaque = "border:2px solid #6B3FA0;" if dia==dia_hoje else "border:1px solid #eee;"
            hoje_label = " <span style='background:#6B3FA0;color:#fff;border-radius:20px;padding:2px 10px;font-size:11px;font-weight:500'>Hoje</span>" if dia==dia_hoje else ""
            st.markdown(f'<div style="{destaque}border-radius:12px;padding:16px 20px;margin-bottom:12px;background:#fff"><div style="font-size:15px;font-weight:600;color:#222;margin-bottom:12px">{dias_nome[dia]}{hoje_label}</div>', unsafe_allow_html=True)
            col_a, col_j = st.columns(2)
            for col, turno_key, icon in [(col_a,"almoco","☀️ Almoço"),(col_j,"jantar","🌙 Jantar")]:
                with col:
                    t = cardapio.get(turno_key)
                    if t:
                        st.markdown(f'<div style="background:#fafafa;border-radius:8px;padding:12px"><div style="font-size:13px;font-weight:600;color:#555;margin-bottom:8px">{icon}</div><div style="font-size:13px;color:#222"><b>Prato:</b> {t["prato_principal"]}<br><b>Guarnição:</b> {t["guarnicao"]}<br><b>Salada:</b> {t["salada"]}<br><b>Sobremesa:</b> {t["sobremesa"]}</div></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    with tab_edit:
        st.markdown("Atualize o cardápio diretamente aqui:")
        dia_sel   = st.selectbox("Dia", list(dias_nome.keys()), format_func=lambda d: dias_nome[d], key="edit_dia")
        turno_sel = st.selectbox("Turno", ["almoco","jantar"], format_func=lambda t: "☀️ Almoço" if t=="almoco" else "🌙 Jantar", key="edit_turno")
        rows = get_cardapio(dia_sel)
        atual = {r["turno"]: r for r in rows}.get(turno_sel, {})
        prato   = st.text_input("Prato principal", value=atual.get("prato_principal",""), key="ep")
        guarnic = st.text_input("Guarnição",       value=atual.get("guarnicao",""),       key="eg")
        salada  = st.text_input("Salada",           value=atual.get("salada",""),          key="es")
        sobrem  = st.text_input("Sobremesa",        value=atual.get("sobremesa",""),       key="eso")
        st.markdown('<div class="btn-amarelo">', unsafe_allow_html=True)
        if st.button("💾  Salvar cardápio", key="btn_salvar_cardapio", use_container_width=True):
            atualizar_cardapio(dia_sel, turno_sel, {"prato_principal":prato,"guarnicao":guarnic,"salada":salada,"sobremesa":sobrem})
            st.success("Cardápio atualizado! O app do aluno já reflete a mudança.")
        st.markdown('</div>', unsafe_allow_html=True)

# ── ROUTER ───────────────────────
if not st.session_state.logado:
    page_login()
else:
    sidebar()
    aba = st.session_state.aba
    if   aba == "catraca":   aba_catraca()
    elif aba == "relatorio": aba_relatorio()
    elif aba == "alunos":    aba_alunos()
    elif aba == "cardapio":  aba_cardapio()
