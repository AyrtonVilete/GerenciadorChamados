import streamlit as st
from database import chamados_proximos_prazo
from notificacoes import enviar_email_lembrete


def render():
    st.markdown('<div class="section-title">⚙️ Configurações</div>', unsafe_allow_html=True)

    st.markdown("### 📧 E-mail e Notificações")
    st.markdown("""
    <div style="background:#111827; border:1px solid #1e2d45; border-radius:8px; padding:20px; margin-bottom:20px;">
        <p style="color:#94a3b8; font-size:0.9rem;">Configure as variáveis abaixo no arquivo <code style="background:#1e2d45; padding:2px 6px; border-radius:4px;">.streamlit/secrets.toml</code>:</p>
        <pre style="background:#0a0e1a; border:1px solid #1e2d45; border-radius:6px; padding:16px; color:#6ee7b7; font-size:0.85rem;">
[secrets]
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_KEY = "sua-chave-anonima"

# E-mail (Gmail com App Password)
SMTP_USER   = "seu@gmail.com"
SMTP_PASS   = "xxxx xxxx xxxx xxxx"   # App Password do Google
DEST_EMAIL  = "destino@email.com"

# Alertas
DIAS_ALERTA = 5   # Quantos dias antes do prazo para alertar
        </pre>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🔑 Como obter a App Password do Gmail")
    with st.expander("Ver instruções passo a passo"):
        st.markdown("""
        1. Acesse [myaccount.google.com](https://myaccount.google.com)
        2. Vá em **Segurança** → **Verificação em duas etapas** (deve estar ativada)
        3. Pesquise por **"Senhas de app"** nas configurações de segurança
        4. Selecione *Outro (nome personalizado)* → digite `GerenciaChamados`
        5. Clique em **Gerar** e copie a senha de 16 caracteres
        6. Cole essa senha no campo `SMTP_PASS` do `secrets.toml`
        """)

    st.markdown("---")
    st.markdown("### 🗄️ SQL — Criação da Tabela no Supabase")
    with st.expander("Ver SQL para criar a tabela `chamados`"):
        st.code("""
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

-- Índices úteis
CREATE INDEX idx_chamados_tipo   ON chamados(tipo);
CREATE INDEX idx_chamados_status ON chamados(status);
CREATE INDEX idx_chamados_prazo  ON chamados(prazo_desenvolvimento);
        """, language="sql")

    st.markdown("---")
    st.markdown("### 🧪 Testar E-mail")
    dias = st.number_input("Buscar chamados com prazo nos próximos X dias", value=5, min_value=1, max_value=30)

    if st.button("🔍 Verificar Chamados e Enviar Lembretes"):
        try:
            proximos = chamados_proximos_prazo(dias)
            if not proximos:
                st.info(f"Nenhum chamado com prazo nos próximos {dias} dias.")
            else:
                st.markdown(f"**{len(proximos)} chamado(s) encontrado(s):**")
                enviados = 0
                for c in proximos:
                    st.markdown(f"- `{c.get('numero_chamado')}` — {c.get('titulo')} | {c.get('dias_restantes')} dia(s)")
                    if enviar_email_lembrete(c):
                        enviados += 1
                if enviados > 0:
                    st.success(f"✅ {enviados} e-mail(s) enviado(s) com sucesso!")
                else:
                    st.warning("Nenhum e-mail enviado. Verifique as configurações SMTP.")
        except Exception as e:
            st.error(f"Erro: {e}")

    st.markdown("---")
    st.markdown("### 📦 Dependências")
    st.code("""
streamlit>=1.35.0
supabase>=2.4.0
    """, language="text")
    st.markdown("Instale com: `pip install -r requirements.txt`")
