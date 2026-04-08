import streamlit as st
from database import listar_chamados, atualizar_chamado, deletar_chamado, buscar_chamado
from notificacoes import gerar_link_google_agenda, gerar_ics
from datetime import date

TIPOS = ["", "Problema", "Sugestão", "Solicitação", "Melhoria", "Outros"]
STATUS_FILTRO = ["", "Aberto", "Aprovado", "Em Desenvolvimento", "Concluído", "Cancelado"]
TECNICOS_FILTRO = ["", "Ayrton", "Thiago Manoel", "Gabriel", "Diego"]

def render():
    st.markdown('<div class="section-title">📋 Chamados</div>', unsafe_allow_html=True)

    with st.expander("🔍 Filtros", expanded=False):
        f1, f2, f3, f4 = st.columns([1, 1, 1, 1.2])
        with f1: f_tipo = st.selectbox("Tipo", TIPOS)
        with f2: f_status = st.selectbox("Status", STATUS_FILTRO)
        with f3: f_tecnico = st.selectbox("Técnico", TECNICOS_FILTRO)
        with f4:
            st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
            f_pendente = st.checkbox("Apenas Pendentes")
            
        f_busca = st.text_input("Buscar por número ou título", placeholder="Digite para buscar...")

    filtros = {}
    if f_tipo: filtros["tipo"] = f_tipo
    if f_status: filtros["status"] = f_status
    if f_tecnico: filtros["tecnico"] = f_tecnico
    if f_pendente: filtros["pendente"] = True

    try: chamados = listar_chamados(filtros)
    except Exception as e:
        st.error(f"Erro ao carregar chamados: {e}")
        return

    if f_busca:
        busca = f_busca.lower()
        chamados = [c for c in chamados if busca in (c.get("numero_chamado") or "").lower() or busca in (c.get("titulo") or "").lower()]

    if not chamados:
        st.info("Nenhum chamado encontrado.")
        return

    st.markdown(f"<div style='color:#64748b; margin-bottom:16px;'>Exibindo <strong style='color:#e2e8f0;'>{len(chamados)}</strong> chamado(s)</div>", unsafe_allow_html=True)

    for c in chamados:
        _renderizar_chamado(c)

def _renderizar_chamado(c):
    hoje = date.today()
    atrasado = False
    prazo_str = c.get("prazo_desenvolvimento")
    if prazo_str and c.get("status") not in ["Concluído", "Cancelado"]:
        try:
            if date.fromisoformat(prazo_str) < hoje: atrasado = True
        except: pass

    with st.expander(f"#{c.get('numero_chamado','?')} | {c.get('cliente', 'Sem Cliente')} | {c.get('titulo','')} {'⚠️' if c.get('pendente') else ''} {'🔴' if atrasado else ''}", expanded=False):
        tab1, tab2 = st.tabs(["📄 Detalhes", "✏️ Editar"])
        with tab1: _detalhes(c, atrasado)
        with tab2: _formulario_edicao(c)

def _detalhes(c, atrasado):
    col1, col2 = st.columns(2)
    setor = c.get('setor', 'Desenvolvimento')
    
    with col1:
        st.markdown(f"**Nº Chamado:** `{c.get('numero_chamado','')}`")
        st.markdown(f"**Cliente:** <span style='color:#0ea5e9; font-weight:bold;'>{c.get('cliente','—')}</span>", unsafe_allow_html=True)
        st.markdown(f"**Setor:** {setor}")
        st.markdown(f"**Tipo:** {c.get('tipo','')}")
        st.markdown(f"**Status:** {c.get('status','')}")
        st.markdown(f"**Solicitante:** {c.get('solicitante','—')}")
        st.markdown(f"**Registrado por:** {c.get('tecnico','—')}")
        if setor == "Suporte":
            st.markdown(f"**Atendente ({c.get('nivel_suporte', 'N/A')}):** <span style='color:#10b981; font-weight:bold;'>{c.get('atendente_suporte','—')}</span>", unsafe_allow_html=True)
        st.markdown(f"**Sistema/Módulo:** {c.get('sistema','—')}")
        
    with col2:
        st.markdown(f"**Abertura:** {(c.get('data_abertura','') or '')[:10]}")
        if setor == "Desenvolvimento":
            st.markdown(f"**Aprovação:** {(c.get('data_aprovacao','') or '—')[:10]}")
            st.markdown(f"**Prazo Dev.:** {c.get('prazo_desenvolvimento','—') or '—'}")
            st.markdown(f"**Tempo Estimado:** {c.get('tempo_estimado_dias','—') or '—'} dia(s)")
            if atrasado: st.markdown('<span style="color:#ef4444;">🔴 **CHAMADO ATRASADO**</span>', unsafe_allow_html=True)
        else:
            st.markdown(f"**Prazo Análise:** {c.get('prazo_analise_dias','—') or '—'} dia(s)")

    if c.get("descricao"):
        st.markdown("**Descrição:**")
        st.markdown(f"> {c['descricao']}")

    if c.get("descricao_reuniao") and setor == "Desenvolvimento":
        st.markdown("**Reunião de Aprovação:**")
        st.markdown(f"> {c['descricao_reuniao']}")

    if c.get("pendente"):
        st.markdown(f"""<div class="alert-box"><strong>⚠️ Pendência:</strong><br>{c.get('descricao_pendencia','Sem descrição')}</div>""", unsafe_allow_html=True)
        
    if c.get("resolucao"):
        st.markdown("---")
        st.markdown(f"#### 🏁 Solução / Resolução (Versão: {c.get('versao_liberacao', 'N/A')})")
        st.markdown(f"> {c.get('resolucao')}")

    if c.get("status") == "Cancelado" and c.get("motivo_cancelamento"):
        st.markdown("---")
        st.markdown("#### 🚫 Motivo do Cancelamento")
        st.markdown(f"> {c.get('motivo_cancelamento')}")

    if c.get("prazo_desenvolvimento"):
        link = gerar_link_google_agenda(c)
        ics = gerar_ics(c)
        cola, colb = st.columns(2)
        with cola:
            if link: st.link_button("📅 Google Agenda", link)
        with colb:
            if ics: st.download_button("📥 Baixar .ics", data=ics, file_name=f"chamado_{c.get('numero_chamado','x')}.ics", mime="text/calendar")


def _formulario_edicao(c):
    status_atual = c.get("status")
    
    if status_atual in ["Concluído", "Cancelado"]:
        st.warning(f"🔒 Este chamado está encerrado ({status_atual}) e não pode ser alterado.")
        if st.button("🔓 Reabrir Chamado (Voltar para Aberto)", key=f"reabrir_{c['id']}"):
            atualizar_chamado(c['id'], {"status": "Aberto", "resolucao": None, "versao_liberacao": None, "motivo_cancelamento": None})
            st.rerun()
        return

    TIPOS_LISTA = ["Problema", "Sugestão", "Solicitação", "Melhoria", "Outros"]
    TECNICOS_EDICAO = ["Ayrton", "Thiago Manoel", "Gabriel", "Diego"]
    ATENDENTES_SUPORTE = ["Davydsson", "Tiago", "João Carlos", "Antonio"]
    CLIENTES_EDICAO = ["FirstClass", "WQ Surf"]

    setor = c.get("setor", "Desenvolvimento")
    
    # Trava 2: Transição de Status
    if status_atual == "Aberto":
        status_permitidos = ["Aberto", "Aprovado", "Cancelado"] if setor == "Desenvolvimento" else ["Aberto", "Em Desenvolvimento", "Concluído", "Cancelado"]
    elif status_atual == "Aprovado":
        status_permitidos = ["Aprovado", "Em Desenvolvimento", "Cancelado"]
    elif status_atual == "Em Desenvolvimento":
        status_permitidos = ["Em Desenvolvimento", "Concluído", "Cancelado"]
    else:
        status_permitidos = [status_atual]

    with st.form(f"edit_{c['id']}"):
        st.markdown(f"#### ✏️ Editando Chamado de {setor}")
        e1, e2 = st.columns(2)
        with e1:
            numero = st.text_input("Nº Chamado", value=c.get("numero_chamado",""))
            tipo_idx = TIPOS_LISTA.index(c.get("tipo")) if c.get("tipo") in TIPOS_LISTA else 0
            tipo = st.selectbox("Tipo", TIPOS_LISTA, index=tipo_idx)
            status = st.selectbox("Status", status_permitidos, index=0)
            
            tecnico_atual = c.get("tecnico")
            tecnico_idx = TECNICOS_EDICAO.index(tecnico_atual) if tecnico_atual in TECNICOS_EDICAO else 0
            tecnico = st.selectbox("Registrado por", TECNICOS_EDICAO, index=tecnico_idx)

        with e2:
            titulo = st.text_input("Título", value=c.get("titulo",""))
            
            cliente_atual = c.get("cliente")
            cliente_idx = CLIENTES_EDICAO.index(cliente_atual) if cliente_atual in CLIENTES_EDICAO else 0
            cliente = st.selectbox("Cliente", CLIENTES_EDICAO, index=cliente_idx)
            
            solicitante = st.text_input("Solicitante", value=c.get("solicitante","") or "")
            sistema = st.text_input("Sistema / Módulo", value=c.get("sistema","") or "")

        st.markdown("---")
        
        # Inicializa as variáveis com nulo para garantir que o banco fique limpo
        data_aprovacao = None
        prazo_dev = None
        tempo_est = None
        descricao_reuniao = None
        atendente_suporte = None
        prazo_analise = None

        # ==========================================
        # SEPARAÇÃO DE DADOS: Suporte vs Desenvolvimento
        # ==========================================
        if setor == "Desenvolvimento":
            try: data_ap = date.fromisoformat(c["data_aprovacao"]) if c.get("data_aprovacao") else None
            except: data_ap = None
            
            try: prazo_d = date.fromisoformat(c["prazo_desenvolvimento"]) if c.get("prazo_desenvolvimento") else None
            except: prazo_d = None

            c3, c4 = st.columns(2)
            with c3:
                data_aprovacao = st.date_input("Data de Aprovação (Dev)", value=data_ap)
                prazo_dev = st.date_input("Prazo Dev.", value=prazo_d)
            with c4:
                tempo_est = st.number_input("Tempo Est. Dev (dias)", value=c.get("tempo_estimado_dias") or 0, min_value=0)
                descricao_reuniao = st.text_area("Reunião de Aprovação", value=c.get("descricao_reuniao","") or "", height=80)
                
        elif setor == "Suporte":
            c3, c4 = st.columns(2)
            with c3:
                atendente_atual = c.get("atendente_suporte")
                atend_idx = ATENDENTES_SUPORTE.index(atendente_atual) if atendente_atual in ATENDENTES_SUPORTE else 0
                atendente_suporte = st.selectbox("Atendente Suporte", ATENDENTES_SUPORTE, index=atend_idx)
            with c4:
                prazo_analise = st.number_input("Prazo Análise Suporte (dias)", value=c.get("prazo_analise_dias") or 0, min_value=0)


        st.markdown("---")
        descricao = st.text_area("Descrição", value=c.get("descricao","") or "", height=100)
        
        st.markdown("---")
        col_pend, col_res = st.columns(2)
        with col_pend:
            pendente = st.checkbox("⚠️ Pendente", value=c.get("pendente", False))
            desc_pend = st.text_area("Descrição da Pendência", value=c.get("descricao_pendencia","") or "", height=70)
        with col_res:
            st.markdown("<span style='font-size:0.85rem; font-weight:600;'>🏁 Fechamento / Cancelamento</span>", unsafe_allow_html=True)
            resolucao = st.text_area("Solução / Motivo Cancelamento", value=c.get("resolucao","") or c.get("motivo_cancelamento","") or "", height=70)
            versao = st.text_input("Versão / Release", value=c.get("versao_liberacao","") or "")

        col_save, col_del = st.columns([3, 1])
        with col_save:
            save = st.form_submit_button("💾 Salvar Alterações", use_container_width=True)
        with col_del:
            delete = st.form_submit_button("🗑️ Excluir", use_container_width=True)

        if save:
            try: data_abertura_banco = date.fromisoformat((c.get("data_abertura") or "")[:10])
            except: data_abertura_banco = date.today()

            if prazo_dev and prazo_dev < data_abertura_banco:
                st.error("⏳ O Prazo de Desenvolvimento não pode ser anterior à Data de Abertura do chamado!")
            elif status == "Aprovado" and not data_aprovacao:
                st.error("📅 É obrigatório informar a Data de Aprovação para mudar o status para 'Aprovado'.")
            elif status in ["Concluído", "Cancelado"] and not resolucao.strip():
                 st.error(f"🏁 Para alterar o status para '{status}', informe a Solução/Motivo na caixa ao lado.")
            else:
                dados = {
                    "numero_chamado": numero, "cliente": cliente, "tipo": tipo, "status": status, "titulo": titulo,
                    "tecnico": tecnico, "atendente_suporte": atendente_suporte,
                    "data_aprovacao": str(data_aprovacao) if data_aprovacao else None,
                    "prazo_desenvolvimento": str(prazo_dev) if prazo_dev else None,
                    "tempo_estimado_dias": tempo_est or None,
                    "prazo_analise_dias": prazo_analise or None,
                    "solicitante": solicitante or None, "sistema": sistema or None,
                    "descricao": descricao, "descricao_reuniao": descricao_reuniao or None,
                    "pendente": pendente, "descricao_pendencia": desc_pend if pendente else None,
                    "resolucao": resolucao if status == "Concluído" else None,
                    "versao_liberacao": versao if status == "Concluído" else None,
                    "motivo_cancelamento": resolucao if status == "Cancelado" else None,
                }
                try:
                    atualizar_chamado(c["id"], dados)
                    st.success("✅ Chamado atualizado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

        if delete:
            try:
                deletar_chamado(c["id"])
                st.success("Chamado excluído.")
                st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")