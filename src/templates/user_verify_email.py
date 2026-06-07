from src.config import config


def generate_user_verify_email_template(name: str, token: str) -> str:
    # If FRONTEND_URL is not defined, use the default verify URL
    verify_url = f"http://localhost:8000/api/auth/verify/{token}"
    if config.FRONTEND_URL:
        verify_url = f"{config.FRONTEND_URL}/confirma-cadastro?token={token}"
    html_message = f"""
        <h1>Bem-vindo ao Raízes do Nordeste, {name}!</h1>
        <p>Para ativar sua conta, clique no link abaixo:</p>
        <br>
        <a
            style="color: blue; font-weight: bold; font-size: 16px;"
            href="{verify_url}"
        >Ativar Conta</a>
        <br>
        <p>Se você não solicitou esta confirmação, ignore este email.</p>
    """
    return html_message
