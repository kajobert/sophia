from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from core.agents import developer_agent
from crewai import Task, Crew, Process
from memory.short_term_memory import ShortTermMemory
short_term_memory = ShortTermMemory()

import os
app = Flask(__name__)
CORS(app)
@app.route('/')
def index():
    # Servíruje webui.html na kořenové adrese
    return send_file(os.path.join(os.path.dirname(__file__), 'webui.html'))

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get('message', '')
    if not user_input:
        return jsonify({'error': 'No message provided'}), 400

    # Vytvoření úkolu pro Sophii
    task = Task(
        description=f"Zpracuj následující požadavek: '{user_input}'. Pokud je to příkaz, použij dostupné nástroje.",
        expected_output="Stručně odpověz nebo proveď požadovanou akci a popiš výsledek.",
        agent=developer_agent
    )
    crew = Crew(
        tasks=[task],
        agents=[developer_agent],
        process=Process.sequential
    )
    result = crew.kickoff()
    short_term_memory.add_event(f"User: {user_input}")
    short_term_memory.add_event(f"Sophia: {result}")
    return jsonify({'response': str(result)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
