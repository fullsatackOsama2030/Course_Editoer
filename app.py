from collections import defaultdict
import time
from flask import Flask, Response, render_template, redirect, url_for, request, flash, jsonify, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_dance.contrib.google import make_google_blueprint, google 
from flask_dance.contrib.github import make_github_blueprint, github
import logging
from model import db, User, Course, reset_database, Message
import json
import httpx
import jwt
from flask_testing import TestCase
import datetime
app = Flask(__name__)
app.secret_key = 'YourSecretKey' 
login_manager = LoginManager()
login_manager.init_app(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SECRET_KEY = 'YourSecretKey' 

google_bp = make_google_blueprint(client_id='YourClientID', client_secret='YourClientSecret', redirect_to='course')
app.register_blueprint(google_bp, url_prefix='/course')

github_bp = make_github_blueprint(client_id='YourClientID', client_secret='YourClientSecret', redirect_to='github_login')
app.register_blueprint(github_bp, url_prefix='/github_login')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_token(user_id):
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=5) 
    payload = {
        'user_id': user_id,
        'exp': expiration_time
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token, expiration_time  

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return 'التوكن منتهي الصلاحية'
    except jwt.InvalidTokenError:
        return 'توكن غير صالح'

def token():
    token = session.get('token')
    if not token:
        return redirect(url_for('login'))

    decoded_payload = verify_token(token)
    if isinstance(decoded_payload, str): 
        flash(decoded_payload)
        return redirect(url_for('login'))

    expiration_time = session.get('token_expiration') 
@app.before_request
def check_admin_token():
    if current_user.is_authenticated and current_user.is_admin and 'token' in session:
        session.pop('token', None)
        session.pop('token_expiration', None)
        return redirect(url_for('home'))



@app.route('/course')
def course():
    return render_template('course.html')

@app.route('/')
@login_required
def home():
    # استرجاع استعلام البحث من شريط البحث
    search_query = request.args.get('q', '').strip()

    # التحقق من التوكن إن لم يكن المستخدم مشرفاً
    if not current_user.is_admin:
        token = session.get('token')
        if not token:
            return redirect(url_for('login'))

        decoded_payload = verify_token(token)
        if isinstance(decoded_payload, str):
            flash(decoded_payload)
            return redirect(url_for('login'))
    else:
        logging.info(f'Admin {current_user.username} accessed home page directly')

    # تنفيذ البحث إن وُجدت كلمة مفتاحية
    if search_query:
        courses = Course.query.filter(
            db.or_(
                Course.title.ilike(f'%{search_query}%'),
                Course.description.ilike(f'%{search_query}%'),
                Course.course_type.ilike(f'%{search_query}%')
            )
        ).all()
    else:
        courses = Course.query.all()

    # تجميع الدورات حسب النوع
    courses_by_type = defaultdict(list)
    for course in courses:
        courses_by_type[course.course_type].append(course)

    # استرجاع الكورسات المميزة
    featured_courses = Course.query.filter_by(is_featured=True).all()
    logging.info(f'Total featured courses retrieved: {len(featured_courses)}')
    logging.info(f'Total courses retrieved: {len(courses)}')

    # استخراج أنواع الدورات الفريدة
    unique_course_types = list(courses_by_type.keys())

    # التحقق إن كانت نتيجة البحث فارغة
    no_results = bool(search_query and not courses)

    # تمرير جميع البيانات إلى القالب
    return render_template(
        'user/index.html',
        username=current_user.username,
        courses_by_type=courses_by_type,
        unique_course_types=unique_course_types,
        is_admin=current_user.is_admin,
        featured_courses=featured_courses,
        search_query=search_query,
        no_results=no_results
    )

@app.route('/user/about')
def about():
    return render_template('user/about.html')

@app.route('/user/Information')
def Information():
    return render_template('user/Information.html')

@app.route('/user/payment/visa')
def visa():
    return render_template('user/payment/visa.html')

@app.route('/user/payment/paypal')
def paypal():
    return render_template('user/payment/paypal.html')


@app.route('/user/login_pass')
def login_pass():
    return render_template('user/login_pass.html')

@app.route('/user/api')
def api():
    all_courses = Course.query.all()
    courses_list = []

    for course in all_courses:
        courses_list.append({
            'id': course.id,
            'title': course.title,
            'description': course.description,
            'image_url': course.image_url,
            'course_type': course.course_type,
            'course_link': course.course_link
        })
    
    json_code = {
        "courses": courses_list
    }
    
    return render_template('user/api.html', json_code=json.dumps(json_code, ensure_ascii=False, indent=4))

@app.route('/stream')
def stream():
    def generate():
        while True:
            all_courses = Course.query.all()
            courses_list = []
            for course in all_courses:
                courses_list.append({
                    'id': course.id,
                    'title': course.title,
                    'description': course.description,
                    'image_url': course.image_url,
                    'course_type': course.course_type,
                    'course_link': course.course_link
                })

            # إرسال البيانات بتنسيق JSON
            yield f"data: {json.dumps({'courses': courses_list}, ensure_ascii=False)}\n\n"
            time.sleep(5) 

    return Response(generate(), content_type='text/event-stream')


@app.route('/user/contantgroup', methods=['GET', 'POST'])
@login_required
def contantgroup():
    if request.method == 'POST':
        message_content = request.form.get('message')
        user_id = current_user.id
        new_message = Message(user_id=user_id, content=message_content)

        db.session.add(new_message)
        db.session.commit()

        return redirect(url_for('contantgroup'))

    messages = Message.query.all() 
    return render_template('user/contantgroup.html', messages=messages)

@app.route('/delete_message/<int:message_id>', methods=['POST'])
@login_required
def delete_message(message_id):
    message = Message.query.get_or_404(message_id)
    if message.user_id == current_user.id:
        db.session.delete(message)
        db.session.commit()
    return redirect(url_for('contantgroup'))

@app.route('/admin/index')
@login_required
def admin():
    return render_template('admin/index.html')


@app.route('/user/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            token, expiration_time = create_token(user.id) 
            session['token'] = token 
            session['token_expiration'] = expiration_time 
            logging.info(f'User {username} logged in successfully.')
            return redirect(url_for('home'))
        else:
            logging.warning(f'Failed login attempt for username: {username}')
            flash('اسم المستخدم أو كلمة المرور غير صحيحة')
            return redirect(url_for('login'))

    return render_template('user/login.html')
@app.route('/user/edit_account', methods=['GET', 'POST'])
@login_required
def edit_account():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        token_expiration = request.form['token_expiration']

        current_user.username = username
        current_user.email = email
       
        db.session.commit()
        
        # flash('تم تحديث الحساب بنجاح!', 'success')
        return redirect(url_for('profile'))

    user_data = {
        'username': current_user.username,
        'email': current_user.email,
        'token_expiration': None 
    }
    
    return render_template('user/edit_account.html', user_data=user_data)


@app.route('/user/profile')
@login_required 
def profile():
    # إذا كان المستخدم مشرفاً، تخطى التحقق من التوكن
    if not current_user.is_admin:
        # التحقق من التوكن للمستخدمين العاديين فقط
        token = session.get('token')
        if not token:
            return redirect(url_for('login'))

        decoded_payload = verify_token(token)
        if isinstance(decoded_payload, str): 
            flash(decoded_payload)
            return redirect(url_for('login'))

        expiration_time = session.get('token_expiration')
        token_expiration_str = expiration_time.strftime('%Y-%m-%d %H:%M:%S') if expiration_time else None
    else:
        token = None
        token_expiration_str = None

    user_data = {
        'username': current_user.username,
        'email': current_user.email,
        'join_date': current_user.created_at, 
        'likes_count': current_user.likes_count,
        'shares_count': current_user.shares_count,
        'token': token,  # سيكون None للمشرفين
        'token_expiration': token_expiration_str  # سيكون None للمشرفين
    }
    
    return render_template('user/profileuserr.html', user_data=user_data)


@app.route('/user/register', methods=['GET', 'POST'])
def register():
    
    message = None
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            message = 'كلمة المرور وتأكيد كلمة المرور غير متطابقتين'
            return render_template('user/register.html', message=message)

        if User.query.filter_by(username=username).first():
            message = 'اسم المستخدم موجود بالفعل'
            return render_template('user/register.html', message=message)

        if User.query.filter_by(email=email).first():
            message = 'البريد الإلكتروني موجود بالفعل'
            return render_template('user/register.html', message=message)

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, email=email)
        db.session.add(new_user)
        db.session.commit()

        logging.info(f'New user registered: {username}')
        return redirect(url_for('login'))

    return render_template('user/register.html', message=message)

class UserRegistrationTest(TestCase):

    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        with app.app_context():
            db.create_all()
        return app

    def tearDown(self):
        db.session.remove()

    def test_register_success(self):
        response = self.client.post('/user/register', data={
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'confirm_password': self.confirm_password
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('تسجيل مستخدم جديد', response.data)

    def test_register_duplicate_username(self):
        self.client.post('/user/register', data={
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'confirm_password': self.confirm_password
        })
        response = self.client.post('/user/register', data={
            'username': self.username,
            'email': 'another@example.com',
            'password': self.password,
            'confirm_password': self.password
        })
        self.assertIn('اسم المستخدم موجود بالفعل', response.data)

    def test_register_duplicate_email(self):
        self.client.post('/user/register', data={
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'confirm_password': self.confirm_password
        })
        response = self.client.post('/user/register', data={
            'username': 'anotheruser',
            'email': self.email,
            'password': self.password,
            'confirm_password': self.password
        })
        self.assertIn('البريد الإلكتروني موجود بالفعل', response.data)

    def test_register_password_mismatch(self):
        response = self.client.post('/user/register', data={
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'confirm_password': 'differentpassword'
        })
        self.assertIn('كلمة المرور وتأكيد كلمة المرور غير متطابقتين', response.data)
@app.route('/admin/add_course', methods=['GET', 'POST'])
def add_course():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        image_url = request.form['image_url']
        course_type = request.form['course_type']
        course_link = request.form['course_link']
        price = request.form.get('price')  # الحصول على سعر الدورة (اختياري)
        is_featured = 'is_featured' in request.form  # تحقق مما إذا تم تحديد الدورة كمميزة

        new_course = Course(
            title=title, 
            description=description, 
            image_url=image_url, 
            course_type=course_type,
            course_link=course_link,
            price=price if price else None,  # احفظ السعر إذا تم إدخاله، وإلا اجعله None
            is_featured=is_featured  # احفظ الحالة المميزة
        )
        db.session.add(new_course)  
        db.session.commit()  

        logging.info(f'New course added: {title} with price: {price}')
        return redirect(url_for('admin_courses')) 
        
    return render_template('admin/add_course.html')

@app.route('/<string:course_link>')
def course_detail(course_link):
    course = Course.query.filter_by(course_link=course_link).first_or_404()
    related_courses = Course.query.filter_by(course_type=course.course_type).filter(Course.course_link != course_link).all()
   
    original_price = course.price
    discounted_price = None
    
    if original_price:
        discounted_price = original_price * 0.8 
    
    return render_template('course_detail.html', 
                         course=course,
                         related_courses=related_courses,
                         original_price=original_price,
                         discounted_price=discounted_price)

@app.route('/admin/users')
def users():
    all_users = User.query.all()
    current_user_count = User.query.count()
    daily_counts = {}
    monthly_counts = {}
    yearly_counts = {}

    for user in all_users:
        date = user.created_at.date()
        month = user.created_at.strftime("%Y-%m")
        year = user.created_at.year

        if date in daily_counts:
            daily_counts[date] += 1
        else:
            daily_counts[date] = 1

        if month in monthly_counts:
            monthly_counts[month] += 1
        else:
            monthly_counts[month] = 1

        if year in yearly_counts:
            yearly_counts[year] += 1
        else:
            yearly_counts[year] = 1

    daily_labels = list(daily_counts.keys())
    daily_values = list(daily_counts.values())

    monthly_labels = list(monthly_counts.keys())
    monthly_values = list(monthly_counts.values())

    yearly_labels = list(yearly_counts.keys())
    yearly_values = list(yearly_counts.values())

    return render_template('admin/users.html', users=all_users, current_user_count=current_user_count, 
                           daily_labels=daily_labels, daily_values=daily_values,
                           monthly_labels=monthly_labels, monthly_values=monthly_values,
                           yearly_labels=yearly_labels, yearly_values=yearly_values)
@app.route('/set_admin/<int:user_id>', methods=['POST'], endpoint='set_admin_endpoint')
def set_admin(user_id):
    user = User.query.get(user_id)
    if user:
        user.is_admin = not user.is_admin 
        db.session.commit()
        flash(f'تم {"تعيين" if user.is_admin else "إلغاء تعيين"} المشرف بنجاح!', 'success')
    else:
        flash('المستخدم غير موجود.', 'error')
    return redirect(url_for('users'))  

@app.route('/admin/users/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        logging.info(f'User {user.username} deleted successfully.')
        return redirect(url_for('users')) 
    else:
        logging.warning(f'Tried to delete a non-existing user with ID: {user_id}.')
        return redirect(url_for('users')) 

@app.route('/admin/users/<int:user_id>/set_admin', methods=['POST'])
def set_admin(user_id):
    user = User.query.get(user_id)
    if user:
        user.is_admin = not user.is_admin
        db.session.commit()
        action = "set as admin" if user.is_admin else "removed from admin"
        logging.info(f'User {user.username} {action} successfully.')
        return redirect(url_for('users'))
    else:
        logging.warning(f'Tried to set a non-existing user as admin with ID: {user_id}.')
        return redirect(url_for('users'))

@app.route('/google_login')
def google_login():
    if not google.authorized:
        return redirect(url_for('google.login'))
    resp = google.get('/plus/v1/people/me')
    assert resp.ok, resp.text
    return f'Welcome, {resp.json()["displayName"]}!'

@app.route('/github_login')
def github_login():
    if not github.authorized:
        return redirect(url_for('github.login'))
    resp = github.get('/user')
    assert resp.ok, resp.text
    return f'Welcome, {resp.json()["login"]}!'

@app.route('/user/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()
    session.pop('token', None) 
    session.pop('token_expiration', None) 
    logging.info(f'User {username} logged out successfully.')
    return redirect(url_for('login'))

@app.route('/admin/admin_courses')
def admin_courses():
    all_courses = Course.query.all()
    return render_template('admin/admin_courses.html', courses=all_courses)

@app.route('/admin/toggle_featured/<int:course_id>', methods=['POST'])
def toggle_featured(course_id):
    course = Course.query.get(course_id)
    if course:
        course.is_featured = not course.is_featured  # قم بتغيير حالة التمييز
        db.session.commit()
    return redirect(url_for('admin_courses'))


@app.route('/like/<int:course_id>', methods=['POST'])
def like_course(course_id):
    course = Course.query.get(course_id)
    if course:
        course.likes += 1 
        current_user.likes_count += 1 
        db.session.commit()
        return jsonify(success=True)
    return jsonify(success=False), 404

@app.route('/admin/admin_courses/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    course = Course.query.get(course_id)
    if course:
        db.session.delete(course)
        db.session.commit()
        logging.info(f'Course {course.title} deleted successfully.')
        return redirect(url_for('admin_courses'))
    else:
        logging.warning(f'Tried to delete a non-existing course with ID: {course_id}.')
        return redirect(url_for('admin_courses'))

API_KEY = 'YourAPIKey' 
API_URL = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={API_KEY}'

async def get_ai_response(user_input):
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": user_input
                    }
                ]
            }
        ]
    }
    headers = {'Content-Type': 'application/json'}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(API_URL, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            response_data = response.json()
            if 'candidates' in response_data and len(response_data['candidates']) > 0:
                content = response_data['candidates'][0].get('content', {})
                parts = content.get('parts', [])
                return parts[0].get('text', "لم أتمكن من الحصول على نص الرد.")
            else:
                return "لم أتمكن من الحصول على رد من الخادم."
    except Exception as e:
        logging.error(f"خطأ: {e}")
        return "حدث خطأ غير متوقع."
    
if __name__ == '__main__':
    reset_database(app)
    app.run(host='0.0.0.0', debug=True, port=5000)