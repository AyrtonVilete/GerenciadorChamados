import smtplib
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date, timedelta
import os


# ─── E-MAIL ───────────────────────────────────────────────────────────────────

def enviar_email_lembrete(chamado: dict) -> bool:
    """Envia e-mail de lembrete de prazo via SMTP (Gmail)."""
    smtp_user = st.secrets.get("SMTP_USER", os.getenv("SMTP_USER", ""))
    smtp_pass = st.secrets.get("SMTP_PASS", os.getenv("SMTP_PASS", ""))
    dest_email = st.secrets.get("DEST_EMAIL", os.getenv("DEST_EMAIL", smtp_user))

    if not smtp_user or not smtp_pass:
        return False

    dias = chamado.get("dias_restantes", "?")
    numero = chamado.get("numero_chamado", "N/A")
    titulo = chamado.get("titulo", "Sem título")
    prazo = chamado.get("prazo_desenvolvimento", "N/A")
    tipo = chamado.get("tipo", "N/A")
    status = chamado.get("status", "N/A")

    html = f"""
    <html><body style="font-family: Arial, sans-serif; background:#f4f6f9; padding:20px;">
    <div style="max-width:600px; margin:auto; background:white; border-radius:8px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.1);">
        <div style="background: linear-gradient(135deg, #1e40af, #0891b2); padding:24px; color:white;">
            <h2 style="margin:0;">⏰ Lembrete de Prazo</h2>
            <p style="margin:6px 0 0; opacity:0.85;">GerenciaChamados — Alerta Automático</p>
        </div>
        <div style="padding:24px;">
            <p style="color:#374151;">Olá! Um chamado está próximo do prazo de entrega:</p>
            <table style="width:100%; border-collapse:collapse; margin:16px 0;">
                <tr style="background:#f9fafb;">
                    <td style="padding:10px 14px; font-weight:600; color:#6b7280; width:40%;">Nº Chamado</td>
                    <td style="padding:10px 14px; color:#111827;"><strong>{numero}</strong></td>
                </tr>
                <tr>
                    <td style="padding:10px 14px; font-weight:600; color:#6b7280;">Título</td>
                    <td style="padding:10px 14px; color:#111827;">{titulo}</td>
                </tr>
                <tr style="background:#f9fafb;">
                    <td style="padding:10px 14px; font-weight:600; color:#6b7280;">Tipo</td>
                    <td style="padding:10px 14px; color:#111827;">{tipo}</td>
                </tr>
                <tr>
                    <td style="padding:10px 14px; font-weight:600; color:#6b7280;">Status</td>
                    <td style="padding:10px 14px; color:#111827;">{status}</td>
                </tr>
                <tr style="background:#fff3cd;">
                    <td style="padding:10px 14px; font-weight:600; color:#856404;">Prazo</td>
                    <td style="padding:10px 14px; color:#856404;"><strong>{prazo}</strong></td>
                </tr>
                <tr style="background:#fff3cd;">
                    <td style="padding:10px 14px; font-weight:600; color:#856404;">Dias Restantes</td>
                    <td style="padding:10px 14px; color:#856404; font-size:1.3rem;"><strong>{dias} dia(s)</strong></td>
                </tr>
            </table>
            <p style="color:#6b7280; font-size:0.85rem;">Este é um lembrete automático do sistema GerenciaChamados.</p>
        </div>
    </div>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"⏰ [{dias} dia(s)] Lembrete — Chamado {numero}: {titulo}"
    msg["From"] = smtp_user
    msg["To"] = dest_email
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, dest_email, msg.as_string())
        return True
    except Exception as e:
        st.warning(f"Erro ao enviar e-mail: {e}")
        return False


def verificar_e_enviar_lembretes(chamados_proximos: list, dias_alerta: int = 5) -> int:
    """Verifica chamados próximos do prazo e envia lembretes. Retorna quantos foram enviados."""
    enviados = 0
    for c in chamados_proximos:
        if enviar_email_lembrete(c):
            enviados += 1
    return enviados


# ─── GOOGLE AGENDA ────────────────────────────────────────────────────────────

def gerar_link_google_agenda(chamado: dict) -> str:
    """Gera link direto para criar evento no Google Agenda (sem OAuth necessário)."""
    from urllib.parse import urlencode, quote

    prazo_str = chamado.get("prazo_desenvolvimento")
    if not prazo_str:
        return ""

    try:
        prazo = date.fromisoformat(prazo_str)
    except:
        return ""

    # Formato do Google: YYYYMMDD
    data_fmt = prazo.strftime("%Y%m%d")
    data_fim = (prazo + timedelta(days=1)).strftime("%Y%m%d")

    titulo = f"[Chamado {chamado.get('numero_chamado', '')}] {chamado.get('titulo', 'Chamado')}"
    descricao = (
        f"Tipo: {chamado.get('tipo', '')}\n"
        f"Status: {chamado.get('status', '')}\n"
        f"Descrição: {chamado.get('descricao', '')}"
    )

    params = {
        "action": "TEMPLATE",
        "text": titulo,
        "dates": f"{data_fmt}/{data_fim}",
        "details": descricao,
    }

    return "https://calendar.google.com/calendar/render?" + urlencode(params)


def gerar_ics(chamado: dict) -> str:
    """Gera conteúdo de arquivo .ics para importar no Google Agenda."""
    prazo_str = chamado.get("prazo_desenvolvimento")
    if not prazo_str:
        return ""

    try:
        prazo = date.fromisoformat(prazo_str)
    except:
        return ""

    uid = f"chamado-{chamado.get('id', 'x')}@gerenciachamados"
    titulo = f"[Chamado {chamado.get('numero_chamado', '')}] {chamado.get('titulo', 'Chamado')}"
    descricao = f"Tipo: {chamado.get('tipo', '')} | Status: {chamado.get('status', '')}"
    data_fmt = prazo.strftime("%Y%m%d")
    agora = datetime.now().strftime("%Y%m%dT%H%M%SZ")

    # Alerta 5 dias antes
    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//GerenciaChamados//BR
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{agora}
DTSTART;VALUE=DATE:{data_fmt}
SUMMARY:{titulo}
DESCRIPTION:{descricao}
BEGIN:VALARM
TRIGGER:-P5D
ACTION:DISPLAY
DESCRIPTION:Prazo se aproximando!
END:VALARM
END:VEVENT
END:VCALENDAR"""
    return ics
