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
from httpx import Limits, Client, TimeoutException
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from config import SUPABASE_URL, SUPABASE_API_KEY

# Blueprint Configuration
cadastro_produto_bp = Blueprint('cadastro_produto', __name__)
SUPABASE_PRODUCTS_TABLE = 'produtos'
supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)

# HTTP Client Configuration with increased timeout
timeout = httpx.Timeout(30.0, connect=10.0)
limits = Limits(max_connections=20, max_keepalive_connections=10)
client = httpx.Client(timeout=timeout, limits=limits)

# Route Handlers
@cadastro_produto_bp.route('/cadastro_produto', methods=['GET', 'POST'])
@login_required
def cadastro_produto():
    if 'logged_in' not in session:
        return redirect(url_for('login.login'))

    items_per_page = 10
    current_page = int(request.args.get('page', 1))
    search_query = request.args.get('query', '').strip()
    
    start_index = (current_page - 1) * items_per_page
    end_index = start_index + items_per_page

    if search_query:
        produtos = supabase.table('produtos').select('*').ilike('nome_produto', f"%{search_query}%").range(start_index, end_index).execute()
    else:
        produtos = supabase.table('produtos').select('*').range(start_index, end_index).execute()

    total_products = supabase.table('produtos').select('*').execute()
    total_products_count = len(total_products.data) if total_products.data else 0
    total_pages = ceil(total_products_count / items_per_page)

    return render_template(
        'cadastro_produto.html',
        produtos=produtos.data if produtos.data else [],
        current_page=current_page,
        total_pages=total_pages,
        search_query=search_query
    )

@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
async def fetch_products(supabase, query=None, page=1, per_page=10):
    try:
        start_index = (page - 1) * per_page
        end_index = start_index + per_page - 1

        if query:
            response = supabase.table('produtos').select('*').ilike('nome_produto', f"%{query}%").range(start_index, end_index).execute()
        else:
            response = supabase.table('produtos').select('*').range(start_index, end_index).execute()

        total_produtos_response = supabase.table('produtos').select('id', count='exact').execute()
        total_produtos = len(total_produtos_response.data) if total_produtos_response.data else 0
        total_pages = ceil(total_produtos / per_page)

        return {
            'produtos': response.data if response.data else [],
            'current_page': page,
            'total_pages': total_pages
        }
    except Exception as e:
        print(f"Error fetching products: {e}")
        return {
            'produtos': [],
            'current_page': page,
            'total_pages': 0
        }

@cadastro_produto_bp.route('/lista_produtos', methods=['GET'])
async def lista_produtos():
    page = int(request.args.get('page', 1))
    query = request.args.get('query', '').strip()

    # Use asyncio to handle the fetch
    result = await fetch_products(supabase, query, page)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(result)
    
    return render_template(
        'cadastro_produto.html',
        produtos=result['produtos'],
        current_page=result['current_page'],
        total_pages=result['total_pages'],
        query=query
    )

@cadastro_produto_bp.route('/buscar_produtos', methods=['GET'])
def buscar_produtos():
    try:
        termo = request.args.get('query', '').strip()
        if not termo:
            return jsonify([])
        
        # Busca por nome do produto ou fornecedor
        response = supabase.table('produtos').select('*').or_(
            f"nome_produto.ilike.%{termo}%,"
            f"fornecedor.ilike.%{termo}%"
        ).execute()

        return jsonify(response.data if response.data else [])

    except Exception as e:
        print(f"Error in buscar_produtos: {str(e)}")
        return jsonify({
            'error': 'Erro ao processar a busca. Por favor, tente novamente.'
        }), 500

@cadastro_produto_bp.route('/alterar_produto', methods=['POST'])
def alterar_produto():
    dados_produto = request.form.to_dict()
    
    for key in dados_produto:
        if isinstance(dados_produto[key], str) and key not in ['data_compra', 'validade_produto']:
            dados_produto[key] = dados_produto[key].upper()
    
    # Convertendo valores numéricos
    for campo in ['quantidade', 'valor_produto', 'quantidade_disponivel']:
        if campo in dados_produto:
            dados_produto[campo] = float(dados_produto[campo])
    
    # Calculando total_gasto
    dados_produto['total_gasto'] = float(dados_produto['quantidade']) * float(dados_produto['valor_produto'])
    
    # Adicionando data de atualização
    dados_produto['data_atualizacao'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    response = supabase.table('produtos').update(dados_produto).eq('id', int(dados_produto['id'])).execute()
    flash('Produto alterado com sucesso!', 'success')
    return redirect(url_for('cadastro_produto.lista_produtos'))

@cadastro_produto_bp.route('/deletar_produto/<int:produto_id>', methods=['POST'])
def deletar_produto(produto_id):
    supabase.table('produtos').delete().eq('id', produto_id).execute()
    flash("Produto excluído com sucesso!", "success")
    return redirect(url_for('cadastro_produto.cadastro_produto'))

@cadastro_produto_bp.route('/salvar_produto', methods=['POST'])
def salvar_produto():
    try:
        dados_produto = {
            'nome_produto': request.form.get('nome_produto', '').upper(),
            'fornecedor': request.form.get('fornecedor', '').upper(),
            'data_compra': request.form.get('data_compra'),
            'validade_produto': request.form.get('validade_produto') or None,
            'quantidade': float(request.form.get('quantidade', 0)),
            'unidade_medida': request.form.get('unidade_medida', '').upper(),
            'valor_produto': float(request.form.get('valor_produto', 0)),
            'quantidade_disponivel': float(request.form.get('quantidade', 0))  # Inicialmente igual à quantidade total
        }
        
        # Calculando o total gasto
        dados_produto['total_gasto'] = dados_produto['quantidade'] * dados_produto['valor_produto']
        
        if not all([
            dados_produto['nome_produto'], 
            dados_produto['fornecedor'], 
            dados_produto['data_compra'],
            dados_produto['quantidade'],
            dados_produto['unidade_medida'],
            dados_produto['valor_produto']
        ]):
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            return redirect(url_for('cadastro_produto.cadastro_produto'))
        
        supabase.table(SUPABASE_PRODUCTS_TABLE).insert(dados_produto).execute()
        flash('Produto salvo com sucesso!', 'success')
        
    except Exception as e:
        flash(f'Ocorreu um erro ao salvar o produto: {str(e)}', 'danger')
    
    return redirect(url_for('cadastro_produto.cadastro_produto'))

if __name__ == '__main__':
    app = Flask(__name__)
    app.register_blueprint(cadastro_produto_bp)
    app.run(debug=True)