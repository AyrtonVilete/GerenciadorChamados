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

def verificar_numero_existe(numero_chamado: str) -> bool:
    """
    Verifica se um número de chamado já existe no banco de dados.
    Retorna True se existir, False caso contrário.
    """
    try:
        # Chama a sua função padrão de conexão!
        client = get_client()
        
        # Usa a variável 'client' em vez de 'supabase'
        response = client.table("chamados").select("numero_chamado").eq("numero_chamado", numero_chamado).execute()
        
        return len(response.data) > 0
    except Exception as e:
        print(f"Erro ao verificar número do chamado: {e}")
        return False

def buscar_perfil_usuario(email: str) -> str:
    """
    Busca o nível de acesso do usuário pelo e-mail.
    Retorna 'Comum' se o usuário não for encontrado na tabela de perfis.
    """
    try:
        client = get_client()
        response = client.table("perfis_acesso").select("perfil").eq("email", email).execute()
        
        if response.data:
            return response.data[0]["perfil"]
        return "Comum" # Perfil de segurança caso o usuário não esteja na tabela
    except Exception as e:
        print(f"Erro ao buscar perfil: {e}")
        return "Comum"

def get_admin_client():
    """Cria uma conexão com privilégios máximos para gerenciar usuários."""
    url = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
    service_key = st.secrets.get("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_SERVICE_KEY", ""))
    
    if not service_key:
        st.error("⚠️ Configure a SUPABASE_SERVICE_KEY no secrets.toml")
        st.stop()
        
    return create_client(url, service_key)

def criar_usuario_sistema(email: str, senha: str, perfil: str) -> bool:
    """Cria a conta no Auth e já vincula o perfil na tabela."""
    admin_client = get_admin_client()
    try:
        # 1. Cria o usuário no sistema de Autenticação
        admin_client.auth.admin.create_user({
            "email": email,
            "password": senha,
            "email_confirm": True # Já entra validado
        })
        
        # 2. Registra o perfil dele na nossa tabela de permissões
        admin_client.table("perfis_acesso").insert({
            "email": email,
            "perfil": perfil
        }).execute()
        return True
    except Exception as e:
        print(f"Erro ao criar usuário: {e}")
        raise e

def listar_perfis_acesso() -> list:
    """Retorna todos os usuários cadastrados na tabela de perfis."""
    client = get_client()
    res = client.table("perfis_acesso").select("*").order("id").execute()
    return res.data or []