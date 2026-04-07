import streamlit as st
from database import criar_chamado
from notificacoes import gerar_link_google_agenda, gerar_ics
from datetime import date

# Listas de opções (Agora com a equipe de técnicos)
TIPOS = ["Problema", "Sugestão", "Solicitação", "Melhoria", "Outros"]
STATUS = ["Aberto", "Aprovado", "Em Desenvolvimento", "Concluído", "Cancelado"]
TECNICOS = ["Ayrton", "Thiago Manoel", "Gabriel", "Diego"]

def render():
    st.markdown('<div class="section-title">➕ Novo Chamado</div>', unsafe_allow_html=True)

    with st.form("form_novo_chamado", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            numero = st.text_input("Nº do Chamado *", placeholder="Ex: CHM-2024-001")
            tipo = st.selectbox("Tipo *", TIPOS)
            status = st.selectbox("Status Inicial", STATUS, index=0)
        with c2:
            titulo = st.text_input("Título / Resumo *", placeholder="Descrição curta do chamado")
            data_abertura = st.date_input("Data de Abertura *", value=date.today())
            data_aprovacao = st.date_input("Data de Aprovação", value=None)

        st.markdown("---")
        c3, c4 = st.columns(2)
        with c3:
            prazo_dev = st.date_input("Prazo de Desenvolvimento", value=None)
            tempo_estimado = st.number_input("Tempo Estimado (dias)", min_value=0, value=0, step=1)
        with c4:
            solicitante = st.text_input("Solicitante", placeholder="Nome ou área solicitante")
            sistema = st.text_input("Sistema / Módulo", placeholder="Ex: ERP, Faturamento...")
            
            # NOVO CAMPO: Selectbox com a sua equipe
            tecnico = st.selectbox("Técnico Responsável *", TECNICOS)

        st.markdown("---")
        descricao = st.text_area("Descrição do Chamado *", height=120,
                                  placeholder="Descreva detalhadamente o que foi solicitado...")
        descricao_reuniao = st.text_area("Descrição da Reunião de Aprovação", height=100,
                                          placeholder="Anotações da reunião de aprovação, decisões tomadas, participantes...")

        st.markdown("---")
        pendente = st.checkbox("⚠️ Marcar como Pendente")
        descricao_pendencia = ""
        if pendente:
            descricao_pendencia = st.text_area("Descrição da Pendência *", height=80,
                                                placeholder="Descreva qual é a pendência deste chamado...")

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
                    "tipo": tipo,
                    "status": status,
                    "titulo": titulo,
                    "tecnico": tecnico,  # Campo adicionado aos dados enviados pro banco
                    "data_abertura": str(data_abertura),
                    "data_aprovacao": str(data_aprovacao) if data_aprovacao else None,
                    "prazo_desenvolvimento": str(prazo_dev) if prazo_dev else None,
                    "tempo_estimado_dias": tempo_estimado or None,
                    "solicitante": solicitante or None,
                    "sistema": sistema or None,
                    "descricao": descricao,
                    "descricao_reuniao": descricao_reuniao or None,
                    "pendente": pendente,
                    "descricao_pendencia": descricao_pendencia if pendente else None,
                }
                
                # Usando o st.session_state para manter o sucesso na tela (como ajustado anteriormente)
                try:
                    chamado = criar_chamado(dados)
                    st.session_state['chamado_criado'] = chamado
                    st.session_state['numero_gerado'] = numero
                    st.session_state['titulo_gerado'] = titulo
                    st.session_state['prazo_dev'] = prazo_dev
                    
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

    # Fora do formulário: Renderiza o sucesso e os botões de agenda
    if 'chamado_criado' in st.session_state:
        st.success(f"✅ Chamado **{st.session_state['numero_gerado']}** criado com sucesso pelo técnico **{tecnico}**!")

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
                    "📥 Baixar .ics (importar)",
                    data=ics_content,
                    file_name=f"chamado_{st.session_state['numero_gerado'].replace(' ','_')}.ics",
                    mime="text/calendar",
                    use_container_width=True
                )
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✨ Cadastrar Novo Chamado", use_container_width=True):
            del st.session_state['chamado_criado']
            st.rerun()