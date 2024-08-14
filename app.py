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
            'tasks': [],
            'documentation': ''
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

    elif action == 'interpret_command':
        project_id = data.get('project_id')
        command = data.get('command')
        if project_id in projects:
            try:
                # Use ChatGPT to interpret the command
                prompt = f"Interpret the following project management command and convert it into structured data for task creation or update:\n{command}"
                interpreted_action = chatgpt({"action": "interpret_command", "command": command})
                return jsonify({"status": "OK", "message": "Command interpreted", "action": interpreted_action})
            except Exception as e:
                return jsonify({"status": "Error", "message": f"Failed to interpret command: {str(e)}"})
        return jsonify({"status": "Error", "message": "Project not found"})

    elif action == 'generate_documentation':
        project_id = data.get('project_id')
        description = data.get('description')
        if project_id in projects:
            try:
                result, status_code = generate_documentation(description, project_id)
                if result['status'] == 'OK':
                    projects[project_id]['documentation'] = result['documentation']
                return jsonify(result), status_code
            except Exception as e:
                app.logger.error(f"Error generating documentation: {str(e)}")
                return jsonify({"status": "Error", "message": "An unexpected error occurred while generating documentation"}), 500
        return jsonify({"status": "Error", "message": "Project not found"}), 404

    else:
        return jsonify({"status": "Error", "message": "Invalid action for Devin AI"})

@app.route('/chatgpt', methods=['POST'])
def chatgpt(data=None):
    try:
        if data is None:
            data = request.get_json(force=True)

        if not isinstance(data, dict):
            return jsonify({"status": "Error", "message": "Invalid input data"}), 400

        action = data.get('action')

        if not CHATGPT_API_KEY:
            return jsonify({"status": "Error", "message": "ChatGPT API key not configured"}), 500

        headers = {
            "Authorization": f"Bearer {CHATGPT_API_KEY}",
            "Content-Type": "application/json"
        }
        api_url = "https://api.openai.com/v1/chat/completions"

        if action == 'generate_code':
            language = data.get('language', 'python')
            description = data.get('description', '')
            prompt = f"Generate {language} code for: {description}"
        elif action == 'generate_documentation':
            description = data.get('description', '')
            prompt = f"Generate documentation for the following project description:\n{description}"
        elif action == 'answer_query':
            prompt = data.get('query', '')
        elif action == 'interpret_command':
            command = data.get('command', '')
            prompt = f"Interpret the following project management command and convert it into structured data for task creation or update:\n{command}"
        else:
            return jsonify({"status": "Error", "message": "Invalid action for ChatGPT"}), 400

        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}]
        }

        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']

        result = {
            "status": "OK",
            "message": f"{action.replace('_', ' ').capitalize()} completed",
            "content": content
        }

        if action == 'generate_code':
            result["code"] = content
        elif action == 'generate_documentation':
            result["documentation"] = content
        elif action == 'answer_query':
            result["answer"] = content
        elif action == 'interpret_command':
            result["interpretation"] = content

        return jsonify(result), 200

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
@api_key_required
def blackbox_ai():
    data = request.json
    action = data.get('action')

    if not BLACKBOX_API_KEY:
        return jsonify({"status": "Error", "message": "Blackbox API key not configured"}), 500

    try:
        headers = {
            "Authorization": f"Bearer {BLACKBOX_API_KEY}",
            "Content-Type": "application/json"
        }
        api_url = os.getenv('BLACKBOX_API_URL', 'https://www.useblackbox.io/api/v1')

        if action == 'search_code':
            query = data.get('query', '')
            language = data.get('language', 'python')
            payload = {
                "query": query,
                "language": language
            }
            response = requests.post(f"{api_url}/search", headers=headers, json=payload)
            response.raise_for_status()
            response_data = response.json()
            found_code = response_data.get('code', '')
            if not found_code:
                return jsonify({"status": "Error", "message": "No code found"}), 404
            return jsonify({"status": "OK", "message": "Code found", "snippet": found_code}), 200

        elif action == 'optimize_code':
            code = data.get('code', '')
            optimization_level = data.get('optimization_level', 'medium')
            payload = {
                "code": code,
                "optimization_level": optimization_level
            }
            response = requests.post(f"{api_url}/optimize", headers=headers, json=payload)
            response.raise_for_status()
            response_data = response.json()
            optimized_code = response_data.get('optimized_code', '')
            if not optimized_code:
                return jsonify({"status": "Error", "message": "Failed to optimize code"}), 500
            return jsonify({"status": "OK", "message": "Code optimized", "optimized_code": optimized_code}), 200

        elif action == 'analyze_complexity':
            code = data.get('code', '')
            payload = {
                "code": code
            }
            response = requests.post(f"{api_url}/analyze", headers=headers, json=payload)
            response.raise_for_status()
            response_data = response.json()
            analysis = response_data.get('analysis', '')
            if not analysis:
                return jsonify({"status": "Error", "message": "Failed to analyze code complexity"}), 500
            return jsonify({"status": "OK", "message": "Code analyzed", "analysis": analysis}), 200

        else:
            return jsonify({"status": "Error", "message": "Invalid action for Blackbox AI"}), 400

    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error in Blackbox API request: {str(e)}")
        if isinstance(e, requests.exceptions.HTTPError):
            if e.response.status_code == 429:
                return jsonify({"status": "Error", "message": "API rate limit exceeded. Please try again later."}), 429
            return jsonify({"status": "Error", "message": f"Blackbox API error: {e.response.status_code}"}), e.response.status_code
        return jsonify({"status": "Error", "message": "An error occurred while processing your request"}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error in Blackbox AI endpoint: {str(e)}")
        return jsonify({"status": "Error", "message": "An unexpected error occurred"}), 500

@app.route('/integrate', methods=['POST'])
def integrate_ai():
    data = request.json
    project_id = data.get('project_id')
    code_description = data.get('code_description')

    if not project_id or not code_description:
        return jsonify({"status": "Error", "message": "Missing project_id or code_description"}), 400

    if project_id not in projects:
        return jsonify({"status": "Error", "message": "Project not found"}), 404

    try:
        # Step 1: Use Devin AI to create a new task
        projects[project_id]['tasks'].append(f"Implement: {code_description}")

        # Step 2: Use ChatGPT to generate code
        chatgpt_data = chatgpt({
            'action': 'generate_code',
            'language': 'python',
            'description': code_description
        })
        if not isinstance(chatgpt_data, dict):
            app.logger.error(f"Invalid response from ChatGPT: {chatgpt_data}")
            return jsonify({"status": "Error", "message": "Failed to generate code"}), 500
        if chatgpt_data.get('status') != 'OK':
            app.logger.error(f"ChatGPT error: {chatgpt_data.get('message')}")
            return jsonify({"status": "Error", "message": "Failed to generate code"}), 500
        generated_code = chatgpt_data.get('code')
        if not generated_code:
            app.logger.error("No code generated by ChatGPT")
            return jsonify({"status": "Error", "message": "No code generated by ChatGPT"}), 500

        # Step 3: Use Blackbox AI to optimize the generated code
        try:
            blackbox_data = blackbox_ai({
                'action': 'optimize_code',
                'code': generated_code,
                'optimization_level': 'medium'
            })
            if not isinstance(blackbox_data, dict) or blackbox_data.get('status') != 'OK':
                app.logger.warning(f"Blackbox AI optimization failed: {blackbox_data}")
                optimized_code = generated_code
            else:
                optimized_code = blackbox_data.get('optimized_code', generated_code)
        except Exception as e:
            app.logger.error(f"Error in Blackbox AI optimization: {str(e)}")
            optimized_code = generated_code

        # Step 4: Update project progress
        projects[project_id]['progress'] = min(100, projects[project_id]['progress'] + 10)

        return jsonify({
            "status": "OK",
            "message": "Integrated AI task completed",
            "generated_code": generated_code,
            "optimized_code": optimized_code,
            "project_progress": projects[project_id]['progress'],
            "project_tasks": projects[project_id]['tasks']
        }), 200
    except Exception as e:
        app.logger.error(f"Error in integrate_ai: {str(e)}")
        return jsonify({"status": "Error", "message": "An unexpected error occurred"}), 500

if __name__ == '__main__':
    app.run(debug=True)

def generate_documentation(description, project_id):
    # Use ChatGPT to generate documentation based on the description
    try:
        chatgpt_response = chatgpt({
            'action': 'generate_documentation',
            'description': description
        })

        if not isinstance(chatgpt_response, dict) or chatgpt_response.get('status') != 'OK':
            app.logger.error(f"Invalid response from ChatGPT: {chatgpt_response}")
            return {"status": "Error", "message": "Failed to generate documentation"}, 500

        generated_docs = chatgpt_response.get('documentation', '')
        if not generated_docs:
            app.logger.error("ChatGPT response did not contain documentation")
            return {"status": "Error", "message": "Failed to generate documentation"}, 500

        return {
            "status": "OK",
            "message": "Documentation generated",
            "documentation": {
                "status": "OK",
                "message": "Documentation generated",
                "documentation": generated_docs
            }
        }, 200
    except Exception as e:
        app.logger.error(f"Unexpected error generating documentation: {str(e)}")
        return {"status": "Error", "message": "An unexpected error occurred while generating documentation"}, 500
