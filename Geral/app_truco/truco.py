
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
import jwt
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.init_app(app)

# Usuário básico
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Lista de usuários
users = {}

# Carregar o usuário pelo ID
@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

# Função para criar um JWT token (JSON Web Token) para autenticar usuários
def create_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': time.time() + 3600  # Token expira em 1 hora
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token

# Página inicial
@app.route('/')
def index():
    return render_template('index.html')

# Rota para login
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    if username:
        user = User(id=username)
        users[username] = user
        login_user(user)
        token = create_token(username)
        return jsonify({'token': token})
    return jsonify({'error': 'Invalid username'}), 401

# Rota para logout
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out'})

# Middleware para validar o token JWT
def validate_token(token):
    try:
        decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return decoded['user_id']
    except jwt.ExpiredSignatureError:
        return None

# WebSocket - Gestão de salas e mensagens
@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        emit('status', {'msg': f'{current_user.id} entrou no jogo!'})
    else:
        return False  # Desconectar se o usuário não está autenticado

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    emit('status', {'msg': f'{current_user.id} entrou na sala {room}.'}, room=room)

@socketio.on('leave')
def on_leave(data):
    room = data['room']
    leave_room(room)
    emit('status', {'msg': f'{current_user.id} saiu da sala {room}.'}, room=room)

@socketio.on('play_card')
def on_play_card(data):
    token = data.get('token')
    room = data['room']
    card = data['card']

    user_id = validate_token(token)
    if user_id:
        # Verificar se a jogada é válida (implementação das regras do truco aqui)
        emit('game_update', {'msg': f'{user_id} jogou {card}.'}, room=room)
    else:
        emit('error', {'msg': 'Token inválido ou expirado'})

if __name__ == '__main__':
    socketio.run(app, debug=True)
