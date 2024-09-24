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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
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
        # Exemplo estático; substitua pela lógica real
        email = "user@example.com"  # Deveria obter do token
        existing_user = supabase_request('GET', f'{SUPABASE_USERS_TABLE}?email=eq.{email}')
        
        if existing_user and not existing_user[0]['is_confirmed']:
            user_id = existing_user[0]['id']
            updated_data = {
                'is_confirmed': True,
                'data_criacao': 'now()'  # PostgreSQL SQL para definir o timestamp atual
            }
            supabase_request('PATCH', f'{SUPABASE_USERS_TABLE}?id=eq.{user_id}', updated_data)
            flash('E-mail confirmado com sucesso! Registro finalizado.', 'success')
        else:
            flash('Token inválido ou e-mail já confirmado.', 'danger')
    except requests.HTTPError as e:
        flash(f'Erro ao confirmar o e-mail: {e}', 'danger')

    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)