import streamlit as st
from supabase import create_client, Client
from datetime import datetime, date
import os

def get_client() -> Client:
    url = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
    key = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY", ""))
    if not url or not key:
        st.error("⚠️ Configure SUPABASE_URL e SUPABASE_KEY em .streamlit/secrets.toml")
        st.stop()
    return create_client(url, key)


def criar_chamado(dados: dict) -> dict:
    client = get_client()
    dados["criado_em"] = datetime.now().isoformat()
    dados["atualizado_em"] = datetime.now().isoformat()
    res = client.table("chamados").insert(dados).execute()
    return res.data[0] if res.data else {}


def listar_chamados(filtros: dict = None) -> list:
    client = get_client()
    query = client.table("chamados").select("*").order("criado_em", desc=True)
    if filtros:
        if filtros.get("tipo"):
            query = query.eq("tipo", filtros["tipo"])
        if filtros.get("status"):
            query = query.eq("status", filtros["status"])
        if filtros.get("pendente"):
            query = query.eq("pendente", True)
    res = query.execute()
    return res.data or []


def buscar_chamado(id: int) -> dict:
    client = get_client()
    res = client.table("chamados").select("*").eq("id", id).execute()
    return res.data[0] if res.data else {}


def atualizar_chamado(id: int, dados: dict) -> dict:
    client = get_client()
    dados["atualizado_em"] = datetime.now().isoformat()
    res = client.table("chamados").update(dados).eq("id", id).execute()
    return res.data[0] if res.data else {}


def deletar_chamado(id: int) -> bool:
    client = get_client()
    client.table("chamados").delete().eq("id", id).execute()
    return True


def chamados_por_tipo() -> list:
    client = get_client()
    res = client.table("chamados").select("tipo").execute()
    dados = res.data or []
    contagem = {}
    for item in dados:
        t = item.get("tipo", "Outros")
        contagem[t] = contagem.get(t, 0) + 1
    return [{"tipo": k, "quantidade": v} for k, v in contagem.items()]


def chamados_por_status() -> list:
    client = get_client()
    res = client.table("chamados").select("status").execute()
    dados = res.data or []
    contagem = {}
    for item in dados:
        s = item.get("status", "Aberto")
        contagem[s] = contagem.get(s, 0) + 1
    return [{"status": k, "quantidade": v} for k, v in contagem.items()]


def chamados_proximos_prazo(dias: int = 5) -> list:
    """Retorna chamados cujo prazo está dentro de X dias."""
    client = get_client()
    res = client.table("chamados")\
        .select("*")\
        .not_.is_("prazo_desenvolvimento", "null")\
        .not_.eq("status", "Concluído")\
        .not_.eq("status", "Cancelado")\
        .execute()
    
    from datetime import timedelta
    hoje = date.today()
    limite = hoje + timedelta(days=dias)
    
    proximos = []
    for c in (res.data or []):
        prazo_str = c.get("prazo_desenvolvimento")
        if prazo_str:
            try:
                prazo = date.fromisoformat(prazo_str)
                if hoje <= prazo <= limite:
                    c["dias_restantes"] = (prazo - hoje).days
                    proximos.append(c)
            except:
                pass
    return proximos


def estatisticas_gerais() -> dict:
    client = get_client()
    todos = client.table("chamados").select("*").execute().data or []
    
    hoje = date.today()
    atrasados = 0
    for c in todos:
        prazo_str = c.get("prazo_desenvolvimento")
        if prazo_str and c.get("status") not in ["Concluído", "Cancelado"]:
            try:
                prazo = date.fromisoformat(prazo_str)
                if prazo < hoje:
                    atrasados += 1
            except:
                pass

    return {
        "total": len(todos),
        "pendentes": sum(1 for c in todos if c.get("pendente")),
        "atrasados": atrasados,
        "concluidos": sum(1 for c in todos if c.get("status") == "Concluído"),
        "em_desenvolvimento": sum(1 for c in todos if c.get("status") == "Em Desenvolvimento"),
        "abertos": sum(1 for c in todos if c.get("status") == "Aberto"),
    }
