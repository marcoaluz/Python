from flask import Flask, render_template, request, redirect, url_for, flash, session, Blueprint, jsonify
from utils import login_required
from supabase import create_client
from datetime import datetime
from math import ceil
import httpx
import asyncio
from httpx import Limits, Client
from tenacity import retry, stop_after_attempt, wait_fixed
import re

from config import SUPABASE_URL, SUPABASE_API_KEY

cadastro_bp  = Blueprint('cadastro_propriedade', __name__)

SUPABASE_PROPERTIES_TABLE = 'cadastro_propriedade'
supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)

timeout = httpx.Timeout(10.0)
client = httpx.Client(timeout=timeout)
limits = Limits(max_connections=10)
client = Client(timeout=timeout, limits=limits)

@cadastro_bp.route('/cadastro_propriedade', methods=['GET', 'POST'])
@login_required
def cadastro_propriedade():
    if 'logged_in' not in session:
        return redirect(url_for('login.login'))

    items_per_page = 10
    current_page = int(request.args.get('page', 1))
    search_query = request.args.get('query', '').strip()
    start_index = (current_page - 1) * items_per_page
    end_index = start_index + items_per_page

    # Modified query to handle integer id_propriedade
    if search_query:
        try:
            # If search query is a number, search by id
            id_query = int(search_query)
            propriedades = supabase.table(SUPABASE_PROPERTIES_TABLE).select('*').eq('id_propriedade', id_query).range(start_index, end_index).execute()
            total_properties = supabase.table(SUPABASE_PROPERTIES_TABLE).select('*').eq('id_propriedade', id_query).execute()
        except ValueError:
            # If search query is not a number, search by nome_propriedade
            propriedades = supabase.table(SUPABASE_PROPERTIES_TABLE).select('*').ilike('nome_propriedade', f"%{search_query}%").range(start_index, end_index).execute()
            total_properties = supabase.table(SUPABASE_PROPERTIES_TABLE).select('*').ilike('nome_propriedade', f"%{search_query}%").execute()
    else:
        propriedades = supabase.table(SUPABASE_PROPERTIES_TABLE).select('*').range(start_index, end_index).execute()
        total_properties = supabase.table(SUPABASE_PROPERTIES_TABLE).select('*').execute()

    total_properties_count = len(total_properties.data) if total_properties.data else 0
    total_pages = ceil(total_properties_count / items_per_page)

    return render_template(
        'cadastro_propriedade.html',
        propriedades=propriedades.data if propriedades.data else [],
        current_page=current_page,
        total_pages=total_pages,
        search_query=search_query
    )

@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
async def fetch_properties(supabase, query=None, page=1, per_page=10):
    try:
        start_index = (page - 1) * per_page
        end_index = start_index + per_page - 1

        if query:
            try:
                id_query = int(query)
                response = supabase.table(SUPABASE_PROPERTIES_TABLE).select('*').eq('id_propriedade', id_query).range(start_index, end_index).execute()
            except ValueError:
                response = supabase.table(SUPABASE_PROPERTIES_TABLE).select('*').ilike('nome_propriedade', f"%{query}%").range(start_index, end_index).execute()
        else:
            response = supabase.table(SUPABASE_PROPERTIES_TABLE).select('*').range(start_index, end_index).execute()

        total_properties_response = supabase.table(SUPABASE_PROPERTIES_TABLE).select('id_propriedade', count='exact').execute()
        total_properties = len(total_properties_response.data) if total_properties_response.data else 0
        total_pages = ceil(total_properties / per_page)

        return {
            'propriedades': response.data if response.data else [],
            'current_page': page,
            'total_pages': total_pages
        }
    except Exception as e:
        print(f"Error fetching properties: {e}")
        return {
            'propriedades': [],
            'current_page': page,
            'total_pages': 0
        }

@cadastro_bp.route('/lista_propriedades', methods=['GET'])
async def lista_propriedades():
    page = int(request.args.get('page', 1))
    query = request.args.get('query', '').strip()
    result = await fetch_properties(supabase, query, page)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(result)

    return render_template(
        'cadastro_propriedade.html',
        propriedades=result['propriedades'],
        current_page=result['current_page'],
        total_pages=result['total_pages'],
        query=query
    )

@cadastro_bp.route('/salvar_propriedade', methods=['POST'])
def salvar_propriedade():
    id_propriedade = request.form.get('id_propriedade')
    nome_propriedade = request.form.get('nome_propriedade')
    endereco = request.form.get('endereco')
    tamanho_hectares = request.form.get('tamanho_hectares')
    tipo_cultura = request.form.get('tipo_cultura')
    administrador_alteracao = request.form.get('administrador_alteracao')

    if not all([id_propriedade, nome_propriedade, tamanho_hectares, tipo_cultura]):
        flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
        return redirect(url_for('cadastro_propriedade.cadastro_propriedade'))

    response = supabase.table(SUPABASE_PROPERTIES_TABLE).select('*').eq('id_propriedade', id_propriedade).execute()
    if response.data:
        flash(f"ID {id_propriedade} já cadastrado. Operação cancelada.", 'danger')
        return redirect(url_for('cadastro_propriedade.cadastro_propriedade'))

    try:
        supabase.table(SUPABASE_PROPERTIES_TABLE).insert({
            'id_propriedade': id_propriedade,
            'nome_propriedade': nome_propriedade,
            'endereco': endereco,
            'tamanho_hectares': tamanho_hectares,
            'tipo_cultura': tipo_cultura,
            'data_alteracao': None,
            'administrador_alteracao': administrador_alteracao,
            'status_propriedade': 'Ativa'
        }).execute()
        flash('Propriedade salva com sucesso!', 'success')
    except Exception as e:
        flash(f"Ocorreu um erro ao salvar a propriedade: {str(e)}", 'danger')

    return redirect(url_for('cadastro_propriedade.cadastro_propriedade'))

if __name__ == '__main__':
    app = Flask(__name__)
    app.register_blueprint(cadastro_bp)
    app.run(debug=True)