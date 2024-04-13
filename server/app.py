#!/usr/bin/env python3

from flask import render_template, request, session, jsonify, make_response
from flask_restful import Resource, reqparse
from sqlalchemy.exc import IntegrityError
from flask_cors import CORS

from config import app, db, api, cors
from models import User, Department, Accounting, UserDepartment, Salary, Job, Registration



@app.route("/")
@app.route('/<int:id>')
def index(id=0):
    return render_template("index.html")
# def home():
#     return "Welcome to my API."


# Frank
class Signup(Resource):

    def post(self):
        json = request.get_json()
        if not json:
            return {"message": "Request body is empty."}, 400

        # Validate required fields
        required_fields = ["username", "fullname", "age", "gender", "role", "password"]
        for field in required_fields:
            if field not in json or not json[field]:
                return {"message": f"Field '{field}' is required."}, 400

        # Check if the username already exists
        existing_user = User.query.filter_by(username=json["username"]).first()
        if existing_user:
            return {"message": "Username already exists."}, 500

        try:
            user = User(
                username=json["username"],
                fullname=json["fullname"],
                age=json["age"],
                gender=json["gender"],
                role=json["role"],
                password_hash=json["password"],
            )

            db.session.add(user)
            db.session.commit()
            return user.to_dict(), 201

        except IntegrityError as e:
            db.session.rollback()
            return {"message": "Username already exists."}, 409

        except Exception as e:
            db.session.rollback()
            return {"message": str(e)}, 500


class Login(Resource):

    def post(self):
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        print(f"Received login request for username: {username}")

        # Check if both username and password are provided
        if not (username and password):
            return {"message": "Both username and password are required."}, 400

        # Query the database for the user with the provided username
        user = User.query.filter(User.username == username).first()

        # Check if the user exists and the password is correct
        if user:
            print(f"User found: {user}")
            if user.authenticate(password):
                # Store user id in session
                session["user_id"] = user.id
                print("User authenticated successfully")
                # Return user details
                return user.to_dict(), 200
            else:
                print("Authentication failed: Incorrect password")
        else:
            print("User not found")

        # Return error message if username or password is incorrect
        return {"message": "Invalid username or password."}, 401


class Logout(Resource):

    def delete(self):
        session["user_id"] = None
        return {}, 204


class CheckSession(Resource):

    def get(self):

        user_id = session.get("user_id")
        if user_id:
            user = User.query.filter(User.id == user_id).first()
            return user.to_dict(), 200
        return {}, 401


class Accounts(Resource):
    def get(self):
        accounting_records = Accounting.query.all()

        accounting_report = []
        for record in accounting_records:
            accounting_report.append(
                {
                    "student_id": record.student_id,
                    "name": record.account_name,
                    "fee_status": record.accounting_status_perterm,
                    "paid": record.amount_paid,
                    "balance": record.balance,
                }
            )

        return make_response(jsonify(accounting_report), 200)


class AccountingReport(Resource):
    def get(self):

        accounting_records = Accounting.query.all()

        accounting_report = []
        for record in accounting_records:
            accounting_report.append(
                {
                    "student_id": record.student_id,
                    "name": record.account_name,
                    "fee_status": record.accounting_status_perterm,
                    "paid": record.amount_paid,
                    "balance": record.balance,
                }
            )

        return make_response(jsonify(accounting_report), 200)


###### admin
class Admin(Resource):

    def delete(self, user_id):
        

        entity = User.query.filter_by(id=user_id).first()
        if entity:
            if entity.role == "teacher" or entity.role == "student":
                salaries = Salary.query.filter_by(user_id=user_id).all()
                accountings = Accounting.query.filter_by(student_id=user_id).all()
                if salaries:
                    for salary in salaries:
                        db.session.delete(salary)
                if accountings:
                    for accounting in accountings:
                        db.session.delete(accounting)
                db.session.delete(entity)
                db.session.commit()
                return {
                    "message": f"{entity.role.capitalize()} deleted successfully"
                }, 200
            else:
                return {
                    "error": "Invalid role. Only 'teacher' or 'student' can be deleted"
                }, 400
        else:
            return {"error": "User not found"}, 404

    def patch(self, user_id):
  
       def patch(self, user_id):
  
        entity = db.session.get(User, user_id)

        if entity:
            
            if entity.role == "student":
                
                data = request.get_json()
                if data:
                    
                    accounting = Accounting.query.filter_by(student_id=user_id).first()
                    if accounting:
                       
                        for key, value in data.items():
                            if key in ["account_name", "accounting_status_perterm", "amount_paid", "balance"]:
                                setattr(accounting, key, value)
                        db.session.commit()
                        return accounting.to_dict(), 200
                    else:
                        return {"error": "No accounting record found for this student"}, 404
                else:
                    return {"error": "No data provided in the request"}, 400
            else:
                return {"error": "Only 'student' records can be edited"}, 400
        else:
            return {"error": "User not found"}, 404
    # ...


# #########
class Salaries(Resource):
    def get(self):
        salary_list = []
        for salary in Salary.query.all():
            user = User.query.filter_by(id=salary.user_id, role="teacher").first()
            if user:
                salary_list.append(
                    {
                        "teacher_id": user.id,
                        "teacher_name": user.fullname,
                        "salary": salary.amount_usd,
                        "pay_date": salary.pay_date.strftime("%Y-%m-%d"),
                        "description": salary.description,
                    }
                )
        return jsonify(salary_list)


class Departments(Resource):
    def get(self, department_id):
        user_department = UserDepartment.query.filter_by(
            department_id=department_id
        ).first()
        if user_department:
            department = Department.query.get(user_department.department_id)
            if department:
                return {
                    "dept_name": department.name,
                    "program": department.subject,
                }, 200
            else:
                return {"error": "Department not found"}, 404
        else:
            return {"error": "UserDepartment not found"}, 404


class AllDepartments(Resource):
    def get(self):
        departments = Department.query.all()
        departments_list = []
        for department in departments:
            departments_list.append(
                {
                    "dept_id": department.id,
                    "dept_name": department.name,
                    "program": department.subject,
                }
            )
        return jsonify(departments_list)


class Users(Resource):
    def get(self):
        users = []
        for user in User.query.all():
            user_dict = {
                "id": user.id,
                "username": user.username,
                "fullname": user.fullname,
                "age": user.age,
                "gender": user.gender,
                "role": user.role,
                "bio": user.bio,
            }

            users.append(user_dict)

        return make_response(jsonify(users), 200)


class Jobs(Resource):
    def get(self):
        jobs = []
        for job in Job.query.all():
            job_dict = {
                "id": job.id,
                "title": job.title,
                "level": job.level,
                "description": job.description,
                "requirements": job.requirements,
            }

            jobs.append(job_dict)

        return make_response(jsonify(jobs), 200)

class Registrations(Resource):
    def get(self):
        registrations = []
        for registration in Registration.query.all():
            registration_dict = {
                "id": registration.id,
                "first_name": registration.first_name,
                "last_name": registration.last_name,
                "father_fname": registration.father_fname,
                "father_lname": registration.father_lname,
                "mother_fname": registration.mother_fname,
                "mother_lname": registration.mother_lname,
                "adress": registration.adress,
                "grade": registration.grade
            }

            registrations.append(registration_dict)

        return make_response(jsonify(registrations), 200)
    
    def post(self):
        json = request.get_json()
        if not json:
            return {"message": "Request body is empty."}, 400

        # Validate required fields
        required_fields = ["first_name", "last_name", "father_fname", "father_lname", "mother_fname", "mother_lname","adress","grade"]
        for field in required_fields:
            if field not in json or not json[field]:
                return {"message": f"Field '{field}' is required."}, 400

        # Check if the username already exists
        existing_user = Registration.query.filter_by(first_name=json["first_name"]).first()
        if existing_user:
            return {"message": "Username already exists."}, 500

        try:
            student = Registration(
                first_name=json["first_name"],
                last_name=json["last_name"],
                father_fname=json["father_fname"],
                father_lname=json["father_lname"],
                mother_fname=json["mother_fname"],
                mother_lname=json["mother_lname"],
                adress=json["adress"],
                grade=json["grade"],
            )

            db.session.add(student)
            db.session.commit()
            return student.to_dict(), 201

        except IntegrityError as e:
            db.session.rollback()
            return {"message": "Student already exists."}, 409

        except Exception as e:
            db.session.rollback()
            return {"message": str(e)}, 500

class ResetPassword(Resource):

    def patch(self):
        # Get JSON data from request
        json_data = request.get_json()

        # Validate JSON data
        if not json_data:
            return {"message": "Request body is empty."}, 400

        # Validate required fields
        required_fields = ["username", "newPassword", "confirmNewPassword"]
        for field in required_fields:
            if field not in json_data or not json_data[field]:
                return {"message": f"Field '{field}' is required."}, 400

        # Check if new password matches confirm new password
        if json_data["newPassword"] != json_data["confirmNewPassword"]:
            return {
                "message": "New password and confirm new password do not match."
            }, 400

        # Query the database for the user with the provided username
        user = User.query.filter_by(username=json_data["username"]).first()

        # Check if the user exists
        if not user:
            return {"message": "User not found."}, 404

        try:
            user.password_hash = json_data["newPassword"]
            db.session.commit()
            return {"message": "Password reset successfully."}, 200
        except IntegrityError:
            db.session.rollback()
            return {"message": "Failed to reset password."}, 500


api.add_resource(Login, "/login", endpoint="login")
api.add_resource(Signup, "/signup", endpoint="signup")
api.add_resource(CheckSession, "/check_session", endpoint="check_session")
api.add_resource(Accounts, "/accounts", endpoint="accounts")
api.add_resource(AccountingReport, "/accounting_report", endpoint="accounting_report")
api.add_resource(Salaries, "/salaries", endpoint="salaries")
# api.add_resource(Departments, "/departments/<int:department_id>", endpoint="department")
api.add_resource(Logout, "/logout", endpoint="logout")
api.add_resource(Users, "/users", endpoint="users")
api.add_resource(Jobs, "/jobs", endpoint="jobs")
api.add_resource(ResetPassword, "/reset_password", endpoint="reset_password")
api.add_resource(AllDepartments, "/departments", endpoint="departments")
api.add_resource(Admin, "/admin/<int:user_id>", endpoint="admin")
api.add_resource(Registrations, "/registrations", endpoint="registrations")


if __name__ == "__main__":
    app.run(port=5555, debug=True)
