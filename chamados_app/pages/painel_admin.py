import streamlit as st
from database import criar_usuario_sistema, listar_perfis_acesso

# ==========================================
# CADEADO DUPLO DE SEGURANÇA (Admin Only)
# ==========================================
if "usuario" not in st.session_state:
    st.error("🔒 Sessão expirada ou acesso direto negado.")
    # Cria um botão que redireciona de volta para o app.py (Tela de Login)
    st.page_link("app.py", label="⬅️ Ir para a Tela de Login")
    st.stop()

if st.session_state.get("perfil") != "Admin":
    st.error("⛔ Acesso Restrito. Apenas Administradores podem visualizar esta página.")
    st.stop()
# ==========================================

def render():
    st.markdown('<div class="section-title">🛡️ Painel de Administração</div>', unsafe_allow_html=True)
    st.markdown("Gerencie os acessos, crie novas contas e defina os perfis da sua equipe.")

    col1, col2 = st.columns([1, 1.5])

    # --- LADO ESQUERDO: CRIAR USUÁRIO ---
    with col1:
        st.markdown("### ➕ Novo Usuário")
        with st.form("form_novo_usuario", clear_on_submit=True):
            novo_email = st.text_input("E-mail corporativo *")
            nova_senha = st.text_input("Senha inicial *", type="password", help="A senha deve ter no mínimo 6 caracteres.")
            
            # Você pode adicionar mais perfis aqui no futuro
            novo_perfil = st.selectbox("Perfil de Acesso *", ["Comum", "Dev", "Suporte", "Admin"])
            
            submitted = st.form_submit_button("Criar Conta", use_container_width=True)

            if submitted:
                if not novo_email or not nova_senha:
                    st.warning("Preencha e-mail e senha.")
                elif len(nova_senha) < 6:
                    st.warning("A senha deve ter pelo menos 6 caracteres.")
                else:
                    try:
                        criar_usuario_sistema(novo_email, nova_senha, novo_perfil)
                        st.success(f"✅ Usuário {novo_email} criado com sucesso como {novo_perfil}!")
                        st.rerun() # Atualiza a tela para mostrar na tabela
                    except Exception as e:
                        st.error(f"Erro ao criar usuário. Verifique se o e-mail já existe. Detalhes: {e}")

    # --- LADO DIREITO: LISTA DE USUÁRIOS ---
    with col2:
        st.markdown("### 👥 Usuários do Sistema")
        
        perfis = listar_perfis_acesso()
        
        if not perfis:
            st.info("Nenhum usuário encontrado na tabela de perfis.")
        else:
            # Monta uma tabela HTML customizada para combinar com seu design Dark Mode
            header = "".join(f'<th style="padding:10px; text-align:left; color:#64748b; border-bottom:1px solid #1e2d45;">{c}</th>' for c in ["ID", "E-mail", "Perfil"])
            
            rows = ""
            for p in perfis:
                # Destaca o Admin com uma cor diferente
                cor_perfil = "#3b82f6" if p.get('perfil') == "Admin" else "#e2e8f0"
                
                rows += f"""
                <tr style="border-bottom:1px solid #1e2d45;">
                    <td style="padding:10px; color:#94a3b8;">{p.get('id', '')}</td>
                    <td style="padding:10px;">{p.get('email', '')}</td>
                    <td style="padding:10px; font-weight:600; color:{cor_perfil};">{p.get('perfil', '')}</td>
                </tr>
                """
                
            tabela = f"""
            <table style="width:100%; border-collapse:collapse; background:#111827; border:1px solid #1e2d45; border-radius:8px; overflow:hidden;">
                <thead><tr>{header}</tr></thead>
                <tbody>{rows}</tbody>
            </table>
            """.replace('\n', '')
            
            st.markdown(tabela, unsafe_allow_html=True)