import streamlit as st
from database import criar_chamado
from notificacoes import gerar_link_google_agenda, gerar_ics
from datetime import date

# Listas de opções globais
TIPOS = ["Problema", "Sugestão", "Solicitação", "Melhoria", "Outros"]
STATUS = ["Aberto", "Aprovado", "Em Desenvolvimento", "Concluído", "Cancelado"]
TECNICOS = ["Ayrton", "Thiago Manoel", "Gabriel", "Diego"]

def render():
    st.markdown('<div class="section-title">➕ Novo Chamado</div>', unsafe_allow_html=True)

    # ==========================================
    # 1. CONTROLES DINÂMICOS (Fora do form para atualizar na hora)
    # ==========================================
    st.markdown("### Configurações Iniciais")
    col_setor, col_nivel, col_atendente = st.columns([1.5, 1, 1.5])
    
    with col_setor:
        setor = st.radio("Setor", ["Desenvolvimento", "Suporte"], horizontal=True)

    nivel_suporte = None
    atendente_suporte = None

    if setor == "Suporte":
        with col_nivel:
            nivel_suporte = st.selectbox("Nível de Atendimento", ["N2", "N3"])
        with col_atendente:
            # A mágica acontece aqui: A lista muda conforme o Nível escolhido!
            if nivel_suporte == "N2":
                atendente_suporte = st.selectbox("Analista N2", ["Davydsson", "Tiago"])
            else:
                atendente_suporte = st.selectbox("Analista N3", ["João Carlos", "Antonio"])

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # 2. FORMULÁRIO PRINCIPAL
    # ==========================================
    with st.form("form_novo_chamado", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            numero = st.text_input("Nº do Chamado *", placeholder="Ex: CHM-2024-001")
            tipo = st.selectbox("Tipo *", TIPOS)
            status = st.selectbox("Status Inicial", STATUS, index=0)
        with c2:
            titulo = st.text_input("Título / Resumo *", placeholder="Descrição curta do chamado")
            data_abertura = st.date_input("Data de Abertura *", value=date.today())
            # Mantive o campo original para registrar quem está "abrindo" o ticket
            tecnico = st.selectbox("Registrado por (Técnico) *", TECNICOS)

        st.markdown("---")
        
        # Variáveis inicializadas como nulas
        data_aprovacao = None
        prazo_dev = None
        tempo_estimado = None
        prazo_analise = None
        
        c3, c4 = st.columns(2)
        
        if setor == "Desenvolvimento":
            st.markdown("<span style='color:#3b82f6; font-weight:600; font-size:0.9rem;'>🛠️ Dados de Desenvolvimento</span>", unsafe_allow_html=True)
            with c3:
                data_aprovacao = st.date_input("Data de Aprovação", value=None)
                prazo_dev = st.date_input("Prazo de Desenvolvimento", value=None)
            with c4:
                tempo_estimado = st.number_input("Tempo Estimado (dias)", min_value=0, value=0, step=1)
                solicitante = st.text_input("Solicitante", placeholder="Nome ou área solicitante")
                sistema = st.text_input("Sistema / Módulo", placeholder="Ex: ERP, Faturamento...")
                
        else: # Se for Suporte
            st.markdown("<span style='color:#10b981; font-weight:600; font-size:0.9rem;'>🎧 Dados de Suporte</span>", unsafe_allow_html=True)
            with c3:
                solicitante = st.text_input("Solicitante", placeholder="Nome do cliente ou usuário")
                prazo_analise = st.number_input("Prazo para Análise (dias)", min_value=0, value=1, step=1)
            with c4:
                sistema = st.text_input("Sistema / Tela com erro", placeholder="Ex: Tela de Login...")

        st.markdown("---")
        descricao = st.text_area("Descrição do Chamado *", height=120, placeholder="Descreva detalhadamente...")
        
        descricao_reuniao = ""
        if setor == "Desenvolvimento":
            descricao_reuniao = st.text_area("Descrição da Reunião de Aprovação", height=80, placeholder="Anotações...")

        st.markdown("---")
        pendente = st.checkbox("⚠️ Marcar como Pendente")
        descricao_pendencia = ""
        if pendente:
            descricao_pendencia = st.text_area("Descrição da Pendência *", height=80)

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("💾 Salvar Chamado", use_container_width=True)

        if submitted:
            if not numero or not titulo or not tipo or not tecnico:
                st.error("Preencha os campos obrigatórios: Nº do Chamado, Título, Tipo e Técnico.")
            elif pendente and not descricao_pendencia.strip():
                st.error("Informe a descrição da pendência.")
            else:
                dados = {
                    "numero_chamado": numero,
                    "setor": setor,
                    "tipo": tipo,
                    "status": status,
                    "titulo": titulo,
                    "tecnico": tecnico,
                    "data_abertura": str(data_abertura),
                    "solicitante": solicitante or None,
                    "sistema": sistema or None,
                    "descricao": descricao,
                    "pendente": pendente,
                    "descricao_pendencia": descricao_pendencia if pendente else None,
                    
                    # Campos de Dev
                    "data_aprovacao": str(data_aprovacao) if data_aprovacao else None,
                    "prazo_desenvolvimento": str(prazo_dev) if prazo_dev else None,
                    "tempo_estimado_dias": tempo_estimado or None,
                    "descricao_reuniao": descricao_reuniao or None,
                    
                    # Campos de Suporte
                    "nivel_suporte": nivel_suporte,
                    "atendente_suporte": atendente_suporte, # NOVO: Salva Davydsson, Tiago, João ou Antonio
                    "prazo_analise_dias": prazo_analise or None
                }
                
                try:
                    chamado = criar_chamado(dados)
                    st.session_state['chamado_criado'] = chamado
                    st.session_state['numero_gerado'] = numero
                    st.session_state['titulo_gerado'] = titulo
                    st.session_state['prazo_dev'] = prazo_dev
                    st.session_state['atendente_sup'] = atendente_suporte
                    
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

    # ==========================================
    # 3. FORA DO FORMULÁRIO: Renderiza o sucesso
    # ==========================================
    if 'chamado_criado' in st.session_state:
        msg_sucesso = f"✅ Chamado **{st.session_state['numero_gerado']}** criado com sucesso!"
        if st.session_state.get('atendente_sup'):
            msg_sucesso += f" Atribuído para: **{st.session_state['atendente_sup']}**"
            
        st.success(msg_sucesso)

        if st.session_state.get('prazo_dev'):
            chamado_sucesso = st.session_state['chamado_criado']
            chamado_sucesso["titulo"] = st.session_state['titulo_gerado']
            
            link_agenda = gerar_link_google_agenda(chamado_sucesso)
            ics_content = gerar_ics(chamado_sucesso)

            st.markdown("---")
            st.markdown("#### 📅 Adicionar ao Google Agenda")
            col_a, col_b = st.columns(2)
            with col_a:
                st.link_button("🗓️ Abrir Google Agenda", link_agenda, use_container_width=True)
            with col_b:
                st.download_button(
                    "📥 Baixar .ics", data=ics_content, file_name=f"chamado_{st.session_state['numero_gerado']}.ics", mime="text/calendar", use_container_width=True
                )
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✨ Cadastrar Novo Chamado", use_container_width=True):
            del st.session_state['chamado_criado']
            st.rerun()