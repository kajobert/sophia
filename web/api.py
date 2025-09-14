from flask import Flask, request, jsonify, send_from_directory
import sys
import os

# Přidání cesty k hlavnímu adresáři projektu, aby bylo možné importovat moduly z `memory`
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from memory.advanced_memory import AdvancedMemory

app = Flask(__name__, static_folder='ui')

@app.route('/')
def serve_ui():
    """
    Servíruje hlavní HTML soubor pro uživatelské rozhraní.
    """
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/start_task', methods=['POST'])
def start_task():
    """
    API endpoint pro přidání nového úkolu do fronty.
    Očekává JSON payload s klíčem 'task_description'.
    """
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
    app.run(debug=False, port=5001)
