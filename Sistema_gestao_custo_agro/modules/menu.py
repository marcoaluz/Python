from flask import Blueprint, render_template, session, redirect, url_for,flash
from utils import login_required

menu_bp = Blueprint('menu', __name__)

@menu_bp.route('/menu')
@login_required
def menu():
    if 'logged_in' in session:  # Verifica se o usuário está logado
        #flash('Login realizado com sucesso!', 'success')
        return render_template('menu.html')  # Exibe o menu principal
    else:
        return redirect(url_for('login.login'))  # Redireciona para o login se não estiver autenticado

