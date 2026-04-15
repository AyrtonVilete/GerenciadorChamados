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
    # 2. FILTROS GERAIS COM DESENVOLVEDOR (4 COLUNAS)
    # ==========================================
    with st.expander("🎛️ Filtros do Dashboard", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            data_min = df['data_abertura'].min().date() if not df['data_abertura'].isnull().all() else datetime.today().date()
            data_max = df['data_abertura'].max().date() if not df['data_abertura'].isnull().all() else datetime.today().date()
            periodo = st.date_input("Período de Abertura", value=(data_min, data_max), format="DD/MM/YYYY")
            
        with c2:
            clientes = ["Todos"] + sorted(df['cliente'].dropna().unique().tolist())
            f_cliente = st.selectbox("Filtrar por Cliente", clientes)
            
        with c3:
            setores = ["Todos"] + sorted(df['setor'].dropna().unique().tolist())
            f_setor = st.selectbox("Filtrar por Setor", setores)
            
        with c4:
            if 'desenvolvedor' in df.columns:
                devs = ["Todos"] + sorted(df['desenvolvedor'].dropna().unique().tolist())
            else:
                devs = ["Todos"]
            f_dev = st.selectbox("Filtrar por Dev", devs)

    # APLICA OS FILTROS NO DATAFRAME
    df_filtrado = df.copy()
    
    if len(periodo) == 2:
        start_date = pd.to_datetime(periodo[0])
        end_date = pd.to_datetime(periodo[1])
        df_filtrado = df_filtrado[(df_filtrado['data_abertura'] >= start_date) & (df_filtrado['data_abertura'] <= end_date)]
        
    if f_cliente != "Todos":
        df_filtrado = df_filtrado[df_filtrado['cliente'] == f_cliente]
        
    if f_setor != "Todos":
        df_filtrado = df_filtrado[df_filtrado['setor'] == f_setor]
        
    if f_dev != "Todos" and 'desenvolvedor' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['desenvolvedor'] == f_dev]

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
    # 4. GRÁFICOS GERAIS (PLOTLY)
    # ==========================================
    template_dark = "plotly_dark"
    cor_azul = "#3b82f6"
    
    col_graf1, col_graf2 = st.columns([2, 1])

    with col_graf1:
        st.markdown("#### Evolução de Chamados (Linha do Tempo)")
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

    # ==========================================
    # 5. NOVO GRÁFICO: ALOCAÇÃO DE DESENVOLVEDORES
    # ==========================================
    st.markdown("<hr style='border-color: #1e2d45; margin: 20px 0;'>", unsafe_allow_html=True)
    st.markdown("### 👨‍💻 Produtividade e Alocação da Equipe (Dev)")
    
    # Filtramos apenas o setor de Desenvolvimento para este gráfico específico
    df_devs = df_filtrado[df_filtrado['setor'] == 'Desenvolvimento']
    
    if not df_devs.empty and 'desenvolvedor' in df_devs.columns:
        # Agrupa por Desenvolvedor e por Status para criar as barras lado a lado
        df_alocacao = df_devs.groupby(['desenvolvedor', 'status']).size().reset_index(name='Quantidade')
        
        # Mapeamento de cores padronizado para ficar visualmente lógico
        cores_status = {
            "Aberto": "#3b82f6",             # Azul
            "Aprovado": "#0ea5e9",           # Ciano
            "Em Desenvolvimento": "#a78bfa", # Roxo
            "Concluído": "#10b981",          # Verde
            "Cancelado": "#ef4444"           # Vermelho
        }

        fig_alocacao = px.bar(
            df_alocacao, 
            x='desenvolvedor', 
            y='Quantidade', 
            color='status',
            barmode='group', # Isso coloca as barras lado a lado em vez de empilhadas
            template=template_dark,
            color_discrete_map=cores_status,
            labels={'desenvolvedor': 'Desenvolvedor', 'Quantidade': 'Volume de Chamados', 'status': 'Status'}
        )
        fig_alocacao.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)', 
            margin=dict(t=10, l=10, r=10, b=10),
            xaxis={'categoryorder': 'total descending'} # Ordena do dev com mais chamados pro com menos
        )
        st.plotly_chart(fig_alocacao, use_container_width=True)
    else:
        st.info("Nenhum dado do setor de Desenvolvimento encontrado para os filtros atuais.")