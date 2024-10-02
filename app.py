from flask import Flask, render_template, request, redirect, url_for, flash, session,current_app
from datetime import datetime, timedelta
from supabase import create_client
import requests
import json
import bcrypt  # Para hashear as senhas
import uuid
import jwt 
import smtplib
from flask_mail import Mail, Message
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


app = Flask(__name__)

# Configuração do Supabase
SUPABASE_URL = 'https://zsiayxkxryslphpnwmmt.supabase.co'
SUPABASE_API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpzaWF5eGt4cnlzbHBocG53bW10Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjY3MDAzNDIsImV4cCI6MjA0MjI3NjM0Mn0.h9rhuu5LrJ1X6qVFAsnQu3WhD8Lqs50txKzVzZnKp6s'
SUPABASE_USERS_TABLE = 'usuarios'
supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)
app.secret_key = 'supersecretkey'
SECRET_KEY = 'ziU5pXB8iB6StifZfBNgFON2VlXQUOEyrrzBNYilQGp0AUIQSRmK8tTLpR0Y7SLdempJ2xlbiGDZDWzrLIatLg=='


def create_token(email):
    token = jwt.encode({
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=1)  # O token expira em 1 hora
    }, SECRET_KEY, algorithm='HS256')
    return token


# Função para realizar chamadas à API Supabase
def supabase_request(method, endpoint, data=None):
    url = f'{SUPABASE_URL}/rest/v1/{endpoint}'
    params = {'apikey': SUPABASE_API_KEY}  # Include API key as query parameter
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    print(f"Paramentros Params: {params}")
    print(f"Request URL: {url}")
    print(f"Request Headers: {headers}")

    response = requests.request(method, url, headers=headers, params=params, data=json.dumps(data))

    # Check response status code
    if response.status_code == 200:
        print(response.json())  # Exibe o JSON de retorno
        return response.json()  # Retorna o JSON para ser utilizado
    else:
        print(f"Error: {response.status_code} - {response.text}")  # Imprime a mensagem de erro
        return None  # Retorna None em caso de erro
    
# Redireciona a rota raiz para a tela de login
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']
        
        # Buscar o usuário pelo nome de usuário
        try:
            user = supabase_request('GET', f'{SUPABASE_USERS_TABLE}?email=eq.{username}')
            print(f"verificar retorno user: {user}" )
            if user and len(user) > 0:
                if not user[0].get('is_confirmed', False):  # Verifica se 'is_confirmed' é False
                    flash('Você deve confirmar seu e-mail para finalizar o registro.', 'warning')
                    return redirect(url_for('login'))
                # Verificar a senha com o hash armazenado
                stored_password = user[0]['senha']
                if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                       flash('Login realizado com sucesso!', 'success')
                       return render_template('index.html')  # Renderiza diretamente com o flash
                else:
                       flash('Senha incorreta!', 'danger')                                      
            else:
                flash('Usuário não encontrado!', 'danger')      
        except requests.HTTPError as e:
            flash(f'Erro ao buscar o usuário: {e}', 'danger')
            
        return redirect(url_for('login'))
    
    return render_template('login.html')


e_mail_rec = 'marco.luz1994@gmail.com'
senha_rec = 'etsf azze ojuf rftb'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = e_mail_rec
app.config['MAIL_PASSWORD'] = senha_rec  # Se 2FA, coloque a senha do aplicativo
app.config['MAIL_DEFAULT_SENDER'] = e_mail_rec

mail = Mail(app)

def send_email(to_email, subject, body):
    msg = Message(subject, recipients=[to_email])
    msg.body = body
    mail.send(msg)


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email'].lower()

        # Verifica se o e-mail está cadastrado
        user = supabase_request('GET', f'{SUPABASE_USERS_TABLE}?email=eq.{email}')
        
        if user and len(user) > 0:
            # Gerar token de redefinição de senha (pode ser um UUID, por exemplo)
            reset_token = str(uuid.uuid4())
            session['reset_token'] = reset_token
            session['email'] = email

            # Enviar o e-mail de redefinição de senha
            reset_link = url_for('reset_password', token=reset_token, _external=True)
            send_email(email, 'Redefinir senha', f'Clique no link para redefinir sua senha: {reset_link}')
            
            flash('E-mail de recuperação enviado!', 'info')
        else:
            flash('E-mail não cadastrado!', 'danger')

        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

# Rota para redefinir a senha (com o token)
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if token != session.get('reset_token'):
        flash('Token inválido ou expirado!', 'danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('As senhas não coincidem!', 'danger')
            return redirect(url_for('reset_password', token=token))

        # Hash da nova senha
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        senha = hashed_password.decode('utf-8')
        # Atualiza a senha no banco de dados
        email = session.get('email')
        #print(f"Email utilizado para a atualização: {email}")#

        # Verificar se o usuário existe
        user_check = supabase.table(SUPABASE_USERS_TABLE).select('*').eq('email', email).execute()
        #print(f"Resultado da verificação do usuário: {user_check.data}")#

        if not user_check.data:
            flash('Usuário não encontrado!', 'danger')
            return redirect(url_for('reset_password', token=token))
        try:
            
            response = supabase.table(SUPABASE_USERS_TABLE).update({'senha': senha}).eq('email', email).execute()
            #print(f"Verificar resp: {response}")  # Exibe a resposta completa
            # Verifica se a atualização foi bem-sucedida
            if response.data:
                flash('Senha redefinida com sucesso!', 'success')
                return redirect(url_for('login'))
            else:
                flash('Erro ao redefinir a senha: Nenhuma linha foi atualizada.', 'danger')
                return redirect(url_for('reset_password', token=token))
        except Exception as e:
            flash(f'Erro ao redefinir a senha: {e}', 'danger')
        return redirect(url_for('reset_password', token=token))


    return render_template('reset_password.html', token=token)

# Rota para registrar um usuário
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].lower()
        email = request.form['email'].lower()
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('As senhas não correspondem. Tente novamente.', 'danger')
            return redirect(url_for('register'))

        # Verificar se o usuário já existe no banco de dados
        try:
            existing_user = supabase_request('GET', f'{SUPABASE_USERS_TABLE}?email=eq.{email}')
            if existing_user:
                flash('E-mail já registrado. Use outro e-mail.', 'danger')
                return redirect(url_for('register'))
        except requests.HTTPError as e:
            flash(f'Erro ao verificar o e-mail: {e}', 'danger')
            return redirect(url_for('register'))

        # Verificar se o nome de usuário já existe
        try:
            existing_user_by_name = supabase_request('GET', f'{SUPABASE_USERS_TABLE}?nome_usuario=eq.{name}')
            if existing_user_by_name:
                flash('Nome de usuário já registrado. Use outro nome.', 'danger')
                return redirect(url_for('register'))
        except requests.HTTPError as e:
            flash(f'Erro ao verificar o nome de usuário: {e}', 'danger')
            return redirect(url_for('register'))

        # Hashear a senha antes de salvar
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Criar um novo usuário
        new_user = {
            'nome_usuario': name,
            'email': email,
            'phone': phone,
            'senha': hashed_password,  # Armazenar o hash da senha
            'data_criacao': datetime.now().isoformat()
        }
        try:
            supabase_request('POST', SUPABASE_USERS_TABLE, new_user)

            # Gerar o token de confirmação
            confirmation_token = create_token(email)

            # Enviar o e-mail de confirmação
            confirmation_link = url_for('confirm_email', token=confirmation_token, _external=True)
            send_email(email, 'Confirmação de E-mail', f'Clique no link para confirmar seu e-mail: {confirmation_link}')

            flash('Registro realizado com sucesso! Verifique seu e-mail para confirmar.', 'success')
            return redirect(url_for('login'))
        except requests.HTTPError as e:
            flash(f'Erro ao criar o usuário: {e}', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')
# Rota para confirmar o e-mail
@app.route('/confirm_email/<token>')
def confirm_email(token):
    try:
        # Decodificando o token para obter o e-mail
        email = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])['email']
        
        # Verificando se o e-mail existe na tabela de usuários
        existing_user_response = supabase.table(SUPABASE_USERS_TABLE).select('*').eq('email', email).execute()

        print("Resposta da consulta:", existing_user_response.data)  # Mensagem de depuração
        
        if existing_user_response.data:
            user = existing_user_response.data[0]
            if 'is_confirmed' not in user:
                print("A coluna 'is_confirmed' não existe no usuário:", user)
                flash('Erro: A coluna is_confirmed não existe.', 'danger')
                return redirect(url_for('login'))

            if not user['is_confirmed']:
                user_id = user['id']
                updated_data = {
                    'is_confirmed': True,
                    'data_criacao': datetime.now().isoformat()  # Atualiza a data de confirmação
                }

                # Atualizando o registro do usuário
                update_response = supabase.table(SUPABASE_USERS_TABLE).update(updated_data).eq('id', user_id).execute()

                # Verificando se a atualização foi bem-sucedida
                if update_response.data:
                    flash('E-mail confirmado com sucesso! Registro finalizado.', 'success')
                else:
                    flash('Erro ao confirmar o e-mail: não foi possível atualizar o registro.', 'danger')
            else:
                flash('O e-mail já foi confirmado anteriormente.', 'info')
        else:
            flash('Token inválido ou e-mail não encontrado.', 'danger')
    except Exception as e:
        flash(f'Erro ao confirmar o e-mail: {e}', 'danger')

    return redirect(url_for('login'))


def send_email(to, subject, body):
    """Envia um e-mail usando SMTP."""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = e_mail_rec
    msg['To'] = to

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(e_mail_rec, senha_rec)
        server.send_message(msg)

if __name__ == '__main__':
   app.run(debug=True)