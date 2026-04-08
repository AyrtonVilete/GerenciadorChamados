import streamlit as st
from database import criar_chamado, verificar_numero_existe # NOVO: Importação da função de validação
from notificacoes import gerar_link_google_agenda, gerar_ics
from datetime import date

if "usuario" not in st.session_state:
    st.error("🔒 Sessão expirada ou acesso direto negado.")
    # Cria um botão que redireciona de volta para o app.py (Tela de Login)
    st.page_link("app.py", label="⬅️ Ir para a Tela de Login")
    st.stop()

TIPOS = ["Problema", "Sugestão", "Solicitação", "Melhoria", "Outros"]
STATUS = ["Aberto", "Aprovado", "Em Desenvolvimento", "Concluído", "Cancelado"]
TECNICOS = ["Ayrton", "Thiago Manoel", "Gabriel", "Diego"]
CLIENTES = ["FirstClass", "WQ Surf"]

def render():
    st.markdown('<div class="section-title">➕ Novo Chamado</div>', unsafe_allow_html=True)

    # ==========================================
    # 1. CONTROLES DINÂMICOS (Fora do form)
    # ==========================================
    st.markdown("### Configurações Iniciais")
    col_setor, col_status = st.columns(2)
    
    with col_setor:
        setor = st.radio("Setor", ["Desenvolvimento", "Suporte"], horizontal=True)
    with col_status:
        status = st.selectbox("Status Inicial", STATUS, index=0)

    nivel_suporte = None
    atendente_suporte = None

    if setor == "Suporte":
        col_nivel, col_atendente = st.columns(2)
        with col_nivel:
            nivel_suporte = st.selectbox("Nível de Atendimento", ["N2", "N3"])
        with col_atendente:
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
        with c2:
            titulo = st.text_input("Título / Resumo *", placeholder="Descrição curta do chamado")
            data_abertura = st.date_input("Data de Abertura *", value=date.today())
            
        tecnico = st.selectbox("Registrado por (Técnico) *", TECNICOS)

        st.markdown("---")
        
        data_aprovacao = None
        prazo_dev = None
        tempo_estimado = None
        prazo_analise = None
        
        if setor == "Desenvolvimento":
            st.markdown("<span style='color:#3b82f6; font-weight:600; font-size:0.9rem;'>🛠️ Dados de Desenvolvimento</span>", unsafe_allow_html=True)
            
            c3, c4 = st.columns(2)
            with c3:
                data_aprovacao = st.date_input("Data de Aprovação", value=None)
                prazo_dev = st.date_input("Prazo de Desenvolvimento", value=None)
            with c4:
                cliente = st.selectbox("Cliente *", CLIENTES)
                tempo_estimado = st.number_input("Tempo Estimado (dias)", min_value=0, value=0, step=1)
                
            c5, c6 = st.columns(2)
            with c5:
                solicitante = st.text_input("Solicitante", placeholder="Nome ou área solicitante")
            with c6:
                sistema = st.text_input("Sistema / Módulo", placeholder="Ex: ERP, Faturamento...")
                
        else: 
            st.markdown("<span style='color:#10b981; font-weight:600; font-size:0.9rem;'>🎧 Dados de Suporte</span>", unsafe_allow_html=True)
            
            c3, c4 = st.columns(2)
            with c3:
                prazo_analise = st.number_input("Prazo para Análise (dias)", min_value=0, value=1, step=1)
            with c4:
                cliente = st.selectbox("Cliente *", CLIENTES)
                
            c5, c6 = st.columns(2)
            with c5:
                solicitante = st.text_input("Solicitante", placeholder="Nome do cliente ou usuário")
            with c6:
                sistema = st.text_input("Sistema / Tela com erro", placeholder="Ex: Tela de Login...")

        st.markdown("---")
        descricao = st.text_area("Descrição do Chamado *", height=120, placeholder="Descreva detalhadamente...")
        
        descricao_reuniao = ""
        if setor == "Desenvolvimento":
            descricao_reuniao = st.text_area("Descrição da Reunião de Aprovação", height=80, placeholder="Anotações...")

        st.markdown("---")
        
        st.markdown("<span style='color:#f59e0b; font-weight:600; font-size:0.85rem;'>⚠️ Tratamento de Pendências</span>", unsafe_allow_html=True)
        pendente = st.checkbox("Marcar chamado como Pendente")
        descricao_pendencia = st.text_area("Motivo da Pendência", height=80, placeholder="Preencha apenas se marcar o chamado como pendente acima...")

        resolucao = ""
        versao_liberacao = ""
        motivo_cancelamento = ""

        if status == "Concluído":
            st.markdown("---")
            st.markdown("<span style='color:#10b981; font-weight:600; font-size:0.85rem;'>🏁 Fechamento de Chamado</span>", unsafe_allow_html=True)
            resolucao = st.text_area("Solução / Comentário do Dev *", height=80, placeholder="O que foi feito para resolver?")
            versao_liberacao = st.text_input("Versão de Liberação")

        if status == "Cancelado":
            st.markdown("---")
            st.markdown("<span style='color:#ef4444; font-weight:600; font-size:0.85rem;'>🚫 Cancelamento de Chamado</span>", unsafe_allow_html=True)
            motivo_cancelamento = st.text_area("Motivo do Cancelamento *", height=80, placeholder="Por que este chamado está sendo cancelado?")

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("💾 Salvar Chamado", use_container_width=True)

        if submitted:
            # ==========================================
            # VALIDAÇÕES INCLUINDO VERIFICAÇÃO DE DUPLICIDADE
            # ==========================================
            if not numero or not titulo or not tipo or not tecnico or not cliente:
                st.error("Preencha os campos obrigatórios: Nº do Chamado, Cliente, Título, Tipo e Técnico.")
            elif verificar_numero_existe(numero): # NOVO: Trava de Duplicidade
                st.error(f"❌ O chamado número **{numero}** já está cadastrado no sistema. Verifique a lista de chamados ou insira um número diferente.")
            elif pendente and not descricao_pendencia.strip():
                st.error("⚠️ Você marcou o chamado como Pendente. Por favor, preencha o Motivo da Pendência.")
            elif prazo_dev and prazo_dev < data_abertura:
                st.error("⏳ O Prazo de Desenvolvimento não pode ser anterior à Data de Abertura do chamado!")
            elif status == "Aprovado" and not data_aprovacao:
                st.error("📅 Para iniciar com status 'Aprovado', é obrigatório preencher a Data de Aprovação.")
            elif status == "Concluído" and not resolucao.strip():
                st.error("🏁 Para criar um chamado 'Concluído', é obrigatório preencher a Solução do Chamado.")
            elif status == "Cancelado" and not motivo_cancelamento.strip():
                st.error("🚫 Para criar um chamado 'Cancelado', é obrigatório preencher o Motivo do Cancelamento.")
            else:
                dados = {
                    "numero_chamado": numero, "setor": setor, "cliente": cliente, "tipo": tipo, "status": status,
                    "titulo": titulo, "tecnico": tecnico, "data_abertura": str(data_abertura),
                    "solicitante": solicitante or None, "sistema": sistema or None, "descricao": descricao,
                    "pendente": pendente, "descricao_pendencia": descricao_pendencia if pendente else None,
                    "resolucao": resolucao if status == "Concluído" else None,
                    "versao_liberacao": versao_liberacao if status == "Concluído" else None,
                    "motivo_cancelamento": motivo_cancelamento if status == "Cancelado" else None,
                    "data_aprovacao": str(data_aprovacao) if data_aprovacao else None,
                    "prazo_desenvolvimento": str(prazo_dev) if prazo_dev else None,
                    "tempo_estimado_dias": tempo_estimado or None, "descricao_reuniao": descricao_reuniao or None,
                    "nivel_suporte": nivel_suporte, "atendente_suporte": atendente_suporte,
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
    # 3. MENSAGEM DE SUCESSO E AGENDA
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
                st.download_button("📥 Baixar .ics", data=ics_content, file_name=f"chamado_{st.session_state['numero_gerado']}.ics", mime="text/calendar", use_container_width=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✨ Cadastrar Novo Chamado", use_container_width=True):
            del st.session_state['chamado_criado']
            st.rerun()