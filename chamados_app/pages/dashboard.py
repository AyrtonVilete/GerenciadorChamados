import streamlit as st
import pandas as pd
import plotly.express as px
from database import listar_chamados
from datetime import datetime, timedelta

# ==========================================
# CADEADO INTELIGENTE DE SEGURANÇA
# ==========================================
if "usuario" not in st.session_state:
    st.error("🔒 Sessão expirada ou acesso direto negado.")
    st.page_link("app.py", label="⬅️ Ir para a Tela de Login")
    st.stop()
# ==========================================

def render():
    st.markdown('<div class="section-title">📊 Dashboard Gerencial</div>', unsafe_allow_html=True)

    # 1. Busca e trata os dados
    try:
        chamados_raw = listar_chamados()
        if not chamados_raw:
            st.info("Nenhum dado disponível para análise.")
            return
            
        df = pd.DataFrame(chamados_raw)
        # Garante que a data de abertura é lida como Data pelo Pandas
        df['data_abertura'] = pd.to_datetime(df['data_abertura'], errors='coerce')
        
    except Exception as e:
        st.error(f"Erro ao carregar dados do banco: {e}")
        return

    # ==========================================
    # 2. FILTROS GERAIS (Sidebar ou Expander)
    # ==========================================
    with st.expander("🎛️ Filtros do Dashboard", expanded=True):
        c1, c2, c3 = st.columns(3)
        
        with c1:
            # Filtro de Data
            data_min = df['data_abertura'].min().date() if not df['data_abertura'].isnull().all() else datetime.today().date()
            data_max = df['data_abertura'].max().date() if not df['data_abertura'].isnull().all() else datetime.today().date()
            
            periodo = st.date_input("Período de Abertura", value=(data_min, data_max), format="DD/MM/YYYY")
            
        with c2:
            clientes = ["Todos"] + sorted(df['cliente'].dropna().unique().tolist())
            f_cliente = st.selectbox("Filtrar por Cliente", clientes)
            
        with c3:
            setores = ["Todos"] + sorted(df['setor'].dropna().unique().tolist())
            f_setor = st.selectbox("Filtrar por Setor", setores)

    # Aplica os filtros no DataFrame
    df_filtrado = df.copy()
    
    if len(periodo) == 2:
        start_date = pd.to_datetime(periodo[0])
        end_date = pd.to_datetime(periodo[1])
        df_filtrado = df_filtrado[(df_filtrado['data_abertura'] >= start_date) & (df_filtrado['data_abertura'] <= end_date)]
        
    if f_cliente != "Todos":
        df_filtrado = df_filtrado[df_filtrado['cliente'] == f_cliente]
        
    if f_setor != "Todos":
        df_filtrado = df_filtrado[df_filtrado['setor'] == f_setor]

    if df_filtrado.empty:
        st.warning("Nenhum chamado encontrado para os filtros selecionados.")
        return

    # ==========================================
    # 3. KPIs DE TOPO
    # ==========================================
    st.markdown("### 📈 Visão Geral")
    
    total = len(df_filtrado)
    concluidos = len(df_filtrado[df_filtrado['status'] == 'Concluído'])
    pendentes = len(df_filtrado[df_filtrado['pendente'] == True])
    taxa_conclusao = (concluidos / total * 100) if total > 0 else 0

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total de Chamados", total)
    kpi2.metric("Taxa de Resolução", f"{taxa_conclusao:.1f}%")
    kpi3.metric("Concluídos", concluidos)
    kpi4.metric("Com Pendência", pendentes)
    
    st.markdown("<hr style='border-color: #1e2d45; margin: 20px 0;'>", unsafe_allow_html=True)

    # ==========================================
    # 4. GRÁFICOS (PLOTLY)
    # ==========================================
    # Ajuste de layout para Dark Mode no Plotly
    template_dark = "plotly_dark"
    cor_azul = "#3b82f6"
    
    col_graf1, col_graf2 = st.columns([2, 1])

    with col_graf1:
        st.markdown("#### Evolução de Chamados (Linha do Tempo)")
        # Agrupa os chamados por dia
        df_tempo = df_filtrado.groupby(df_filtrado['data_abertura'].dt.date).size().reset_index(name='Quantidade')
        
        fig_tempo = px.area(
            df_tempo, x='data_abertura', y='Quantidade', 
            template=template_dark, 
            color_discrete_sequence=[cor_azul],
            labels={'data_abertura': 'Data', 'Quantidade': 'Volume'}
        )
        fig_tempo.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, l=10, r=10, b=10))
        st.plotly_chart(fig_tempo, use_container_width=True)

    with col_graf2:
        st.markdown("#### Distribuição por Status")
        df_status = df_filtrado['status'].value_counts().reset_index()
        df_status.columns = ['Status', 'Quantidade']
        
        fig_status = px.pie(
            df_status, values='Quantidade', names='Status', hole=0.4,
            template=template_dark,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_status.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, l=10, r=10, b=10))
        st.plotly_chart(fig_status, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_graf3, col_graf4 = st.columns(2)

    with col_graf3:
        st.markdown("#### Demanda por Cliente")
        df_cliente = df_filtrado['cliente'].value_counts().reset_index()
        df_cliente.columns = ['Cliente', 'Quantidade']
        
        fig_cliente = px.bar(
            df_cliente, x='Quantidade', y='Cliente', orientation='h',
            template=template_dark, color_discrete_sequence=["#10b981"]
        )
        fig_cliente.update_layout(yaxis={'categoryorder':'total ascending'}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, l=10, r=10, b=10))
        st.plotly_chart(fig_cliente, use_container_width=True)

    with col_graf4:
        st.markdown("#### Chamados por Tipo")
        df_tipo = df_filtrado['tipo'].value_counts().reset_index()
        df_tipo.columns = ['Tipo', 'Quantidade']
        
        fig_tipo = px.bar(
            df_tipo, x='Tipo', y='Quantidade',
            template=template_dark, color_discrete_sequence=["#a78bfa"]
        )
        fig_tipo.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, l=10, r=10, b=10))
        st.plotly_chart(fig_tipo, use_container_width=True)