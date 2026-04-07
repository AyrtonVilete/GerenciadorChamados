# ============================================================
#  GerenciaChamados — README
# ============================================================

## 📦 Instalação

```bash
pip install -r requirements.txt
```

## ⚙️ Configuração

Crie o arquivo `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_KEY = "sua-anon-key"

SMTP_USER   = "seu@gmail.com"
SMTP_PASS   = "xxxx xxxx xxxx xxxx"
DEST_EMAIL  = "destino@email.com"

DIAS_ALERTA = 5
```

## 🗄️ Banco de Dados (Supabase)

Execute o SQL abaixo no **SQL Editor** do Supabase:

```sql
CREATE TABLE chamados (
    id                   BIGSERIAL PRIMARY KEY,
    numero_chamado       TEXT NOT NULL,
    tipo                 TEXT NOT NULL,
    status               TEXT NOT NULL DEFAULT 'Aberto',
    titulo               TEXT NOT NULL,
    solicitante          TEXT,
    sistema              TEXT,
    data_abertura        DATE,
    data_aprovacao       DATE,
    prazo_desenvolvimento DATE,
    tempo_estimado_dias  INT,
    descricao            TEXT,
    descricao_reuniao    TEXT,
    pendente             BOOLEAN DEFAULT FALSE,
    descricao_pendencia  TEXT,
    criado_em            TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em        TIMESTAMPTZ DEFAULT NOW()
);
```

## ▶️ Executar

```bash
streamlit run app.py
```

## 📧 E-mail (Gmail App Password)

1. Ative a verificação em duas etapas no Gmail
2. Vá em Segurança → Senhas de app
3. Gere uma senha para "GerenciaChamados"
4. Use essa senha (16 chars) no campo `SMTP_PASS`

## 📅 Google Agenda

- Botão de link direto ao salvar/visualizar chamado com prazo
- Download de arquivo `.ics` para importar no Google Agenda
  (com alerta automático 5 dias antes do prazo)

## 📁 Estrutura

```
chamados_app/
├── app.py              # Aplicação principal
├── database.py         # Operações Supabase
├── notificacoes.py     # E-mail + Google Agenda
├── requirements.txt
└── pages/
    ├── painel.py
    ├── novo_chamado.py
    ├── lista_chamados.py
    ├── relatorios.py
    └── configuracoes.py
```

## 🖥️ Descrição das Telas
O sistema é dividido em módulos para facilitar a navegação e a gestão do ciclo de vida dos chamados:

## 🏠 Painel Geral (painel.py) 
Dashboard inicial com KPIs rápidos (Total, Abertos, Pendentes, Atrasados). Exibe alertas visuais para chamados próximos do prazo e permite disparar e-mails de cobrança em lote. Também lista os últimos tickets registrados.

## ➕ Novo Chamado (novo_chamado.py)
Formulário completo para registro de novos atendimentos. Permite vincular técnicos, definir prazos e gerar alertas de pendências. Ao salvar, gera automaticamente botões para integração com o Google Agenda.

## 📋 Lista de Chamados (lista_chamados.py)
Visão detalhada de todo o backlog. Possui sistema de busca por texto e filtros combinados (Tipo, Status, Técnico, Pendências). Permite expandir os detalhes de cada chamado para leitura completa, edição de dados e exclusão de registros.

## 📊 Relatórios (relatorios.py)
Central de inteligência de dados. Processa a listagem completa com filtros globais, recalculando dinamicamente gráficos de barras e rosca (donut). Permite a exportação dos dados filtrados para formato .CSV com codificação correta para Excel.

## ⚙️ Configurações (configuracoes.py)
Área reservada para ajustes de parâmetros do sistema e definições de ambiente.