import requests
import json

# Configuração do Supabase
SUPABASE_URL = 'https://zsiayxkxryslphpnwmmt.supabase.co'
SUPABASE_API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpzaWF5eGt4cnlzbHBocG53bW10Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjY3MDAzNDIsImV4cCI6MjA0MjI3NjM0Mn0.h9rhuu5LrJ1X6qVFAsnQu3WhD8Lqs50txKzVzZnKp6s'  # Replace with your public key
SUPABASE_USERS_TABLE = 'usuarios'


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

# Testando a requisição com o e-mail
email = "marco@email.com"
try:
    supabase_request('GET', f'{SUPABASE_USERS_TABLE}?email=eq.{email}')
except Exception as e:
    print(f"Erro ao verificar o e-mail: {e}")