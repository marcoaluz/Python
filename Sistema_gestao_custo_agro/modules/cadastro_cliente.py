from flask import (
    Flask, 
    render_template, 
    request, 
    redirect, 
    url_for, 
    flash, 
    session, 
    Blueprint, 
    jsonify
)
from utils import login_required
from supabase import create_client
from datetime import datetime
from math import ceil
import httpx
import asyncio
from httpx import Limits, Client, TimeoutException
import re
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from config import SUPABASE_URL, SUPABASE_API_KEY

# Blueprint Configuration
cadastro_bp = Blueprint('cadastro_cliente', __name__)
SUPABASE_USERS_TABLE = 'cadastro_cliente'
supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)

# HTTP Client Configuration with increased timeout
timeout = httpx.Timeout(30.0, connect=10.0)  # Aumentado para 30 segundos
limits = Limits(max_connections=20, max_keepalive_connections=10)
client = httpx.Client(timeout=timeout, limits=limits)

# Route Handlers
@cadastro_bp.route('/cadastro_cliente', methods=['GET', 'POST'])
@login_required
def cadastro_cliente():
    if 'logged_in' not in session:
        return redirect(url_for('login.login'))

    items_per_page = 10
    current_page = int(request.args.get('page', 1))
    search_query = request.args.get('query', '').strip()
    
    start_index = (current_page - 1) * items_per_page
    end_index = start_index + items_per_page

    if search_query:
        clientes = supabase.table('cadastro_cliente').select('*').like('cpf_cnpj', f"%{search_query}%").range(start_index, end_index).execute()
    else:
        clientes = supabase.table('cadastro_cliente').select('*').range(start_index, end_index).execute()

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
@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
async def fetch_clients(supabase, query=None, page=1, per_page=10):
    try:
        start_index = (page - 1) * per_page
        end_index = start_index + per_page - 1

        if query:
            response = supabase.table('cadastro_cliente').select('*').ilike('cpf_cnpj', f"%{query}%").range(start_index, end_index).execute()
        else:
            response = supabase.table('cadastro_cliente').select('*').range(start_index, end_index).execute()

        total_clientes_response = supabase.table('cadastro_cliente').select('cpf_cnpj', count='exact').execute()
        total_clientes = len(total_clientes_response.data) if total_clientes_response.data else 0
        total_pages = ceil(total_clientes / per_page)

        return {
            'clientes': response.data if response.data else [],
            'current_page': page,
            'total_pages': total_pages
        }
    except Exception as e:
        print(f"Error fetching clients: {e}")
        return {
            'clientes': [],
            'current_page': page,
            'total_pages': 0
        }

@cadastro_bp.route('/lista_clientes', methods=['GET'])
async def lista_clientes():
    page = int(request.args.get('page', 1))
    query = request.args.get('query', '').strip()

    # Use asyncio to handle the fetch
    result = await fetch_clients(supabase, query, page)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(result)
    
    return render_template(
        'cadastro_cliente.html',
        clientes=result['clientes'],
        current_page=result['current_page'],
        total_pages=result['total_pages'],
        query=query
    )

def normalizar_termo(termo):
    """Normaliza o termo de busca removendo formatação e caracteres especiais"""
    # Para documentos, remove tudo que não for número
    if any(c.isdigit() for c in termo):
        return re.sub(r'[^0-9]', '', termo)
    # Para nomes, remove caracteres especiais mas mantém espaços
    return re.sub(r'[^a-zA-Z0-9\s]', '', termo).upper().strip()

def formatar_cpf_cnpj(numero):
    """Formata um número como CPF ou CNPJ"""
    numero = re.sub(r'[^0-9]', '', numero)
    if len(numero) == 11:
        return f"{numero[:3]}.{numero[3:6]}.{numero[6:9]}-{numero[9:]}"
    elif len(numero) == 14:
        return f"{numero[:2]}.{numero[2:5]}.{numero[5:8]}/{numero[8:12]}-{numero[12:]}"
    return numero

@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
    retry=retry_if_exception_type((TimeoutException, ConnectionError))
)



@cadastro_bp.route('/buscar_clientes', methods=['GET'])
def buscar_clientes():
    try:
        termo = request.args.get('query', '').strip()
        if not termo:
            return jsonify([])

        # Normaliza o termo de busca
        termo_normalizado = normalizar_termo(termo)

        # is_documento = len(termo_normalizado) in [11, 14]
        
        # Busca por CPF/CNPJ normalizado e formatado
        response_doc = supabase.table('cadastro_cliente').select('*').or_(
            f"cpf_cnpj.ilike.%{termo_normalizado}%,cpf_cnpj.ilike.%{formatar_cpf_cnpj(termo_normalizado)}%"
        ).execute()

        # Busca por nome
        response_nome = supabase.table('cadastro_cliente').select('*').ilike(
            'nome_razaosocial', f"%{termo_normalizado}%"
        ).execute()

        # Combina e remove duplicatas
        clientes = {
            cliente['cpf_cnpj']: cliente 
            for cliente in (response_doc.data + response_nome.data)
        }.values()

        # Formata CPF/CNPJ nos resultados
        clientes_formatados = []
        for cliente in clientes:
            cliente_copy = dict(cliente)
            cliente_copy['cpf_cnpj'] = formatar_cpf_cnpj(cliente['cpf_cnpj'])
            clientes_formatados.append(cliente_copy)

        return jsonify(clientes_formatados)

    except TimeoutException as e:
        print(f"Timeout error: {str(e)}")
        return jsonify({
            'error': 'Tempo limite de conexão excedido. Por favor, tente novamente.'
        }), 504

    except Exception as e:
        print(f"Error in buscar_clientes: {str(e)}")
        return jsonify({
            'error': 'Erro ao processar a busca. Por favor, tente novamente.'
        }), 500

@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
async def fetch_clients(supabase, query=None, page=1, per_page=10):
    try:
        start_index = (page - 1) * per_page
        end_index = start_index + per_page - 1

        # Se houver query, busca com termo normalizado
        if query:
            termo_normalizado = normalizar_termo(query)
            response = supabase.table('cadastro_cliente').select('*').or_(
                f"cpf_cnpj.ilike.%{termo_normalizado}%,"
                f"nome_razaosocial.ilike.%{termo_normalizado}%"
            ).range(start_index, end_index).execute()
        else:
            response = supabase.table('cadastro_cliente').select('*').range(
                start_index, end_index
            ).execute()

        # Conta total de registros
        total_clientes_response = supabase.table('cadastro_cliente').select(
            'cpf_cnpj', count='exact'
        ).execute()
        
        total_clientes = len(total_clientes_response.data) if total_clientes_response.data else 0
        total_pages = ceil(total_clientes / per_page)

        # Formata CPF/CNPJ nos resultados
        clientes_formatados = []
        for cliente in (response.data or []):
            cliente_copy = dict(cliente)
            cliente_copy['cpf_cnpj'] = formatar_cpf_cnpj(cliente['cpf_cnpj'])
            clientes_formatados.append(cliente_copy)

        return {
            'clientes': clientes_formatados,
            'current_page': page,
            'total_pages': total_pages
        }

    except Exception as e:
        print(f"Error fetching clients: {e}")
        return {
            'clientes': [],
            'current_page': page,
            'total_pages': 0,
            'error': str(e)
        }

@cadastro_bp.route('/alterar_cliente', methods=['POST'])
def alterar_cliente():
    dados_cliente = request.form.to_dict()
    
    for key in dados_cliente:
        if isinstance(dados_cliente[key], str):
            dados_cliente[key] = dados_cliente[key].upper()
    
    dados_cliente['data_alteracao'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    response = supabase.table('cadastro_cliente').update(dados_cliente).eq('cpf_cnpj', dados_cliente['cpf_cnpj']).execute()
    flash('Cadastro alterado com sucesso!', 'success')
    return redirect(url_for('cadastro_cliente.lista_clientes'))

@cadastro_bp.route('/deletar_cliente/<string:cpf_cnpj>', methods=['POST'])
def deletar_cliente(cpf_cnpj):
    supabase.table('cadastro_cliente').delete().eq('cpf_cnpj', cpf_cnpj).execute()
    flash("Cliente excluído com sucesso!", "success")
    return redirect(url_for('cadastro_cliente.cadastro_cliente'))

@cadastro_bp.route('/salvar_cliente', methods=['POST'])
def salvar_cliente():
    nome_razaosocial = request.form.get('nome_razaosocial')
    apelido_nomefantasia = request.form.get('apelido_nomefantasia')
    endereco = request.form.get('endereco')
    cpf_cnpj = request.form.get('cpf_cnpj')
    telefone = request.form.get('telefone')
    email = request.form.get('email')
    tipo_cliente = request.form.get('tipo_cliente')
    administrador_alteracao = request.form.get('administrador_alteracao')

    if not all([nome_razaosocial, cpf_cnpj, telefone, email, tipo_cliente]):
        flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
        return redirect(url_for('cadastro_cliente.cadastro_cliente'))

    response = supabase.table(SUPABASE_USERS_TABLE).select('*').eq('cpf_cnpj', cpf_cnpj).execute()
    if response.data:
        flash(f"CPF/CNPJ {cpf_cnpj} já cadastrado. Operação cancelada.", 'danger')
        return redirect(url_for('cadastro_cliente.cadastro_cliente'))

    try:
        supabase.table(SUPABASE_USERS_TABLE).insert({
            'nome_razaosocial': nome_razaosocial,
            'apelido_nomefantasia': apelido_nomefantasia,
            'endereco': endereco,
            'cpf_cnpj': cpf_cnpj,
            'telefone': telefone,
            'email': email,
            'tipo_cliente': tipo_cliente,
            'data_alteracao': None,
            'administrador_alteracao': administrador_alteracao,
            'status_cliente': 'Ativo',
            'data_desativacao': None
        }).execute()
        flash('Cliente salvo com sucesso!', 'success')
    except Exception as e:
        flash(f'Ocorreu um erro ao salvar o cliente: {str(e)}', 'danger')

    return redirect(url_for('cadastro_cliente.cadastro_cliente'))

if __name__ == '__main__':
    app = Flask(__name__)
    app.register_blueprint(cadastro_bp)
    app.run(debug=True)