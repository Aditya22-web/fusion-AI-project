import unittest
from app import app
import json

class TestAIFusionAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

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
        response = self.app.post('/chatgpt', json={
            'action': 'generate_code',
            'language': 'python',
            'description': 'Hello World program'
        })
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'OK')
        self.assertEqual(data['message'], 'Code generated')
        self.assertIn('code', data)

    def test_blackbox_search_code(self):
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
        response = self.app.post('/chatgpt', json={
            'action': 'generate_documentation',
            'code': 'def hello_world():\n    print("Hello, World!")'
        })
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'OK')
        self.assertEqual(data['message'], 'Documentation generated')
        self.assertIn('documentation', data)

    def test_blackbox_optimize_code(self):
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

    def test_integrate_ai(self):
        # First, create a project
        create_response = self.app.post('/devin', json={
            'action': 'create_project',
            'name': 'Integration Test Project'
        })
        create_data = json.loads(create_response.data)
        project_id = create_data['project_id']

        # Then, test the integrate endpoint
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

if __name__ == '__main__':
    unittest.main()
