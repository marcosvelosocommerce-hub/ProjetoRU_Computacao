import streamlit as st
from datetime import datetime
import random, string, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from db.database import (
    login_aluno, get_saldo, get_historico_fichas,
    get_historico_refeicoes, comprar_fichas, salvar_avaliacao,
    get_cardapio, get_aluno
)
from agenteia import renderizar_agente_ia

st.set_page_config(page_title="UTFPR", page_icon="🎓", layout="centered", initial_sidebar_state="collapsed")

def init_state():
    defaults = {
        "logged_in": False, "page": "carteirinha",
        "aluno": None, "pix_pendente": None,
        "avaliacao_enviada": False, "ficha_tipo_sel": "Almoço",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# Inicializadores de estado do Agente Inteligente no session_state
if "agente_aberto" not in st.session_state:
    st.session_state.agente_aberto = False
if "agente_mensagens" not in st.session_state:
    st.session_state.agente_mensagens = []

# ── AUTO-REFRESH: detecta mudança de saldo vinda do RU ───────────
if st.session_state.logged_in and st.session_state.aluno:
    ra = st.session_state.aluno["ra_num"]
    saldo_atual_a = get_saldo(ra, "Almoço")
    saldo_atual_j = get_saldo(ra, "Jantar")
    snap_a = st.session_state.get("snap_almoco")
    snap_j = st.session_state.get("snap_jantar")

    if snap_a is None:
        st.session_state.snap_almoco = saldo_atual_a
        st.session_state.snap_jantar = saldo_atual_j
    else:
        if saldo_atual_a != snap_a or saldo_atual_j != snap_j:
            diff_a = saldo_atual_a - snap_a
            diff_j = saldo_atual_j - snap_j
            st.session_state.snap_almoco = saldo_atual_a
            st.session_state.snap_jantar = saldo_atual_j
            if diff_a < 0:
                st.toast(f"🎟️ 1 ficha de Almoço utilizada na catraca! Saldo: {saldo_atual_a}", icon="✅")
            if diff_j < 0:
                st.toast(f"🎟️ 1 ficha de Jantar utilizada na catraca! Saldo: {saldo_atual_j}", icon="✅")
            if diff_a > 0 or diff_j > 0:
                st.toast("🎉 Fichas adicionadas ao seu saldo!", icon="💳")
# ── Streamlit fragment para auto-refresh a cada 5s ───────────────────────────
import time as _time

@st.fragment(run_every=5)
def _auto_refresh():
    if st.session_state.logged_in and st.session_state.aluno:
        ra = st.session_state.aluno["ra_num"]
        sa = get_saldo(ra, "Almoço")
        sj = get_saldo(ra, "Jantar")
        if sa != st.session_state.get("snap_almoco") or sj != st.session_state.get("snap_jantar"):
            st.rerun()

_auto_refresh()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
* { font-family: 'Roboto', sans-serif !important; box-sizing: border-box; }
[data-testid="stHeader"],footer,#MainMenu,[data-testid="stToolbar"],
[data-testid="stDecoration"],[data-testid="stSidebar"],.stDeployButton{display:none!important}
[data-testid="stAppViewContainer"]{background:#e5e5e5!important}
.block-container{padding:0 0 80px 0!important;max-width:480px!important;margin:0 auto!important;
    background:#fff!important;min-height:100vh!important;box-shadow:0 0 40px rgba(0,0,0,.18)!important;overflow-x:hidden!important}
.full-width{margin-left:-1rem;margin-right:-1rem}
.topbar{background:#F4A100;padding:14px 16px 12px;display:flex;align-items:center;gap:10px}
.topbar-logo{font-size:22px;font-weight:700;color:#fff;letter-spacing:-1px}
.topbar-logo span{color:#412402}
.topbar-right{margin-left:auto}
.section-hdr{background:#6B3FA0;color:#fff;font-size:13px;font-weight:500;padding:8px 16px}
.card{background:#fff;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,.10);margin:12px 0;overflow:hidden}
.card-header{background:#6B84B0;color:#fff;font-size:14px;font-weight:500;padding:10px 14px}
.card-body{padding:12px 14px}
.card-row{display:flex;justify-content:space-between;padding:5px 0;font-size:14px;border-bottom:1px solid #f0f0f0}
.card-row:last-child{border-bottom:none}
.card-label{font-weight:700;color:#222}
.card-value{color:#444}
.carteirinha{background:#fff;border-radius:12px;margin:12px 0;box-shadow:0 4px 20px rgba(0,0,0,.12);padding:24px 20px;text-align:center}
.carteirinha-name{font-size:16px;font-weight:700;color:#111;text-transform:uppercase;margin:16px 0 4px;line-height:1.2}
.carteirinha-ra{font-family:'Courier New',monospace!important;font-size:22px;font-weight:700;letter-spacing:4px;color:#111;margin:16px 0 4px}
.ficha-saldo-box{background:#6B3FA0;border-radius:14px;margin:12px 0;padding:20px;color:#fff;text-align:center}
.ficha-saldo-num{font-size:48px;font-weight:700;line-height:1}
.pix-key-box{background:#f0f0f0;border-radius:8px;padding:12px 14px;font-family:'Courier New',monospace!important;font-size:10px;word-break:break-all;color:#333;margin:8px 0}
.historico-item{display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid #f0f0f0;font-size:13px}
.historico-item:last-child{border-bottom:none}
.hist-badge-compra{background:#e8f5e9;color:#2e7d32;border-radius:20px;padding:2px 10px;font-size:11px;font-weight:500}
.hist-badge-uso{background:#fce4e4;color:#c62828;border-radius:20px;padding:2px 10px;font-size:11px;font-weight:500}
.login-hero{background:#F4A100;padding:48px 24px 36px;text-align:center}
.login-logo{font-size:42px;font-weight:700;color:#fff;letter-spacing:-2px;margin-bottom:4px}
.login-logo span{color:#412402}
.login-sub{font-size:14px;color:#fff;opacity:.85}
div[data-testid="stTextInput"] input,div[data-testid="stNumberInput"] input{border-radius:8px!important;border:1.5px solid #ddd!important;padding:10px 12px!important}
div[data-testid="stTextInput"] input:focus{border-color:#F4A100!important}
.stButton>button{border-radius:8px!important;font-weight:500!important;font-family:'Roboto',sans-serif!important;width:100%!important}
.btn-primary .stButton>button{background:#F4A100!important;color:#412402!important;border:none!important}
.btn-success .stButton>button{background:#2e7d32!important;color:#fff!important;border:none!important}
.btn-danger  .stButton>button{background:#f5f5f5!important;color:#c62828!important;border:1px solid #e0e0e0!important}
.btn-purple  .stButton>button{background:#6B3FA0!important;color:#fff!important;border:none!important}
.btn-outline .stButton>button{background:#fff!important;color:#6B3FA0!important;border:1.5px solid #6B3FA0!important}
.nav-btn .stButton>button{background:transparent!important;color:#888!important;border:none!important;box-shadow:none!important;font-size:12px!important;padding:4px 0!important}
.nav-btn-active .stButton>button{color:#F4A100!important;font-weight:600!important}

/* Estilos adicionais do container expandido da IA Minerva */
.agent-header { background: #6B3FA0; color: white; padding: 8px 12px; border-radius: 8px 8px 0 0; font-weight: 500; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

def barcode_svg(code):
    bars, x = [], 0
    widths = [1,1,2,1,3,1,2,1,1,2,3,1,1,2,1,3,2,1,1,2,1,1,3,1,2,1,1,2,3,1,1,2,1,1,2,3,1,2,1,1]
    for i, w in enumerate(widths):
        if i % 2 == 0:
            bars.append(f'<rect x="{x}" y="0" width="{w*2}" height="60" fill="#000"/>')
        x += w * 2 + 2
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {x} 60" width="220" height="60">{"".join(bars)}</svg>'

def gerar_chave_pix(qtd, tipo):
    valor = qtd * 3.50
    uid = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
    return f"00020126580014BR.GOV.BCB.PIX0136utfpr-ru@bancoutfpr.edu.br520400005303986540{valor:.2f}5802BR5913UTFPR RU PG6010PontaGrossa62290525FICHA{tipo[:3].upper()}{uid}6304ABCD"

def dia_semana_pt():
    return ["Seg","Ter","Qua","Qui","Sex","Sáb","Dom"][datetime.now().weekday()]

def topbar(title=""):
    extra = f"<span style='font-size:15px;color:#412402;font-weight:500;margin-left:4px'>{title}</span>" if title else ""
    st.markdown(f'<div class="topbar full-width"><div class="topbar-logo">UT<span>F</span>PR</div>{extra}<div class="topbar-right">🔔</div></div>', unsafe_allow_html=True)


# ── BOTTOM NAV (ATUALIZADA) ──────────────────────────────────────────────────
def bottom_nav():
    # Injeta a janela do Agente Inteligente logo antes de desenhar os botões de navegação
    renderizar_agente_ia()
    
    st.markdown("<hr style='margin:0 -1rem;border:none;border-top:1px solid #e0e0e0'>", unsafe_allow_html=True)
    cols = st.columns(4)
    for col, (pg, icon, label) in zip(cols, [("carteirinha","👤","Aluno"),("horarios","🕐","Horários"),("boletim","📖","Boletim"),("mais","☰","Mais")]):
        with col:
            st.markdown(f'<div class="{"nav-btn-active" if st.session_state.page==pg else "nav-btn"}">', unsafe_allow_html=True)
            if st.button(f"{icon}\n{label}", key=f"nav_{pg}", use_container_width=True):
                st.session_state.page = pg; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# ── PÁGINAS ──────────────────────────────────────────────────────────────────
def page_login():
    st.markdown('<div class="login-hero full-width"><div class="login-logo">UT<span>F</span>PR</div><div class="login-sub">Portal do Estudante</div></div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:15px;color:#333;margin-top:20px;font-weight:500;">Entrar na sua conta</p>', unsafe_allow_html=True)
    ra    = st.text_input("RA", placeholder="a2828227", key="login_ra")
    senha = st.text_input("Senha", type="password", key="login_senha")
    st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
    if st.button("Entrar", key="btn_login", use_container_width=True):
        aluno = login_aluno(ra.strip(), senha)
        if aluno:
            st.session_state.logged_in = True
            st.session_state.aluno = aluno
            st.session_state.page = "carteirinha"
            st.rerun()
        else:
            st.error("RA ou senha inválidos.")
    st.markdown('</div>', unsafe_allow_html=True)
    

def page_carteirinha():
    topbar()
    a = st.session_state.aluno
    fichas_total = get_saldo(a["ra_num"], "Almoço") + get_saldo(a["ra_num"], "Jantar")
    st.markdown(f"""
    <div class="carteirinha">
      <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/Bras%C3%A3o_de_armas_do_brasil.svg/120px-Bras%C3%A3o_de_armas_do_brasil.svg.png" style="width:54px"/>
      <p style="font-size:12px;color:#555;margin:8px 0 4px">Ministério da Educação<br>Universidade Tecnológica Federal do Paraná</p>
      <div style="width:120px;height:140px;background:#111;border-radius:6px;margin:12px auto;display:flex;align-items:center;justify-content:center;color:#666;font-size:12px;">📷 Foto</div>
      <div class="carteirinha-name">{a['nome']}</div>
      <div style="font-size:13px;color:#555;margin-bottom:2px">{a['curso']}</div>
      <div style="font-size:13px;color:#777">{a['periodo']} &nbsp;·&nbsp; Campus {a['campus']}</div>
      <div style="margin:16px auto 8px">{barcode_svg(a['ra_num'])}</div>
      <div class="carteirinha-ra">{a['ra_num']}</div>
      <div style="font-size:12px;color:#888">Validade: 31/12/2030</div>
    </div>
    """, unsafe_allow_html=True)
    saldo_almoco = get_saldo(a["ra_num"], "Almoço")
    saldo_jantar = get_saldo(a["ra_num"], "Jantar")
    if fichas_total > 0:
        st.markdown(f'''
        <div style="background:#F3EEFF;border-radius:10px;padding:12px 16px;border:1px solid #D7BFFF;margin-bottom:8px">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
            <span style="font-size:14px;color:#6B3FA0;font-weight:500">🎟️ Fichas disponíveis</span>
            <span style="font-size:18px;font-weight:700;color:#6B3FA0">{fichas_total}</span>
          </div>
          <div style="display:flex;gap:8px">
            <div style="flex:1;background:#fff;border-radius:8px;padding:10px;text-align:center;border:1px solid #D7BFFF">
              <div style="font-size:11px;color:#888;margin-bottom:4px">☀️ Almoço</div>
              <div style="font-size:22px;font-weight:700;color:#6B3FA0">{saldo_almoco}</div>
              <div style="font-size:10px;color:#aaa">fichas</div>
            </div>
            <div style="flex:1;background:#fff;border-radius:8px;padding:10px;text-align:center;border:1px solid #D7BFFF">
              <div style="font-size:11px;color:#888;margin-bottom:4px">🌙 Jantar</div>
              <div style="font-size:22px;font-weight:700;color:#6B3FA0">{saldo_jantar}</div>
              <div style="font-size:10px;color:#aaa">fichas</div>
            </div>
          </div>
        </div>
        ''', unsafe_allow_html=True)
    bottom_nav()

def page_mais():
    topbar()
    a = st.session_state.aluno
    fichas_total = get_saldo(a["ra_num"], "Almoço") + get_saldo(a["ra_num"], "Jantar")
    st.markdown(f'<div style="background:#F4A100;padding:16px;margin:0 -1rem"><div style="font-weight:700;font-size:15px;color:#412402">{a["nome"]}</div><div style="font-size:13px;color:#633806">RA: {a["ra"]}</div><div style="margin-top:8px;background:rgba(255,255,255,.25);border-radius:8px;padding:6px 12px;display:inline-block;font-size:13px;color:#412402">{a["curso"]} ▾</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-hdr full-width">Sobre o Aluno</div>', unsafe_allow_html=True)
    for pg, icon, label in [("carteirinha","👤","Aluno"),("horarios","🕐","Horários"),("boletim","📖","Boletim"),("historico_ac","📋","Histórico Acadêmico"),("matriz","⊞","Matriz"),("noticias","📰","Notícias")]:
        if st.button(f"{icon}  {label}", key=f"m_{pg}", use_container_width=True):
            st.session_state.page = pg; st.rerun()

    st.markdown('<div class="section-hdr full-width">Restaurante</div>', unsafe_allow_html=True)
    for pg, icon, label, badge in [("cardapio","🍎","Cardápio",""),("fichas","🎟️","Fichas Virtuais",f"{fichas_total} fichas" if fichas_total else ""),("hist_ref","🍽️","Histórico de Refeições",""),("avaliacao","👍","Avaliação do Restaurante","")]:
        col_a, col_b = st.columns([5,1])
        with col_a:
            if st.button(f"{icon}  {label}", key=f"m_{pg}", use_container_width=True):
                st.session_state.page = pg; st.rerun()
        with col_b:
            if badge:
                st.markdown(f'<div style="background:#e8f5e9;color:#2e7d32;border-radius:20px;padding:4px 8px;font-size:11px;font-weight:500;text-align:center;margin-top:6px">{badge}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-hdr full-width">Assistência Estudantil</div>', unsafe_allow_html=True)
    for pg, icon, label in [("nuape","💼","Nuape"),("serv_est","♿","Serviço Estudantil")]:
        if st.button(f"{icon}  {label}", key=f"m_{pg}", use_container_width=True):
            st.session_state.page = pg; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
    if st.button("Sair da conta", key="btn_sair", use_container_width=True):
        st.session_state.logged_in = False; st.session_state.aluno = None; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    bottom_nav()

def page_cardapio():
    topbar("Cardápio")
    dia = dia_semana_pt()
    rows = get_cardapio(dia if dia in ["Seg","Ter","Qua","Qui","Sex"] else "Seg")
    cardapio = {r["turno"]: r for r in rows}
    tab1, tab2 = st.tabs(["☀️ Almoço","🌙 Jantar"])
    for tab, turno_key, label in [(tab1,"almoco","Almoço"),(tab2,"jantar","Jantar")]:
        with tab:
            m = cardapio.get(turno_key)
            if m:
                st.markdown(f'<div class="card"><div class="card-header">📅 {dia} — {label} · Campus {st.session_state.aluno["campus"]}</div><div class="card-body"><div class="card-row"><span class="card-label">Prato principal</span><span class="card-value">{m["prato_principal"]}</span></div><div class="card-row"><span class="card-label">Guarnição</span><span class="card-value">{m["guarnicao"]}</span></div><div class="card-row"><span class="card-label">Salada</span><span class="card-value">{m["salada"]}</span></div><div class="card-row"><span class="card-label">Sobremesa</span><span class="card-value">{m["sobremesa"]}</span></div><div class="card-row"><span class="card-label">Valor pago</span><span class="card-value" style="color:#2e7d32;font-weight:600">R$ 3,50</span></div></div></div>', unsafe_allow_html=True)
            else:
                st.info("Cardápio não disponível.")
    bottom_nav()

def page_hist_refeicoes():
    topbar("Histórico de Refeições")
    a = st.session_state.aluno
    rows = get_historico_refeicoes(a["ra_num"])
    tab1, tab2 = st.tabs(["ALMOÇO","JANTAR"])
    for tab, turno in [(tab1,"Almoço"),(tab2,"Jantar")]:
        with tab:
            items = [r for r in rows if r["turno"] == turno]
            if not items:
                st.info("Nenhum registro.")
            for r in items:
                dt = r["criado_em"]
                st.markdown(f'<div class="card"><div class="card-header">{dt[:10].replace("-","/")[::-1].replace("/","/",2)[::-1]} {dt[11:16]}</div><div class="card-body"><div class="card-row"><span class="card-label">Valor pago:</span><span class="card-value">R$ 3,50</span></div><div class="card-row"><span class="card-label">Valor Subsídio:</span><span class="card-value">R$ 8,38</span></div><div class="card-row"><span class="card-label">Campus:</span><span class="card-value">{a["campus"]}</span></div></div></div>', unsafe_allow_html=True)
    bottom_nav()

def page_fichas():
    topbar("Fichas Virtuais")
    a    = st.session_state.aluno
    tipo = st.session_state.ficha_tipo_sel
    saldo = get_saldo(a["ra_num"], tipo)

    col1, col2 = st.columns(2)
    with col1:
        sel = "background:#F3EEFF;border:2px solid #6B3FA0;color:#6B3FA0;" if tipo=="Almoço" else "background:#f5f5f5;border:1px solid #ddd;color:#555;"
        st.markdown(f'<div style="{sel}border-radius:8px;padding:10px;text-align:center;font-size:13px;font-weight:500">☀️ Almoço<br><small style="color:#888">R$ 3,50 / ficha</small></div>', unsafe_allow_html=True)
        if st.button("Selecionar Almoço", key="sel_a", use_container_width=True):
            st.session_state.ficha_tipo_sel = "Almoço"; st.rerun()
    with col2:
        sel = "background:#F3EEFF;border:2px solid #6B3FA0;color:#6B3FA0;" if tipo=="Jantar" else "background:#f5f5f5;border:1px solid #ddd;color:#555;"
        st.markdown(f'<div style="{sel}border-radius:8px;padding:10px;text-align:center;font-size:13px;font-weight:500">🌙 Jantar<br><small style="color:#888">R$ 3,50 / ficha</small></div>', unsafe_allow_html=True)
        if st.button("Selecionar Jantar", key="sel_j", use_container_width=True):
            st.session_state.ficha_tipo_sel = "Jantar"; st.rerun()

    st.markdown(f'<div class="ficha-saldo-box"><div style="font-size:13px;opacity:.85;margin-bottom:6px">Saldo de fichas · {tipo}</div><div class="ficha-saldo-num">{saldo}</div><div style="font-size:12px;opacity:.75;margin-top:6px">Campus {a["campus"]}</div></div>', unsafe_allow_html=True)

    st.markdown("**Comprar fichas**")
    qtd = st.number_input("Quantidade", min_value=1, max_value=20, value=3, step=1, key="qtd_fichas")
    valor_total = qtd * 3.50
    st.markdown(f'<div style="display:flex;justify-content:space-between;font-size:14px;padding:10px;background:#F3EEFF;border-radius:8px;margin:8px 0"><span style="color:#555">{int(qtd)} ficha{"s" if qtd>1 else ""} de {tipo}</span><span style="font-weight:700;color:#6B3FA0">R$ {valor_total:.2f}</span></div>', unsafe_allow_html=True)

    pend = st.session_state.pix_pendente
    if pend and pend["tipo"] == tipo:
        st.markdown(f'<div style="background:#fff8e1;border-radius:10px;padding:14px;border:1px solid #ffe082;margin-top:8px"><div style="font-size:13px;font-weight:600;color:#e65100;margin-bottom:8px">⏳ Pix gerado — aguardando pagamento</div><div style="font-size:12px;color:#555;margin-bottom:6px">{pend["qtd"]} ficha{"s" if pend["qtd"]>1 else ""} · R$ {pend["valor"]:.2f}</div><div style="font-size:11px;color:#777;margin-bottom:4px">Chave Pix copia e cola:</div><div class="pix-key-box">{pend["chave"]}</div></div>', unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown('<div class="btn-success">', unsafe_allow_html=True)
            if st.button("✅ Simular pagamento", key="btn_pagar", use_container_width=True):
                comprar_fichas(a["ra_num"], tipo, pend["qtd"], pend["valor"])
                st.session_state.pix_pendente = None
                st.success(f"🎉 {pend['qtd']} ficha{'s' if pend['qtd']>1 else ''} adicionada{'s' if pend['qtd']>1 else ''}!")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col_b:
            st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
            if st.button("Cancelar", key="btn_cancel", use_container_width=True):
                st.session_state.pix_pendente = None; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="btn-purple">', unsafe_allow_html=True)
        if st.button(f"Gerar Pix · R$ {valor_total:.2f}", key="btn_gerar_pix", use_container_width=True):
            chave = gerar_chave_pix(int(qtd), tipo)
            st.session_state.pix_pendente = {"qtd":int(qtd),"valor":valor_total,"tipo":tipo,"chave":chave}
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Histórico de movimentações**")
    for h in get_historico_fichas(a["ra_num"]):
        badge = f'<span class="hist-badge-compra">+{h["qtd"]} ficha{"s" if h["qtd"]>1 else ""}</span>' if h["tipo"]=="Compra" else '<span class="hist-badge-uso">−1 ficha</span>'
        valor_str = f"R$ {h['valor']:.2f}" if h["valor"] else ""
        dt = h["criado_em"][:16]
        st.markdown(f'<div class="historico-item"><div><div style="font-weight:500;color:#222">{h["tipo"]} · {h["refeicao"]}</div><div style="font-size:12px;color:#888">{dt} {valor_str}</div></div>{badge}</div>', unsafe_allow_html=True)
    bottom_nav()

def page_avaliacao():
    topbar("Avaliação do Restaurante")
    if st.session_state.avaliacao_enviada:
        st.markdown('<div style="text-align:center;padding:48px 24px"><div style="font-size:64px;margin-bottom:16px">🏆</div><div style="font-size:18px;font-weight:600;color:#222;margin-bottom:8px">Obrigado pela avaliação!</div><div style="font-size:14px;color:#777">Sua opinião ajuda a melhorar o RU.</div></div>', unsafe_allow_html=True)
    else:
        st.markdown("**Avalie sua refeição de hoje**")
        notas = {}
        for asp, key in [("Qualidade da comida","qualidade"),("Atendimento","atendimento"),("Higiene","higiene"),("Variedade do cardápio","variedade")]:
            st.markdown(f'<p style="font-size:14px;color:#555;margin:12px 0 4px">{asp}</p>', unsafe_allow_html=True)
            notas[key] = st.select_slider(asp, options=[1,2,3,4,5], value=4, key=f"nota_{key}", label_visibility="collapsed", format_func=lambda x:"⭐"*x)
        comentario = st.text_area("Comentário (opcional)", placeholder="Sua opinião...", key="comentario")
        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
        if st.button("Enviar avaliação", key="btn_avaliar", use_container_width=True):
            salvar_avaliacao(st.session_state.aluno["ra_num"], notas, comentario)
            st.session_state.avaliacao_enviada = True; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    bottom_nav()

def page_placeholder(title, icon, msg):
    topbar(title)
    st.markdown(f'<div style="text-align:center;padding:64px 24px;color:#aaa"><div style="font-size:48px;margin-bottom:12px">{icon}</div><div style="font-size:15px">{msg}</div></div>', unsafe_allow_html=True)
    bottom_nav()

# ── ROUTER ────────────────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    page_login()
else:
    pg = st.session_state.page
    if   pg == "carteirinha": page_carteirinha()
    elif pg == "mais":        page_mais()
    elif pg == "cardapio":    page_cardapio()
    elif pg == "fichas":      page_fichas()
    elif pg == "hist_ref":    page_hist_refeicoes()
    elif pg == "avaliacao":   page_avaliacao()
    elif pg == "horarios":    page_placeholder("Horários","🕐","Horários de aula em breve.")
    elif pg == "boletim":     page_placeholder("Boletim","📖","Boletim acadêmico em breve.")
    elif pg == "historico_ac":page_placeholder("Histórico Acadêmico","📋","Histórico em breve.")
    elif pg == "matriz":      page_placeholder("Matriz Curricular","⊞","Matriz em breve.")
    elif pg == "noticias":    page_placeholder("Notícias","📰","Notícias em breve.")
    elif pg == "nuape":       page_placeholder("Nuape","💼","Nuape em breve.")
    else:                     page_carteirinha()