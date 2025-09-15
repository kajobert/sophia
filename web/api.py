from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
import sys
import os

# Přidání cesty k hlavnímu adresáři projektu, aby bylo možné importovat moduly z `memory`
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from memory.advanced_memory import AdvancedMemory

from authlib.integrations.flask_client import OAuth

app = Flask(__name__, static_folder='ui')
app.secret_key = os.environ.get("SOPHIA_SECRET_KEY", "dev-secret")

# OAuth2 konfigurace
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "demo-google-client-id")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "demo-google-client-secret")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

oauth = OAuth(app)
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url=GOOGLE_DISCOVERY_URL,
    client_kwargs={
        'scope': 'openid email profile'
    }
)
def get_current_user():
    # Demo: uživatel je v session pod klíčem 'user', jinak None
    return session.get("user")


# Google OAuth2 login endpoint
@app.route('/api/login/google')
def login_google():
    redirect_uri = url_for('auth_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

# Google OAuth2 callback endpoint
@app.route('/api/auth/callback')
def auth_callback():
    token = oauth.google.authorize_access_token()
    userinfo = token.get('userinfo')
    if not userinfo:
        # Pokud userinfo není v tokenu, získej ho explicitně
        resp = oauth.google.get('userinfo')
        userinfo = resp.json()
    if not userinfo or not userinfo.get('email'):
        return jsonify({"error": "Google OAuth2 selhalo, chybí email"}), 400
    session['user'] = {
        "name": userinfo.get('name', ''),
        "email": userinfo.get('email', ''),
        "avatar": userinfo.get('picture', '')
    }
    # Po přihlášení přesměrovat na frontend (kořen)
    return redirect('/')

# Demo login pro testování (ponechán pro fallback/testy)
@app.route('/api/login', methods=['POST'])
def api_login():
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
