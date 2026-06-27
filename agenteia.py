import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
from db.database import get_saldo, get_cardapio, get_historico_refeicoes


def renderizar_agente_ia():
    """
    FAB flutuante + painel de chat 100% em HTML/JS/CSS puro,
    renderizado via components.html num iframe que injeta no documento pai.
    A API Gemini é chamada diretamente do JavaScript — zero dependência do
    runtime Streamlit para o chat funcionar.
    """
    if not st.session_state.get("logged_in") or not st.session_state.get("aluno"):
        return

    # ── Coleta contexto do aluno para passar ao prompt ──────────────────────
    aluno  = st.session_state.aluno
    ra_num = aluno["ra_num"]

    saldo_almoco        = get_saldo(ra_num, "Almoço")
    saldo_jantar        = get_saldo(ra_num, "Jantar")
    historico_refeicoes = get_historico_refeicoes(ra_num)[:5]
    cardapio_completo   = get_cardapio()

    dias_pt = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"]
    hoje    = dias_pt[datetime.now().weekday()]

    system_prompt = f"""Você é a "Minerva", assistente virtual do Restaurante Universitário (RU) da UTFPR Campus Ponta Grossa.
Seja prestativa, jovem, natural e direta (use emojis moderadamente).

DADOS DO ESTUDANTE (RA: {ra_num}):
- Saldo Almoço: {saldo_almoco} fichas
- Saldo Jantar: {saldo_jantar} fichas
- Últimos acessos: {historico_refeicoes}
- Hoje: {hoje}

CARDÁPIO DA SEMANA:
{cardapio_completo}

REGRAS DO RU:
- Ficha: R$ 3,50 por aluno
- Almoço: 11h00–13h30 | Jantar: 17h45–20h00
- Compra de fichas: via Pix no app (crédito imediato)
- Catraca: aproximar código de barras da carteirinha
- Problemas: procurar DEALÉ (Assistência Estudantil)

Responda apenas sobre o RU. Para outros assuntos, oriente a procurar a administração. Nunca invente dados."""

    # Pega a chave da API
    try:
        gemini_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        gemini_key = ""

    # ── HTML completo do FAB + painel ───────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; font-family:'Roboto',sans-serif; }}
  body {{ background:transparent; overflow:hidden; }}
</style>
</head>
<body>
<script>
(function() {{
  const GEMINI_KEY    = {repr(gemini_key)};
  const SYSTEM_PROMPT = {repr(system_prompt)};

  const doc = window.parent.document;

  /* ── Remove instância anterior (reruns do Streamlit) ── */
  ['minerva-fab','minerva-panel','minerva-overlay','minerva-styles'].forEach(id => {{
    const el = doc.getElementById(id);
    if (el) el.remove();
  }});

  /* ── Estilos injetados no pai ── */
  const style = doc.createElement('style');
  style.id = 'minerva-styles';
  style.textContent = `
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');

    #minerva-fab {{
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: linear-gradient(135deg, #6B3FA0, #9B6FD0);
      box-shadow: 0 4px 20px rgba(107,63,160,.55);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      z-index: 999998;
      transition: transform .18s, box-shadow .18s;
      -webkit-tap-highlight-color: transparent;
      user-select: none;
    }}
    #minerva-fab:hover  {{ transform: scale(1.10); box-shadow: 0 6px 28px rgba(107,63,160,.70); }}
    #minerva-fab:active {{ transform: scale(0.92); }}
    #minerva-fab .fab-icon {{ font-size:27px; line-height:1; pointer-events:none; }}

    #minerva-panel {{
      position: fixed;
      bottom: 96px;
      right: 24px;
      width: 320px;
      height: 460px;
      background: #fff;
      border-radius: 18px;
      box-shadow: 0 8px 40px rgba(107,63,160,.28), 0 2px 8px rgba(0,0,0,.10);
      border: 1.5px solid #D7BFFF;
      z-index: 999997;
      display: none;
      flex-direction: column;
      overflow: hidden;
      font-family: 'Roboto', sans-serif;
    }}
    #minerva-panel.open {{ display: flex; }}

    /* Cabeçalho */
    #minerva-header {{
      background: linear-gradient(135deg, #6B3FA0, #9B6FD0);
      padding: 12px 14px;
      display: flex;
      align-items: center;
      gap: 10px;
      flex-shrink: 0;
      border-radius: 16px 16px 0 0;
    }}
    #minerva-header .av {{ font-size:22px; line-height:1; }}
    #minerva-header .info .nm {{ font-size:14px; font-weight:700; color:#fff; line-height:1.2; }}
    #minerva-header .info .sb {{ font-size:11px; color:rgba(255,255,255,.75); }}
    #minerva-header .close {{
      margin-left:auto; color:rgba(255,255,255,.8); font-size:20px;
      cursor:pointer; padding:2px 7px; border-radius:50%;
      transition: background .15s;
    }}
    #minerva-header .close:hover {{ background:rgba(255,255,255,.18); color:#fff; }}

    /* Mensagens */
    #minerva-msgs {{
      flex: 1;
      overflow-y: auto;
      padding: 12px 12px 4px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      scroll-behavior: smooth;
    }}
    .msg-row {{ display:flex; align-items:flex-end; gap:7px; }}
    .msg-row.user {{ flex-direction:row-reverse; }}
    .msg-bubble {{
      max-width: 78%;
      padding: 9px 12px;
      border-radius: 16px;
      font-size: 13px;
      line-height: 1.5;
      word-break: break-word;
    }}
    .msg-row.bot  .msg-bubble {{ background:#F3EEFF; color:#222; border-bottom-left-radius:4px; }}
    .msg-row.user .msg-bubble {{ background:#6B3FA0; color:#fff; border-bottom-right-radius:4px; }}
    .msg-avatar {{
      width:28px; height:28px; border-radius:50%;
      background:linear-gradient(135deg,#6B3FA0,#9B6FD0);
      display:flex; align-items:center; justify-content:center;
      font-size:14px; flex-shrink:0;
    }}
    .msg-empty {{
      text-align:center; color:#bbb; font-size:13px;
      padding: 32px 16px; line-height:1.7;
    }}

    /* Digitando */
    .typing-dot {{
      display:inline-block; width:7px; height:7px; border-radius:50%;
      background:#9B6FD0; margin:0 2px;
      animation: bounce 1.2s infinite;
    }}
    .typing-dot:nth-child(2) {{ animation-delay:.2s; }}
    .typing-dot:nth-child(3) {{ animation-delay:.4s; }}
    @keyframes bounce {{
      0%,80%,100% {{ transform:translateY(0); }}
      40%          {{ transform:translateY(-6px); }}
    }}

    /* Input */
    #minerva-input-row {{
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 10px 10px;
      border-top: 1px solid #f0f0f0;
      flex-shrink: 0;
      background: #fff;
    }}
    #minerva-input {{
      flex: 1;
      border: 1.5px solid #D7BFFF;
      border-radius: 22px;
      padding: 9px 14px;
      font-size: 13px;
      outline: none;
      font-family: 'Roboto', sans-serif;
      transition: border-color .2s;
    }}
    #minerva-input:focus {{ border-color: #6B3FA0; }}
    #minerva-send {{
      width: 36px; height: 36px; border-radius: 50%;
      background: #6B3FA0; border: none; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0; transition: background .15s, transform .12s;
    }}
    #minerva-send:hover  {{ background: #5a3490; }}
    #minerva-send:active {{ transform: scale(0.90); }}
    #minerva-send svg {{ pointer-events:none; }}
  `;
  doc.head.appendChild(style);

  /* ── FAB ── */
  const fab = doc.createElement('div');
  fab.id = 'minerva-fab';
  fab.innerHTML = '<span class="fab-icon">🤖</span>';
  doc.body.appendChild(fab);

  /* ── Painel ── */
  const panel = doc.createElement('div');
  panel.id = 'minerva-panel';
  panel.innerHTML = `
    <div id="minerva-header">
      <div class="av">🤖</div>
      <div class="info">
        <div class="nm">Minerva</div>
        <div class="sb">Assistente do RU · UTFPR</div>
      </div>
      <div class="close" id="minerva-close">✕</div>
    </div>
    <div id="minerva-msgs">
      <div class="msg-empty">
        Olá! Como posso te ajudar? 👋<br>
        <i style="font-size:12px">"Qual o cardápio de hoje?"<br>"Quantas fichas eu tenho?"</i>
      </div>
    </div>
    <div id="minerva-input-row">
      <input id="minerva-input" type="text" placeholder="Digite sua dúvida..." />
      <button id="minerva-send">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
        </svg>
      </button>
    </div>
  `;
  doc.body.appendChild(panel);

  /* ── Estado e histórico ── */
  const history = []; // {{role:'user'|'model', parts:[{{text:...}}]}}

  function togglePanel() {{
    panel.classList.toggle('open');
  }}

  fab.addEventListener('click', togglePanel);
  doc.getElementById('minerva-close').addEventListener('click', togglePanel);

  /* ── Scroll para o fim ── */
  function scrollBottom() {{
    const msgs = doc.getElementById('minerva-msgs');
    msgs.scrollTop = msgs.scrollHeight;
  }}

  /* ── Adiciona bolha de mensagem ── */
  function addBubble(role, text) {{
    const msgs = doc.getElementById('minerva-msgs');
    // Remove empty state
    const empty = msgs.querySelector('.msg-empty');
    if (empty) empty.remove();

    const row = doc.createElement('div');
    row.className = 'msg-row ' + (role === 'user' ? 'user' : 'bot');

    if (role === 'bot') {{
      row.innerHTML = `
        <div class="msg-avatar">🤖</div>
        <div class="msg-bubble">${{text.replace(/\\n/g,'<br>')}}</div>
      `;
    }} else {{
      row.innerHTML = `<div class="msg-bubble">${{text.replace(/\\n/g,'<br>')}}</div>`;
    }}
    msgs.appendChild(row);
    scrollBottom();
    return row;
  }}

  /* ── Indicador "digitando..." ── */
  function addTyping() {{
    const msgs = doc.getElementById('minerva-msgs');
    const row = doc.createElement('div');
    row.className = 'msg-row bot';
    row.id = 'minerva-typing';
    row.innerHTML = `
      <div class="msg-avatar">🤖</div>
      <div class="msg-bubble" style="padding:10px 14px">
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
      </div>
    `;
    msgs.appendChild(row);
    scrollBottom();
  }}
  function removeTyping() {{
    const t = doc.getElementById('minerva-typing');
    if (t) t.remove();
  }}

  /* ── Chama a API Gemini ── */
  async function callGemini(userText) {{
    history.push({{ role:'user', parts:[{{text: userText}}] }});

    addTyping();

    const body = {{
      system_instruction: {{ parts: [{{ text: SYSTEM_PROMPT }}] }},
      contents: history,
      generationConfig: {{ maxOutputTokens: 512, temperature: 0.7 }}
    }};

    try {{
      const res = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${{GEMINI_KEY}}`,
        {{ method:'POST', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify(body) }}
      );
      const data = await res.json();
      removeTyping();

      let reply = 'Desculpe, não consegui processar sua pergunta agora.';
      if (data.candidates && data.candidates[0].content) {{
        reply = data.candidates[0].content.parts.map(p => p.text).join('');
      }} else if (data.error) {{
        reply = 'Erro: ' + data.error.message;
      }}

      history.push({{ role:'model', parts:[{{text: reply}}] }});
      addBubble('bot', reply);

    }} catch(e) {{
      removeTyping();
      addBubble('bot', 'Erro de conexão. Tente novamente.');
    }}
  }}

  /* ── Envio ── */
  function enviar() {{
    const input = doc.getElementById('minerva-input');
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    addBubble('user', text);
    callGemini(text);
  }}

  doc.getElementById('minerva-send').addEventListener('click', enviar);
  doc.getElementById('minerva-input').addEventListener('keydown', function(e) {{
    if (e.key === 'Enter' && !e.shiftKey) {{ e.preventDefault(); enviar(); }}
  }});

}})();
</script>
</body>
</html>"""

    
    components.html(html, height=0, scrolling=False)
