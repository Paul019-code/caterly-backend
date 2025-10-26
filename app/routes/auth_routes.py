# app/routes/auth_routes.py
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import User, UserRole, CatererProfile, CustomerProfile
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app.extensions import jwt

auth_bp = Blueprint("auth", __name__)


@jwt.user_identity_loader
def user_identity_lookup(user):
    # This is called when creating JWTs
    return str(user.id) if isinstance(user, User) else str(user)


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    # This is called when protected routes are accessed
    identity = jwt_data["sub"]
    return User.query.get(int(identity))


@auth_bp.route("/register/customer", methods=["POST"])
def register_customer():
    """
    Customer registration endpoint
    Accepts: {
        "full_name": "",
        "address": "",
        "email": "",
        "phone_number": "",
        "password": ""
    }
    Returns: access & refresh tokens + user object
    """
    data = request.get_json() or {}

    required_fields = ["full_name", "address", "email", "phone_number", "password"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"msg": f"{field} is required"}), 400

    email = data.get("email")

    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "user already exists"}), 409

    try:
        # Create user with CLIENT role
        user = User(
            email=email,
            role=UserRole.CLIENT,
            phone_number=data.get("phone_number")
        )
        user.set_password(data.get("password"))
        db.session.add(user)
        db.session.flush()  # Get user ID without committing

        # Create customer profile
        customer_profile = CustomerProfile(
            user_id=user.id,
            full_name=data.get("full_name"),
            address=data.get("address")
        )
        db.session.add(customer_profile)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "registration failed", "error": str(e)}), 500

    # FIX: Use user.id as string for identity instead of dict
    identity = str(user.id)
    access = create_access_token(identity=identity)
    refresh = create_refresh_token(identity=identity)

    return jsonify({
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role.value,
            "full_name": customer_profile.full_name,
            "phone_number": user.phone_number,
            "address": customer_profile.address
        },
        "access_token": access,
        "refresh_token": refresh
    }), 201


@auth_bp.route("/register/caterer", methods=["POST"])
def register_caterer():
    """
    Caterer registration endpoint
    Accepts: {
        "full_name": "",
        "company_name": "",
        "email": "",
        "phone_number": "",
        "password": ""
    }
    Returns: access & refresh tokens + user object
    """
    data = request.get_json() or {}

    required_fields = ["full_name", "company_name", "email", "phone_number", "password"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"msg": f"{field} is required"}), 400

    email = data.get("email")

    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "user already exists"}), 409

    try:
        # Create user with CATERER role
        user = User(
            email=email,
            role=UserRole.CATERER,
            phone_number=data.get("phone_number")
        )
        user.set_password(data.get("password"))
        db.session.add(user)
        db.session.flush()  # Get user ID without committing

        # Create caterer profile using full_name as business contact name
        caterer_profile = CatererProfile(
            user_id=user.id,
            business_name=data.get("company_name"),
            phone=data.get("phone_number")  # Using the same phone number
        )
        db.session.add(caterer_profile)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "registration failed", "error": str(e)}), 500

    # FIX: Use user.id as string for identity instead of dict
    identity = str(user.id)
    access = create_access_token(identity=identity)
    refresh = create_refresh_token(identity=identity)

    return jsonify({
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role.value,
            "full_name": data.get("full_name"),  # From request, not stored in caterer_profile
            "company_name": caterer_profile.business_name,
            "phone_number": user.phone_number
        },
        "access_token": access,
        "refresh_token": refresh
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Common login endpoint for both customers and caterers
    Accepts: { "email": "", "password": "" }
    Returns: access & refresh tokens + user object with profile data
    """
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"msg": "email and password required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"msg": "invalid credentials"}), 401

    # Build user response with profile data
    user_data = {
        "id": user.id,
        "email": user.email,
        "role": user.role.value,
        "phone_number": user.phone_number
    }

    # Add role-specific profile data
    if user.role == UserRole.CATERER and user.caterer_profile:
        user_data["company_name"] = user.caterer_profile.business_name
        # For caterers, we don't have full_name stored, so we might want to add it later
    elif user.role == UserRole.CLIENT and user.customer_profile:
        user_data["full_name"] = user.customer_profile.full_name
        user_data["address"] = user.customer_profile.address

    # FIX: Use user.id as string for identity instead of dict
    identity = str(user.id)
    access = create_access_token(identity=identity)
    refresh = create_refresh_token(identity=identity)

    return jsonify({
        "user": user_data,
        "access_token": access,
        "refresh_token": refresh
    }), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """
    Protected: returns the authenticated user's complete profile
    """
    # FIX: Now identity is just the user ID as string
    user_id = get_jwt_identity()  # This is now a string
    user = User.query.get(int(user_id))  # Convert back to int for query

    if not user:
        return jsonify({"msg": "user not found"}), 404

    result = {
        "id": user.id,
        "email": user.email,
        "role": user.role.value,
        "phone_number": user.phone_number
    }

    # Add role-specific profile data
    if user.role == UserRole.CATERER and user.caterer_profile:
        result["company_name"] = user.caterer_profile.business_name
        result["business_phone"] = user.caterer_profile.phone
        result["business_address"] = user.caterer_profile.address
    elif user.role == UserRole.CLIENT and user.customer_profile:
        result["full_name"] = user.customer_profile.full_name
        result["address"] = user.customer_profile.address

    return jsonify(result), 200