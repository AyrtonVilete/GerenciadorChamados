import streamlit as st
from database import listar_chamados
from datetime import date
from collections import Counter
import pandas as pd
import io

# ==========================================
# CADEADO INTELIGENTE DE SEGURANÇA
# ==========================================
if "usuario" not in st.session_state:
    st.error("🔒 Sessão expirada ou acesso direto negado.")
    st.page_link("app.py", label="⬅️ Ir para a Tela de Login")
    st.stop()
# ==========================================

def render():
    st.markdown('<div class="section-title">📊 Relatórios e Pesquisa</div>', unsafe_allow_html=True)

    try:
        todos_chamados = listar_chamados()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return

    if not todos_chamados:
        st.info("Nenhum dado disponível ainda. Cadastre chamados para visualizar relatórios.")
        return

    with st.expander("🔍 Filtros de Busca", expanded=True):
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1: 
            f_numero = st.text_input("Nº do Chamado", placeholder="Ex: 1079")
        with col2:
            clientes_unicos = sorted(list(set(c.get("cliente") for c in todos_chamados if c.get("cliente"))))
            f_cliente = st.selectbox("Cliente", ["Todos"] + clientes_unicos)
        with col3:
            tecnicos_unicos = sorted(list(set(c.get("tecnico") for c in todos_chamados if c.get("tecnico"))))
            f_tecnico = st.selectbox("Técnico", ["Todos"] + tecnicos_unicos)
        with col4:
            status_unicos = sorted(list(set(c.get("status") for c in todos_chamados if c.get("status"))))
            f_status = st.multiselect("Status", status_unicos, placeholder="Selecione...")
        with col5:
            tipos_unicos = sorted(list(set(c.get("tipo") for c in todos_chamados if c.get("tipo"))))
            f_tipo = st.multiselect("Tipo", tipos_unicos, placeholder="Selecione...")

    dados_filtrados = todos_chamados

    if f_numero: dados_filtrados = [c for c in dados_filtrados if f_numero.lower() in str(c.get("numero_chamado", "")).lower()]
    if f_cliente != "Todos": dados_filtrados = [c for c in dados_filtrados if c.get("cliente") == f_cliente]
    if f_tecnico != "Todos": dados_filtrados = [c for c in dados_filtrados if c.get("tecnico") == f_tecnico]
    if f_status: dados_filtrados = [c for c in dados_filtrados if c.get("status") in f_status]
    if f_tipo: dados_filtrados = [c for c in dados_filtrados if c.get("tipo") in f_tipo]

    if not dados_filtrados:
        st.warning("Nenhum chamado encontrado com esses filtros.")
        return

    stats = _calcular_stats_memoria(dados_filtrados)
    por_tipo = _calcular_agrupamento(dados_filtrados, "tipo")
    por_status = _calcular_agrupamento(dados_filtrados, "status")

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
    
    # NOVO BOTÃO DE DOWNLOAD (Excel)
    excel_data = _gerar_excel(dados_filtrados)
    if excel_data:
        st.download_button(
            label="📥 Exportar Excel Formatado",
            data=excel_data,
            file_name=f"Relatorio_Chamados_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=False
        )


# ==========================================
# FUNÇÕES AUXILIARES E CÁLCULOS
# ==========================================
def _calcular_stats_memoria(chamados):
    hoje = date.today()
    stats = {"total": len(chamados), "concluidos": 0, "pendentes": 0, "atrasados": 0}
    for c in chamados:
        if c.get("status") == "Concluído": stats["concluidos"] += 1
        if c.get("pendente"): stats["pendentes"] += 1
        prazo_str = c.get("prazo_desenvolvimento")
        if prazo_str and c.get("status") not in ["Concluído", "Cancelado"]:
            try:
                if date.fromisoformat(prazo_str[:10]) < hoje: stats["atrasados"] += 1
            except ValueError: pass
    return stats

def _calcular_agrupamento(chamados, chave):
    contagem = Counter(c.get(chave, "Não Informado") for c in chamados)
    resultado = [{chave: k, "quantidade": v} for k, v in contagem.items()]
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
    st.markdown(f'<div style="background:#111827; border:1px solid #1e2d45; border-radius:8px; padding:16px;">{html}</div>'.replace('\n', ''), unsafe_allow_html=True)

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
    html += '<div style="display:flex; height:10px; border-radius:6px; overflow:hidden; margin-top:12px;">'
    for i, d in enumerate(dados):
        cor = cores[i % len(cores)]
        pct = d[key_val] / total * 100 if total else 0
        html += f'<div style="width:{pct}%; background:{cor};"></div>'
    html += "</div></div>"
    st.markdown(f'<div style="background:#111827; border:1px solid #1e2d45; border-radius:8px; padding:16px;">{html}</div>'.replace('\n', ''), unsafe_allow_html=True)

def _tabela_chamados(chamados):
    hoje = date.today()
    colunas = ["Nº", "Cliente", "Setor", "Tipo", "Status", "Título", "Responsável", "Abertura", "Prazo", "Pend."]
    header = "".join(f'<th style="padding:10px 12px; text-align:left; color:#64748b; font-size:0.8rem; border-bottom:1px solid #1e2d45;">{c}</th>' for c in colunas)
    rows = ""
    for c in chamados:
        setor = c.get("setor", "Dev")
        prazo_str = c.get("prazo_desenvolvimento") if setor != "Suporte" else None
        atrasado = False
        if prazo_str and c.get("status") not in ["Concluído", "Cancelado"]:
            try:
                if date.fromisoformat(prazo_str) < hoje: atrasado = True
            except ValueError: pass

        pend_icon = "⚠️" if c.get("pendente") else "—"
        atr_style = "color:#ef4444;" if atrasado else ""
        tipo_cores = {"Problema":"#fca5a5","Sugestão":"#93c5fd","Solicitação":"#6ee7b7","Melhoria":"#c4b5fd","Outros":"#d6d3d1"}
        tipo_cor = tipo_cores.get(c.get("tipo",""), "#d6d3d1")
        responsavel = c.get('atendente_suporte', '') if setor == "Suporte" else c.get('tecnico', '')

        # ==========================================
        # NOVO: Geração do Link Dinâmico para o PDVNet
        # ==========================================
        numero_chamado = c.get('numero_chamado', '')
        link_pdvnet = f"https://app.pdvnet.com.br/app/Chamado/{numero_chamado}"

        rows += f"""
        <tr style="border-bottom:1px solid #1e2d45; transition:background 0.15s;" onmouseover="this.style.background='#1a2235'" onmouseout="this.style.background='transparent'">
            <td style="padding:10px 12px; font-family:'JetBrains Mono'; font-size:0.85rem;">
                <a href="{link_pdvnet}" target="_blank" style="color:#3b82f6; text-decoration:none; font-weight:bold;" onmouseover="this.style.textDecoration='underline'" onmouseout="this.style.textDecoration='none'">{numero_chamado} 🔗</a>
            </td>
            <td style="padding:10px 12px; font-size:0.82rem; color:#0ea5e9; font-weight: 500;">{c.get('cliente','')}</td>
            <td style="padding:10px 12px; font-size:0.82rem; color:#cbd5e1;">{setor[:3].upper()}</td>
            <td style="padding:10px 12px;"><span style="color:{tipo_cor}; font-size:0.82rem;">{c.get('tipo','')}</span></td>
            <td style="padding:10px 12px; font-size:0.82rem; color:#e2e8f0;">{c.get('status','')}</td>
            <td style="padding:10px 12px; font-size:0.85rem; color:#e2e8f0;">{c.get('titulo','')}</td>
            <td style="padding:10px 12px; font-size:0.82rem; color:#3b82f6; font-weight: 500;">{responsavel or '—'}</td>
            <td style="padding:10px 12px; font-size:0.82rem; color:#64748b;">{(c.get('data_abertura','') or '')[:10]}</td>
            <td style="padding:10px 12px; font-size:0.82rem; {atr_style}">{prazo_str[:10] if prazo_str else '—'}{' 🔴' if atrasado else ''}</td>
            <td style="padding:10px 12px; font-size:0.9rem; text-align: center;">{pend_icon}</td>
        </tr>
        """
    tabela = f"""<div style="overflow-x:auto;"><table style="width:100%; border-collapse:collapse; background:#111827; border:1px solid #1e2d45; border-radius:8px; overflow:hidden;"><thead><tr>{header}</tr></thead><tbody>{rows}</tbody></table></div>""".replace('\n', '')
    st.markdown(tabela, unsafe_allow_html=True)


# ==========================================
# NOVA FUNÇÃO DE EXCEL FORMATADO
# ==========================================
def _gerar_excel(chamados):
    if not chamados:
        return None

    # Transforma a lista do banco de dados em uma tabela Pandas
    df = pd.DataFrame(chamados)

    # Dicionário para renomear as colunas para o português bonito
    mapeamento_colunas = {
        "numero_chamado": "Nº Chamado",
        "cliente": "Cliente",
        "setor": "Setor",
        "tipo": "Tipo",
        "status": "Status",
        "titulo": "Título do Chamado",
        "solicitante": "Solicitante",
        "tecnico": "Registrado por",
        "nivel_suporte": "Nível Sup.",
        "atendente_suporte": "Atendente Sup.",
        "sistema": "Sistema/Módulo",
        "data_abertura": "Data de Abertura",
        "data_aprovacao": "Data de Aprovação",
        "prazo_desenvolvimento": "Prazo Dev.",
        "tempo_estimado_dias": "Tempo Estimado (dias)",
        "prazo_analise_dias": "Prazo Análise (dias)",
        "pendente": "Possui Pendência?",
        "descricao_pendencia": "Motivo da Pendência",
        "resolucao": "Solução do Dev",
        "motivo_cancelamento": "Motivo do Cancelamento",
        "versao_liberacao": "Versão Liberada"
    }

    # Mantém apenas as colunas mapeadas que existem e aplica os nomes bonitos
    cols_existentes = [c for c in mapeamento_colunas.keys() if c in df.columns]
    df = df[cols_existentes]
    df = df.rename(columns=mapeamento_colunas)

    # Deixa o True/False de pendência mais profissional (Sim/Não)
    if "Possui Pendência?" in df.columns:
        df["Possui Pendência?"] = df["Possui Pendência?"].apply(lambda x: "Sim" if x else "Não")

    # Cria o arquivo na memória
    buffer = io.BytesIO()

    # Aplica o estilo corporativo usando xlsxwriter
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Base de Chamados')
        
        workbook = writer.book
        worksheet = writer.sheets['Base de Chamados']

        # Formato do cabeçalho: Azul com texto branco e negrito
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#1e40af', # Azul escuro
            'font_color': 'white',
            'border': 1
        })

        # Aplica o formato na primeira linha
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)

        # Ajusta as larguras das colunas
        for i, col in enumerate(df.columns):
            # Jeito blindado: usa o .str.len() que o novo Pandas adora
            tamanho_conteudo = df[col].astype(str).str.len().max()
            
            # Se a coluna vier completamente vazia, previne o erro de NaN
            if pd.isna(tamanho_conteudo):
                tamanho_conteudo = 0
                
            tamanho_max = max(tamanho_conteudo, len(str(col))) + 2
            
            # Limita a largura máxima para não estourar a tela em descrições muito grandes
            tamanho_ajustado = min(tamanho_max, 60)
            worksheet.set_column(i, i, tamanho_ajustado)
            
        # Ativa os filtros automáticos no topo
        worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)

    return buffer.getvalue()