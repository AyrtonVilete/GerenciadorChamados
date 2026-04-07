import streamlit as st
from database import listar_chamados, chamados_por_tipo, chamados_por_status, estatisticas_gerais
from datetime import date, datetime
import json
import streamlit as st
from database import listar_chamados
from datetime import date
from collections import Counter

def render():
    st.markdown('<div class="section-title">📊 Relatórios e Pesquisa</div>', unsafe_allow_html=True)

    try:
        # Puxamos apenas a lista completa uma vez. Os agregados serão calculados em memória.
        todos_chamados = listar_chamados()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return

    if not todos_chamados:
        st.info("Nenhum dado disponível ainda. Cadastre chamados para visualizar relatórios.")
        return

    # ==========================================
    # 1. FILTROS DE BUSCA (Nova Seção)
    # ==========================================
    with st.expander("🔍 Filtros de Busca", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            f_numero = st.text_input("Nº do Chamado", placeholder="Ex: 1079")
            
        with col2:
            # Pega dinamicamente os técnicos que existem no banco
            tecnicos_unicos = sorted(list(set(c.get("tecnico") for c in todos_chamados if c.get("tecnico"))))
            f_tecnico = st.selectbox("Técnico", ["Todos"] + tecnicos_unicos)
            
        with col3:
            status_unicos = sorted(list(set(c.get("status") for c in todos_chamados if c.get("status"))))
            f_status = st.multiselect("Status", status_unicos, placeholder="Selecione...")
            
        with col4:
            tipos_unicos = sorted(list(set(c.get("tipo") for c in todos_chamados if c.get("tipo"))))
            f_tipo = st.multiselect("Tipo", tipos_unicos, placeholder="Selecione...")

    # ==========================================
    # 2. APLICANDO OS FILTROS NOS DADOS
    # ==========================================
    dados_filtrados = todos_chamados

    if f_numero:
        dados_filtrados = [c for c in dados_filtrados if f_numero.lower() in str(c.get("numero_chamado", "")).lower()]
    
    if f_tecnico != "Todos":
        dados_filtrados = [c for c in dados_filtrados if c.get("tecnico") == f_tecnico]
        
    if f_status:
        dados_filtrados = [c for c in dados_filtrados if c.get("status") in f_status]
        
    if f_tipo:
        dados_filtrados = [c for c in dados_filtrados if c.get("tipo") in f_tipo]

    if not dados_filtrados:
        st.warning("Nenhum chamado encontrado com esses filtros.")
        return

    # ==========================================
    # 3. RECALCULANDO ESTATÍSTICAS COM OS DADOS FILTRADOS
    # ==========================================
    stats = _calcular_stats_memoria(dados_filtrados)
    por_tipo = _calcular_agrupamento(dados_filtrados, "tipo")
    por_status = _calcular_agrupamento(dados_filtrados, "status")

    # ==========================================
    # 4. EXIBINDO KPIs E GRÁFICOS
    # ==========================================
    st.markdown("### 📈 Indicadores")
    cols = st.columns(4)
    kpis = [
        ("Total Filtrado", stats["total"], "#3b82f6"),
        ("Taxa de Conclusão", f"{round(stats['concluidos']/max(stats['total'],1)*100)}%", "#10b981"),
        ("Pendências", stats["pendentes"], "#f59e0b"),
        ("Atrasados", stats["atrasados"], "#ef4444"),
    ]
    for col, (label, val, cor) in zip(cols, kpis):
        with col:
            st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:{cor};">{val}</div><div class="metric-label">{label}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### Por Tipo")
        _grafico_barras(por_tipo, "tipo", "quantidade", ["#ef4444","#3b82f6","#10b981","#a78bfa","#94a3b8"], "por_tipo")

    with col_b:
        st.markdown("#### Por Status")
        _grafico_donut(por_status, "status", "quantidade", ["#3b82f6","#10b981","#a78bfa","#06b6d4","#64748b"])

    st.markdown("---")

    st.markdown(f"### 📋 Lista de Chamados ({len(dados_filtrados)})")
    _tabela_chamados(dados_filtrados)

    st.markdown("---")
    csv = _gerar_csv(dados_filtrados)
    st.download_button(
        "📥 Exportar CSV (Dados Filtrados)",
        data=csv,
        file_name=f"chamados_filtrados_{date.today()}.csv",
        mime="text/csv",
        use_container_width=False
    )

def _calcular_stats_memoria(chamados):
    hoje = date.today()
    stats = {"total": len(chamados), "concluidos": 0, "pendentes": 0, "atrasados": 0}
    
    for c in chamados:
        if c.get("status") == "Concluído":
            stats["concluidos"] += 1
        if c.get("pendente"):
            stats["pendentes"] += 1
            
        prazo_str = c.get("prazo_desenvolvimento")
        if prazo_str and c.get("status") not in ["Concluído", "Cancelado"]:
            try:
                if date.fromisoformat(prazo_str[:10]) < hoje:
                    stats["atrasados"] += 1
            except ValueError:
                pass
    return stats

def _calcular_agrupamento(chamados, chave):
    contagem = Counter(c.get(chave, "Não Informado") for c in chamados)
    # Converte o formato do Counter para a lista de dicionários que os gráficos esperam
    resultado = [{chave: k, "quantidade": v} for k, v in contagem.items()]
    # Ordena do maior para o menor
    return sorted(resultado, key=lambda x: x["quantidade"], reverse=True)


def _grafico_barras(dados, key_label, key_val, cores, uid):
    if not dados:
        st.info("Sem dados")
        return

    labels = [d[key_label] for d in dados]
    valores = [d[key_val] for d in dados]
    max_val = max(valores) if valores else 1

    html = '<div style="padding:10px;">'
    for i, (label, val) in enumerate(zip(labels, valores)):
        cor = cores[i % len(cores)]
        pct = val / max_val * 100
        html += f"""
        <div style="margin-bottom:14px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                <span style="color:#e2e8f0; font-size:0.85rem;">{label}</span>
                <span style="color:{cor}; font-weight:700; font-family:'JetBrains Mono';">{val}</span>
            </div>
            <div style="background:#1e2d45; border-radius:4px; height:8px; overflow:hidden;">
                <div style="width:{pct}%; height:100%; background:{cor}; border-radius:4px; transition:width 0.6s ease;"></div>
            </div>
        </div>
        """
    html += "</div>"

    st.markdown(f'<div style="background:#111827; border:1px solid #1e2d45; border-radius:8px; padding:16px;">{html}</div>', unsafe_allow_html=True)


def _grafico_donut(dados, key_label, key_val, cores):
    if not dados:
        st.info("Sem dados")
        return

    total = sum(d[key_val] for d in dados)
    html = '<div style="padding:10px;">'
    for i, d in enumerate(dados):
        cor = cores[i % len(cores)]
        pct = round(d[key_val] / total * 100) if total else 0
        html += f"""
        <div style="display:flex; align-items:center; margin-bottom:10px;">
            <div style="width:12px; height:12px; border-radius:50%; background:{cor}; margin-right:10px; flex-shrink:0;"></div>
            <span style="color:#e2e8f0; font-size:0.85rem; flex:1;">{d[key_label]}</span>
            <span style="color:#64748b; font-size:0.82rem; margin-right:8px;">{d[key_val]}</span>
            <span style="color:{cor}; font-weight:700; font-family:'JetBrains Mono'; font-size:0.82rem;">{pct}%</span>
        </div>
        """

    # Barra empilhada
    html += '<div style="display:flex; height:10px; border-radius:6px; overflow:hidden; margin-top:12px;">'
    for i, d in enumerate(dados):
        cor = cores[i % len(cores)]
        pct = d[key_val] / total * 100 if total else 0
        html += f'<div style="width:{pct}%; background:{cor};"></div>'
    html += "</div></div>"

    st.markdown(f'<div style="background:#111827; border:1px solid #1e2d45; border-radius:8px; padding:16px;">{html}</div>', unsafe_allow_html=True)


def _tabela_chamados(chamados):
    hoje = date.today()

    # Adicionado "Técnico" na lista de colunas
    colunas = ["Nº", "Tipo", "Status", "Título", "Solicitante", "Técnico", "Abertura", "Prazo", "Pendente"]
    header = "".join(f'<th style="padding:10px 12px; text-align:left; color:#64748b; font-size:0.8rem; border-bottom:1px solid #1e2d45;">{c}</th>' for c in colunas)

    rows = ""
    for c in chamados:
        prazo_str = c.get("prazo_desenvolvimento") or ""
        atrasado = False
        if prazo_str and c.get("status") not in ["Concluído", "Cancelado"]:
            try:
                if date.fromisoformat(prazo_str) < hoje:
                    atrasado = True
            except ValueError:
                pass

        pend_icon = "⚠️" if c.get("pendente") else "—"
        atr_style = "color:#ef4444;" if atrasado else ""

        tipo_cores = {"Problema":"#fca5a5","Sugestão":"#93c5fd","Solicitação":"#6ee7b7","Melhoria":"#c4b5fd","Outros":"#d6d3d1"}
        tipo_cor = tipo_cores.get(c.get("tipo",""), "#d6d3d1")

        rows += f"""
        <tr style="border-bottom:1px solid #1e2d45; transition:background 0.15s;" onmouseover="this.style.background='#1a2235'" onmouseout="this.style.background='transparent'">
            <td style="padding:10px 12px; font-family:'JetBrains Mono'; font-size:0.8rem; color:#94a3b8;">{c.get('numero_chamado','')}</td>
            <td style="padding:10px 12px;"><span style="color:{tipo_cor}; font-size:0.82rem;">{c.get('tipo','')}</span></td>
            <td style="padding:10px 12px; font-size:0.82rem; color:#e2e8f0;">{c.get('status','')}</td>
            <td style="padding:10px 12px; font-size:0.85rem; color:#e2e8f0;">{c.get('titulo','')}</td>
            <td style="padding:10px 12px; font-size:0.82rem; color:#64748b;">{c.get('solicitante','') or '—'}</td>
            
            <td style="padding:10px 12px; font-size:0.82rem; color:#3b82f6; font-weight: 500;">{c.get('tecnico','') or '—'}</td>
            
            <td style="padding:10px 12px; font-size:0.82rem; color:#64748b;">{(c.get('data_abertura','') or '')[:10]}</td>
            <td style="padding:10px 12px; font-size:0.82rem; {atr_style}">{prazo_str[:10] if prazo_str else '—'}{' 🔴' if atrasado else ''}</td>
            <td style="padding:10px 12px; font-size:0.9rem; text-align: center;">{pend_icon}</td>
        </tr>
        """

    # O replace('\n', '') previne que o Streamlit quebre a tabela e tente renderizar como Markdown
    tabela = f"""
    <div style="overflow-x:auto;">
    <table style="width:100%; border-collapse:collapse; background:#111827; border:1px solid #1e2d45; border-radius:8px; overflow:hidden;">
        <thead><tr>{header}</tr></thead>
        <tbody>{rows}</tbody>
    </table>
    </div>
    """.replace('\n', '')
    
    st.markdown(tabela, unsafe_allow_html=True)


def _gerar_csv(chamados):
    # Adicionado o "tecnico" na lista de colunas exportadas
    cols = ["numero_chamado","tipo","status","titulo","solicitante","tecnico","sistema","data_abertura",
            "data_aprovacao","prazo_desenvolvimento","tempo_estimado_dias","pendente","descricao_pendencia"]
    
    header = ",".join(cols)
    rows = []
    for c in chamados:
        row = []
        for col in cols:
            val = str(c.get(col, "") or "").replace(",", ";").replace("\n", " ")
            row.append(val)
        rows.append(",".join(row))
    
    # Adicionando um BOM (Byte Order Mark) para garantir que o Excel no Windows leia os acentos do PT-BR corretamente
    csv_string = "\n".join([header] + rows)
    return "\ufeff" + csv_string