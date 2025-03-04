from flask import Flask, render_template, request, redirect, url_for, flash, session, Blueprint, jsonify
from utils import login_required
from supabase import create_client
from datetime import datetime
from math import ceil
import traceback

from config import SUPABASE_URL, SUPABASE_API_KEY

cadastro_estoque_bp = Blueprint('cadastro_estoque', __name__)

SUPABASE_ESTOQUE_TABLE = 'estoque'
SUPABASE_PRODUTOS_TABLE = 'produtos'
SUPABASE_PROPERTIES_TABLE = 'cadastro_propriedade'

supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)

@cadastro_estoque_bp.route('/cadastro_estoque', methods=['GET'])
@login_required
def index():
    """Rota principal que lista os estoques"""
    if 'logged_in' not in session:
        return redirect(url_for('login.login'))

    items_per_page = 10
    current_page = int(request.args.get('page', 1))
    search_query = request.args.get('query', '').strip()
    start_index = (current_page - 1) * items_per_page
    end_index = start_index + items_per_page - 1

    try:
        # Busca estoques com filtro de busca se fornecido
        if search_query:
            query = supabase.table(SUPABASE_ESTOQUE_TABLE)\
                .select('*')\
                .or_(f'nome_propriedade_e.ilike.%{search_query}%, cnpj_cpf_propr_e.ilike.%{search_query}%, nome_razaosocial_e.ilike.%{search_query}%')\
                .order('nome_propriedade_e', desc=False)
            
            # Obter total para paginação
            total_count_query = supabase.table(SUPABASE_ESTOQUE_TABLE)\
                .select('Id_estoque')\
                .or_(f'nome_propriedade_e.ilike.%{search_query}%, cnpj_cpf_propr_e.ilike.%{search_query}%, nome_razaosocial_e.ilike.%{search_query}%')
        else:
            query = supabase.table(SUPABASE_ESTOQUE_TABLE)\
                .select('*')\
                .order('nome_propriedade_e', desc=False)
            
            # Obter total para paginação
            total_count_query = supabase.table(SUPABASE_ESTOQUE_TABLE)\
                 .select('id_estoque') 

        # Executar consulta paginada
        estoques = query.range(start_index, end_index).execute()
        print(f"DEBUG - Consulta paginada: {len(estoques.data)} estoques encontrados")
        
        # Executar consulta para contagem total
        total_count_result = total_count_query.execute()
        total_count = len(total_count_result.data)
        
        # Calcular total de páginas
        total_pages = ceil(total_count / items_per_page)
        
        print(f"DEBUG - Total de estoques: {total_count}, Total de páginas: {total_pages}")

        return render_template(
            'cadastro_estoque.html',
            estoques=estoques.data if estoques.data else [],
            current_page=current_page,
            total_pages=total_pages,
            search_query=search_query
        )

    except Exception as e:
        # Captura e exibe o erro detalhado
        tb = traceback.format_exc()
        print(f'Erro completo: {tb}')
        flash(f'Erro ao carregar estoques: {str(e)}', 'danger')
        return render_template(
            'cadastro_estoque.html', 
            estoques=[],
            current_page=1,
            total_pages=0,
            search_query=''
        )

@cadastro_estoque_bp.route('/buscar_propriedades', methods=['GET'])
@login_required
def buscar_propriedades():
    """Rota para buscar todas as propriedades cadastradas"""
    try:
        # Faz a busca por todas as propriedades ativas
        response = supabase.table(SUPABASE_PROPERTIES_TABLE).select('*').eq('status', 'Ativo').execute()

        # Retorna os resultados encontrados
        return jsonify(response.data if response.data else [])
        
    except Exception as e:
        print(f"Erro ao buscar propriedades: {str(e)}")
        return jsonify({'error': str(e)}), 500

@cadastro_estoque_bp.route('/cadastro_estoque/estoque/<int:id_estoque>', methods=['GET'])
@login_required
def obter_estoque(id_estoque):
    """Rota para obter os dados de um estoque"""
    try:
        estoque = supabase.table(SUPABASE_ESTOQUE_TABLE)\
            .select('*')\
            .eq('id_estoque', id_estoque)\
            .execute()
        
        if not estoque.data:
            return jsonify({
                'success': False,
                'message': 'Estoque não encontrado'
            }), 404
            
        return jsonify({
            'success': True,
            'estoque': estoque.data[0]
        })
        
    except Exception as e:
        print(f"Erro ao obter estoque: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@cadastro_estoque_bp.route('/cadastro_estoque/produtos/<int:id_estoque>', methods=['GET'])
@login_required
def listar_produtos_estoque(id_estoque):
    """Rota para listar todos os produtos de um estoque"""
    try:
        produtos = supabase.table(SUPABASE_PRODUTOS_TABLE)\
            .select('*')\
            .eq('id_estoque', id_estoque)\
            .execute()
        
        return jsonify({
            'success': True,
            'produtos': produtos.data
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Erro completo ao listar produtos: {tb}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@cadastro_estoque_bp.route('/cadastro_estoque/produto/<int:id_produto>', methods=['GET'])
@login_required
def obter_produto(id_produto):
    """Rota para obter os dados de um produto específico pelo ID"""
    try:
        # Debug log to see what ID we're receiving
        print(f"DEBUG - Tentando obter produto com ID: {id_produto}")
        
        produto = supabase.table(SUPABASE_PRODUTOS_TABLE)\
            .select('*')\
            .eq('id_produto', id_produto)\
            .execute()
        
        if not produto.data or len(produto.data) == 0:
            print(f"DEBUG - Produto não encontrado com ID: {id_produto}")
            return jsonify({
                'success': False,
                'message': 'Produto não encontrado'
            }), 404
        
        print(f"DEBUG - Produto encontrado: {produto.data[0]}")
        
        return jsonify({
            'success': True,
            'produto': produto.data[0]
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Erro completo ao obter produto específico: {tb}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@cadastro_estoque_bp.route('/cadastro_estoque/salvar_produto', methods=['POST'])
@login_required
def salvar_produto():
    """Rota para salvar um novo produto no estoque"""
    try:
        # Obtém os dados JSON enviados
        data = request.json
        
        if not data or 'ID_estoque' not in data:
            return jsonify({'error': 'Dados inválidos'}), 400
            
        id_estoque = data.get('ID_estoque')
        
        # Busca o estoque para verificar se existe
        estoque = supabase.table(SUPABASE_ESTOQUE_TABLE)\
            .select('*')\
            .eq('id_estoque', id_estoque)\
            .execute()
            
        if not estoque.data:
            return jsonify({'error': 'Estoque não encontrado'}), 404
            
        # Prepara dados para inserção na tabela de produtos
        produto_data = {
            'id_estoque': id_estoque,
            'nome_produto': data.get('nome_produto', '').upper(),
            'fornecedor': data.get('fornecedor', '').upper(),
            'data_compra': data.get('data_compra'),
            'validade_produto': data.get('validade_produto'),
            'quantidade': float(data.get('quantidade', 0)),
            'unidade_medida': data.get('unidade_medida', ''),
            'valor_produto': float(data.get('valor_produto', 0)),
            'total_gasto': float(data.get('quantidade', 0)) * float(data.get('valor_produto', 0)),
            'quantidade_disponivel': float(data.get('quantidade_disponivel', 0)),
            'data_criacao': datetime.now().isoformat()
        }
        
        # Insere na tabela de produtos
        result = supabase.table(SUPABASE_PRODUTOS_TABLE).insert(produto_data).execute()
        
        # Log para debug
        print(f"DEBUG - Produto inserido: {result.data}")
            
        return jsonify({
            'success': True, 
            'message': 'Produto cadastrado com sucesso!'
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Erro ao salvar produto: {str(e)}")
        print(f"Traceback: {tb}")
        return jsonify({'error': str(e)}), 500

@cadastro_estoque_bp.route('/cadastro_estoque/atualizar_produto/<int:id_produto>', methods=['PUT'])
@login_required
def atualizar_produto(id_produto):
    """Rota para atualizar um produto existente"""
    try:
        data = request.get_json()
        
        # Verificar se o produto existe
        produto = supabase.table(SUPABASE_PRODUTOS_TABLE)\
            .select('*')\
            .eq('id_produto', id_produto)\
            .execute()
            
        if not produto.data or len(produto.data) == 0:
            return jsonify({
                'success': False,
                'message': 'Produto não encontrado'
            }), 404
        
        # Preparar dados para atualização
        update_data = {
            'nome_produto': data.get('nome_produto', '').upper(),
            'fornecedor': data.get('fornecedor', '').upper(),
            'data_compra': data.get('data_compra'),
            'validade_produto': data.get('validade_produto'),
            'quantidade': float(data.get('quantidade', 0)),
            'unidade_medida': data.get('unidade_medida', ''),
            'valor_produto': float(data.get('valor_produto', 0)),
            'total_gasto': float(data.get('quantidade', 0)) * float(data.get('valor_produto', 0)),
            'quantidade_disponivel': float(data.get('quantidade_disponivel', 0)),
            'data_atualizacao': datetime.now().isoformat()
        }
        
        # Logs para debug
        print(f"DEBUG - Atualizando produto {id_produto}")
        print(f"DEBUG - Dados de atualização: {update_data}")
        
        # Executar atualização
        result = supabase.table(SUPABASE_PRODUTOS_TABLE)\
            .update(update_data)\
            .eq('id_produto', id_produto)\
            .execute()
            
        print(f"DEBUG - Resultado da atualização: {result.data}")
        
        return jsonify({
            'success': True,
            'message': 'Produto atualizado com sucesso!'
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Erro completo ao atualizar produto: {tb}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@cadastro_estoque_bp.route('/cadastro_estoque/produto/<int:id_produto>', methods=['DELETE'])
@login_required
def excluir_produto(id_produto):
    """Rota para excluir um produto"""
    try:
        # Verificar se o produto existe
        produto = supabase.table(SUPABASE_PRODUTOS_TABLE)\
            .select('*')\
            .eq('id_produto', id_produto)\
            .execute()
            
        if not produto.data or len(produto.data) == 0:
            return jsonify({
                'success': False,
                'message': 'Produto não encontrado'
            }), 404
        
        # Excluir o produto
        result = supabase.table(SUPABASE_PRODUTOS_TABLE)\
            .delete()\
            .eq('id_produto', id_produto)\
            .execute()
            
        print(f"DEBUG - Produto {id_produto} excluído: {result.data}")
        
        return jsonify({
            'success': True,
            'message': 'Produto excluído com sucesso!'
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Erro completo ao excluir produto: {tb}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500    

@cadastro_estoque_bp.route('/cadastro_estoque/salvar_estoque', methods=['POST'])
@login_required
def salvar_estoque():
    """Rota para salvar um novo estoque"""
    try:
        # Obter ID da propriedade
        id_propriedade_e = request.form.get('id_propriedade_e')
        
        # Buscar dados da propriedade para completar informações
        propriedade = supabase.table(SUPABASE_PROPERTIES_TABLE)\
            .select('*')\
            .eq('id_propriedade', id_propriedade_e)\
            .execute()
            
        if not propriedade.data:
            return jsonify({'error': 'Propriedade não encontrada'}), 404
            
        prop_data = propriedade.data[0]
            
        # Preparar dados para inserção no estoque
        estoque_data = {
            'Id_propriedade_e': int(id_propriedade_e),
            'nome_propriedade_e': prop_data['nome_propriedade'],
            'cnpj_cpf_propr_e': prop_data['cpf_cnpj_cliente'],
            'nome_razaosocial_e': prop_data['nome_razaosocial'],
            'data_criacao': datetime.now().isoformat()
            
        }

        # Log para debug
        print(f"DEBUG - Dados para inserção: {estoque_data}")
            
        result = supabase.table(SUPABASE_ESTOQUE_TABLE).insert(estoque_data).execute()
        
        # Obtém o ID do estoque inserido
        id_estoque = result.data[0]['id_estoque'] if result.data else None

        
        return jsonify({
        'success': True, 
        'message': 'Estoque cadastrado com sucesso!',
        'id_estoque': result.data[0]['id_estoque'],  # Make sure this is consistent with your database
        'Id_propriedade_e': int(id_propriedade_e),
        'nome_propriedade_e': prop_data['nome_propriedade'],
        'cnpj_cpf_propr_e': prop_data['cpf_cnpj_cliente'],
        'nome_razaosocial_e': prop_data['nome_razaosocial']
    })

    except Exception as e:
        tb = traceback.format_exc()
        print(f"Erro ao salvar estoque: {str(e)}")
        print(f"Traceback: {tb}")
        return jsonify({'error': str(e)}), 500

@cadastro_estoque_bp.route('/cadastro_estoque/excluir/<int:id_estoque>', methods=['DELETE'])
@login_required
def excluir_estoque(id_estoque):
    """Rota para excluir permanentemente um estoque e seus produtos relacionados"""
    try:
        # Verificar se existem produtos relacionados
        try:
            produtos = supabase.table(SUPABASE_PRODUTOS_TABLE)\
                .select('id_produto')\
                .eq('id_estoque', id_estoque)\
                .execute()
                
            # Se existirem produtos, excluir primeiro
            if produtos.data and len(produtos.data) > 0:
                for produto in produtos.data:
                    supabase.table(SUPABASE_PRODUTOS_TABLE)\
                        .delete()\
                        .eq('id_produto', produto['id_produto'])\
                        .execute()
                print(f"DEBUG - {len(produtos.data)} produtos excluídos do estoque {id_estoque}")
        except Exception as e:
            print(f"Aviso: Erro ao verificar produtos: {str(e)}")
        
        # Excluir o estoque
        result = supabase.table(SUPABASE_ESTOQUE_TABLE)\
            .delete()\
            .eq('id_estoque', id_estoque)\
            .execute()
            
        print(f"DEBUG - Estoque {id_estoque} excluído: {result.data}")

        return jsonify({'success': True, 'message': 'Estoque excluído com sucesso!'})

    except Exception as e:
        tb = traceback.format_exc()
        print(f"Erro completo ao excluir estoque: {tb}")
        return jsonify({'error': str(e)}), 500

# Função para registrar o blueprint no aplicativo principal
def init_app(app):
    app.register_blueprint(cadastro_estoque_bp)

if __name__ == '__main__':
    app = Flask(__name__)
    app.register_blueprint(cadastro_estoque_bp)
    app.run(debug=True) 