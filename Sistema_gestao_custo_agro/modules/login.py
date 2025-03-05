from flask import Flask, render_template, request, redirect, url_for, flash, session,current_app,Blueprint
from datetime import datetime, timedelta
from supabase import create_client
from utils import login_required
from config import SUPABASE_URL, SUPABASE_API_KEY, SECRET_KEY,SUPABASE_USERS_TABLE  # Importa as configurações do Supabase
import requests
import json
import bcrypt  # Para hashear as senhas
import uuid
import jwt 
import smtplib
import socket
from flask_mail import Mail, Message
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart



login_bp = Blueprint('login', __name__)

# Configuração do Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)

#print(SUPABASE_URL, SUPABASE_API_KEY, SECRET_KEY, SUPABASE_USERS_TABLE)  # Teste se as variáveis estão sendo importadas corretamente


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

    #print(f"Paramentros Params: {params}")
    #print(f"Request URL: {url}")
    #print(f"Request Headers: {headers}")

    response = requests.request(method, url, headers=headers, params=params, data=json.dumps(data))

    # Check response status code
    if response.status_code == 200:
     #   print(response.json())  # Exibe o JSON de retorno
        return response.json()  # Retorna o JSON para ser utilizado
    else:
      #  print(f"Error: {response.status_code} - {response.text}")  # Imprime a mensagem de erro
        return None
    


def send_email(to, subject, body):
    """Envia um e-mail usando SMTP."""
    
    # Cria a mensagem
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = current_app.config['MAIL_USERNAME']  # Acessa o e-mail do remetente
    msg['To'] = to

    # Envia o e-mail usando SMTP
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])  # Acessa a senha do e-mail
        server.send_message(msg)

# Redireciona a rota raiz para a tela de login
@login_bp.route('/')

def index():
    #return redirect(url_for('login'))
    return redirect(url_for('login.login'))

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']
        
        # Buscar o usuário pelo nome de usuário
        try:
            user = supabase_request('GET', f'{SUPABASE_USERS_TABLE}?email=eq.{username}')
       #     print(f"verificar retorno user: {user}" )
            if user and len(user) > 0:
                if not user[0].get('is_confirmed', False):  # Verifica se 'is_confirmed' é False
                    flash('Você deve confirmar seu e-mail para finalizar o registro.', 'warning')
                    #return redirect(url_for('login'))
                    return redirect(url_for('login.login'))
                # Verificar a senha com o hash armazenado
                stored_password = user[0]['senha']
                if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                       session['logged_in'] = True 
                       #session['logged_in'] = True
                       session['user_id'] = user[0]['id']
                       #flash('Login realizado com sucesso!', 'success')
                       return redirect(url_for('menu.menu'))  # Renderiza diretamente com o flash
                else:
                       flash('Senha incorreta!', 'danger')                                      
            else:
                flash('Usuário não encontrado!', 'danger')   
        # Tratamento específico para timeout
        except socket.timeout as e:
                 flash('Erro de timeout: O servidor demorou muito para responder. Tente novamente mais tarde.', 'danger')
    
    # Tratamento para outros erros de conexão
        except requests.exceptions.RequestException as e:
                 flash(f'Erro de conexão: {e}', 'danger')              
        except requests.HTTPError as e:
            flash(f'Erro ao buscar o usuário: {e}', 'danger')
        
        return redirect(url_for('login.login'))  
        #return redirect(url_for('login'))
    
    return render_template('login.html')



def send_email(to_email, subject, body):
    msg = Message(subject, recipients=[to_email])
    msg.body = body
    mail = current_app.extensions['mail']  # Acessa a instância do Mail configurada no app
    mail.send(msg)

@login_bp.route('/forgot_password', methods=['GET', 'POST'])
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
            reset_link = url_for('login.reset_password', token=reset_token, _external=True)
            
            try:
                # Usa a função send_email definida acima
                send_email(email, 'Redefinir senha', f'Clique no link para redefinir sua senha: {reset_link}')
                flash('E-mail de recuperação enviado!', 'info')
            except (smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError, 
                    smtplib.SMTPResponseException, socket.timeout, 
                    ConnectionRefusedError, TimeoutError) as e:
                flash('Não foi possível estabelecer conexão com o servidor de e-mail. Por favor, tente novamente mais tarde.', 'danger')
            except Exception as e:
                flash(f'Erro ao enviar e-mail: {e}', 'danger')
        else:
            flash('E-mail não cadastrado!', 'danger')
        
        return redirect(url_for('login.login'))  # Redireciona para a página de login
    
    return render_template('forgot_password.html')
    #return current_app.send_static_file('forgot_password.html')

# Rota para redefinir a senha (com o token)
@login_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if token != session.get('reset_token'):
        flash('Token inválido ou expirado!', 'danger')
        return redirect(url_for('login.forgot_password'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('As senhas não coincidem!', 'danger')
            return redirect(url_for('login.reset_password', token=token))

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
            return redirect(url_for('login.reset_password', token=token))
        try:
            
            response = supabase.table(SUPABASE_USERS_TABLE).update({'senha': senha}).eq('email', email).execute()
            #print(f"Verificar resp: {response}")  # Exibe a resposta completa
            # Verifica se a atualização foi bem-sucedida
            if response.data:
                flash('Senha redefinida com sucesso!', 'success')
                return redirect(url_for('login.login'))
            else:
                flash('Erro ao redefinir a senha: Nenhuma linha foi atualizada.', 'danger')
                return redirect(url_for('login.reset_password', token=token))
        # Tratamento específico para timeout
        except socket.timeout as e:
            flash('Erro de timeout: O servidor demorou muito para responder. Tente novamente mais tarde.', 'danger')
    
    # Tratamento para outros erros de conexão
        except requests.exceptions.RequestException as e:
             flash(f'Erro de conexão: {e}', 'danger')    
        except Exception as e:
            flash(f'Erro ao redefinir a senha: {e}', 'danger') 
        return redirect(url_for('login.reset_password', token=token))


    return render_template('reset_password.html', token=token)

# Rota para registrar um usuário
@login_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].lower()
        email = request.form['email'].lower()
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('As senhas não correspondem. Tente novamente.', 'danger')
            #return redirect(url_for('register'))
            return redirect(url_for('login.register'))

        # Verificar se o usuário já existe no banco de dados
        try:
            existing_user = supabase_request('GET', f'{SUPABASE_USERS_TABLE}?email=eq.{email}')
            if existing_user:
                flash('E-mail já registrado. Use outro e-mail.', 'danger')
                #return redirect(url_for('register'))
                return redirect(url_for('login.register'))
        except requests.HTTPError as e:
            flash(f'Erro ao verificar o e-mail: {e}', 'danger')
            #return redirect(url_for('register'))
            return redirect(url_for('login.register'))

        # Verificar se o nome de usuário já existe
        try:
            existing_user_by_name = supabase_request('GET', f'{SUPABASE_USERS_TABLE}?nome_usuario=eq.{name}')
            if existing_user_by_name:
                flash('Nome de usuário já registrado. Use outro nome.', 'danger')
                #return redirect(url_for('register'))
                return redirect(url_for('login.register'))
        except requests.HTTPError as e:
            flash(f'Erro ao verificar o nome de usuário: {e}', 'danger')
            #return redirect(url_for('register'))
            return redirect(url_for('login.register'))
        # Tratamento específico para timeout
        except socket.timeout as e:
             flash('Erro de timeout: O servidor demorou muito para responder. Tente novamente mais tarde.', 'danger')
    
    # Tratamento para outros erros de conexão
        except requests.exceptions.RequestException as e:
            flash(f'Erro de conexão: {e}', 'danger')
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
            confirmation_link = url_for('login.confirm_email', token=confirmation_token, _external=True)
           # confirmation_link = url_for('confirm_email', token=confirmation_token, _external=True)
            send_email(email, 'Confirmação de E-mail', f'Clique no link para confirmar seu e-mail: {confirmation_link}')

            flash('Registro realizado com sucesso! Verifique seu e-mail para confirmar.', 'success')
            return redirect(url_for('login.login'))
        # Tratamento específico para timeout
        except socket.timeout as e:
            flash('Erro de timeout: O servidor demorou muito para responder. Tente novamente mais tarde.', 'danger')
    
    # Tratamento para outros erros de conexão
        except requests.exceptions.RequestException as e:
            flash(f'Erro de conexão: {e}', 'danger')
        except requests.HTTPError as e:
            flash(f'Erro ao criar o usuário: {e}', 'danger')
            #return redirect(url_for('register'))
            return redirect(url_for('login.register'))
    return render_template('register.html')
# Rota para confirmar o e-mail
@login_bp.route('/confirm_email/<token>')
def confirm_email(token):
    try:
        # Decodificando o token para obter o e-mail
        email = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])['email']
        
        # Verificando se o e-mail existe na tabela de usuários
        existing_user_response = supabase.table(SUPABASE_USERS_TABLE).select('*').eq('email', email).execute()

        #print("Resposta da consulta:", existing_user_response.data)  # Mensagem de depuração
        
        if existing_user_response.data:
            user = existing_user_response.data[0]
            if 'is_confirmed' not in user:
                print("A coluna 'is_confirmed' não existe no usuário:", user)
                flash('Erro: A coluna is_confirmed não existe.', 'danger')
                return redirect(url_for('login.login'))

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
    return redirect(url_for('login.login'))


@login_bp.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    session.clear()
    flash('Você foi desconectado!', 'success')

    print(f"User logged in: {session.get('logged_in')}")    

    return redirect(url_for('login.login'))



if __name__ == '__main__':
   login_bp.run(debug=True)