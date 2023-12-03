from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
import jwt                                         # importing json web token encoder
from datetime import datetime, timedelta
import smtplib
import os
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)
app.config['SECRET_KEY'] = 'banana'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///file_sharing.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.app_context().push()

db = SQLAlchemy(app)

# serializer -> used for creating secure download link
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])


# SQLite DB Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False)
    is_ops_user = db.Column(db.Boolean, default=False)


class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)


def generate_token(user_id, is_ops_user):
    payload = {
        'user_id': user_id,
        'is_ops_user': is_ops_user,
        'exp': datetime.utcnow() + timedelta(hours=1)   # token expiration time
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')


# Inserting an ops user
# new_ops_user = User(username='aditya101', password='adityasingh', email='adityasingh@hehe.com',
#                 email_verified=True, is_ops_user=True)
# db.session.add(new_ops_user)
# db.session.commit()

# Flask routes:

@app.route('/ops-user/login', methods=['POST'])
def ops_user_login():
    # data = request.get_json()
    username = request.headers.get('username')
    password = request.headers.get('password')

    user = User.query.filter_by(username=username, password=password, is_ops_user=True).first()

    if user:
        token = generate_token(user.id, True)
        return jsonify({"message": "Login Successful", 'token': token})
    else:
        return jsonify({'message': 'Invalid credentials'}), 401


@app.route('/ops-user/upload-file', methods=['POST'])
def ops_user_upload_file():
    ops_user_token = request.headers.get('Authorization')            # encoded token
    print(ops_user_token)
    try:
        ops_user_data = jwt.decode(ops_user_token, app.config['SECRET_KEY'], algorithms=['HS256'])     # provides us with the ops_user's data dictionary
        print(ops_user_data)
        if ops_user_data['is_ops_user']:

            file = request.files['file']

            allowed_extensions = ['pptx', 'docx', 'xlsx']
            if file and '.' in file.filename and file.filename.split('.')[-1].lower() in allowed_extensions:
                # Save the file
                file.save(os.path.join('uploads', file.filename))

                # Record file information in the database
                new_file = File(filename=file.filename, filepath=os.path.join('uploads', file.filename),
                                uploaded_by=ops_user_data['user_id'])
                db.session.add(new_file)
                db.session.commit()

                return jsonify({'message': 'File uploaded successfully'})
            else:
                return jsonify({'message': 'Invalid File type. Allowed file types: pptx, doc, xlsx'})
        else:
            return jsonify({'message': 'Unauthorized'}), 401
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid Token'}), 401


@app.route('/client-user/signup', methods=['POST'])
def client_user_signup():
    # data = request.get_json()
    username = request.headers.get('username')
    password = request.headers.get('password')
    email = request.headers.get('email')

    new_user = User(username=username, password=password, email=email)
    db.session.add(new_user)
    db.session.commit()

    # Send verification email
    token = generate_token(new_user.id, False)
    api_url = 'http://127.0.0.1:5000'                                                              # base url
    verification_url = f'{api_url}/verify-email/{token}'

    my_email = "your-email@gmail.com"           # ################ Enter your email and pass here ##########
    password_ = "your-password"

    connection = smtplib.SMTP_SSL("smtp.gmail.com", 465)

    connection.login(user=my_email, password=password_)
    connection.sendmail(
        from_addr=my_email,
        to_addrs=email,
        msg=f"Subject: Verification email\n\nClick the link to verify your email: {verification_url}")  # after two \n the body of the mail starts
    connection.close()

    return jsonify({'message': 'Check your email for verification'})


@app.route('/verify-email/<token>', methods=['GET'])
def verify_email(token):
    try:
        user_data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = user_data['user_id']
        user = User.query.get(user_id)
        user.email_verified = True
        db.session.commit()
        return jsonify({'message': 'Email verified successful'})
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401


@app.route('/client-user/login', methods=['POST'])
def client_user_login():
    # data = request.get_json()
    username = request.headers.get('username')
    password = request.headers.get('password')

    user = User.query.filter_by(username=username, password=password, email_verified=True).first()

    if user:
        token = generate_token(user.id, False)
        return jsonify({"message": "Login Successful", 'token': token})
    else:
        return jsonify({'message': 'Invalid credentials or email not verified'}), 401


@app.route('/client-user/list-files', methods=['GET'])
def client_user_list_files():
    client_user_token = request.headers.get('Authorization')
    try:
        client_user_data = jwt.decode(client_user_token, app.config['SECRET_KEY'], algorithms=['HS256'])
        if not client_user_data['is_ops_user']:
            files = File.query.all()
            file_list = [{'file_id': file.id, 'filename': file.filename, 'upload_time': str(file.upload_time)} for file in files]
            return jsonify({"message": "success", 'files': file_list})
        else:
            return jsonify({'message': 'Unauthorized'}), 401
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401


# Creating a function to generate secure download url
def generate_download_url(file_id):
    # serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    # Create a signed token containing the file ID
    token = serializer.dumps(file_id)

    # Assuming your download route is '/client-user/download-file/<token>'
    api_url = 'http://127.0.0.1:5000'
    download_url = f'{api_url}/client-user/download-file/secure/{token}'

    return download_url


@app.route('/client-user/download-file/<int:file_id>', methods=['GET'])
def client_user_download_file(file_id):
    client_user_token = request.headers.get('Authorization')
    try:
        client_user_data = jwt.decode(client_user_token, app.config['SECRET_KEY'], algorithms=['HS256'])
        if not client_user_data['is_ops_user']:
            file = File.query.get(file_id)
            if file:
                # return send_from_directory(os.getcwd(), file.filepath)

                # Generate a secure download URL for the file
                download_url = generate_download_url(file.id)

                # Return the download link in the response
                response_data = {
                    'download-link': download_url,
                    'message': 'success'
                }

                return jsonify(response_data)
            else:
                return jsonify({'message': 'File not found'}), 404
        else:
            return jsonify({'message': 'Unauthorized'}), 401
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401


@app.route('/client-user/download-file/secure/<token>', methods=['GET'])
def client_user_download_file_by_token(token):
    file_id = serializer.loads(token, max_age=3600)  # token expiration age is 1 hr
    file = File.query.get(file_id)

    file_path = f'uploads/{file.filename}'
    return send_file(file_path, as_attachment=True)


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True, port=5000)                   # default port = 'http://127.0.0.1:5000'
