from flask import Flask, request, jsonify, send_from_directory, session
import sys
import os

# Přidání cesty k hlavnímu adresáři projektu, aby bylo možné importovat moduly z `memory`
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from memory.advanced_memory import AdvancedMemory

app = Flask(__name__, static_folder='ui')
app.secret_key = os.environ.get("SOPHIA_SECRET_KEY", "dev-secret")
def get_current_user():
    # Demo: uživatel je v session pod klíčem 'user', jinak None
    return session.get("user")

@app.route('/api/login', methods=['POST'])
def api_login():
    # Demo login: přijme JSON s 'name', uloží do session
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Missing 'name' in request body"}), 400
    session['user'] = {
        "name": data['name'],
        "email": data.get('email', ''),
        "avatar": data.get('avatar', '')
    }
    return jsonify({"message": "Přihlášení úspěšné"})

@app.route('/api/me')
def api_me():
    user = get_current_user()
    if not user:
        return jsonify({"detail": "Not authenticated"}), 401
    return jsonify(user)

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.pop('user', None)
    return jsonify({"message": "Odhlášení úspěšné"})

@app.route('/')
def serve_ui():
    """
    Servíruje hlavní HTML soubor pro uživatelské rozhraní.
    """
    return send_from_directory(app.static_folder, 'index.html')


from functools import wraps
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not get_current_user():
            return jsonify({"detail": "Not authenticated"}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/start_task', methods=['POST'])
@login_required
def start_task():
    data = request.get_json()
    if not data or 'task_description' not in data:
        return jsonify({"error": "Missing 'task_description' in request body"}), 400
    task_description = data['task_description']
    try:
        memory = AdvancedMemory()
        task_id = memory.add_task(task_description)
        memory.close()
        return jsonify({"message": "Task added successfully", "task_id": task_id}), 201
    except Exception as e:
        return jsonify({"error": f"Failed to add task: {str(e)}"}), 500

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=None, help='Port pro spuštění backendu')
    args = parser.parse_args()
    port = args.port or int(os.environ.get('FLASK_RUN_PORT', 5001))
    app.run(debug=False, port=port)
