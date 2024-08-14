import unittest
from unittest.mock import patch
from app import app
import json
import os
import requests

class TestAIFusionAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        # Mock environment variables for API keys
        self.env_patcher = patch.dict('os.environ', {
            'CHATGPT_API_KEY': 'mock_chatgpt_key',
            'BLACKBOX_API_KEY': 'mock_blackbox_key'
        })
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    def test_health_check(self):
        response = self.app.get('/')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'OK')
        self.assertEqual(data['message'], 'AI Fusion API is running')

    def test_devin_create_project(self):
        response = self.app.post('/devin', json={
            'action': 'create_project',
            'name': 'Test Project'
        })
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'OK')
        self.assertEqual(data['message'], 'New project created')
        self.assertIn('project_id', data)

    def test_chatgpt_generate_code(self):
        # Test successful code generation
        with patch('app.requests.post') as mock_post:
            mock_post.return_value.json.return_value = {
                'choices': [{'message': {'content': 'print("Hello, World!")'}}]
            }
            response = self.app.post('/chatgpt', json={
                'action': 'generate_code',
                'language': 'python',
                'description': 'Hello World program'
            })
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data['status'], 'OK')
            self.assertEqual(data['message'], 'Generate code completed')
            self.assertIn('content', data)
            self.assertIn('code', data)
            self.assertIsInstance(data['content'], str)
            self.assertIsInstance(data['code'], str)
            self.assertTrue(len(data['content']) > 0)
            self.assertTrue(len(data['code']) > 0)

        # Test invalid action
        response = self.app.post('/chatgpt', json={
            'action': 'invalid_action',
            'language': 'python',
            'description': 'Hello World program'
        })
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['status'], 'Error')
        self.assertEqual(data['message'], 'Invalid action for ChatGPT')

        # Test missing description
        with patch('app.requests.post') as mock_post:
            mock_post.return_value.json.return_value = {
                'choices': [{'message': {'content': 'print("Default code")'}}]
            }
            response = self.app.post('/chatgpt', json={
                'action': 'generate_code',
                'language': 'python'
            })
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data['status'], 'OK')
            self.assertEqual(data['message'], 'Generate code completed')
            self.assertIn('content', data)
            self.assertIn('code', data)

        # Test API key not configured
        with patch('app.CHATGPT_API_KEY', None):
            response = self.app.post('/chatgpt', json={
                'action': 'generate_code',
                'language': 'python',
                'description': 'Hello World program'
            })
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 500)
            self.assertEqual(data['status'], 'Error')
            self.assertEqual(data['message'], 'ChatGPT API key not configured')

        # Test API error
        with patch('app.requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException("API Error")
            response = self.app.post('/chatgpt', json={
                'action': 'generate_code',
                'language': 'python',
                'description': 'Hello World program'
            })
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 500)
            self.assertEqual(data['status'], 'Error')
            self.assertEqual(data['message'], 'An error occurred while processing your request')

    def test_blackbox_search_code(self):
        # Test successful code search
        with patch('app.requests.post') as mock_post:
            mock_post.return_value.json.return_value = {'code': 'def quicksort(arr): pass'}
            response = self.app.post('/blackbox', json={
                'action': 'search_code',
                'query': 'quicksort algorithm',
                'language': 'python'
            })
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data['status'], 'OK')
            self.assertEqual(data['message'], 'Code found')
            self.assertIn('snippet', data)

        # Test no code found
        with patch('app.requests.post') as mock_post:
            mock_post.return_value.json.return_value = {}
            response = self.app.post('/blackbox', json={
                'action': 'search_code',
                'query': 'nonexistent algorithm',
                'language': 'python'
            })
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 404)
            self.assertEqual(data['status'], 'Error')
            self.assertEqual(data['message'], 'No code found')

        # Test API key not configured
        with patch('app.BLACKBOX_API_KEY', None):
            response = self.app.post('/blackbox', json={
                'action': 'search_code',
                'query': 'quicksort algorithm',
                'language': 'python'
            })
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 500)
            self.assertEqual(data['status'], 'Error')
            self.assertEqual(data['message'], 'Blackbox API key not configured')

        # Test invalid action
        response = self.app.post('/blackbox', json={
            'action': 'invalid_action',
            'query': 'quicksort algorithm',
            'language': 'python'
        })
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['status'], 'Error')
        self.assertEqual(data['message'], 'Invalid action for Blackbox AI')

    def test_devin_update_status(self):
        # First, create a project
        create_response = self.app.post('/devin', json={
            'action': 'create_project',
            'name': 'Test Project'
        })
        create_data = json.loads(create_response.data)
        project_id = create_data['project_id']

        # Then, update its status
        update_response = self.app.post('/devin', json={
            'action': 'update_status',
            'project_id': project_id,
            'status': 'In Progress'
        })
        update_data = json.loads(update_response.data)
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_data['status'], 'OK')
        self.assertEqual(update_data['message'], 'Project status updated')

    def test_chatgpt_generate_documentation(self):
        with patch('app.requests.post') as mock_post:
            mock_post.return_value.json.return_value = {
                'choices': [{'message': {'content': 'Sample documentation'}}]
            }
            response = self.app.post('/chatgpt', json={
                'action': 'generate_documentation',
                'description': 'Create a function that prints "Hello, World!"'
            })
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data['status'], 'OK')
            self.assertEqual(data['message'], 'Generate documentation completed')
            self.assertIn('content', data)
            self.assertIn('documentation', data)
            self.assertIsInstance(data['content'], str)
            self.assertIsInstance(data['documentation'], str)
            self.assertTrue(len(data['content']) > 0)
            self.assertTrue(len(data['documentation']) > 0)

    def test_blackbox_optimize_code(self):
        with patch('app.requests.post') as mock_post:
            mock_post.return_value.json.return_value = {
                'status': 'OK',
                'message': 'Code optimized',
                'optimized_code': 'def factorial(n): return 1 if n == 0 else n * factorial(n-1)'
            }
            mock_post.return_value.status_code = 200
            response = self.app.post('/blackbox', json={
                'action': 'optimize_code',
                'code': 'def factorial(n):\n    if n == 0:\n        return 1\n    else:\n        return n * factorial(n-1)',
                'optimization_level': 'high'
            })
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data['status'], 'OK')
            self.assertEqual(data['message'], 'Code optimized')
            self.assertIn('optimized_code', data)
            self.assertEqual(data['optimized_code'], 'def factorial(n): return 1 if n == 0 else n * factorial(n-1)')

    @patch('app.chatgpt')
    @patch('app.blackbox_ai')
    def test_integrate_ai(self, mock_blackbox, mock_chatgpt):
        # Test successful integration
        mock_chatgpt.return_value = {
            'status': 'OK',
            'message': 'Generate code completed',
            'code': 'def factorial(n):\n    return 1 if n == 0 else n * factorial(n-1)'
        }
        mock_blackbox.return_value = {
            'status': 'OK',
            'message': 'Code optimized',
            'optimized_code': 'def factorial(n):\n    return 1 if n == 0 else n * factorial(n-1)'
        }

        create_response = self.app.post('/devin', json={
            'action': 'create_project',
            'name': 'Integration Test Project'
        })
        create_data = json.loads(create_response.data)
        project_id = create_data['project_id']

        response = self.app.post('/integrate', json={
            'project_id': project_id,
            'code_description': 'Create a function to calculate the factorial of a number'
        })
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'OK')
        self.assertEqual(data['message'], 'Integrated AI task completed')
        self.assertIn('generated_code', data)
        self.assertIn('optimized_code', data)
        self.assertIn('project_progress', data)
        self.assertIn('project_tasks', data)
        self.assertIn('Implement: Create a function to calculate the factorial of a number', data['project_tasks'])

        mock_chatgpt.assert_called_once()
        mock_blackbox.assert_called_once()

        # Test ChatGPT error handling
        mock_chatgpt.reset_mock()
        mock_chatgpt.return_value = {'status': 'Error', 'message': 'Failed to generate code'}

        response = self.app.post('/integrate', json={
            'project_id': project_id,
            'code_description': 'Test ChatGPT error'
        })
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(data['status'], 'Error')
        self.assertEqual(data['message'], 'Failed to generate code')

        # Test Blackbox AI error handling
        mock_chatgpt.reset_mock()
        mock_blackbox.reset_mock()
        mock_chatgpt.return_value = {
            'status': 'OK',
            'message': 'Generate code completed',
            'code': 'def test(): pass'
        }
        mock_blackbox.side_effect = Exception("Blackbox AI error")

        response = self.app.post('/integrate', json={
            'project_id': project_id,
            'code_description': 'Test Blackbox AI error'
        })
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'OK')
        self.assertEqual(data['message'], 'Integrated AI task completed')
        self.assertEqual(data['generated_code'], data['optimized_code'])

        # Test invalid project ID
        response = self.app.post('/integrate', json={
            'project_id': 'invalid_id',
            'code_description': 'Test invalid project ID'
        })
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['status'], 'Error')
        self.assertEqual(data['message'], 'Project not found')

if __name__ == '__main__':
    unittest.main()

    def test_chatgpt_api_error(self):
        # Test ChatGPT API error handling
        with patch('app.requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException("API Error")
            response = self.app.post('/chatgpt', json={
                'action': 'generate_code',
                'language': 'python',
                'description': 'Test error handling'
            })
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 500)
            self.assertEqual(data['status'], 'Error')
            self.assertEqual(data['message'], 'An error occurred while processing your request')
            self.assertNotIn('error_details', data)  # We don't expose internal error details

        # Test unexpected error
        with patch('app.requests.post') as mock_post:
            mock_post.side_effect = Exception("Unexpected error")
            response = self.app.post('/chatgpt', json={
                'action': 'generate_code',
                'language': 'python',
                'description': 'Test unexpected error'
            })
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 500)
            self.assertEqual(data['status'], 'Error')
            self.assertEqual(data['message'], 'An unexpected error occurred')
            self.assertNotIn('error_details', data)

def test_blackbox_api_error(self):
    # Test Blackbox AI API error handling
    with patch('app.BLACKBOX_API_KEY', None):
        response = self.app.post('/blackbox', json={
            'action': 'search_code',
            'query': 'Test error handling',
            'language': 'python'
        })
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(data['status'], 'Error')
        self.assertEqual(data['message'], 'Blackbox API key not configured')

    with patch('app.requests.post') as mock_post:
        mock_post.side_effect = requests.exceptions.RequestException("API Error")
        response = self.app.post('/blackbox', json={
            'action': 'search_code',
            'query': 'Test error handling',
            'language': 'python'
        })
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(data['status'], 'Error')
        self.assertEqual(data['message'], 'An error occurred while processing your request')

    # Test rate limit error
    with patch('app.requests.post') as mock_post:
        mock_post.side_effect = requests.exceptions.HTTPError(response=mock_post.return_value)
        mock_post.return_value.status_code = 429
        response = self.app.post('/blackbox', json={
            'action': 'search_code',
            'query': 'Test rate limit',
            'language': 'python'
        })
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(data['status'], 'Error')
        self.assertEqual(data['message'], 'API rate limit exceeded. Please try again later.')

    # Test invalid action
    response = self.app.post('/blackbox', json={
        'action': 'invalid_action',
        'query': 'Test invalid action',
        'language': 'python'
    })
    data = json.loads(response.data)
    self.assertEqual(response.status_code, 400)
    self.assertEqual(data['status'], 'Error')
    self.assertEqual(data['message'], 'Invalid action for Blackbox AI')

    # Test unexpected error
    with patch('app.requests.post') as mock_post:
        mock_post.side_effect = Exception("Unexpected error")
        response = self.app.post('/blackbox', json={
            'action': 'search_code',
            'query': 'Test unexpected error',
            'language': 'python'
        })
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(data['status'], 'Error')
        self.assertEqual(data['message'], 'An unexpected error occurred')

    # Test optimize_code action
    with patch('app.requests.post') as mock_post:
        mock_post.return_value.json.return_value = {'optimized_code': 'optimized code'}
        response = self.app.post('/blackbox', json={
            'action': 'optimize_code',
            'code': 'def test(): pass',
            'optimization_level': 'medium'
        })
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'OK')
        self.assertEqual(data['message'], 'Code optimized')
        self.assertIn('optimized_code', data)

    # Test analyze_complexity action
    with patch('app.requests.post') as mock_post:
        mock_post.return_value.json.return_value = {'analysis': 'complexity analysis'}
        response = self.app.post('/blackbox', json={
            'action': 'analyze_complexity',
            'code': 'def test(): pass'
        })
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'OK')
        self.assertEqual(data['message'], 'Code analyzed')
        self.assertIn('analysis', data)

def test_invalid_project_id(self):
    # Test handling of invalid project ID
    response = self.app.post('/integrate', json={
        'project_id': 'invalid_id',
        'code_description': 'Test invalid project ID'
    })
    data = json.loads(response.data)
    self.assertEqual(response.status_code, 404)
    self.assertEqual(data['status'], 'Error')
    self.assertEqual(data['message'], 'Project not found')

def test_interpret_command(self):
    # Test the interpret_command action in Devin AI
    create_response = self.app.post('/devin', json={
        'action': 'create_project',
        'name': 'Test Project'
    })
    create_data = json.loads(create_response.data)
    project_id = create_data['project_id']

    with patch('app.chatgpt') as mock_chatgpt:
        mock_chatgpt.return_value = {
            'status': 'OK',
            'message': 'Command interpreted',
            'interpretation': 'Add task: Implement user authentication'
        }
        response = self.app.post('/devin', json={
            'action': 'interpret_command',
            'project_id': project_id,
            'command': 'Add a new task to implement user authentication'
        })
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'OK')
        self.assertEqual(data['message'], 'Command interpreted')
        self.assertIn('action', data)
        self.assertEqual(data['action']['interpretation'], 'Add task: Implement user authentication')

    # Test with invalid project_id
    response = self.app.post('/devin', json={
        'action': 'interpret_command',
        'project_id': 'invalid_id',
        'command': 'Add a new task'
    })
    data = json.loads(response.data)
    self.assertEqual(response.status_code, 404)
    self.assertEqual(data['status'], 'Error')
    self.assertEqual(data['message'], 'Project not found')

def test_generate_documentation(self):
    # Test the generate_documentation action in Devin AI
    create_response = self.app.post('/devin', json={
        'action': 'create_project',
        'name': 'Documentation Test Project'
    })
    create_data = json.loads(create_response.data)
    project_id = create_data['project_id']

    with patch('app.chatgpt') as mock_chatgpt:
        mock_chatgpt.return_value = {
            'status': 'OK',
            'message': 'Generate documentation completed',
            'documentation': 'Sample documentation for user authentication system'
        }

        response = self.app.post('/devin', json={
            'action': 'generate_documentation',
            'project_id': project_id,
            'description': 'Create documentation for a user authentication system'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'OK')
        self.assertEqual(data['message'], 'Documentation generated')
        self.assertIn('documentation', data)
        self.assertIsInstance(data['documentation'], dict)
        self.assertEqual(data['documentation']['status'], 'OK')
        self.assertEqual(data['documentation']['message'], 'Documentation generated')
        self.assertIsInstance(data['documentation']['documentation'], str)
        self.assertTrue(len(data['documentation']['documentation']) > 0)

    # Test with invalid project ID
    invalid_response = self.app.post('/devin', json={
        'action': 'generate_documentation',
        'project_id': 'invalid_id',
        'description': 'This should fail'
    })
    invalid_data = json.loads(invalid_response.data)
    self.assertEqual(invalid_response.status_code, 404)
    self.assertEqual(invalid_data['status'], 'Error')
    self.assertEqual(invalid_data['message'], 'Project not found')

    # Test error handling in generate_documentation
    with patch('app.chatgpt') as mock_chatgpt:
        mock_chatgpt.return_value = {'status': 'Error', 'message': 'Failed to generate documentation'}
        error_response = self.app.post('/devin', json={
            'action': 'generate_documentation',
            'project_id': project_id,
            'description': 'This should trigger an error'
        })
        error_data = json.loads(error_response.data)
        self.assertEqual(error_response.status_code, 500)
        self.assertEqual(error_data['status'], 'Error')
        self.assertEqual(error_data['message'], 'Failed to generate documentation')
