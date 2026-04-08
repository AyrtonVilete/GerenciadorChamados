import streamlit as st
from datetime import datetime
import os
from database import get_client
from database import get_client, buscar_perfil_usuario

# Configuração da página DEVE ser a primeira chamada do Streamlit
st.set_page_config(
    page_title="Gerenciador de Chamados",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 1. CSS CUSTOMIZADO (Seu design original mantido!)
# ==========================================
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

/* Oculta apenas os menus superiores padrão do Streamlit, não a sua sidebar */
[data-testid="stSidebarNav"] { display: none; }

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
</style>
""", unsafe_allow_html=True)


# ==========================================
# 2. FUNÇÃO DE LOGIN
# ==========================================
def realizar_login(email, senha):
    client = get_client()
    try:
        resposta = client.auth.sign_in_with_password({"email": email, "password": senha})
        st.session_state["usuario"] = resposta.user
        
        # A MÁGICA ACONTECE AQUI: Buscamos e salvamos o perfil!
        st.session_state["perfil"] = buscar_perfil_usuario(email)
        
        return True
    except Exception as e:
        return False


# ==========================================
# 3. MOTOR PRINCIPAL
# ==========================================
def main():
    # SE NÃO ESTIVER LOGADO -> TELA DE LOGIN
    if "usuario" not in st.session_state:
        # Esconde a Sidebar inteira para quem não está logado
        st.markdown("""<style>[data-testid="stSidebar"] {display: none !important;}</style>""", unsafe_allow_html=True)
        
        # Centraliza o login na tela usando colunas
        c1, c2, c3 = st.columns([1, 1, 1])
        with c2:
            st.markdown("<br><br><br>", unsafe_allow_html=True)
            st.markdown("<div style='text-align: center; font-size: 4rem;'>🎫</div>", unsafe_allow_html=True)
            st.markdown("<h2 style='text-align: center; color: #3b82f6;'>Gerenciador de Chamados</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #64748b; margin-bottom: 30px;'>Acesso restrito. Faça login para continuar.</p>", unsafe_allow_html=True)

            with st.form("form_login"):
                email = st.text_input("E-mail")
                senha = st.text_input("Senha", type="password")
                submit = st.form_submit_button("Entrar", use_container_width=True)

                if submit:
                    if not email or not senha:
                        st.warning("Preencha e-mail e senha.")
                    elif realizar_login(email, senha):
                        st.success("Acesso liberado!")
                        st.rerun()
                    else:
                        st.error("❌ E-mail ou senha incorretos.")

    # SE ESTIVER LOGADO -> TELA NORMAL DO SISTEMA
    else:
        email_logado = st.session_state["usuario"].email

        # Sua Sidebar Original
        with st.sidebar:
            st.markdown("""
            <div style="text-align:center; padding: 20px 0 30px;">
                <div style="font-size:2.5rem">🎫</div>
                <div style="font-size:1.3rem; font-weight:700; color:#e2e8f0;">Gerenciador de Chamados</div>
                <div style="font-size:0.75rem; color:#64748b; margin-top:4px;">Sistema de Controle Interno</div>
            </div>
            """, unsafe_allow_html=True)

            paginas = ["🏠  Painel", "➕  Novo Chamado", "📋  Chamados", "📊  Relatórios"]
            
            # Se for Admin, adiciona o painel de administração no menu
            if st.session_state.get("perfil") == "Admin":
                paginas.append("🛡️  Painel Admin")
                
            paginas.append("⚙️  Configurações")

            menu = st.radio("Navegação", paginas, label_visibility="collapsed")

            st.markdown("---")
            st.markdown(f"<div style='color:#3b82f6; font-size:0.80rem; text-align:center; margin-bottom:10px;'>👤 {email_logado} ({st.session_state.get('perfil', 'Comum')})</div>", unsafe_allow_html=True)
            # Botão de Logout adicionado discretamente na sidebar
            if st.button("🚪 Sair", use_container_width=True):
                try:
                    get_client().auth.sign_out()
                except: pass

                del st.session_state["usuario"]
                st.rerun()
                
            st.markdown(f"<div style='color:#64748b; font-size:0.75rem; text-align:center; margin-top:15px;'>{datetime.now().strftime('%d/%m/%Y %H:%M')}</div>", unsafe_allow_html=True)

        # Roteamento das páginas
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
        elif page == "Painel Admin":
            from pages import painel_admin
            painel_admin.render()
        elif page == "Configurações":
            from pages import configuracoes
            configuracoes.render()
if __name__ == "__main__":
    main()