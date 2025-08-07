import unittest
from flask import url_for, session
from werkzeug.security import generate_password_hash
import jwt
import datetime
from unittest.mock import patch, MagicMock
import time
import pytest
from locust import HttpUser, task, between
import multiprocessing
from app import app, db, User, Course, Message, create_token, verify_token, get_ai_response

class TestFlaskApp(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        
        with app.app_context():
            db.create_all()
            self.add_test_data()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def add_test_data(self):
        # Add test user
        hashed_pass = generate_password_hash('testpass')
        user = User(username='testuser', email='test@example.com', password=hashed_pass)
        db.session.add(user)
        
        # Add test admin
        admin_pass = generate_password_hash('adminpass')
        admin = User(username='admin', email='admin@example.com', password=admin_pass, is_admin=True)
        db.session.add(admin)
        
        # Add test course
        course = Course(title='Python Course', description='Learn Python', 
                       image_url='python.jpg', course_type='programming', 
                       course_link='python-course')
        db.session.add(course)
        
        # Add test message
        message = Message(user_id=1, content='Test message')
        db.session.add(message)
        
        db.session.commit()

    def login(self, username, password):
        return self.app.post('/user/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)

    def logout(self):
        return self.app.get('/user/logout', follow_redirects=True)

    ####################################
    # 1. الاختبارات الوحدوية (Unit Tests)
    ####################################
    
    def test_token_creation_and_verification(self):
        """اختبار وحدات صغيرة (الدوال)"""
        # Test create_token
        token, exp = create_token(1)
        self.assertIsInstance(token, str)
        self.assertIsInstance(exp, datetime.datetime)
        
        # Test verify_token with valid token
        payload = verify_token(token)
        self.assertEqual(payload['user_id'], 1)
        
        # Test verify_token with expired token
        old_payload = {'user_id': 1, 'exp': datetime.datetime.utcnow() - datetime.timedelta(hours=1)}
        old_token = jwt.encode(old_payload, app.secret_key, algorithm='HS256')
        result = verify_token(old_token)
        self.assertEqual(result, 'التوكن منتهي الصلاحية')
        
        # Test verify_token with invalid token
        result = verify_token('invalidtoken')
        self.assertEqual(result, 'توكن غير صالح')

    @patch('app.httpx.AsyncClient')
    def test_ai_response_function(self, mock_client):
        """اختبار وحدة الذكاء الاصطناعي باستخدام mock"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": "Mocked AI Response"
                    }]
                }
            }]
        }
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Test the function
        import asyncio
        response = asyncio.run(get_ai_response("test input"))
        self.assertEqual(response, "Mocked AI Response")

    ####################################
    # 2. اختبارات التكامل (Integration Tests)
    ####################################
    
    def test_user_registration_flow(self):
        """اختبار تكامل سير عمل تسجيل المستخدم"""
        # Registration
        response = self.app.post('/user/register', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass',
            'confirm_password': 'newpass'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Login with new credentials
        response = self.login('newuser', 'newpass')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'newuser', response.data)
        
        # Access profile
        response = self.app.get('/user/profile', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'newuser', response.data)

    def test_course_management_flow(self):
        """اختبار تكامل إدارة الكورسات"""
        self.login('admin', 'adminpass')
        
        # Add course
        response = self.app.post('/admin/add_course', data={
            'title': 'New Course',
            'description': 'New Description',
            'image_url': 'new.jpg',
            'course_type': 'design',
            'course_link': 'new-course'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # View course
        response = self.app.get('/new-course')
        self.assertEqual(response.status_code, 200)
        
        # Like course (API integration)
        course = Course.query.filter_by(title='New Course').first()
        response = self.app.post(f'/like/{course.id}')
        self.assertEqual(response.status_code, 200)
        
        # Delete course
        response = self.app.post(f'/admin/admin_courses/{course.id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    ####################################
    # 3. اختبارات النظام (System Tests)
    ####################################
    
    def test_full_application_flow(self):
        """اختبار النظام ككل من البداية للنهاية"""
        # Home page
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Register
        response = self.app.post('/user/register', data={
            'username': 'enduser',
            'email': 'end@example.com',
            'password': 'endpass',
            'confirm_password': 'endpass'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Login
        response = self.login('enduser', 'endpass')
        self.assertEqual(response.status_code, 200)
        
        # View courses
        response = self.app.get('/courses')
        self.assertEqual(response.status_code, 200)
        
        # Send message
        response = self.app.post('/user/contantgroup', data={
            'message': 'System test message'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Logout
        response = self.logout()
        self.assertEqual(response.status_code, 200)

    ####################################
    # 4. اختبارات القبول (Acceptance Tests)
    ####################################
    
    def test_business_requirements(self):
        """اختبار متطلبات العمل الأساسية"""
        # Requirement: Users can register
        response = self.app.post('/user/register', data={
            'username': 'acceptuser',
            'email': 'accept@example.com',
            'password': 'acceptpass',
            'confirm_password': 'acceptpass'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Requirement: Users can login
        response = self.login('acceptuser', 'acceptpass')
        self.assertEqual(response.status_code, 200)
        
        # Requirement: Admins can manage courses
        self.login('admin', 'adminpass')
        course = Course.query.first()
        response = self.app.get(f'/{course.course_link}')
        self.assertEqual(response.status_code, 200)
        
        # Requirement: Users can interact with AI
        with patch('app.httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "candidates": [{
                    "content": {
                        "parts": [{
                            "text": "AI Response"
                        }]
                    }
                }]
            }
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            import asyncio
            response = asyncio.run(get_ai_response("test input"))
            self.assertEqual(response, "AI Response")

    ####################################
    # 5. اختبارات الأداء (Performance Tests)
    ####################################
    
    @pytest.mark.performance
    def test_response_time(self):
        """قياس زمن استجابة الصفحات الرئيسية"""
        start_time = time.time()
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        end_time = time.time()
        self.assertLess(end_time - start_time, 0.5)  # يجب أن يكون أقل من 500ms
        
        start_time = time.time()
        self.login('testuser', 'testpass')
        end_time = time.time()
        self.assertLess(end_time - start_time, 1.0)  # يجب أن يكون أقل من 1 ثانية

    ####################################
    # 6. اختبارات الحمل (Load Tests)
    ####################################
    
    class WebsiteUser(HttpUser):
        """اختبار الحمل باستخدام Locust"""
        wait_time = between(1, 5)
        
        @task
        def load_test_homepage(self):
            self.client.get("/")
            
        @task(3)
        def load_test_login(self):
            self.client.post("/user/login", data={
                "username": "testuser",
                "password": "testpass"
            })
            
        @task(2)
        def load_test_courses(self):
            self.client.get("/courses")

    def run_load_test(self):
        """تشغيل اختبار الحمل في عملية منفصلة"""
        from locust.main import main
        import sys
        sys.argv = ['locust', '-f', __file__, '--headless', '-u', '100', '-r', '10', '--run-time', '1m']
        main()

    ####################################
    # 7. اختبارات الأمان (Security Tests)
    ####################################
    
    def test_security_measures(self):
        """اختبارات الأمان الأساسية"""
        # SQL Injection attempt
        response = self.app.post('/user/login', data={
            'username': "' OR '1'='1",
            'password': "' OR '1'='1"
        }, follow_redirects=True)
        self.assertNotIn(b'testuser', response.data)
        
        # XSS attempt
        response = self.app.post('/user/register', data={
            'username': '<script>alert(1)</script>',
            'email': 'xss@example.com',
            'password': 'xsspass',
            'confirm_password': 'xsspass'
        }, follow_redirects=True)
        self.assertNotIn(b'<script>', response.data)
        
        # CSRF protection (should be disabled in testing)
        response = self.app.post('/user/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    ####################################
    # 8. اختبارات التراجع (Regression Tests)
    ####################################
    
    def test_regression_after_changes(self):
        """اختبار التراجع للتأكد من أن التغييرات الجديدة لم تكسر الوظائف القديمة"""
        # Test old registration still works
        response = self.app.post('/user/register', data={
            'username': 'regressionuser',
            'email': 'regression@example.com',
            'password': 'regressionpass',
            'confirm_password': 'regressionpass'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Test old login still works
        response = self.login('testuser', 'testpass')
        self.assertEqual(response.status_code, 200)
        
        # Test old course viewing still works
        course = Course.query.first()
        response = self.app.get(f'/{course.course_link}')
        self.assertEqual(response.status_code, 200)

    # باقي الاختبارات الموجودة سابقاً
    def test_user_login_logout(self):
        # Successful login
        response = self.login('testuser', 'testpass')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'testuser', response.data)
        
        # Check session token was set
        self.assertIsNotNone(session.get('token'))
        
        # Logout
        response = self.logout()
        self.assertEqual(response.status_code, 200)
        self.assertIn('زائر', response.data)
        self.assertIsNone(session.get('token'))

    def test_course_operations(self):
        self.login('admin', 'adminpass')
        
        # Add new course
        response = self.app.post('/admin/add_course', data={
            'title': 'New Course',
            'description': 'New Description',
            'image_url': 'new.jpg',
            'course_type': 'design',
            'course_link': 'new-course'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'New Course', response.data)
        
        # View course detail
        response = self.app.get('/new-course')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'New Description', response.data)
        
        # Delete course
        course = Course.query.filter_by(title='New Course').first()
        response = self.app.post(f'/admin/admin_courses/{course.id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'New Course', response.data)

    def test_message_operations(self):
        self.login('testuser', 'testpass')
        
        # Send new message
        response = self.app.post('/user/contantgroup', data={
            'message': 'Hello World'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Hello World', response.data)
        
        # Delete message
        message = Message.query.filter_by(content='Hello World').first()
        response = self.app.post(f'/delete_message/{message.id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'Hello World', response.data)

    def test_admin_functions(self):
        self.login('admin', 'adminpass')
        
        # User management
        response = self.app.get('/admin/users')
        self.assertEqual(response.status_code, 200)
        
        # Set admin privilege
        user = User.query.filter_by(username='testuser').first()
        response = self.app.post(f'/admin/users/{user.id}/set_admin', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        updated_user = User.query.get(user.id)
        self.assertTrue(updated_user.is_admin)
        
        # Delete user
        response = self.app.post(f'/admin/users/{user.id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(User.query.get(user.id))

    def test_like_course_api(self):
        self.login('testuser', 'testpass')
        course = Course.query.first()
        
        response = self.app.post(f'/like/{course.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['success'], True)
        
        # Verify like count increased
        updated_course = Course.query.get(course.id)
        self.assertEqual(updated_course.likes, 1)

    def test_protected_routes(self):
        # Try to access profile without login
        response = self.app.get('/user/profile', follow_redirects=True)
        self.assertIn(b'login', response.data)
        
        # Try to access admin page as regular user
        self.login('testuser', 'testpass')
        response = self.app.get('/admin/index')
        self.assertEqual(response.status_code, 403)

if __name__ == '__main__':
    # تشغيل اختبارات unittest العادية
    unittest.main()
    
    # لتشغيل اختبارات الأداء (يتطلب pytest)
    # pytest.main([__file__])
    
    # لتشغيل اختبارات الحمل (يتطلب locust)
    # TestFlaskApp().run_load_test()