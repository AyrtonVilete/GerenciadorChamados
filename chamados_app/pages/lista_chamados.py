import streamlit as st
from database import listar_chamados, atualizar_chamado, deletar_chamado, buscar_chamado
from notificacoes import gerar_link_google_agenda, gerar_ics
from datetime import date

# Listas globais
TIPOS = ["", "Problema", "Sugestão", "Solicitação", "Melhoria", "Outros"]
STATUS = ["", "Aberto", "Aprovado", "Em Desenvolvimento", "Concluído", "Cancelado"]
TECNICOS_FILTRO = ["", "Ayrton", "Thiago Manoel", "Gabriel", "Diego"]
TECNICOS_EDICAO = ["Ayrton", "Thiago Manoel", "Gabriel", "Diego"]

def render():
    st.markdown('<div class="section-title">📋 Chamados</div>', unsafe_allow_html=True)

    # Filtros
    with st.expander("🔍 Filtros", expanded=False):
        # Aumentei para 4 colunas para encaixar o filtro de técnico
        f1, f2, f3, f4 = st.columns([1, 1, 1, 1.2])
        with f1:
            f_tipo = st.selectbox("Tipo", TIPOS)
        with f2:
            f_status = st.selectbox("Status", STATUS)
        with f3:
            f_tecnico = st.selectbox("Técnico", TECNICOS_FILTRO)
        with f4:
            st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
            f_pendente = st.checkbox("Apenas Pendentes")
            
        f_busca = st.text_input("Buscar por número ou título", placeholder="Digite para buscar...")

    filtros = {}
    if f_tipo: filtros["tipo"] = f_tipo
    if f_status: filtros["status"] = f_status
    if f_tecnico: filtros["tecnico"] = f_tecnico
    if f_pendente: filtros["pendente"] = True

    try:
        chamados = listar_chamados(filtros)
    except Exception as e:
        st.error(f"Erro ao carregar chamados: {e}")
        return

    if f_busca:
        busca = f_busca.lower()
        chamados = [c for c in chamados if
                    busca in (c.get("numero_chamado") or "").lower() or
                    busca in (c.get("titulo") or "").lower()]

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
            if date.fromisoformat(prazo_str) < hoje:
                atrasado = True
        except:
            pass

    tipo_cores = {
        "Problema": ("#7f1d1d", "#fca5a5"),
        "Sugestão": ("#1e3a5f", "#93c5fd"),
        "Solicitação": ("#064e3b", "#6ee7b7"),
        "Melhoria": ("#4c1d95", "#c4b5fd"),
        "Outros": ("#292524", "#d6d3d1"),
    }
    bg_tipo, fg_tipo = tipo_cores.get(c.get("tipo"), ("#292524", "#d6d3d1"))
    borda = "#ef4444" if atrasado else ("#f59e0b" if c.get("pendente") else "#3b82f6")

    with st.expander(
        f"#{c.get('numero_chamado','?')} | {c.get('tipo','')} | {c.get('titulo','')} {'⚠️' if c.get('pendente') else ''} {'🔴' if atrasado else ''}",
        expanded=False
    ):
        tab1, tab2 = st.tabs(["📄 Detalhes", "✏️ Editar"])

        with tab1:
            _detalhes(c, atrasado)

        with tab2:
            _formulario_edicao(c)


def _detalhes(c, atrasado):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Nº Chamado:** `{c.get('numero_chamado','')}`")
        st.markdown(f"**Tipo:** {c.get('tipo','')}")
        st.markdown(f"**Status:** {c.get('status','')}")
        st.markdown(f"**Solicitante:** {c.get('solicitante','—')}")
        # Técnico adicionado na exibição de detalhes
        st.markdown(f"**Técnico:** {c.get('tecnico','—')}")
        st.markdown(f"**Sistema/Módulo:** {c.get('sistema','—')}")
    with col2:
        st.markdown(f"**Abertura:** {(c.get('data_abertura','') or '')[:10]}")
        st.markdown(f"**Aprovação:** {(c.get('data_aprovacao','') or '—')[:10]}")
        st.markdown(f"**Prazo Dev.:** {c.get('prazo_desenvolvimento','—') or '—'}")
        st.markdown(f"**Tempo Estimado:** {c.get('tempo_estimado_dias','—') or '—'} dia(s)")
        if atrasado:
            st.markdown('<span style="color:#ef4444;">🔴 **CHAMADO ATRASADO**</span>', unsafe_allow_html=True)

    if c.get("descricao"):
        st.markdown("**Descrição:**")
        st.markdown(f"> {c['descricao']}")

    if c.get("descricao_reuniao"):
        st.markdown("**Reunião de Aprovação:**")
        st.markdown(f"> {c['descricao_reuniao']}")

    if c.get("pendente"):
        st.markdown(f"""
        <div class="alert-box">
            <strong>⚠️ Pendência:</strong><br>
            {c.get('descricao_pendencia','Sem descrição')}
        </div>
        """, unsafe_allow_html=True)

    if c.get("prazo_desenvolvimento"):
        link = gerar_link_google_agenda(c)
        ics = gerar_ics(c)
        cola, colb = st.columns(2)
        with cola:
            if link:
                st.link_button("📅 Google Agenda", link)
        with colb:
            if ics:
                st.download_button("📥 Baixar .ics", data=ics,
                                   file_name=f"chamado_{c.get('numero_chamado','x')}.ics",
                                   mime="text/calendar")


def _formulario_edicao(c):
    # Usando as listas globais para edição para não permitir campos vazios
    TIPOS_LISTA = ["Problema", "Sugestão", "Solicitação", "Melhoria", "Outros"]
    STATUS_LISTA = ["Aberto", "Aprovado", "Em Desenvolvimento", "Concluído", "Cancelado"]

    with st.form(f"edit_{c['id']}"):
        e1, e2 = st.columns(2)
        with e1:
            numero = st.text_input("Nº Chamado", value=c.get("numero_chamado",""))
            tipo_idx = TIPOS_LISTA.index(c.get("tipo")) if c.get("tipo") in TIPOS_LISTA else 0
            tipo = st.selectbox("Tipo", TIPOS_LISTA, index=tipo_idx)
            status_idx = STATUS_LISTA.index(c.get("status")) if c.get("status") in STATUS_LISTA else 0
            status = st.selectbox("Status", STATUS_LISTA, index=status_idx)
            
            # Novo campo Técnico no formulário
            tecnico_atual = c.get("tecnico")
            tecnico_idx = TECNICOS_EDICAO.index(tecnico_atual) if tecnico_atual in TECNICOS_EDICAO else 0
            tecnico = st.selectbox("Técnico", TECNICOS_EDICAO, index=tecnico_idx)

        with e2:
            titulo = st.text_input("Título", value=c.get("titulo",""))
            solicitante = st.text_input("Solicitante", value=c.get("solicitante","") or "")
            sistema = st.text_input("Sistema", value=c.get("sistema","") or "")

        try:
            data_ap = date.fromisoformat(c["data_aprovacao"]) if c.get("data_aprovacao") else None
            prazo_d = date.fromisoformat(c["prazo_desenvolvimento"]) if c.get("prazo_desenvolvimento") else None
        except:
            data_ap = None
            prazo_d = None

        data_aprovacao = st.date_input("Data de Aprovação", value=data_ap)
        prazo_dev = st.date_input("Prazo de Desenvolvimento", value=prazo_d)
        tempo_est = st.number_input("Tempo Estimado (dias)", value=c.get("tempo_estimado_dias") or 0, min_value=0)
        descricao = st.text_area("Descrição", value=c.get("descricao","") or "", height=100)
        descricao_reuniao = st.text_area("Reunião de Aprovação", value=c.get("descricao_reuniao","") or "", height=80)
        pendente = st.checkbox("⚠️ Pendente", value=c.get("pendente", False))
        desc_pend = st.text_area("Descrição da Pendência", value=c.get("descricao_pendencia","") or "", height=70)

        col_save, col_del = st.columns([3, 1])
        with col_save:
            save = st.form_submit_button("💾 Salvar Alterações", use_container_width=True)
        with col_del:
            delete = st.form_submit_button("🗑️ Excluir", use_container_width=True)

        if save:
            dados = {
                "numero_chamado": numero, 
                "tipo": tipo, 
                "status": status, 
                "titulo": titulo,
                "tecnico": tecnico,  # Incluído no dicionário de salvamento
                "data_aprovacao": str(data_aprovacao) if data_aprovacao else None,
                "prazo_desenvolvimento": str(prazo_dev) if prazo_dev else None,
                "tempo_estimado_dias": tempo_est or None,
                "solicitante": solicitante or None, 
                "sistema": sistema or None,
                "descricao": descricao, 
                "descricao_reuniao": descricao_reuniao or None,
                "pendente": pendente, 
                "descricao_pendencia": desc_pend if pendente else None,
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