from flask import Flask, render_template, request, redirect, url_for, flash, session, Blueprint, jsonify
from utils import login_required
from supabase import create_client
from datetime import datetime
from math import ceil

from config import SUPABASE_URL, SUPABASE_API_KEY

cadastro_bp = Blueprint('cadastro_cliente', __name__)

SUPABASE_USERS_TABLE = 'cadastro_cliente'
supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)



@cadastro_bp.route('/cadastro_cliente', methods=['GET', 'POST'])
@login_required
def cadastro_cliente():
    if 'logged_in' not in session:
        return redirect(url_for('login.login'))
    

    # Número de itens por página
    items_per_page = 10
    # Página atual (padrão: 1)
    current_page = int(request.args.get('page', 1))

    # Obter o termo de pesquisa, se houver
    search_query = request.args.get('query', '').strip()

    # Fatiando os dados para a paginação
    start_index = (current_page - 1) * items_per_page
    end_index = start_index + items_per_page

    # Caso haja pesquisa
    if search_query:
        clientes = supabase.table('cadastro_cliente').select('*').like('cpf_cnpj', f"%{search_query}%").range(start_index, end_index).execute()
    else:
        # Se não houver pesquisa, carrega todos os clientes
        clientes = supabase.table('cadastro_cliente').select('*').range(start_index, end_index).execute()

    # Calcular total de clientes
    total_clients = supabase.table('cadastro_cliente').select('*').like('cpf_cnpj', f"%{search_query}%").execute()
    total_clients_count = len(total_clients.data) if total_clients.data else 0
    total_pages = ceil(total_clients_count / items_per_page)

    return render_template(
        'cadastro_cliente.html',
        clientes=clientes.data if clientes.data else [],
        current_page=current_page,
        total_pages=total_pages,
        search_query=search_query
    )
    
    

@cadastro_bp.route('/lista_clientes', methods=['GET'])
def lista_clientes():
    # Obter número da página e limite por página
    page = int(request.args.get('page', 1))  # Página padrão: 1
    per_page = 10  # Quantidade de  registros por página
    start_index = (page - 1) * per_page
    end_index = start_index + per_page - 1

    # Obter termo de busca, se houver
    query = request.args.get('query', '').strip()
    # Busca no banco de dados com paginação
    if query:
         response = supabase.table('cadastro_cliente').select('*').like('cpf_cnpj', f"%{query}%").range(start_index, end_index).execute()
#        response = supabase.table('cadastro_cliente').select('*').like('cpf_cnpj', f"%{query}%").range(start_index, end_index).execute()
         #total_clientes_response = supabase.table('cadastro_cliente').select('cpf_cnpj').like('cpf_cnpj', f"%{query}%").execute()    

    else:

     response = supabase.table('cadastro_cliente').select('*').range(start_index, end_index).execute()


    #   response = supabase.table('cadastro_cliente').select('*').range(start_index, end_index).execute()
     #  total_clientes_response = supabase.table('cadastro_cliente').select('cpf_cnpj').execute()
    # Total de registros para calcular o número de páginas
    
    total_clientes_response = supabase.table('cadastro_cliente').select('cpf_cnpj', count='exact').execute()
    total_clientes = len(total_clientes_response.data) if total_clientes_response.data else 0
    total_pages = ceil(total_clientes / per_page)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  # Se for requisição AJAX
        return jsonify({
            'clientes': response.data if response.data else [],
            'current_page': page,
            'total_pages': total_pages
        })
    
    return render_template(
        'cadastro_cliente.html',
        clientes=response.data if response.data else [],
        current_page=page,
        total_pages=total_pages,
        query=query
    )
    

   # return render_template(
    #   'cadastro_cliente.html',
     #  clientes=response.data if response.data else [],
      # current_page=page,
       #total_pages=total_pages,
       #query=query
    #)


@cadastro_bp.route('/buscar_clientes', methods=['GET'])
def buscar_clientes():
    termo = request.args.get('query', '').strip()

    if not termo:
        return jsonify([])  # Retorna uma lista vazia se não houver termo

    # Busca no banco de dados por CPF/CNPJ ou nome que contenham o termo
    response = supabase.table('cadastro_cliente').select('*').ilike('cpf_cnpj', f"%{termo}%").execute()
    response_nome = supabase.table('cadastro_cliente').select('*').ilike('nome_razaosocial', f"%{termo}%").execute()

    # Combina os resultados de ambas as consultas, evitando duplicados
    clientes = {cliente['cpf_cnpj']: cliente for cliente in (response.data + response_nome.data)}.values()

    return jsonify(list(clientes))





@cadastro_bp.route('/alterar_cliente', methods=['POST'])
def alterar_cliente():
    dados_cliente = request.form.to_dict()

    for key in dados_cliente:
        if isinstance(dados_cliente[key], str):
            dados_cliente[key] = dados_cliente[key].upper()
    # Atualizar a data de alteração
    dados_cliente['data_alteracao'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # print(dados_cliente)  # Adicionado para debug
    response = supabase.table('cadastro_cliente').update(dados_cliente).eq('cpf_cnpj', dados_cliente['cpf_cnpj']).execute()
   # print(response)  # Adicionado para verificar a resposta

   
    flash('Cadastro alterado com sucesso!', 'success')
    return redirect(url_for('cadastro_cliente.lista_clientes'))


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

@cadastro_bp.route('/salvar_cliente', methods=['POST'])
def salvar_cliente():
    # Obtenção de dados do formulário
    nome_razaosocial = request.form.get('nome_razaosocial')
    apelido_nomefantasia = request.form.get('apelido_nomefantasia')
    endereco = request.form.get('endereco')
    cpf_cnpj = request.form.get('cpf_cnpj')
    telefone = request.form.get('telefone')
    email = request.form.get('email')
    tipo_cliente = request.form.get('tipo_cliente')
    administrador_alteracao = request.form.get('administrador_alteracao')

    # Verifica se todos os campos obrigatórios foram preenchidos
    if not all([nome_razaosocial, cpf_cnpj, telefone, email, tipo_cliente]):
        flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
        return redirect(url_for('cadastro_cliente.cadastro_cliente'))

    # Verificar se o CPF/CNPJ já está cadastrado
    response = supabase.table(SUPABASE_USERS_TABLE).select('*').eq('cpf_cnpj', cpf_cnpj).execute()
    if response.data:
        flash(f"CPF/CNPJ {cpf_cnpj} já cadastrado. Operação cancelada.", 'danger')
        return redirect(url_for('cadastro_cliente.cadastro_cliente'))

    # Inserir os dados no Supabase
    try:
        supabase.table(SUPABASE_USERS_TABLE).insert({
            'nome_razaosocial': nome_razaosocial,
            'apelido_nomefantasia': apelido_nomefantasia,
            'endereco': endereco,
            'cpf_cnpj': cpf_cnpj,
            'telefone': telefone,
            'email': email,
            'tipo_cliente': tipo_cliente,
            'data_alteracao': None,  # Inicialmente como None
            'administrador_alteracao': administrador_alteracao,
            'status_cliente': 'Ativo',  # Status inicial como 'Ativo'
            'data_desativacao': None  # Nenhuma data de desativação no início
        }).execute()
        flash('Cliente salvo com sucesso!', 'success')
    except Exception as e:
        flash(f'Ocorreu um erro ao salvar o cliente: {str(e)}', 'danger')

    # Redireciona de volta para a tela de cadastro
    return redirect(url_for('cadastro_cliente.cadastro_cliente'))


if __name__ == '__main__':
    app = Flask(__name__)
    app.register_blueprint(cadastro_bp)
    app.run(debug=True)