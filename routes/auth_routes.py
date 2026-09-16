from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from database.models import db, User
from datetime import timedelta

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# Token expiration time
ACCESS_TOKEN_EXPIRES = timedelta(hours=24)


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user"""
    data = request.get_json()
    
    # Validate required fields
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"error": "Username and password are required"}), 400
    
    # Check if user already exists
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username already exists"}), 400
    
    if data.get("email") and User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already exists"}), 400
    
    # Create new user
    user = User(
        username=data["username"],
        email=data.get("email"),
        full_name=data.get("full_name"),
    )
    user.set_password(data["password"])
    
    try:
        db.session.add(user)
        db.session.commit()
        
        # Generate access token
        access_token = create_access_token(
            identity=user.id, 
            expires_delta=ACCESS_TOKEN_EXPIRES
        )
        
        return jsonify({
            "message": "User registered successfully",
            "token": access_token,
            "user": user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    """Login user and return JWT token"""
    data = request.get_json()
    
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"error": "Username and password are required"}), 400
    
    user = User.query.filter_by(username=data["username"]).first()
    
    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid username or password"}), 401
    
    if not user.is_active:
        return jsonify({"error": "Account is deactivated"}), 401
    
    # Generate access token
    access_token = create_access_token(
        identity=user.id, 
        expires_delta=ACCESS_TOKEN_EXPIRES
    )
    
    return jsonify({
        "message": "Login successful",
        "token": access_token,
        "user": user.to_dict()
    }), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    """Get current user information"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({"user": user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get user: {str(e)}"}), 500


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """Logout user (JWT tokens are stateless, client should discard token)"""
    return jsonify({"message": "Logout successful"}), 200
