from src.config import config


def generate_user_request_reset_password_template(token: str) -> str:

    # If FRONTEND_URL is not defined, use the token as plain text
    reset_link = f"<p>Para resetar sua senha utilize este token: <code style='color: gray'>{token}</code></p>"
    if config.FRONTEND_URL:
        reset_link = f"""
            <a href="{config.FRONTEND_URL}/nova-senha?token={token}">Redefinir Senha</a>
        """
    html_message = f"""
        <h1>Recuperação de Senha</h1>
        <p>Você solicitou a recuperação de senha. Clique no link abaixo para redefinir sua senha:</p>
        <br>
        {reset_link}
        <br>
        <p>Se você não solicitou a recuperação de senha, ignore este e-mail.</p>
    """
    return html_message
