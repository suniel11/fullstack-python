import os
from flask import Flask, request, redirect, url_for, render_template, flash
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Get MongoDB URI from environment variable
Mongo_uri = os.getenv('Mongo_uri')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.secret_key = os.getenv('SECRET_KEY', 'mysecretkey')

client = MongoClient(Mongo_uri)
db = client.users_data
users_collection = db.users
professors_collection = db.professors
announcements_collection = db.announcements  # New collection for announcements

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class Professor(UserMixin):
    def __init__(self, professor_id, username, password):
        self.id = professor_id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(professor_id):
    professor = professors_collection.find_one({'_id': ObjectId(professor_id)})
    if professor:
        return Professor(str(professor['_id']), professor['username'], professor['password'])
    return None

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        subjects = request.form.getlist('subjects')
        if professors_collection.find_one({'username': username}):
            flash('Username already exists')
            return redirect(url_for('register'))
        professor_id = professors_collection.insert_one({'username': username, 'password': password, 'subjects': subjects}).inserted_id
        login_user(Professor(str(professor_id), username, password))
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        professor = professors_collection.find_one({'username': username})
        if professor and professor['password'] == password:
            login_user(Professor(str(professor['_id']), username, password))
            return redirect(url_for('home'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return redirect(url_for('register'))

@app.route('/home')
@login_required
def home():
    announcements = list(announcements_collection.find().sort('timestamp', -1))
    for announcement in announcements:
        professor = professors_collection.find_one({'_id': announcement['professor_id']})
        announcement['username'] = professor['username']
        announcement['time'] = announcement.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')
    return render_template('home.html', announcements=announcements)

@app.route('/profile')
@login_required
def profile():
    professor = professors_collection.find_one({'_id': ObjectId(current_user.id)})
    students = list(users_collection.find({'professor_id': ObjectId(current_user.id)}))
    return render_template('profile.html', professor=professor, students=students)

@app.route('/profile/<subject>')
@login_required
def profile_subject(subject):
    professor = professors_collection.find_one({'_id': ObjectId(current_user.id)})
    students = list(users_collection.find({'professor_id': ObjectId(current_user.id), 'subject': subject}))
    return render_template('profile_subject.html', professor=professor, students=students, subject=subject)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    professor = professors_collection.find_one({'_id': ObjectId(current_user.id)})
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        professors_collection.update_one(
            {'_id': ObjectId(current_user.id)},
            {'$set': {'username': username, 'password': password}}
        )
        flash('Profile updated successfully')
        return redirect(url_for('profile'))
    return render_template('edit_profile.html', professor=professor)

@app.route('/edit_student/<student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    student = users_collection.find_one({'_id': ObjectId(student_id)})
    if request.method == 'POST':
        name = request.form['name']
        dob = request.form['dob']
        course = request.form['course']
        semester = request.form['semester']
        cgpa = request.form['cgpa']
        subject = request.form['subject']
        users_collection.update_one(
            {'_id': ObjectId(student_id)},
            {'$set': {'name': name, 'dob': dob, 'course': course, 'semester': semester, 'cgpa': cgpa, 'subject': subject}}
        )
        flash('Student information updated successfully')
        return redirect(url_for('profile'))
    return render_template('edit_student.html', student=student)

@app.route('/add_grade/<student_id>', methods=['GET', 'POST'])
@login_required
def add_grade(student_id):
    student = users_collection.find_one({'_id': ObjectId(student_id)})
    if request.method == 'POST':
        subject = request.form['subject']
        grade = request.form['grade']
        users_collection.update_one(
            {'_id': ObjectId(student_id)},
            {'$push': {'grades': {'subject': subject, 'grade': grade}}}
        )
        flash('Grade added successfully')
        return redirect(url_for('user_detail', user_id=student_id))
    return render_template('add_grade.html', student=student)

@app.route('/user/<user_id>')
@login_required
def user_detail(user_id):
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    return render_template('user_detail.html', user=user)

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if request.method == 'POST':
        name = request.form['name']
        dob = request.form['dob']
        course = request.form['course']
        semester = request.form['semester']
        cgpa = request.form['cgpa']
        subject = request.form['subject']
        picture = request.files.get('picture')

        filename = None
        if picture and allowed_file(picture.filename):
            filename = secure_filename(picture.filename)
            picture_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            picture.save(picture_path)

        user = {
            'name': name,
            'dob': dob,
            'course': course,
            'semester': semester,
            'cgpa': cgpa,
            'subject': subject,
            'picture': filename,
            'professor_id': ObjectId(current_user.id),
            'grades': []
        }

        # Insert user into the MongoDB database
        users_collection.insert_one(user)

        return redirect(url_for('profile'))

    professor = professors_collection.find_one({'_id': ObjectId(current_user.id)})
    subjects = professor.get('subjects', [])
    return render_template('add_user.html', subjects=subjects)

@app.route('/user_list')
@login_required
def user_list():
    # Fetch users from the MongoDB database
    users = list(users_collection.find())
    return render_template('user_list.html', users=users)

@app.route('/delete_user/<user_id>', methods=['GET', 'POST'])
@login_required
def delete_user(user_id):
    if request.method == 'POST':
        users_collection.delete_one({'_id': ObjectId(user_id)})
        return redirect(url_for('user_list'))
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    return render_template('delete_user.html', user=user)

@app.route('/add_announcement', methods=['GET', 'POST'])
@login_required
def add_announcement():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        announcement = {
            'title': title,
            'content': content,
            'professor_id': ObjectId(current_user.id),
            'timestamp': datetime.now()
        }
        announcements_collection.insert_one(announcement)
        flash('Announcement added successfully')
        return redirect(url_for('profile'))
    return render_template('add_announcement.html')

@app.route('/announcements')
@login_required
def announcements():
    announcements = list(announcements_collection.find({'professor_id': ObjectId(current_user.id)}))
    return render_template('announcements.html', announcements=announcements)

@app.route('/students')
@login_required
def students():
    students = list(users_collection.find({'professor_id': ObjectId(current_user.id)}))
    return render_template('students.html', students=students)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

if __name__ == '__main__':
    app.run(debug=True)