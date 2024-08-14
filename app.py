from flask import Flask, jsonify, request
import uuid
import git
import json
import os
import requests
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

app = Flask(__name__)

# Configuration
CHATGPT_API_KEY = os.getenv('CHATGPT_API_KEY')
BLACKBOX_API_KEY = os.getenv('BLACKBOX_API_KEY')

# In-memory storage for projects and their details
projects = {}

def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not CHATGPT_API_KEY or not BLACKBOX_API_KEY:
            return jsonify({"status": "Error", "message": "API keys are not configured"}), 500
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def health_check():
    return jsonify({"status": "OK", "message": "AI Fusion API is running"})

@app.route('/devin', methods=['POST'])
def devin_ai():
    data = request.json
    action = data.get('action')

    if action == 'create_project':
        project_id = str(uuid.uuid4())
        projects[project_id] = {
            'name': data.get('name', 'Untitled Project'),
            'status': 'Created',
            'progress': 0,
            'tasks': []
        }
        return jsonify({"status": "OK", "message": "New project created", "project_id": project_id})

    elif action == 'update_status':
        project_id = data.get('project_id')
        new_status = data.get('status')
        if project_id in projects:
            projects[project_id]['status'] = new_status
            return jsonify({"status": "OK", "message": "Project status updated"})
        return jsonify({"status": "Error", "message": "Project not found"})

    elif action == 'update_progress':
        project_id = data.get('project_id')
        progress = data.get('progress')
        if project_id in projects:
            projects[project_id]['progress'] = progress
            return jsonify({"status": "OK", "message": "Project progress updated"})
        return jsonify({"status": "Error", "message": "Project not found"})

    elif action == 'add_task':
        project_id = data.get('project_id')
        task = data.get('task')
        if project_id in projects:
            projects[project_id]['tasks'].append(task)
            return jsonify({"status": "OK", "message": "Task added to project"})
        return jsonify({"status": "Error", "message": "Project not found"})

    elif action == 'integrate_git':
        project_id = data.get('project_id')
        repo_url = data.get('repo_url')
        if project_id in projects:
            try:
                git.Repo.clone_from(repo_url, f"/tmp/{project_id}")
                return jsonify({"status": "OK", "message": "Git repository integrated successfully"})
            except git.GitCommandError:
                return jsonify({"status": "Error", "message": "Failed to clone Git repository"})
        return jsonify({"status": "Error", "message": "Project not found"})

    else:
        return jsonify({"status": "Error", "message": "Invalid action for Devin AI"})

@app.route('/chatgpt', methods=['POST'])
def chatgpt():
    data = request.json
    action = data.get('action')

    if not CHATGPT_API_KEY:
        return jsonify({"status": "Error", "message": "ChatGPT API key not configured"}), 500

    headers = {
        "Authorization": f"Bearer {CHATGPT_API_KEY}",
        "Content-Type": "application/json"
    }
    api_url = "https://api.openai.com/v1/chat/completions"

    try:
        if action == 'generate_code':
            language = data.get('language', 'python')
            description = data.get('description', '')
            prompt = f"Generate {language} code for: {description}"

            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}]
            }

            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            generated_code = response.json()['choices'][0]['message']['content']

            return jsonify({"status": "OK", "message": "Code generated", "code": generated_code})

        elif action == 'generate_documentation':
            code = data.get('code', '')
            prompt = f"Generate documentation for the following code:\n{code}"

            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}]
            }

            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            generated_docs = response.json()['choices'][0]['message']['content']

            return jsonify({"status": "OK", "message": "Documentation generated", "documentation": generated_docs})

        elif action == 'answer_query':
            query = data.get('query', '')

            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": query}]
            }

            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            answer = response.json()['choices'][0]['message']['content']

            return jsonify({"status": "OK", "message": "Query answered", "answer": answer})

        else:
            return jsonify({"status": "Error", "message": "Invalid action for ChatGPT"}), 400

    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error in ChatGPT API request: {str(e)}")
        if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 429:
            return jsonify({"status": "Error", "message": "API rate limit exceeded. Please try again later."}), 429
        return jsonify({"status": "Error", "message": "An error occurred while processing your request"}), 500
    except KeyError as e:
        app.logger.error(f"Unexpected response format from ChatGPT API: {str(e)}")
        return jsonify({"status": "Error", "message": "Unexpected response from ChatGPT API"}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error in ChatGPT API: {str(e)}")
        return jsonify({"status": "Error", "message": "An unexpected error occurred"}), 500

@app.route('/blackbox', methods=['POST'])
def blackbox_ai():
    data = request.json
    action = data.get('action')

    if not BLACKBOX_API_KEY:
        return jsonify({"status": "Error", "message": "Blackbox API key not configured"}), 500

    try:
        if action == 'search_code':
            query = data.get('query', '')
            language = data.get('language', 'python')
            # Here you would integrate with the actual Blackbox AI API
            # Replace this with actual API call using BLACKBOX_API_KEY
            found_code = f"# {language} code found for query: {query}\n# Placeholder for actual found code"
            return jsonify({"status": "OK", "message": "Code found", "snippet": found_code})

        elif action == 'optimize_code':
            code = data.get('code', '')
            optimization_level = data.get('optimization_level', 'medium')
            # Here you would integrate with the actual Blackbox AI API
            # Replace this with actual API call using BLACKBOX_API_KEY
            optimized_code = f"# Optimized code (level: {optimization_level}):\n{code}\n# Placeholder for actual optimized code"
            return jsonify({"status": "OK", "message": "Code optimized", "optimized_code": optimized_code})

        elif action == 'analyze_complexity':
            code = data.get('code', '')
            # Here you would integrate with the actual Blackbox AI API
            # Replace this with actual API call using BLACKBOX_API_KEY
            analysis = f"Complexity analysis for:\n{code}\nPlaceholder for actual complexity analysis"
            return jsonify({"status": "OK", "message": "Code analyzed", "analysis": analysis})

        else:
            return jsonify({"status": "Error", "message": "Invalid action for Blackbox AI"}), 400

    except Exception as e:
        app.logger.error(f"Error in Blackbox AI endpoint: {str(e)}")
        return jsonify({"status": "Error", "message": "An error occurred while processing your request"}), 500

@app.route('/integrate', methods=['POST'])
def integrate_ai():
    data = request.json
    project_id = data.get('project_id')
    code_description = data.get('code_description')

    if project_id not in projects:
        return jsonify({"status": "Error", "message": "Project not found"})

    # Step 1: Use Devin AI to create a new task
    projects[project_id]['tasks'].append(f"Implement: {code_description}")

    # Step 2: Use ChatGPT to generate code
    chatgpt_response = chatgpt()
    chatgpt_data = json.loads(chatgpt_response.get_data(as_text=True))
    generated_code = chatgpt_data['code']

    # Step 3: Use Blackbox AI to optimize the generated code
    blackbox_response = blackbox_ai()
    blackbox_data = json.loads(blackbox_response.get_data(as_text=True))
    optimized_code = blackbox_data['optimized_code']

    # Step 4: Update project progress
    projects[project_id]['progress'] += 10

    return jsonify({
        "status": "OK",
        "message": "Integrated AI task completed",
        "generated_code": generated_code,
        "optimized_code": optimized_code,
        "project_progress": projects[project_id]['progress']
    })

if __name__ == '__main__':
    app.run(debug=True)
