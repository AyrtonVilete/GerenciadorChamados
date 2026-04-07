import streamlit as st
from datetime import datetime
import os
import streamlit as st

# Oculta o menu de navegação padrão do Streamlit
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

st.set_page_config(
    page_title="GerenciaChamados",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg: #0a0e1a;
    --surface: #111827;
    --surface2: #1a2235;
    --border: #1e2d45;
    --accent: #3b82f6;
    --accent2: #06b6d4;
    --warn: #f59e0b;
    --danger: #ef4444;
    --success: #10b981;
    --text: #e2e8f0;
    --muted: #64748b;
}

html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

.stApp {
    background-color: var(--bg) !important;
}

section[data-testid="stSidebar"] {
    background-color: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}

section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span {
    color: var(--text) !important;
}

.metric-card {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    transition: transform 0.2s;
}
.metric-card:hover { transform: translateY(-2px); }
.metric-value { font-size: 2.5rem; font-weight: 700; color: var(--accent); font-family: 'JetBrains Mono'; }
.metric-label { color: var(--muted); font-size: 0.85rem; margin-top: 4px; }

.chamado-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 12px;
    transition: all 0.2s;
}
.chamado-card:hover { border-left-color: var(--accent2); background: var(--surface2); }
.chamado-card.pendente { border-left-color: var(--warn); }
.chamado-card.atrasado { border-left-color: var(--danger); }

.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 6px;
}
.badge-problema { background: #7f1d1d; color: #fca5a5; }
.badge-sugestao { background: #1e3a5f; color: #93c5fd; }
.badge-solicitacao { background: #064e3b; color: #6ee7b7; }
.badge-melhoria { background: #4c1d95; color: #c4b5fd; }
.badge-outros { background: #292524; color: #d6d3d1; }
.badge-pendente { background: #78350f; color: #fcd34d; }

.status-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 500;
}
.status-aberto { background: #1e3a5f; color: #60a5fa; }
.status-aprovado { background: #064e3b; color: #34d399; }
.status-em-desenvolvimento { background: #4c1d95; color: #a78bfa; }
.status-concluido { background: #134e4a; color: #5eead4; }
.status-cancelado { background: #1c1917; color: #78716c; }

.section-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 1.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--accent);
    display: inline-block;
}

div[data-testid="stForm"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px;
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > select,
.stDateInput > div > div > input,
.stNumberInput > div > div > input {
    background-color: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 6px !important;
}

.stButton > button {
    background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.5rem !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

.stCheckbox label { color: var(--text) !important; }

.alert-box {
    background: #78350f22;
    border: 1px solid var(--warn);
    border-radius: 8px;
    padding: 12px 16px;
    color: #fcd34d;
    margin: 8px 0;
}
</style>
""", unsafe_allow_html=True)


def main():
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding: 20px 0 30px;">
            <div style="font-size:2.5rem">🎫</div>
            <div style="font-size:1.3rem; font-weight:700; color:#e2e8f0;">GerenciaChamados</div>
            <div style="font-size:0.75rem; color:#64748b; margin-top:4px;">Sistema de Controle Interno</div>
        </div>
        """, unsafe_allow_html=True)

        menu = st.radio(
            "Navegação",
            ["🏠  Painel", "➕  Novo Chamado", "📋  Chamados", "📊  Relatórios", "⚙️  Configurações"],
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.markdown(f"<div style='color:#64748b; font-size:0.75rem; text-align:center;'>{datetime.now().strftime('%d/%m/%Y %H:%M')}</div>", unsafe_allow_html=True)

    page = menu.split("  ")[1]

    if page == "Painel":
        from pages import painel
        painel.render()
    elif page == "Novo Chamado":
        from pages import novo_chamado
        novo_chamado.render()
    elif page == "Chamados":
        from pages import lista_chamados
        lista_chamados.render()
    elif page == "Relatórios":
        from pages import relatorios
        relatorios.render()
    elif page == "Configurações":
        from pages import configuracoes
        configuracoes.render()


if __name__ == "__main__":
    main()
