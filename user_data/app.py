import os
from flask import Flask, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson.objectid import ObjectId


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

client = MongoClient("mongodb+srv://sunil:Suniel07@cluster0.ebv5vfe.mongodb.net/users_data")
db = client.users_data
users_collection = db.users

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/user/<user_id>')
def user_detail(user_id):
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    return render_template('user_detail.html', user=user)


@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        name = request.form['name']
        dob = request.form['dob']
        course = request.form['course']
        semester = request.form['semester']
        cgpa = request.form['cgpa']
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
            'picture': filename

        }

        # Insert user into the MongoDB database
        users_collection.insert_one(user)

        return redirect(url_for('user_list'))

    return render_template('add_user.html')

@app.route('/user_list')
def user_list():
    # Fetch users from the MongoDB database
    users = list(users_collection.find())
    return render_template('user_list.html', users=users)

@app.route('/delete_user/<user_id>', methods=['GET', 'POST'])
def delete_user(user_id):
    if request.method == 'POST':
        users_collection.delete_one({'_id': ObjectId(user_id)})
        return redirect(url_for('user_list'))
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    return render_template('delete_user.html', user=user)



if __name__ == '__main__':
    app.run(debug=True)