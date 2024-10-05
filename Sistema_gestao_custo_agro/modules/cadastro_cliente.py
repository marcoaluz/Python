from flask import Flask, render_template, request, redirect, flash
from supabase import create_client, Client
import csv
import os

app = Flask(__name__)

SUPABASE_URL = 'https://zsiayxkxryslphpnwmmt.supabase.co'
SUPABASE_API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpzaWF5eGt4cnlzbHBocG53bW10Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjY3MDAzNDIsImV4cCI6MjA0MjI3NjM0Mn0.h9rhuu5LrJ1X6qVFAsnQu3WhD8Lqs50txKzVzZnKp6s'
SUPABASE_USERS_TABLE = 'cadastro_cliente'
app.secret_key = 'supersecretkey'
SECRET_KEY = 'ziU5pXB8iB6StifZfBNgFON2VlXQUOEyrrzBNYilQGp0AUIQSRmK8tTLpR0Y7SLdempJ2xlbiGDZDWzrLIatLg=='
supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)



@app.route('/cadastro_cliente', methods=['GET', 'POST'])
def cadastro_cliente():
    if request.method == 'POST':
        nome = request.form['nome']
        apelido = request.form['apelido']
        endereco = request.form['endereco']
        cpf_cnpj = request.form['cpf_cnpj']
        telefone = request.form['telefone']
        email = request.form['email']
        tipo_cliente = request.form['tipo_cliente']
        
        # Verificar se o CPF/CNPJ já está cadastrado
        response = supabase.table('cadastro_cliente').select('*').eq('cpf_cnpj', cpf_cnpj).execute()
        if response.data:
            flash("CPF/CNPJ já cadastrado!", "danger")
            return redirect('/cadastro_cliente')

        # Inserir novo cliente
        supabase.table('cadastro_cliente').insert({
            'nome_razaosocial': nome,
            'apelido_nomefantasia': apelido,
            'endereco': endereco,
            'cpf_cnpj': cpf_cnpj,
            'telefone': telefone,
            'email': email,
            'tipo_cliente': tipo_cliente
        }).execute()

        flash("Cliente cadastrado com sucesso!", "success")
        return redirect('/cadastro_cliente')

    return render_template('cadastro_cliente.html')

# Função para importar clientes via CSV
@app.route('/importar_csv', methods=['POST'])
def importar_csv():
    if 'file' not in request.files:
        flash('Nenhum arquivo enviado', 'danger')
        return redirect('/cadastro_cliente')

    file = request.files['file']
    if file.filename == '':
        flash('Nenhum arquivo selecionado', 'danger')
        return redirect('/cadastro_cliente')

    csv_file = csv.reader(file)
    for row in csv_file:
        cpf_cnpj = row[3]  # Coluna do CPF/CNPJ no CSV

        # Verificar se já existe o CPF/CNPJ
        response = supabase.table('cadastro_cliente').select('*').eq('cpf_cnpj', cpf_cnpj).execute()
        if response.data:
            flash(f"CPF/CNPJ {cpf_cnpj} já cadastrado. Importação ignorada.", "danger")
        else:
            supabase.table('cadastro_cliente').insert({
                'nome_razaosocial': row[0],
                'apelido_nomefantasia': row[1],
                'endereco': row[2],
                'cpf_cnpj': row[3],
                'telefone': row[4],
                'email': row[5],
                'tipo_cliente': row[6]
            }).execute()

    flash('Clientes importados com sucesso!', 'success')
    return redirect('/cadastro_cliente')

if __name__ == '__main__':
    app.run(debug=True)