from flask import Flask, render_template, request, redirect, url_for, flash, session, Blueprint, jsonify
from utils import login_required
from supabase import create_client
from datetime import datetime
from math import ceil
import httpx
from httpx import Limits, Client

from config import SUPABASE_URL, SUPABASE_API_KEY

cadastro_propriedade_bp = Blueprint('cadastro_propriedade', __name__)

SUPABASE_PROPERTIES_TABLE = 'cadastro_propriedade'
SUPABASE_CLIENTS_TABLE = 'cadastro_cliente'

supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)

@cadastro_propriedade_bp.route('/cadastro_propriedade', methods=['GET'])
@login_required
def index():
    """Rota principal que lista as propriedades"""
    if 'logged_in' not in session:
        return redirect(url_for('login.login'))

    items_per_page = 10
    current_page = int(request.args.get('page', 1))
    search_query = request.args.get('query', '').strip()
    start_index = (current_page - 1) * items_per_page
    end_index = start_index + items_per_page

    try:
        if search_query:
            propriedades = supabase.table(SUPABASE_PROPERTIES_TABLE)\
                .select('*')\
                .or_(f'nome_propriedade.ilike.%{search_query}%, cpf_cnpj_cliente.ilike.%{search_query}%')\
                .order('id_propriedade', desc=True)\
                .range(start_index, end_index)\
                .execute()
            
            total_count = len(supabase.table(SUPABASE_PROPERTIES_TABLE)\
                .select('id_propriedade')\
                .or_(f'nome_propriedade.ilike.%{search_query}%, cpf_cnpj_cliente.ilike.%{search_query}%')\
                .execute().data)
        else:
            propriedades = supabase.table(SUPABASE_PROPERTIES_TABLE)\
                .select('*')\
                .order('id_propriedade', desc=True)\
                .range(start_index, end_index)\
                .execute()
            
            total_count = len(supabase.table(SUPABASE_PROPERTIES_TABLE)\
                .select('id_propriedade')\
                .execute().data)

        total_pages = ceil(total_count / items_per_page)

        return render_template(
            'cadastro_propriedade.html',
            propriedades=propriedades.data if propriedades.data else [],
            current_page=current_page,
            total_pages=total_pages,
            search_query=search_query
        )

    except Exception as e:
        flash(f'Erro ao carregar propriedades: {str(e)}', 'danger')
        # Mesmo em caso de erro, retornamos os valores padrão para evitar erros no template
        return render_template(
            'cadastro_propriedade.html', 
            propriedades=[],
            current_page=1,
            total_pages=0,
            search_query=''
        )

@cadastro_propriedade_bp.route('/cadastro_propriedade/buscar_cliente/<cpf_cnpj>', methods=['GET'])
@login_required
def buscar_clientes():
    """Rota para buscar clientes por CPF/CNPJ ou nome (busca parcial)"""
    try:
        termo = request.args.get('query', '').strip()
        
        if not termo or len(termo) < 3:
            return jsonify([])

        # Faz a busca por CPF/CNPJ ou por nome
        response = supabase.table(SUPABASE_CLIENTS_TABLE).select('*').or_(
            f"cpf_cnpj.ilike.%{termo}%,"
            f"nome_razaosocial.ilike.%{termo}%"
        ).execute()

        # Retorna os resultados encontrados
        return jsonify(response.data if response.data else [])
        
    except Exception as e:
        print(f"Erro ao buscar clientes: {str(e)}")
        return jsonify({'error': str(e)}), 500

@cadastro_propriedade_bp.route('/cadastro_propriedade/propriedade/<int:id_propriedade>', methods=['GET'])
@login_required
def obter_safras(id_propriedade):
    """Rota para obter as safras de uma propriedade"""
    try:
        # Verifique se a tabela cadastro_safra existe no seu banco
        # Se existir, busque as safras relacionadas à propriedade
        try:
            safras = supabase.table('cadastro_safra')\
                .select('*')\
                .eq('id_propriedade', id_propriedade)\
                .execute()
            
            return jsonify({
                'success': True,
                'safras': safras.data if safras.data else []
            })
        except Exception as e:
            # Se der erro (tabela não existe), vamos buscar os dados de safra da própria tabela de propriedades
            propriedade = supabase.table(SUPABASE_PROPERTIES_TABLE)\
                .select('id_propriedade, qtd_produzida_total, qtd_produzida_t, tamanho_colido, nome_talhao, ano_safra')\
                .eq('id_propriedade', id_propriedade)\
                .execute()
            
            if not propriedade.data:
                return jsonify({
                    'success': False,
                    'message': 'Propriedade não encontrada'
                }), 404
            
            # Se os dados de safra existirem na propriedade, retorne como uma safra
            prop = propriedade.data[0]
            if prop.get('nome_talhao') or prop.get('ano_safra'):
                # Formatar como uma lista de safras para manter compatibilidade com a interface
                safras = [{
                    'id_safra': prop['id_propriedade'],  # Usar o mesmo ID da propriedade como ID da safra
                    'id_propriedade': prop['id_propriedade'],
                    'qtd_produzida_total': prop.get('qtd_produzida_total', 0),
                    'qtd_produzida_t': prop.get('qtd_produzida_t', 0),
                    'tamanho_colido': prop.get('tamanho_colido', 0),
                    'nome_talhao': prop.get('nome_talhao', ''),
                    'ano_safra': prop.get('ano_safra', '')
                }]
            else:
                safras = []
                
            return jsonify({
                'success': True,
                'safras': safras
            })
            
    except Exception as e:
        print(f"Erro ao obter safras: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



# Modifique a função salvar_safra para usar a tabela separada:
@cadastro_propriedade_bp.route('/cadastro_propriedade/salvar_safra', methods=['POST'])
@login_required
def salvar_safra():
    """Rota para salvar dados de safra para uma propriedade"""
    try:
        # Obtém os dados JSON enviados
        data = request.json
        
        if not data or 'id_propriedade' not in data:
            return jsonify({'error': 'Dados inválidos'}), 400
            
        id_propriedade = data.get('id_propriedade')
        
        # Busca a propriedade para verificar se existe
        propriedade = supabase.table(SUPABASE_PROPERTIES_TABLE)\
            .select('*')\
            .eq('id_propriedade', id_propriedade)\
            .execute()
            
        if not propriedade.data:
            return jsonify({'error': 'Propriedade não encontrada'}), 404
            
        # Prepara dados para inserção na tabela de safras
        safra_data = {
            'id_propriedade': id_propriedade,
            'qtd_produzida_total': float(data.get('qtd_produzida_total', 0)),
            'qtd_produzida_t': float(data.get('qtd_produzida_t', 0)),
            'tamanho_colido': float(data.get('tamanho_colido', 0)),
            'nome_talhao': data.get('nome_talhao', '').upper(),
            'ano_safra': data.get('ano_safra', ''),
            'data_cadastro': datetime.now().isoformat()
        }
        
        # Insere na tabela de safras
        supabase.table('cadastro_safra').insert(safra_data).execute()
            
        return jsonify({
            'success': True, 
            'message': 'Safra cadastrada com sucesso!'
        })
        
    except Exception as e:
        print(f"Erro ao salvar safra: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Modifique a função salvar_propriedade para retornar o ID da propriedade criada
@cadastro_propriedade_bp.route('/cadastro_propriedade/salvar', methods=['POST'])
@login_required
def salvar_propriedade():
    """Rota para salvar uma nova propriedade"""
    try:
        data = {
            'cpf_cnpj_cliente': request.form.get('cpf_cnpj_cliente'),
            'nome_razaosocial': request.form.get('nome_razaosocial'),
            'nome_propriedade': request.form.get('nome_propriedade').upper(),
            'tamanho_propriedade': float(request.form.get('tamanho_propriedade')),
            'respons_propriedade': request.form.get('respons_propriedade').upper(),
            'tipo_cultura': int(request.form.get('tipo_cultura')),
            'local_long': request.form.get('local_long'),
            'local_lat': request.form.get('local_lat'),
            'status': 'Ativo',
            'data_cadastro': datetime.now().isoformat(),
            'usuario_cadastro': session.get('user_id')
        }

        result = supabase.table(SUPABASE_PROPERTIES_TABLE).insert(data).execute()
        
        # Obtém o ID da propriedade inserida
        id_propriedade = result.data[0]['id_propriedade'] if result.data else None
        
        return jsonify({
            'success': True, 
            'message': 'Propriedade cadastrada com sucesso!',
            'id_propriedade': id_propriedade
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@cadastro_propriedade_bp.route('/cadastro_propriedade/safras/<int:id_propriedade>', methods=['GET'])
@login_required
def listar_safras_propriedade(id_propriedade):  # Nome modificado para evitar duplicidade
    """Rota para obter as safras de uma propriedade"""
    try:
        # Buscar safras relacionadas à propriedade na tabela cadastro_safra
        safras = supabase.table('cadastro_safra')\
            .select('*')\
            .eq('id_propriedade', id_propriedade)\
            .execute()
        
        return jsonify({
            'success': True,
            'safras': safras.data if safras.data else []
        })
            
    except Exception as e:
        print(f"Erro ao obter safras: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 
    

@cadastro_propriedade_bp.route('/cadastro_propriedade/atualizar/<int:id_propriedade>', methods=['PUT'])
@login_required
def atualizar_propriedade(id_propriedade):
    """Rota para atualizar uma propriedade existente"""
    try:
        data = request.get_json()
        
        update_data = {
            'nome_propriedade': data.get('nome_propriedade').upper(),
            'tamanho_propriedade': float(data.get('tamanho_propriedade')),
            'respons_propriedade': data.get('respons_propriedade').upper(),
            'tipo_cultura': int(data.get('tipo_cultura')),
            'local_long': data.get('local_long'),
            'local_lat': data.get('local_lat'),
            'qtd_produzida_total': float(data.get('qtd_produzida_total', 0)),
            'qtd_produzida_t': float(data.get('qtd_produzida_t', 0)),
            'tamanho_colido': float(data.get('tamanho_colido', 0)),
            'nome_talhao': data.get('nome_talhao', '').upper(),
            'ano_safra': data.get('ano_safra', ''),
            'data_alteracao': datetime.now().isoformat(),
            'usuario_alteracao': session.get('user_id')
        }

        supabase.table(SUPABASE_PROPERTIES_TABLE)\
            .update(update_data)\
            .eq('id_propriedade', id_propriedade)\
            .execute()

        return jsonify({'success': True, 'message': 'Propriedade atualizada com sucesso!'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cadastro_propriedade_bp.route('/cadastro_propriedade/desativar/<int:id_propriedade>', methods=['POST'])
@login_required
def desativar_propriedade(id_propriedade):
    """Rota para desativar uma propriedade"""
    try:
        supabase.table(SUPABASE_PROPERTIES_TABLE)\
            .update({
                'status': 'Inativo',
                'data_desativacao': datetime.now().isoformat(),
                'usuario_desativacao': session.get('user_id')
            })\
            .eq('id_propriedade', id_propriedade)\
            .execute()

        return jsonify({'success': True, 'message': 'Propriedade desativada com sucesso!'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app = Flask(__name__)
    app.register_blueprint(cadastro_propriedade_bp)
    app.run(debug=True)