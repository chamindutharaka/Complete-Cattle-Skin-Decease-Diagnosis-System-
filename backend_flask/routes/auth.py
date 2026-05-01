from flask import Blueprint, request, jsonify
from backend_flask.models import User
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    phone = data.get('phone')
    
    if not username or not password:
        return jsonify({"message": "Username and password required"}), 400
        
    if User.objects(username=username).first():
        return jsonify({"message": "User already exists"}), 400
        
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password, phone=phone)
    
    try:
        new_user.save()
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.objects(username=username).first()
    
    if user and check_password_hash(user.password, password):
        # In MongoEngine, id is automatically mapped to the MongoDB _id
        access_token = create_access_token(identity=str(user.id))
        return jsonify({"token": access_token, "username": user.username, "role": user.role}), 200
        
    return jsonify({"message": "Invalid credentials"}), 401
