from flask import Flask, render_template, request, redirect, url_for, flash, session, Blueprint
from utils import login_required

from supabase import create_client
from config import SUPABASE_URL, SUPABASE_API_KEY

cadastro_bp = Blueprint('cadastro_cliente', __name__)

SUPABASE_USERS_TABLE = 'cadastro_cliente'
supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)


@cadastro_bp.route('/cadastro_cliente', methods=['GET', 'POST'])
@login_required
def cadastro_cliente():
    if 'logged_in' not in session:
        return redirect(url_for('login.login'))
    
    clientes = supabase.table('cadastro_cliente').select('*').execute()

    if request.method == 'POST' and 'consultar' in request.form:
        search_query = request.form.get('cpf_cnpj', '').strip()
        if search_query:
            response = supabase.table('cadastro_cliente').select('*').eq('cpf_cnpj', search_query).execute()
            if response.data:
                cliente_pesquisado = response.data[0]
            else:
                flash("CPF/CNPJ não cadastrado ou informado incorretamente.", "danger")
        else:
            flash("Por favor, informe um CPF/CNPJ para consultar.", "danger")

    return render_template('cadastro_cliente.html', clientes=clientes.data if clientes.data else [])


@cadastro_bp.route('/lista_clientes', methods=['GET'])
def lista_clientes():
    query = request.args.get('query', '')
    if query:
        clientes = supabase.table('cadastro_cliente').select('*').like('cpf_cnpj', f"%{query}%").execute()
    else:
        clientes = supabase.table('cadastro_cliente').select('*').execute()

    return render_template('cadastro_cliente.html', clientes=clientes.data if clientes.data else [])




@cadastro_bp.route('/alterar_cliente/<string:cpf_cnpj>', methods=['GET', 'POST'])
def alterar_cliente(cpf_cnpj):
    cliente = supabase.table('cadastro_cliente').select('*').eq('cpf_cnpj', cpf_cnpj).execute()
    if request.method == 'POST':
        # Dados que podem ser alterados
        nome = request.form['nome']
        apelido = request.form['apelido']
        endereco = request.form['endereco']
        telefone = request.form['telefone']
        email = request.form['email']
        tipo_cliente = request.form['tipo_cliente']
        administrador_alteracao = request.form['administrador_alteracao']
        status_cliente = request.form['status_cliente']

        # Atualizar cliente
        supabase.table('cadastro_cliente').update({
            'nome_razaosocial': nome,
            'apelido_nomefantasia': apelido,
            'endereco': endereco,
            'telefone': telefone,
            'email': email,
            'tipo_cliente': tipo_cliente,
            'administrador_alteracao': administrador_alteracao,
            'status_cliente': status_cliente
        }).eq('cpf_cnpj', cpf_cnpj).execute()

        flash("Cliente alterado com sucesso!", "success")
        return redirect(url_for('cadastro_cliente.cadastro_cliente'))

    if cliente.data:
        return render_template('cadastro_cliente.html', cliente_pesquisado=cliente.data[0])
    else:
        flash("Cliente não encontrado!", "danger")
        return redirect(url_for('cadastro_cliente.cadastro_cliente'))


@cadastro_bp.route('/deletar_cliente/<string:cpf_cnpj>', methods=['POST'])
def deletar_cliente(cpf_cnpj):
    supabase.table('cadastro_cliente').delete().eq('cpf_cnpj', cpf_cnpj).execute()
    flash("Cliente deletado com sucesso!", "success")
    return redirect(url_for('cadastro_cliente.cadastro_cliente'))



# Função para importar clientes via CSV
@cadastro_bp.route('/importar_csv', methods=['POST'])
def importar_csv():
    if 'file' not in request.files:
        flash('Nenhum arquivo enviado', 'danger')
        return redirect(url_for('cadastro_cliente.cadastro_cliente'))

    file = request.files['file']
    if file.filename == '':
        flash('Nenhum arquivo selecionado', 'danger')
        return redirect(url_for('cadastro_cliente.cadastro_cliente'))

    csv_file = csv.reader(file)
    for row in csv_file:
        cpf_cnpj = row[3]  # Coluna do CPF/CNPJ no CSV

        # Verificar se já existe o CPF/CNPJ
        response = supabase.table(SUPABASE_USERS_TABLE).select('*').eq('cpf_cnpj', cpf_cnpj).execute()
        if response.data:
            flash(f"CPF/CNPJ {cpf_cnpj} já cadastrado. Importação ignorada.", "danger")
        else:
            # Inserindo os campos adicionais
            supabase.table(SUPABASE_USERS_TABLE).insert({
                'nome_razaosocial': row[0],
                'apelido_nomefantasia': row[1],
                'endereco': row[2],
                'cpf_cnpj': row[3],
                'telefone': row[4],
                'email': row[5],
                'tipo_cliente': row[6],
                'data_alteracao': None,  # Inicia como None
                'administrador_alteracao': None,  # Pode ser None
                'status_cliente': 'Ativo',  # Definindo como 'Ativo'
                'data_desativacao': None  # Pode ser None
            }).execute()

    flash('Clientes importados com sucesso!', 'success')
    return redirect(url_for('cadastro_cliente.cadastro_cliente'))

if __name__ == '__main__':
    app = Flask(__name__)
    app.register_blueprint(cadastro_bp)
    app.run(debug=True)