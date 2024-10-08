from flask import Flask
from flask_mail import Mail
from config import SECRET_KEY



app = Flask(__name__)

# Configurações de e-mail
e_mail_rec = 'marco.luz1994@gmail.com'
senha_rec = 'etsf azze ojuf rftb'  # Lembre-se de usar uma senha de aplicativo se tiver 2FA habilitado

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = e_mail_rec
app.config['MAIL_PASSWORD'] = senha_rec
app.config['MAIL_DEFAULT_SENDER'] = e_mail_rec

# Inicializar o Mail com a aplicação
mail = Mail(app)

# Configurações da aplicação
app.secret_key = SECRET_KEY

# Registrar os módulos (blueprints) no final
from modules.login import login_bp
from modules.cadastro_cliente import cadastro_bp
from modules.menu import menu_bp


app.register_blueprint(login_bp)
app.register_blueprint(cadastro_bp)
app.register_blueprint(menu_bp)


if __name__ == '__main__':
    app.run(debug=True)