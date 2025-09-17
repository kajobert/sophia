from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
import sys
import os

# Přidání cesty k hlavnímu adresáři projektu, aby bylo možné importovat moduly z `memory`
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Importy a cesty ---
import sys
import os
import uuid
import re
from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
from functools import wraps

# Přidání cesty k hlavnímu adresáři projektu, aby bylo možné importovat moduly z core, agents, memory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Testovací mockování LLM (z FastAPI části) ---
from unittest.mock import patch
if os.getenv('SOPHIA_ENV') == 'test':
    from core.mocks import mock_litellm_completion_handler
    print("--- RUNNING IN TEST MODE: Patching litellm.completion with mock handler. ---")
    patcher_completion = patch('litellm.completion', new=mock_litellm_completion_handler)
    patcher_acompletion = patch('litellm.acompletion', new=mock_litellm_completion_handler)
    patcher_completion.start()
    patcher_acompletion.start()


# --- Sophia core a agents importy s automatickým hledáním ---
import importlib
import glob
def try_import(module_name, class_names=None):
    try:
        mod = importlib.import_module(module_name)
        if class_names:
            return tuple(getattr(mod, name) for name in class_names)
        return mod
    except ModuleNotFoundError as e:
        # Automatické hledání cesty
        mod_path = module_name.replace('.', os.sep)
        candidates = glob.glob(f"**/{mod_path}.py", recursive=True)
        if candidates:
            found_path = os.path.abspath(os.path.dirname(candidates[0]))
            if found_path not in sys.path:
                sys.path.insert(0, found_path)
            try:
                mod = importlib.import_module(module_name)
                if class_names:
                    return tuple(getattr(mod, name) for name in class_names)
                return mod
            except Exception as e2:
                raise ImportError(f"Nepodařilo se importovat {module_name} ani po přidání {found_path}: {e2}")
        raise ImportError(f"Modul {module_name} nenalezen: {e}")

# Importy s fallbackem
"""
SharedContext, = try_import('core.context', ['SharedContext'])
get_llm, = try_import('core.llm_config', ['get_llm'])
PlannerAgent, = try_import('agents.planner_agent', ['PlannerAgent'])
EngineerAgent, = try_import('agents.engineer_agent', ['EngineerAgent'])
"""
AdvancedMemory, = try_import('memory.advanced_memory', ['AdvancedMemory'])

# --- Flask app a OAuth ---
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

# --- Uživatelská session ---
def get_current_user():
    return session.get("user")

# --- Login required dekorátor ---
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not get_current_user():
            return jsonify({"detail": "Not authenticated"}), 401
        return f(*args, **kwargs)
    return decorated

# --- API endpointy ---

# Dummy chat endpoint (původní)
@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    data = request.get_json()
    msg = data.get('message', '').strip() if data else ''
    if not msg:
        return jsonify({"error": "Chybí zpráva"}), 400
    return jsonify({"response": f"Sophia říká: {msg}"})

"""
# --- Nový endpoint: Sophia plánování a kódování (FastAPI logika) ---
#@app.route('/api/plan_and_code', methods=['POST'])
#@login_required
#def plan_and_code():
#    data = request.get_json()
#    prompt = data.get('prompt', '').strip() if data else ''
#    if not prompt:
#        return jsonify({"error": "Chybí prompt"}), 400
#    try:
#        session_id = str(uuid.uuid4())
#        context = SharedContext(session_id=session_id, original_prompt=prompt)
#        llm_instance = get_llm()
#        planner_agent = PlannerAgent(llm=llm_instance)
#        context_with_plan = planner_agent.run_task(context)
#        engineer_agent = EngineerAgent(llm=llm_instance)
#        final_context = engineer_agent.run_task(context_with_plan)
#        output_text = final_context.payload.get('code', '')
#        file_path_match = re.search(r"['\"](sandbox\/[^'\"]+)['\"]", output_text)
#        file_path = file_path_match.group(1) if file_path_match else "No file path found"
#        return jsonify({
#            "status": "success",
#            "message": "EngineerAgent successfully executed the plan.",
#            "file_path": file_path,
#            "final_context": {
#                "plan": final_context.payload.get('plan'),
#                "code_output": output_text,
#                "ethical_review": final_context.payload.get('ethical_review')
#            }
#        })
#    except Exception as e:
#        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
"""

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
        resp = oauth.google.get('userinfo')
        userinfo = resp.json()
    if not userinfo or not userinfo.get('email'):
        return jsonify({"error": "Google OAuth2 selhalo, chybí email"}), 400
    session['user'] = {
        "name": userinfo.get('name', ''),
        "email": userinfo.get('email', ''),
        "avatar": userinfo.get('picture', '')
    }
    return redirect('/')

# Demo login pro testování
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

# Hlavní React chat UI (public/index.html)
@app.route('/')
def serve_react_ui():
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'ui', 'public'), 'index.html')

# Statické soubory pro React (bundle.js, atd.)
@app.route('/bundle.js')
def serve_bundle():
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'ui', 'dist'), 'bundle.js')

# Creator's Interface na /creator
@app.route('/creator')
def serve_creator():
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'ui'), 'index.html')

# Přidání tasku do paměti
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

# --- Spuštění serveru ---
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=None, help='Port pro spuštění backendu')
    args = parser.parse_args()
    port = args.port or int(os.environ.get('FLASK_RUN_PORT', 5001))
    app.run(debug=False, port=port)
