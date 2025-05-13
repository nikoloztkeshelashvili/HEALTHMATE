from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///healthmate.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(6), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    surname = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    height = db.Column(db.Float, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    goal_weight = db.Column(db.Float, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    weight_records = db.relationship('WeightRecord', backref='student', lazy=True)


class Instructor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    surname = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    students = db.relationship('StudentInstructor', backref='instructor', lazy=True)


class WeightRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    weight = db.Column(db.Float, nullable=False)
    bmi = db.Column(db.Float, nullable=False)
    bmr = db.Column(db.Float, nullable=False)


class StudentInstructor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('instructor.id'), nullable=False)


def generate_unique_id():
    while True:
        unique_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Student.query.filter_by(unique_id=unique_id).first():
            return unique_id


def calculate_bmi(weight, height):
    height_m = height / 100
    return round(weight / (height_m * height_m), 2)


def calculate_bmr(gender, weight, height, age):
    if gender.lower() == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    return round(bmr, 0)


def calculate_age(birth_date):
    today = date.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register_student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        birth_date = datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date()

        if birth_date > date.today():
            flash('Birth date cannot be in the future!', 'error')
            return redirect(url_for('register_student'))


        height = float(request.form['height'])
        weight = float(request.form['weight'])
        gender = request.form['gender']
        goal_weight = float(request.form['goal_weight'])
        password = request.form['password']

        if Student.query.filter_by(email=email).first() or Instructor.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('register_student'))

        unique_id = generate_unique_id()

        student = Student(
            unique_id=unique_id,
            email=email,
            name=name,
            surname=surname,
            birth_date=birth_date,
            height=height,
            weight=weight,
            gender=gender,
            goal_weight=goal_weight,
            password=password
        )

        db.session.add(student)
        db.session.commit()

        age = calculate_age(birth_date)
        bmi = calculate_bmi(weight, height)
        bmr = calculate_bmr(gender, weight, height, age)

        weight_record = WeightRecord(
            student_id=student.id,
            weight=weight,
            bmi=bmi,
            bmr=bmr
        )

        db.session.add(weight_record)
        db.session.commit()

        flash(f'Registration successful! Your unique ID is: {unique_id}', 'success')
        return redirect(url_for('home'))

    return render_template('register_student.html')


@app.route('/register_instructor', methods=['GET', 'POST'])
def register_instructor():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        password = request.form['password']
        email = request.form['email']

        if Instructor.query.filter_by(email=email).first() or Student.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('register_instructor'))

        instructor = Instructor(
            email=email,
            name=name,
            surname=surname,
            password=password
        )

        db.session.add(instructor)
        db.session.commit()

        flash('Registration successful!', 'success')
        return redirect(url_for('home'))

    return render_template('register_instructor.html')


@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    student = Student.query.filter_by(email=email, password=password).first()
    if student:
        session['student_id'] = student.id
        return redirect(url_for('student_dashboard'))

    instructor = Instructor.query.filter_by(email=email, password=password).first()
    if instructor:
        session['instructor_id'] = instructor.id
        return redirect(url_for('instructor_dashboard'))

    flash('Invalid email or password!', 'error')
    return redirect(url_for('home'))


@app.route('/student_dashboard', methods=['GET', 'POST'])
def student_dashboard():
    if 'student_id' not in session:
        return redirect(url_for('home'))

    student = Student.query.get(session['student_id'])

    if request.method == 'POST':
        weight = float(request.form['weight'])
        age = calculate_age(student.birth_date)
        bmi = calculate_bmi(weight, student.height)
        bmr = calculate_bmr(student.gender, weight, student.height, age)

        weight_record = WeightRecord(
            student_id=student.id,
            weight=weight,
            bmi=bmi,
            bmr=bmr
        )

        db.session.add(weight_record)
        db.session.commit()

        flash('Weight record added successfully!', 'success')
        return redirect(url_for('student_dashboard'))

    weight_records = WeightRecord.query.filter_by(student_id=student.id).all()

    return render_template('student_dashboard.html', student=student, weight_records=weight_records)


@app.route('/update_student_profile', methods=['GET', 'POST'])
def update_student_profile():
    if 'student_id' not in session:
        return redirect(url_for('home'))

    student = Student.query.get(session['student_id'])

    if request.method == 'POST':
        if 'height' in request.form:
            student.height = float(request.form['height'])
        if 'goal_weight' in request.form:
            student.goal_weight = float(request.form['goal_weight'])

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('student_dashboard'))

    return render_template('update_student_profile.html', student=student)


@app.route('/instructor_dashboard')
def instructor_dashboard():
    if 'instructor_id' not in session:
        return redirect(url_for('home'))

    return redirect(url_for('instructor_students'))


@app.route('/bmi_calculator', methods=['GET', 'POST'])
def bmi_calculator():
    if 'instructor_id' not in session:
        return redirect(url_for('home'))

    instructor = Instructor.query.get(session['instructor_id'])
    bmi_result = None
    height = None

    if request.method == 'POST':
        weight = float(request.form['weight'])
        height = float(request.form['height'])
        bmi_result = calculate_bmi(weight, height)

    return render_template('bmi_calculator.html', instructor=instructor, bmi_result=bmi_result, height=height)


@app.route('/bmr_calculator', methods=['GET', 'POST'])
def bmr_calculator():
    if 'instructor_id' not in session:
        return redirect(url_for('login_instructor'))

    instructor = Instructor.query.get(session['instructor_id'])
    bmr_result = None
    activity_factor = None

    if request.method == 'POST':
        gender = request.form['gender']
        weight = float(request.form['weight'])
        height = float(request.form['height'])
        age = int(request.form['age'])
        activity_factor = float(request.form['activity_level'])
        bmr_result = calculate_bmr(gender, weight, height, age)

    return render_template('bmr_calculator.html', instructor=instructor, bmr_result=bmr_result,
                           activity_factor=activity_factor)


@app.route('/instructor_students', methods=['GET', 'POST'])
def instructor_students():
    if 'instructor_id' not in session:
        return redirect(url_for('home'))

    instructor = Instructor.query.get(session['instructor_id'])

    if request.method == 'POST':
        student_id = request.form['student_id']
        student = Student.query.filter_by(unique_id=student_id).first()

        if student:
            existing_relation = StudentInstructor.query.filter_by(
                student_id=student.id,
                instructor_id=instructor.id
            ).first()

            if not existing_relation:
                relation = StudentInstructor(student_id=student.id, instructor_id=instructor.id)
                db.session.add(relation)
                db.session.commit()
                flash('Student added successfully!', 'success')
            else:
                flash('Student already in your list!', 'info')
        else:
            flash('Student not found!', 'error')

    students = db.session.query(Student).join(StudentInstructor).filter(
        StudentInstructor.instructor_id == instructor.id
    ).all()

    return render_template('instructor_dashboard.html', students=students, instructor=instructor)


@app.route('/student_details/<int:student_id>')
def student_details(student_id):
    if 'instructor_id' not in session:
        return redirect(url_for('home'))

    instructor = Instructor.query.get(session['instructor_id'])

    relation = StudentInstructor.query.filter_by(
        student_id=student_id,
        instructor_id=instructor.id
    ).first()

    if not relation:
        flash('Access denied!', 'error')
        return redirect(url_for('instructor_students'))

    student = Student.query.get(student_id)
    weight_records = WeightRecord.query.filter_by(student_id=student_id).all()

    from datetime import date as date_obj

    return render_template('student_details.html', student=student, weight_records=weight_records, date=date_obj)


@app.route('/delete_weight_record/<int:record_id>')
def delete_weight_record(record_id):
    if 'student_id' not in session:
        return redirect(url_for('login_student'))

    record = WeightRecord.query.get(record_id)
    if record and record.student_id == session['student_id']:
        # Check if this is the first (starting) weight
        first_record = WeightRecord.query.filter_by(student_id=session['student_id']).order_by(WeightRecord.id).first()
        if record.id != first_record.id:
            db.session.delete(record)
            db.session.commit()
            flash('Weight record deleted successfully!', 'success')
        else:
            flash('Cannot delete starting weight!', 'error')

    return redirect(url_for('student_dashboard'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)