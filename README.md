# 🎓 Sistema RU UTFPR — Portal do Estudante & Terminal de Catraca

Sistema de gestão do Restaurante Universitário (RU) da UTFPR — Campus Ponta Grossa, desenvolvido em **Python + Streamlit**, com banco de dados **SQLite** compartilhado entre dois aplicativos independentes: um para o **aluno** (mobile-first) e outro para o **terminal do funcionário do RU** (catraca/administração). Inclui também um assistente virtual de IA ("Minerva") integrado via API do Gemini.

---

## 📁 Estrutura do projeto

```
projeto/
├── app_aluno.py        # App do estudante (carteirinha, fichas, cardápio, avaliação)
├── app_ru.py            # Terminal do funcionário do RU (catraca, relatórios, gestão)
├── agenteia.py           # Chatbot "Minerva" (assistente de IA via Gemini)
├── db/
│   └── database.py      # Camada de dados — SQLite, regras de negócio, seed inicial
├── alunos.csv            # Base inicial de alunos (carga automática no 1º start)
└── utfpr.db               # Banco SQLite gerado automaticamente (não versionar)
```

> ⚠️ Os imports usam `from db.database import ...`, portanto **`database.py` deve estar dentro de uma pasta `db/`**, na mesma raiz dos dois apps.

---

## 🧩 Visão geral da arquitetura

```
alunos.csv ──(seed automático)──▶  database.py (SQLite: utfpr.db)
                                          ▲                ▲
                                          │                │
                                    app_aluno.py       app_ru.py
                                          │
                                    agenteia.py (chat Minerva)
```

Os dois apps Streamlit são **processos independentes**, mas leem e escrevem no **mesmo arquivo SQLite** (modo `WAL`, que permite leitura concorrente). Isso significa que uma ação feita no terminal do RU (ex.: debitar uma ficha na catraca) é refletida quase em tempo real no app do aluno, graças a um mecanismo de auto-refresh.

---

## 🗄️ `database.py` — Camada de dados

Módulo central, importado pelos dois apps. Na primeira execução, cria as tabelas e popula o banco automaticamente.

### Tabelas

| Tabela | Descrição |
|---|---|
| `alunos` | Dados cadastrais do estudante (RA, nome, curso, período, campus, senha em hash, status ativo/inativo) |
| `fichas` | Saldo de fichas por aluno e tipo de refeição (`Almoço` / `Jantar`) |
| `transacoes` | Histórico de compra (`Compra`) e uso (`Uso`) de fichas |
| `acessos` | Log de cada passagem na catraca (liberado, sem ficha, inativo etc.) |
| `cardapio` | Prato principal, guarnição, salada e sobremesa por dia da semana (`Seg`–`Sex`) e turno (`almoco`/`jantar`) |
| `avaliacoes` | Avaliação do aluno sobre o restaurante: notas (qualidade, atendimento, higiene, variedade), comentário, **turno** e **prato avaliado** (snapshot no momento do envio) |

### Segurança de senha

```python
def gerar_hash_senha(senha_pura: str) -> str:
    return hashlib.sha256(senha_pura.strip().encode('utf-8')).hexdigest()
```

O banco **nunca armazena a senha em texto puro** — apenas o hash SHA-256. No login, a senha digitada é hasheada e comparada com o hash salvo (`login_aluno`).

> ℹ️ SHA-256 puro não tem *salt* nem *work factor* — para produção real, recomenda-se migrar para `bcrypt` ou `argon2`.

### Seed automático (`popular_banco`)

- Se a tabela `alunos` estiver vazia, procura `alunos.csv` em alguns caminhos relativos e importa cada linha (hasheando a senha antes de gravar) + cria os saldos iniciais de fichas.
- Se a tabela `cardapio` estiver vazia, insere um cardápio padrão para a semana toda (Segunda a Sexta, almoço e jantar).
- `criar_tabelas()` e `popular_banco()` são chamadas automaticamente no final do arquivo — ou seja, **basta importar o módulo** que o banco já é criado/populado.

### Principais funções

| Função | Uso |
|---|---|
| `login_aluno(ra, senha)` | Autentica comparando hash da senha |
| `get_saldo(ra_num, tipo)` | Retorna saldo de fichas (Almoço/Jantar) |
| `comprar_fichas(...)` | Credita fichas e grava transação de compra |
| `processar_acesso(ra_num, turno)` | Lógica central da catraca: valida aluno ativo, saldo > 0, debita ficha, grava acesso |
| `get_historico_fichas` / `get_historico_refeicoes` | Histórico de transações / refeições do aluno |
| `get_cardapio(dia)` / `get_cardapio_dia(dia, turno)` | Cardápio completo de um dia, ou item específico dia+turno |
| `atualizar_cardapio(dia, turno, dados)` | Edita/insere item do cardápio |
| `salvar_avaliacao(ra_num, turno, prato, notas, comentario)` | Grava avaliação com snapshot do turno e prato avaliados |
| `get_avaliacoes(limite)` | Lista as avaliações mais recentes |
| `get_media_por_prato()` | Nota média (qualidade+atendimento+higiene+variedade)/4 agrupada por prato — usada no ranking de melhor/pior prato |
| `get_stats_dia()` | Métricas do dia: total de acessos, liberados, receita estimada, subsídio |
| `get_todos_alunos(busca)` | Lista alunos com saldo de fichas, com busca por nome/RA |

---

## 👤 `app_aluno.py` — App do Estudante

Interface mobile-first (largura fixa de 480px, sidebar/menu nativo do Streamlit ocultado via CSS) simulando um app real, com identidade visual da UTFPR.

### Funcionalidades

- **Login** por RA + senha (`login_aluno`).
- **Carteirinha digital**: nome, curso, período, campus, código de barras gerado em SVG puro (`barcode_svg`) e saldo de fichas em destaque.
- **Cardápio da semana**: abas Almoço/Jantar, prato do dia atual.
- **Fichas virtuais**: seleção de Almoço/Jantar, geração de chave Pix fictícia (`gerar_chave_pix`) e botão "Simular pagamento" que credita o saldo (⚠️ fluxo de demonstração, sem gateway de pagamento real).
- **Histórico de refeições**: lista de acessos liberados na catraca.
- **Avaliação do restaurante**: aluno escolhe o turno (Almoço/Jantar), o sistema busca automaticamente o prato real daquele turno no cardápio do dia (`get_cardapio_dia`) e grava nota + comentário com esse snapshot do prato.
- **Páginas placeholder**: Horários, Boletim, Histórico Acadêmico, Matriz Curricular, Notícias, Nuape — reservadas para integrações futuras.
- **Assistente Minerva**: botão flutuante de chat, injetado em todas as páginas internas via `bottom_nav()` → `renderizar_agente_ia()`.

### Auto-refresh de saldo

```python
@st.fragment(run_every=5)
def _auto_refresh():
    ...
```

A cada 5 segundos, compara o saldo atual no banco com um snapshot guardado em `session_state`. Se mudou (ex.: catraca debitou uma ficha no terminal do RU), dispara `st.rerun()` e mostra um toast de notificação — é assim que o app do aluno "sente" ações feitas em outro processo quase em tempo real.

---

## 🏪 `app_ru.py` — Terminal do Funcionário do RU

Layout `wide`, com sidebar escura, voltado para o uso operacional no balcão do restaurante.

> ⚠️ Login atualmente fixo no código (`usuario="ru"`, `senha="ru123"`), sem hash — recomenda-se mover para `st.secrets` antes de produção.

### Abas

| Aba | Função |
|---|---|
| **Terminal da Catraca** | Campo de RA (digitado ou lido por leitor de código de barras USB), seleção de turno, processa acesso via `processar_acesso` e mostra resultado (liberado / sem ficha / inativo / não encontrado) |
| **Relatório do Dia** | Métricas do dia (`get_stats_dia`): total de acessos, refeições servidas, arrecadação, subsídio aplicado, divisão por turno, acessos negados, histórico completo do dia, **+ seção de Avaliações dos Alunos** (ver abaixo) |
| **Gerenciar Alunos** | Busca por nome/RA, listagem com status (ativo/inativo) e saldo de fichas |
| **Cardápio** | Visualização da semana inteira, ou edição de prato/guarnição/salada/sobremesa por dia e turno |

### 📊 Seção de Avaliações (dentro do Relatório do Dia)

- 4 cards com a **nota média geral** por critério (Qualidade, Atendimento, Higiene, Variedade).
- **Gráfico de barras** (`st.bar_chart`, requer `pandas`) com a **nota média por prato avaliado**, calculada via `get_media_por_prato()`.
- Destaque automático do **🏆 melhor prato avaliado** e **⚠️ pior prato avaliado**.
- Lista dos **comentários mais recentes**, com turno, prato e data/hora — texto sempre escapado via `html.escape()` (função `esc()`) para evitar XSS.

> ℹ️ Atualmente as médias e o ranking por prato consideram **todo o histórico acumulado** de avaliações (sem filtro por data). Se um mesmo prato for servido em semanas diferentes, a média junta todas as ocasiões.

---

## 🤖 `agenteia.py` — Assistente Virtual "Minerva"

Chatbot flutuante (FAB + painel) renderizado via `streamlit.components.v1.html`, com uma particularidade técnica: o HTML/JS gerado **acessa `window.parent.document`** e injeta o botão/painel diretamente no DOM da página principal do Streamlit — não dentro do iframe isolado do componente — permitindo que o chat fique sobreposto a toda a interface mesmo vindo de um component isolado.

### Como funciona

1. Monta um `system_prompt` com dados reais do aluno logado: saldo de fichas, últimos acessos, cardápio da semana, regras do RU.
2. Gera HTML/CSS/JS completo do FAB (🤖) + painel de chat estilizado.
3. O **JavaScript no navegador do aluno** chama diretamente a API do Gemini (`generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent`), sem passar pelo backend Streamlit — zero round-trip pro servidor depois do carregamento da página.
OBS Segurança da Chave de API: Embora a chave de API seja carregada pelo JavaScript no lado do cliente, o ecossistema está totalmente protegido contra uso indevido. Foi configurada uma Restrição de Origem HTTP (HTTP Referrer Restriction) diretamente no console de gerenciamento de nuvem da API (Google Cloud / Google AI Studio). Dessa forma, a chave de acesso foi vinculada estritamente aos domínios autorizados da aplicação (ex: *.streamlit.app). Se qualquer usuário mal-intencionado copiar a chave através do painel de desenvolvedor do navegador e tentar usá-la externamente (via Postman, robôs ou outros sites), o Google rejeitará e bloqueará a requisição imediatamente. Além disso, o escopo da chave é limitado exclusivamente à Generative Language API, impedindo o acesso a quaisquer outros serviços da conta.
4. Mantém histórico da conversa em memória (`history`), enviado junto a cada chamada para dar contexto multi-turno.

---

## ⚙️ Requisitos

```
streamlit
pandas        # usado no gráfico de avaliações por prato (app_ru.py)
```

A chave da API Gemini deve ser definida em `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "sua-chave-aqui"
```

## ▶️ Como executar

```bash
# Terminal 1 — App do aluno
streamlit run app_aluno.py 
python -m streamlit run app_aluno.py

# Terminal 2 — Terminal do RU
streamlit run app_ru.py
python -m streamlit run app_ru.py
```

Ambos compartilham o mesmo `utfpr.db`, criado automaticamente na primeira execução de qualquer um dos dois.

---

## 📋 Formato esperado do `alunos.csv`

| Coluna | Descrição |
|---|---|
| `ra_num` | RA numérico (preenchido com zeros à esquerda até 8 dígitos) |
| `ra` | RA textual (ex.: `a2828227`) |
| `nome` | Nome completo |
| `nome_curto` | Nome para exibição |
| `curso` | Curso do aluno |
| `periodo` | Período/semestre |
| `campus` | Campus |
| `senha_hash` | ⚠️ Nome de coluna mantido por legado — contém a **senha em texto puro**, que é hasheada (SHA-256) somente no momento da importação para o banco |
| `ativo` | `1` ou `0` |
| `fichas_almoco` / `fichas_jantar` | Saldo inicial de fichas por tipo |

---

