from model import db, User, Course, Message
from werkzeug.security import generate_password_hash
import logging

def get_all_courses():
    return Course.query.all()

def get_courses_by_type(all_courses):
    courses_by_type = {}
    for course in all_courses:
        if course.course_type not in courses_by_type:
            courses_by_type[course.course_type] = []
        courses_by_type[course.course_type].append(course)
    return courses_by_type

def add_message(user_id, message_content):
    new_message = Message(user_id=user_id, content=message_content)
    db.session.add(new_message)
    db.session.commit()

def delete_message(message_id):
    message = Message.query.get(message_id)
    if message:
        db.session.delete(message)
        db.session.commit()

def register_user(username, email, password):
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password, email=email)
    db.session.add(new_user)
    db.session.commit()
    logging.info(f'New user registered: {username}')

def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        logging.info(f'User {user.username} deleted successfully.')

def add_course(title, description, image_url, course_type):
    new_course = Course(title=title, description=description, image_url=image_url, course_type=course_type)
    db.session.add(new_course)
    db.session.commit()
    logging.info(f'New course added: {title}')