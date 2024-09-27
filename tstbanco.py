import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask_mail import Mail, Message

from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
from supabase import create_client
import requests
import json
import bcrypt  # Para hashear as senhas

app = Flask(__name__)

# Configuração do Supabase
SUPABASE_URL = 'https://zsiayxkxryslphpnwmmt.supabase.co'
SUPABASE_API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpzaWF5eGt4cnlzbHBocG53bW10Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjY3MDAzNDIsImV4cCI6MjA0MjI3NjM0Mn0.h9rhuu5LrJ1X6qVFAsnQu3WhD8Lqs50txKzVzZnKp6s'
SUPABASE_USERS_TABLE = 'usuarios'
supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)
app.secret_key = 'supersecretkey'

# Função para realizar chamadas à API Supabase
def supabase_request(method, endpoint, data=None):
    url = f'{SUPABASE_URL}/rest/v1/{endpoint}'
    params = {'apikey': SUPABASE_API_KEY}  # Include API key as query parameter
    headers = {
        'Accept': 'application/json'
    }

    print(f"Request URL: {url}")
    print(f"Request Headers: {headers}")

    response = requests.request(method, url, headers=headers, params=params, data=json.dumps(data) if data else None)

    # Check response status code
    if response.status_code == 200:
        print(response.json())  # Assuming you want the JSON data
    else:
        print(f"Error: {response.status_code} - {response.text}")  # Print error message



app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'seuemail@gmail.com'
app.config['MAIL_PASSWORD'] = 'suasenha'
app.config['MAIL_DEFAULT_SENDER'] = 'seuemail@gmail.com'

mail = Mail(app)

def send_email(to_email, subject, body):
    msg = Message(subject, recipients=[to_email])
    msg.body = body
    mail.send(msg)




def send_email(to_email, subject, body):
    # Configurações do servidor de e-mail (Gmail, por exemplo)
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    from_email = 'seuemail@gmail.com'  # Seu e-mail
    from_password = 'suasenha'         # Sua senha de e-mail

    # Configurando o conteúdo do e-mail
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Corpo do e-mail
    msg.attach(MIMEText(body, 'plain'))

    # Enviando o e-mail
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Segurança (TLS)
        server.login(from_email, from_password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        print("E-mail enviado com sucesso!")
    except Exception as e:
        print(f"Falha ao enviar o e-mail: {e}")

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

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
