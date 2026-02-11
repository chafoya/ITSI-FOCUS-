from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
import hashlib
from datetime import datetime

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'tu_clave_secreta_super_segura'  # Necesario para las sesiones

# Archivos de datos
DATA_FILE = 'planner_data.json'
USERS_FILE = 'users.json'

# --- FUNCIONES DE UTILIDAD ---
def load_data(filename, default):
    if not os.path.exists(filename):
        return default
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return default

def save_data(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- RUTAS DE VISTAS (HTML) ---
@app.route('/')
def index():
    return render_template('index.html')

# --- API: AUTENTICACIÓN (LOGIN/REGISTRO) ---
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    users = load_data(USERS_FILE, {})
    
    email = data.get('email').strip().lower()
    
   # Validaciones básicas
    if not email.endswith('@clases.edu.sv'):
        return jsonify({'error': 'Solo se permiten correos @clases.edu.sv'}), 400
    
    if email in users:
        return jsonify({'error': 'Este correo ya está registrado'}), 400
        
    # Crear usuario
    users[email] = {
        'name': data.get('name'),
        'password': hash_password(data.get('password')),
        'joined': datetime.now().strftime("%Y-%m-%d")
    }
    
    save_data(USERS_FILE, users)
    
    # Inicializar datos vacíos para este usuario en el planner
    all_planner_data = load_data(DATA_FILE, {})
    if email not in all_planner_data:
        all_planner_data[email] = {
            'tasks': [],
            'events': [],
            'notes': [],
            'stats': {'completed': 0, 'focus_hours': 0}
        }
        save_data(DATA_FILE, all_planner_data)

    return jsonify({'success': True})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    users = load_data(USERS_FILE, {})
    
    email = data.get('email').strip().lower()
    password = data.get('password')
    
    user = users.get(email)
    
    if not user or user['password'] != hash_password(password):
        return jsonify({'error': 'Correo o contraseña incorrectos'}), 401
    
    # Iniciar sesión
    session['user'] = email
    session['user_name'] = user['name']
    
    return jsonify({
        'success': True, 
        'user': {'email': email, 'name': user['name']}
    })

@app.route('/api/logout')
def logout():
    session.clear()
    return jsonify({'success': True})

# --- API: FUNCIONALIDAD PLANNER (Protegido por usuario) ---
def get_current_user_data():
    if 'user' not in session:
        return None, None
    
    email = session['user']
    all_data = load_data(DATA_FILE, {})
    
    # Asegurar que el usuario tenga estructura de datos
    if email not in all_data:
        all_data[email] = { 'tasks': [], 'events': [], 'notes': [] }
    
    return all_data, email

@app.route('/api/data', methods=['GET'])
def get_data():
    all_data, email = get_current_user_data()
    if not email:
        return jsonify({'error': 'No autorizado'}), 401
    return jsonify(all_data[email])

@app.route('/api/save', methods=['POST'])
def save_user_data():
    all_data, email = get_current_user_data()
    if not email:
        return jsonify({'error': 'No autorizado'}), 401
    
    # Actualizar solo los datos de este usuario
    new_data = request.json
    all_data[email] = new_data
    save_data(DATA_FILE, all_data)
    
    return jsonify({'success': True})

if __name__ == '__main__':
    # Crear archivos vacíos si no existen
    if not os.path.exists(DATA_FILE):
        save_data(DATA_FILE, {})
    if not os.path.exists(USERS_FILE):
        save_data(USERS_FILE, {})

    app.run(host='0.0.0.0', port=5000)
