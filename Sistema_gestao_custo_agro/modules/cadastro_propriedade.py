from flask import Flask, render_template, request, redirect, url_for, flash, session, Blueprint, jsonify
from utils import login_required
from supabase import create_client
from datetime import datetime
from math import ceil
import httpx
import traceback
from httpx import Limits, Client

from config import SUPABASE_URL, SUPABASE_API_KEY

cadastro_propriedade_bp = Blueprint('cadastro_propriedade', __name__)

SUPABASE_PROPERTIES_TABLE = 'cadastro_propriedade'
SUPABASE_CLIENTS_TABLE = 'cadastro_cliente'
SUPABASE_TALHAO_TABLE = 'cadastro_safra'
SUPABASE_FUNCIONARIO_TABLE = 'funcionarios'

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
    end_index = start_index + items_per_page - 1  # Corrigido para considerar o início em 0

    try:
        # Teste de consulta simples para debugging
        teste = supabase.table(SUPABASE_PROPERTIES_TABLE).select('*').execute()
        print(f"DEBUG - Total de registros na tabela: {len(teste.data)}")
        
        # Busca propriedades (sem filtro de status para garantir que todas apareçam)
        if search_query:
            query = supabase.table(SUPABASE_PROPERTIES_TABLE)\
                .select('*')\
                .or_(f'nome_propriedade.ilike.%{search_query}%, cpf_cnpj_cliente.ilike.%{search_query}%, nome_razaosocial.ilike.%{search_query}%')\
                .order('nome_razaosocial', desc=False)
            
            # Obter total para paginação
            total_count_query = supabase.table(SUPABASE_PROPERTIES_TABLE)\
                .select('id_propriedade')\
                .or_(f'nome_propriedade.ilike.%{search_query}%, cpf_cnpj_cliente.ilike.%{search_query}%, nome_razaosocial.ilike.%{search_query}%')
        else:
            query = supabase.table(SUPABASE_PROPERTIES_TABLE)\
                .select('*')\
                .order('nome_razaosocial', desc=False)
            
            # Obter total para paginação
            total_count_query = supabase.table(SUPABASE_PROPERTIES_TABLE)\
                .select('id_propriedade')

        # Executar consulta paginada
        propriedades = query.range(start_index, end_index).execute()
        print(f"DEBUG - Consulta paginada: {len(propriedades.data)} propriedades encontradas")
        
        # Executar consulta para contagem total
        total_count_result = total_count_query.execute()
        total_count = len(total_count_result.data)
        
        # Calcular total de páginas
        total_pages = ceil(total_count / items_per_page)
        
        print(f"DEBUG - Total de propriedades: {total_count}, Total de páginas: {total_pages}")

        return render_template(
            'cadastro_propriedade.html',
            propriedades=propriedades.data if propriedades.data else [],
            current_page=current_page,
            total_pages=total_pages,
            search_query=search_query
        )

    except Exception as e:
        # Captura e exibe o erro detalhado
        tb = traceback.format_exc()
        print(f'Erro completo: {tb}')
        flash(f'Erro ao carregar propriedades: {str(e)}', 'danger')
        return render_template(
            'cadastro_propriedade.html', 
            propriedades=[],
            current_page=1,
            total_pages=0,
            search_query=''
        )

@cadastro_propriedade_bp.route('/buscar_clientes', methods=['GET'])
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
def obter_propriedade(id_propriedade):
    """Rota para obter os dados de uma propriedade"""
    try:
        propriedade = supabase.table(SUPABASE_PROPERTIES_TABLE)\
            .select('*')\
            .eq('id_propriedade', id_propriedade)\
            .execute()
        
        if not propriedade.data:
            return jsonify({
                'success': False,
                'message': 'Propriedade não encontrada'
            }), 404
            
        return jsonify({
            'success': True,
            'propriedade': propriedade.data[0]
        })
        
    except Exception as e:
        print(f"Erro ao obter propriedade: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@cadastro_propriedade_bp.route('/cadastro_propriedade/safra/<int:id_propriedade>', methods=['GET'])
@login_required
def listar_safras_propriedade(id_propriedade):
    """Rota para listar todas as safras de uma propriedade"""
    try:
        safras = supabase.table('cadastro_safra')\
            .select('*')\
            .eq('id_propriedade', id_propriedade)\
            .execute()
        
        return jsonify({
            'success': True,
            'safras': safras.data
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Erro completo ao listar safras: {tb}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
        
@cadastro_propriedade_bp.route('/cadastro_propriedade/safras/<int:id_propriedade>', methods=['GET'])
                                     
@login_required
def obter_safra(id_safra):
    """Rota para obter os dados de uma safra específica"""
    try:
        safra = supabase.table('cadastro_safra')\
            .select('*')\
            .eq('id_safra', id_safra)\
            .execute()
        
        if not safra.data or len(safra.data) == 0:
            return jsonify({
                'success': False,
                'message': 'Safra não encontrada'
            }), 404
            
        return jsonify({
            'success': True,
            'safra': safra.data[0]
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Erro completo ao obter safra: {tb}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
        
        
@cadastro_propriedade_bp.route('/cadastro_propriedade/safra/<int:id_safra>', methods=['GET'])
@login_required
def obter_safra_especifica(id_safra):
    """Rota para obter os dados de uma safra específica pelo ID"""
    try:
        safra = supabase.table('cadastro_safra')\
            .select('*')\
            .eq('id_safra', id_safra)\
            .execute()
        
        if not safra.data or len(safra.data) == 0:
            return jsonify({
                'success': False,
                'message': 'Safra não encontrada'
            }), 404
            
        return jsonify({
            'success': True,
            'safra': safra.data[0]
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Erro completo ao obter safra específica: {tb}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500  

@cadastro_propriedade_bp.route('/cadastro_propriedade/salvar_propriedade', methods=['POST'])
@login_required
def salvar_propriedade():
    """Rota para salvar uma nova propriedade"""
    try:
        # Obter e tratar dados do formulário
        local_long = request.form.get('local_long', '').strip()
        local_lat = request.form.get('local_lat', '').strip()
                         
        
        # Preparar dados para inserção, convertendo para None os campos vazios
        data = {
            'cpf_cnpj_cliente': request.form.get('cpf_cnpj_cliente'),
            'nome_razaosocial': request.form.get('nome_razaosocial'),
            'nome_propriedade': request.form.get('nome_propriedade').upper(),
            'tamanho_propriedade': float(request.form.get('tamanho_propriedade')),
            'respons_propriedade': request.form.get('respons_propriedade').upper(),
            'tipo_cultura': int(request.form.get('tipo_cultura')),
            'status': 'Ativo',
            'data_cadastro': datetime.now().isoformat(),
            'usuario_cadastro': session.get('user_id')
        }
        
        # Adicionar longitude e latitude apenas se não estiverem vazios
        if local_long:
            data['local_long'] = float(local_long)
        else:
            data['local_long'] = None
            
        if local_lat:
            data['local_lat'] = float(local_lat)
        else:
            data['local_lat'] = None

        # Log para debug
        print(f"DEBUG - Dados para inserção: {data}")
            
        result = supabase.table(SUPABASE_PROPERTIES_TABLE).insert(data).execute()
        
        # Obtém o ID da propriedade inserida
        id_propriedade = result.data[0]['id_propriedade'] if result.data else None
        
        return jsonify({
            'success': True, 
            'message': 'Propriedade cadastrada com sucesso!',
            'id_propriedade': id_propriedade,
            'prompt_talhao': True  # Flag para perguntar se deseja cadastrar talhão
        })

    except Exception as e:
        print(f"Erro ao salvar propriedade: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
@cadastro_propriedade_bp.route('/cadastro_propriedade/atualizar/<int:id_propriedade>', methods=['PUT'])
@login_required
def atualizar_propriedade(id_propriedade):
    """Rota para atualizar uma propriedade existente"""
    try:
        data = request.get_json()
        
        # Verificar se a propriedade existe
        propriedade = supabase.table(SUPABASE_PROPERTIES_TABLE)\
            .select('*')\
            .eq('id_propriedade', id_propriedade)\
            .execute()
            
        if not propriedade.data:
            return jsonify({'success': False, 'error': 'Propriedade não encontrada'}), 404
        
        # Obter e tratar dados de longitude e latitude
        local_long = data.get('local_long', '').strip() if data.get('local_long') else None
        local_lat = data.get('local_lat', '').strip() if data.get('local_lat') else None
        
        # Preparar dados para atualização
        update_data = {
            'nome_propriedade': data.get('nome_propriedade', '').upper(),
            'tamanho_propriedade': float(data.get('tamanho_propriedade', 0)),
            'respons_propriedade': data.get('respons_propriedade', '').upper(),
            'tipo_cultura': int(data.get('tipo_cultura', 1)),
            'data_alteracao': datetime.now().isoformat(),
            'usuario_alteracao': session.get('user_id')
        }
        
        # Adicionar longitude e latitude apenas se não estiverem vazios
        if local_long:
            update_data['local_long'] = float(local_long)
        else:
            update_data['local_long'] = None
            
        if local_lat:
            update_data['local_lat'] = float(local_lat)
        else:
            update_data['local_lat'] = None

        # Adicionar logs para debug
        print(f"DEBUG - Atualizando propriedade {id_propriedade}")
        print(f"DEBUG - Dados de atualização: {update_data}")

        # Executar atualização
        result = supabase.table(SUPABASE_PROPERTIES_TABLE)\
            .update(update_data)\
            .eq('id_propriedade', id_propriedade)\
            .execute()
            
        print(f"DEBUG - Resultado da atualização: {result.data}")

        return jsonify({'success': True, 'message': 'Propriedade atualizada com sucesso!'})

    except Exception as e:
        tb = traceback.format_exc()
        print(f"Erro completo ao atualizar propriedade: {tb}")
        return jsonify({'success': False, 'error': str(e)}), 500
                                                                
                        
                             

@cadastro_propriedade_bp.route('/cadastro_propriedade/excluir/<int:id_propriedade>', methods=['DELETE'])
@login_required
def excluir_propriedade(id_propriedade):
    """Rota para excluir permanentemente uma propriedade"""
    try:
        # Verificar se existem safras relacionadas
        try:
            safras = supabase.table('cadastro_safra')\
                .select('id_safra')\
                .eq('id_propriedade', id_propriedade)\
                .execute()
                
            # Se existirem safras, excluir primeiro
            if safras.data and len(safras.data) > 0:
                for safra in safras.data:
                    supabase.table('cadastro_safra')\
                        .delete()\
                        .eq('id_safra', safra['id_safra'])\
                        .execute()
                print(f"DEBUG - {len(safras.data)} safras excluídas da propriedade {id_propriedade}")
        except Exception as e:
            print(f"Aviso: Erro ao verificar safras (pode ser que a tabela não exista): {str(e)}")
            
        # Verificar se existem funcionários relacionados
        try:
            funcionarios = supabase.table(SUPABASE_FUNCIONARIO_TABLE)\
                .select('id')\
                .eq('id_propriedade', id_propriedade)\
                .execute()
                
            # Se existirem funcionários, excluir primeiro
            if funcionarios.data and len(funcionarios.data) > 0:
                for funcionario in funcionarios.data:
                    supabase.table(SUPABASE_FUNCIONARIO_TABLE)\
                        .delete()\
                        .eq('id', funcionarios['id'])\
                        .execute()
                print(f"DEBUG - {len(funcionarios.data)} funcionários excluídos da propriedade {id_propriedade}")
        except Exception as e:
            print(f"Aviso: Erro ao verificar funcionários (pode ser que a tabela não exista): {str(e)}")
        
        # Excluir a propriedade
        result = supabase.table(SUPABASE_PROPERTIES_TABLE)\
            .delete()\
            .eq('id_propriedade', id_propriedade)\
            .execute()
            
        print(f"DEBUG - Propriedade {id_propriedade} excluída: {result.data}")

        return jsonify({'success': True, 'message': 'Propriedade excluída com sucesso!'})

    except Exception as e:
        tb = traceback.format_exc()
        print(f"Erro completo ao excluir propriedade: {tb}")
        return jsonify({'error': str(e)}), 500

# Rotas para cadastro de safra (talhão)
@cadastro_propriedade_bp.route('/cadastro_propriedade/salvar_safra', methods=['POST'])
@login_required
def salvar_safra():
    """Rota para salvar dados de safra (talhão) para uma propriedade"""
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
    

                                                                                                       
            'nome_talhao': data.get('nome_talhao', '').upper(),
            'variedade': data.get('variedade', ''),
            'plantio': data.get('plantio', ''),
            'linha': data.get('linha', ''),
            'planta': data.get('planta', ''),
            'n_plantas': int(data.get('n_plantas', 0)),
            'area_ha': float(data.get('area_ha', 0)),
            'status': data.get('status', 'Produção'),  # Produção ou Formação
            'data_cadastro': datetime.now().isoformat()
        }
        
        # Insere na tabela de safras
        result = supabase.table('cadastro_safra').insert(safra_data).execute()
        
        # Obtém o ID da safra (talhão) inserida
        id_safra = result.data[0]['id_safra'] if result.data else None
            
        return jsonify({
            'success': True, 
            'message': 'Talhão cadastrado com sucesso!',
            'id_safra': id_safra,
            'prompt_outro_talhao': True  # Flag para perguntar se deseja cadastrar outro talhão
        })
        
    except Exception as e:
        print(f"Erro ao salvar talhão: {str(e)}")
        return jsonify({'error': str(e)}), 500
                                                

@cadastro_propriedade_bp.route('/cadastro_propriedade/atualizar_safra/<int:id_safra>', methods=['PUT'])
@login_required
def atualizar_safra(id_safra):
    """Rota para atualizar uma safra (talhão) existente"""
    try:
        data = request.get_json()
        
        # Verificar se a safra existe
        safra = supabase.table('cadastro_safra')\
            .select('*')\
            .eq('id_safra', id_safra)\
            .execute()
            
        if not safra.data or len(safra.data) == 0:
            return jsonify({
                'success': False,
                'message': 'Talhão não encontrado'
            }), 404
        
        # Preparar dados para atualização
        update_data = {
          
        
                          
            'nome_talhao': data.get('nome_talhao', '').upper(),
            'variedade': data.get('variedade', ''),
            'plantio': data.get('plantio', ''),
            'linha': data.get('linha', ''),
            'planta': data.get('planta', ''),
            'n_plantas': int(data.get('n_plantas', 0)),
            'area_ha': float(data.get('area_ha', 0)),
            'status': data.get('status', 'Produção'),
            'data_alteracao': datetime.now().isoformat()
                            
        }
        
        # Logs para debug
        print(f"DEBUG - Atualizando talhão {id_safra}")
        print(f"DEBUG - Dados de atualização: {update_data}")
        
        # Executar atualização
        result = supabase.table('cadastro_safra')\
            .update(update_data)\
            .eq('id_safra', id_safra)\
            .execute()
            
        print(f"DEBUG - Resultado da atualização: {result.data}")
        
        return jsonify({
            'success': True,
            'message': 'Talhão atualizado com sucesso!'
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Erro completo ao atualizar talhão: {tb}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@cadastro_propriedade_bp.route('/cadastro_propriedade/safra/<int:id_safra>', methods=['DELETE'])
@login_required
def excluir_safra(id_safra):
    """Rota para excluir uma safra (talhão)"""
    try:
        # Verificar se a safra existe
        safra = supabase.table('cadastro_safra')\
            .select('*')\
            .eq('id_safra', id_safra)\
            .execute()
            
        if not safra.data or len(safra.data) == 0:
            return jsonify({
                'success': False,
                'message': 'Talhão não encontrado'
            }), 404
        
        # Excluir a safra
        result = supabase.table('cadastro_safra')\
            .delete()\
            .eq('id_safra', id_safra)\
            .execute()
            
        print(f"DEBUG - Talhão {id_safra} excluído: {result.data}")
        
        return jsonify({
            'success': True,
            'message': 'Talhão excluído com sucesso!'
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Erro completo ao excluir talhão: {tb}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500    

# Rotas para o gerenciamento de funcionários
@cadastro_propriedade_bp.route('/cadastro_propriedade/funcionarios/<int:id_propriedade>', methods=['GET'])
@login_required
def listar_funcionarios(id_propriedade):
    """Rota para listar todos os funcionários de uma propriedade"""
    try:
        funcionarios = supabase.table(SUPABASE_FUNCIONARIO_TABLE)\
            .select('*')\
            .eq('id_propriedade_f', id_propriedade)\
            .execute()
        
        return jsonify({
            'success': True,
            'funcionarios': funcionarios.data
        })
                                                                     
                                                                     
                                                                             
                                                                                  
                                                                                   
                                                                  
                        
                             
        
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Erro completo ao listar funcionários: {tb}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
                                                                                                       
                     
                                                

@cadastro_propriedade_bp.route('/cadastro_propriedade/funcionario/<int:id_funcionario>', methods=['GET'])
@login_required
def obter_funcionario(id_funcionario):
    """Rota para obter os dados de um funcionário específico pelo ID"""
    try:
        funcionarios = supabase.table(SUPABASE_FUNCIONARIO_TABLE)\
            .select('*')\
            .eq('id', id_funcionarios)\
            .execute()
        
        if not funcionarios.data or len(funcionarios.data) == 0:
            return jsonify({
                'success': False,
                'message': 'Funcionário não encontrado'
            }), 404
            
        return jsonify({
            'success': True,
            'funcionario': funcionario.data[0]
                                                                                           
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Erro completo ao obter funcionário: {tb}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@cadastro_propriedade_bp.route('/cadastro_propriedade/salvar_funcionario', methods=['POST'])
@login_required
def salvar_funcionario():
    """Rota para salvar um novo funcionário"""
    try:
        data = request.json
        
        if not data or 'id_propriedade' not in data:
            return jsonify({'error': 'Dados inválidos'}), 400
            
        id_propriedade = data.get('id_propriedade')
        
        # Verificar se a propriedade existe
        propriedade = supabase.table(SUPABASE_PROPERTIES_TABLE)\
            .select('*')\
            .eq('id_propriedade', id_propriedade)\
            .execute()
            
        if not propriedade.data:
            return jsonify({'error': 'Propriedade não encontrada'}), 404
        
        # Preparar dados para inserção
        funcionario_data = {
            'id_propriedade_f': id_propriedade,
            'nome_funcionario': data.get('nome_funcionario', '').upper(),
            'apelido': data.get('apelido', ''),
            'data_criacao': datetime.now().isoformat()
        }
        
        # Insere na tabela de funcionários
        result = supabase.table(SUPABASE_FUNCIONARIO_TABLE).insert(funcionario_data).execute()
        
        # Obtém o ID do funcionário inserido
        id_funcionario = result.data[0]['id'] if result.data else None
        
        return jsonify({
            'success': True,
            'message': 'Funcionário cadastrado com sucesso!',
            'id_funcionario': id_funcionario,
            'prompt_outro_funcionario': True  # Flag para perguntar se deseja cadastrar outro funcionário
        })
        
    except Exception as e:
        print(f"Erro ao salvar funcionário: {str(e)}")
        return jsonify({'error': str(e)}), 500

@cadastro_propriedade_bp.route('/cadastro_propriedade/atualizar_funcionario/<int:id_funcionario>', methods=['PUT'])
@login_required
def atualizar_funcionario(id_funcionario):
    """Rota para atualizar um funcionário existente"""
    try:
        data = request.get_json()
        
        # Verificar se o funcionário existe
        funcionario = supabase.table(SUPABASE_FUNCIONARIO_TABLE)\
            .select('*')\
            .eq('id', id_funcionario)\
            .execute()
            
        if not funcionario.data or len(funcionario.data) == 0:
            return jsonify({
                'success': False,
                'message': 'Funcionário não encontrado'
            }), 404
        
        # Preparar dados para atualização
        update_data = {
            'nome_funcionario': data.get('nome_funcionario', '').upper(),
            'apelido': data.get('apelido', ''),
            'data_alteracao': datetime.now().isoformat()
                                                                             
                                                                               
                                                             
        }
        
        # Logs para debug
        print(f"DEBUG - Atualizando funcionário {id_funcionario}")
                                                                        
                      
                                                         

                                                                                                        
               
                                        
                                                           
        
                                                  
            
        print(f"DEBUG - Dados de atualização: {update_data}")
        
        # Executar atualização
        result = supabase.table(SUPABASE_FUNCIONARIO_TABLE)\
            .update(update_data)\
            .eq('id', id_funcionario)\
            .execute()
            
        print(f"DEBUG - Resultado da atualização: {result.data}")
        
        return jsonify({
            'success': True,
            'message': 'Funcionário atualizado com sucesso!'
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Erro completo ao atualizar funcionário: {tb}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@cadastro_propriedade_bp.route('/cadastro_propriedade/funcionario/<int:id_funcionario>', methods=['DELETE'])
@login_required
def excluir_funcionario(id_funcionario):
    """Rota para excluir um funcionário"""
    try:
        # Verificar se o funcionário existe
        funcionario = supabase.table(SUPABASE_FUNCIONARIO_TABLE)\
            .select('*')\
            .eq('id', id_funcionario)\
            .execute()
            
        if not funcionario.data or len(funcionario.data) == 0:
            return jsonify({
                'success': False,
                'message': 'Funcionário não encontrado'
            }), 404
                                         
                                                     
                                  
                                                           
                                  
                                                                                                      
        
        # Excluir o funcionário
        result = supabase.table(SUPABASE_FUNCIONARIO_TABLE)\
            .delete()\
            .eq('id', id_funcionario)\
            .execute()
            
        print(f"DEBUG - Funcionário {id_funcionario} excluído: {result.data}")
        
        return jsonify({
            'success': True,
            'message': 'Funcionário excluído com sucesso!'
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Erro completo ao excluir funcionário: {tb}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Rota para finalizar o cadastro e perguntar sobre o próximo passo
@cadastro_propriedade_bp.route('/cadastro_propriedade/finalizar_talhao/<int:id_propriedade>', methods=['POST'])
@login_required
def finalizar_talhao(id_propriedade):
    """Rota para finalizar o cadastro de talhões e perguntar sobre funcionários"""
    try:
        return jsonify({
            'success': True,
            'message': 'Cadastro de talhões finalizado',
            'prompt_funcionario': True  # Flag para perguntar se deseja cadastrar funcionários
        })
    except Exception as e:
        print(f"Erro: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Função para finalizar o cadastro de funcionários
@cadastro_propriedade_bp.route('/cadastro_propriedade/finalizar_funcionario/<int:id_propriedade>', methods=['POST'])
@login_required
def finalizar_funcionario(id_propriedade):
    """Rota para finalizar o cadastro de funcionários e concluir o processo"""
    try:
        return jsonify({
            'success': True,
            'message': 'Cadastro de funcionários finalizado',
            'redirect': url_for('cadastro_propriedade.index')  # Redirecionar para a listagem de propriedades
        })
    except Exception as e:
        print(f"Erro: {str(e)}")
                          
        return jsonify({'error': str(e)}), 500

# Função para registrar todos os dados do processo de cadastro
@cadastro_propriedade_bp.route('/cadastro_propriedade/registrar_completo', methods=['POST'])
@login_required
def registrar_completo():
    """Função para registrar todos os dados do processo de cadastro"""
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'Dados inválidos'}), 400
            
        # Registrar o status completo da propriedade
        id_propriedade = data.get('id_propriedade')
        
        # Verificar se a propriedade existe
        propriedade = supabase.table(SUPABASE_PROPERTIES_TABLE)\
            .select('*')\
            .eq('id_propriedade', id_propriedade)\
            .execute()
            
        if not propriedade.data:
            return jsonify({'error': 'Propriedade não encontrada'}), 404
            
        # Atualizar o status da propriedade para completo
        update_data = {
            'cadastro_completo': True,
            'data_completado': datetime.now().isoformat()
        }
        
        result = supabase.table(SUPABASE_PROPERTIES_TABLE)\
            .update(update_data)\
            .eq('id_propriedade', id_propriedade)\
            .execute()
            
        return jsonify({
            'success': True,
            'message': 'Cadastro completo registrado com sucesso!',
            'redirect': url_for('cadastro_propriedade.index')  # Redirecionar para a listagem de propriedades
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Erro completo ao registrar cadastro completo: {tb}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Rota para obter informações de estatísticas da propriedade
@cadastro_propriedade_bp.route('/cadastro_propriedade/estatisticas/<int:id_propriedade>', methods=['GET'])
@login_required
def estatisticas_propriedade(id_propriedade):
    """Rota para obter estatísticas da propriedade (talhões e funcionários)"""
    try:
        # Verificar se a propriedade existe
        propriedade = supabase.table(SUPABASE_PROPERTIES_TABLE)\
            .select('*')\
            .eq('id_propriedade', id_propriedade)\
            .execute()
            
        if not propriedade.data:
            return jsonify({'error': 'Propriedade não encontrada'}), 404
        
        # Obter contagem de talhões
        talhoes = supabase.table('cadastro_safra')\
            .select('id_safra')\
            .eq('id_propriedade', id_propriedade)\
            .execute()
            
        # Obter contagem de funcionários
        funcionarios = supabase.table(SUPABASE_FUNCIONARIO_TABLE)\
            .select('id')\
            .eq('id_propriedade_f', id_propriedade)\
            .execute()
            
        # Obter área total dos talhões
        area_total = 0
        if talhoes.data:
            talhoes_completos = supabase.table('cadastro_safra')\
                .select('area_ha')\
                .eq('id_propriedade', id_propriedade)\
                .execute()
            
            if talhoes_completos.data:
                for talhao in talhoes_completos.data:
                    area_total += float(talhao.get('area_ha', 0))
        
        return jsonify({
            'success': True,
            'estatisticas': {
                'total_talhoes': len(talhoes.data) if talhoes.data else 0,
                'total_funcionarios': len(funcionarios.data) if funcionarios.data else 0,
                'area_total_talhoes': round(area_total, 2),
                'tamanho_propriedade': propriedade.data[0].get('tamanho_propriedade', 0) if propriedade.data else 0
            }
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Erro completo ao obter estatísticas: {tb}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500