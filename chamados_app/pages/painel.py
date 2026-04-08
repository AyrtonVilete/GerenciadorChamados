import streamlit as st
import re
from database import estatisticas_gerais, chamados_proximos_prazo, listar_chamados
from notificacoes import enviar_email_lembrete
from datetime import date

if "usuario" not in st.session_state:
    st.error("🔒 Sessão expirada ou acesso direto negado.")
    # Cria um botão que redireciona de volta para o app.py (Tela de Login)
    st.page_link("app.py", label="⬅️ Ir para a Tela de Login")
    st.stop()

def render():
    st.markdown('<div class="section-title">🏠 Painel Geral</div>', unsafe_allow_html=True)

    try:
        stats = estatisticas_gerais()
    except Exception as e:
        st.error(f"Erro ao conectar com o banco: {e}")
        st.info("Configure suas credenciais do Supabase em `.streamlit/secrets.toml`")
        return

    # ==========================================
    # 1. CONTADORES GERAIS (MANTIDOS)
    # ==========================================
    cols = st.columns(6)
    metricas = [
        ("Total", stats.get("total", 0), "#3b82f6"),
        ("Abertos", stats.get("abertos", 0), "#06b6d4"),
        ("Em Dev.", stats.get("em_desenvolvimento", 0), "#a78bfa"),
        ("Concluídos", stats.get("concluidos", 0), "#10b981"),
        ("Pendentes", stats.get("pendentes", 0), "#f59e0b"),
        ("Atrasados", stats.get("atrasados", 0), "#ef4444"),
    ]
    for col, (label, val, cor) in zip(cols, metricas):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color:{cor};">{val}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br><hr style='border-color: #334155; margin: 10px 0 30px 0;'>", unsafe_allow_html=True)

    # ==========================================
    # 2. NOVO CAMPO: ÚLTIMOS CHAMADOS
    # ==========================================
    st.markdown("### 📋 Últimos Chamados")
    chamados = listar_chamados()[:8]

    if not chamados:
        st.info("Nenhum chamado cadastrado ainda.")
        return

    for c in chamados:
        _novo_card_chamado(c)


def _novo_card_chamado(c):
    """
    Nova estrutura de renderização do chamado à prova de quebras de layout.
    """
    # 1. Captura os dados essenciais e os novos campos
    numero = c.get('numero_chamado', 'N/A')
    status = c.get('status', 'Indefinido')
    tecnico = c.get('tecnico', 'Não atribuído')
    
    # Formatando datas (pegando apenas os 10 primeiros caracteres YYYY-MM-DD)
    criado_em = (c.get('criado_em', '') or '')[:10]
    data_aprovacao = (c.get('data_aprovacao', '') or '')[:10]
    prazo_dev = (c.get('prazo_desenvolvimento', '') or '')[:10]

    # 2. Tratamento rigoroso da descrição (Remove tags, quebras de linha e limita tamanho)
    desc_raw = str(c.get('descricao', '') or '')
    desc_sem_html = re.sub('<[^<]+?>', '', desc_raw) 
    desc_limpa = re.sub(r'\s+', ' ', desc_sem_html).strip() 
    resumo = (desc_limpa[:150] + '...') if len(desc_limpa) > 150 else desc_limpa

    # Se o resumo ficar vazio, coloca um aviso sutil
    if not resumo:
        resumo = "<span style='color: #475569; font-style: italic;'>Sem descrição detalhada.</span>"

    # 3. Definição de cores dinâmicas baseadas no Status
    cor_status = "#64748b" # Cinza (Padrão)
    if status == "Aberto": cor_status = "#3b82f6" # Azul
    elif status == "Concluído": cor_status = "#10b981" # Verde
    elif status == "Em Desenvolvimento": cor_status = "#a78bfa" # Roxo
    elif status == "Cancelado": cor_status = "#ef4444" # Vermelho
    elif status == "Aprovado": cor_status = "#0ea5e9" # Ciano

    # 4. Construção dinâmica da coluna de datas (Direita)
    html_datas = f"""
    <div style="margin-bottom: {'8px' if data_aprovacao or prazo_dev else '0'};">
        <div style="color: #64748b; font-size: 0.70rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">Abertura</div>
        <div style="color: #f8fafc; font-size: 0.85rem; margin-top: 2px; font-weight: 500;">{criado_em}</div>
    </div>
    """
    
    if data_aprovacao:
        html_datas += f"""
        <div style="margin-bottom: {'8px' if prazo_dev else '0'};">
            <div style="color: #64748b; font-size: 0.70rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">Aprovação</div>
            <div style="color: #cbd5e1; font-size: 0.85rem; margin-top: 2px;">{data_aprovacao}</div>
        </div>
        """
        
    if prazo_dev:
        html_datas += f"""
        <div>
            <div style="color: #64748b; font-size: 0.70rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">Prazo Dev.</div>
            <div style="color: #f59e0b; font-size: 0.85rem; margin-top: 2px; font-weight: 600;">{prazo_dev}</div>
        </div>
        """

    # 5. Montagem do HTML (Design Dark Mode Nativo)
    html_card = f"""
    <div style="background-color: #1e293b; padding: 18px 24px; border-radius: 10px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: stretch; border-left: 5px solid {cor_status}; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);">
        <div style="flex: 1; padding-right: 20px; display: flex; flex-direction: column; justify-content: center;">
            <div style="margin-bottom: 10px; display: flex; align-items: center; flex-wrap: wrap; gap: 12px;">
                <span style="color: #94a3b8; font-family: 'Courier New', Courier, monospace; font-size: 1rem; font-weight: bold;">#{numero}</span>
                <span style="background-color: {cor_status}15; color: {cor_status}; padding: 4px 12px; border-radius: 12px; font-size: 0.85rem; font-weight: 600; border: 1px solid {cor_status}40;">{status}</span>
                <span style="color: #cbd5e1; font-size: 0.85rem; display: flex; align-items: center; gap: 6px;">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                    {tecnico}
                </span>
            </div>
            <div style="color: #94a3b8; font-size: 0.90rem; line-height: 1.5;">
                {resumo}
            </div>
        </div>
        <div style="text-align: right; min-width: 110px; flex-shrink: 0; border-left: 1px solid #334155; padding-left: 20px; display: flex; flex-direction: column; justify-content: center;">
            {html_datas}
        </div>
    </div>
    """

    # 6. O segredo da estabilidade: transformar todo o bloco HTML em uma linha única
    html_seguro = html_card.replace('\n', '')

    st.markdown(html_seguro, unsafe_allow_html=True)