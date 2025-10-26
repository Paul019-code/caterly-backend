# app/routes/menu_routes.py
import json
import os
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import MenuItem, User
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.file_upload import save_menu_item_image

menu_bp = Blueprint("menu", __name__)


# ===== HYBRID ENDPOINT - HANDLES BOTH JSON AND FILE UPLOAD =====
@menu_bp.route("/items", methods=["POST"])
@jwt_required()
def create_menu_item():
    """
    Create menu item - accepts both:
    1. JSON with image_url (external URL)
    2. Form-data with image file upload + JSON data

    Smart detection: checks Content-Type header
    """
    identity = get_jwt_identity()
    user_id = int(identity)

    # Verify user is a caterer
    user = User.query.get(user_id)
    if not user or user.role.value != "caterer" or not user.caterer_profile:
        return jsonify({"msg": "Caterer access required"}), 403

    try:
        image_url = None

        # Check if this is a file upload (form-data) or JSON request
        if request.content_type and 'multipart/form-data' in request.content_type:
            # ===== FILE UPLOAD MODE =====
            print("Processing as form-data with file upload")

            # Handle image file upload
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file and image_file.filename != '':
                    image_url = save_menu_item_image(image_file)
                    print(f"Image saved: {image_url}")

            # Get JSON data from form field
            menu_data_str = request.form.get('menu_data')
            if menu_data_str:
                try:
                    data = json.loads(menu_data_str)
                except json.JSONDecodeError:
                    return jsonify({"msg": "Invalid JSON in menu_data"}), 400
            else:
                # Fallback: get individual form fields
                data = {
                    'name': request.form.get('name'),
                    'description': request.form.get('description', ''),
                    'price': request.form.get('price'),
                    'category': request.form.get('category'),
                    'dietary_tags': request.form.get('dietary_tags', '[]'),
                    'preparation_time': request.form.get('preparation_time'),
                    'is_trending': request.form.get('is_trending', 'false'),
                    'is_recommended': request.form.get('is_recommended', 'false')
                }

                # Parse dietary tags if it's a string
                if isinstance(data['dietary_tags'], str):
                    try:
                        data['dietary_tags'] = json.loads(data['dietary_tags'])
                    except:
                        data['dietary_tags'] = []

        else:
            # ===== PURE JSON MODE =====
            print("Processing as JSON request")
            data = request.get_json() or {}
            image_url = data.get('image_url')  # Use external URL from JSON

        # Validate required fields
        if not data.get('name') or not data.get('price'):
            return jsonify({"msg": "Name and price are required"}), 400

        # Create menu item
        menu_item = MenuItem(
            name=data.get('name'),
            description=data.get('description', ''),
            price=float(data.get('price')),
            image_url=image_url,
            category=data.get('category'),
            dietary_tags=data.get('dietary_tags', []),
            preparation_time=int(data.get('preparation_time')) if data.get('preparation_time') else None,
            is_trending=data.get('is_trending', 'false').lower() == 'true',
            is_recommended=data.get('is_recommended', 'false').lower() == 'true',
            caterer_id=user.caterer_profile.id
        )

        db.session.add(menu_item)
        db.session.commit()

        return jsonify({
            "msg": "Menu item created successfully",
            "menu_item": menu_item.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Error: {str(e)}")
        return jsonify({"msg": "Failed to create menu item", "error": str(e)}), 500


@menu_bp.route("/items", methods=["GET"])
@jwt_required()
def get_my_menu_items():
    """
    Get all menu items for the authenticated caterer
    """
    identity = get_jwt_identity()
    user_id = int(identity)

    user = User.query.get(user_id)
    if not user or user.role.value != "caterer" or not user.caterer_profile:
        return jsonify({"msg": "Caterer access required"}), 403

    menu_items = MenuItem.query.filter_by(caterer_id=user.caterer_profile.id).all()

    return jsonify({
        "menu_items": [item.to_dict() for item in menu_items],
        "total": len(menu_items)
    }), 200


# ===== ADD THIS MISSING ENDPOINT =====
@menu_bp.route("/items/<int:item_id>", methods=["GET"])
@jwt_required()
def get_menu_item(item_id):
    """
    Get a specific menu item (caterer only - must own the item)
    """
    identity = get_jwt_identity()
    user_id = int(identity)

    user = User.query.get(user_id)
    if not user or user.role.value != "caterer" or not user.caterer_profile:
        return jsonify({"msg": "Caterer access required"}), 403

    menu_item = MenuItem.query.filter_by(
        id=item_id,
        caterer_id=user.caterer_profile.id
    ).first()

    if not menu_item:
        return jsonify({"msg": "Menu item not found"}), 404

    return jsonify({"menu_item": menu_item.to_dict()}), 200


@menu_bp.route("/items/<int:item_id>", methods=["PUT"])
@jwt_required()
def update_menu_item(item_id):
    """
    Update a menu item (Caterer only)
    """
    identity = get_jwt_identity()
    user_id = int(identity)

    user = User.query.get(user_id)
    if not user or user.role.value != "caterer" or not user.caterer_profile:
        return jsonify({"msg": "Caterer access required"}), 403

    menu_item = MenuItem.query.filter_by(
        id=item_id,
        caterer_id=user.caterer_profile.id
    ).first()

    if not menu_item:
        return jsonify({"msg": "Menu item not found"}), 404

    data = request.get_json() or {}

    # Update fields
    updatable_fields = [
        "name", "description", "price", "image_url", "category",
        "dietary_tags", "preparation_time", "is_active",
        "is_trending", "is_recommended"
    ]

    for field in updatable_fields:
        if field in data:
            setattr(menu_item, field, data[field])

    db.session.commit()

    return jsonify({
        "msg": "Menu item updated successfully",
        "menu_item": menu_item.to_dict()
    }), 200


# @menu_bp.route("/items/<int:item_id>", methods=["DELETE"])
# @jwt_required()
# def delete_menu_item(item_id):
#     """
#     Delete a menu item (Caterer only - soft delete)
#     """
#     identity = get_jwt_identity()
#     user_id = int(identity)
#
#     user = User.query.get(user_id)
#     if not user or user.role.value != "caterer" or not user.caterer_profile:
#         return jsonify({"msg": "Caterer access required"}), 403
#
#     menu_item = MenuItem.query.filter_by(
#         id=item_id,
#         caterer_id=user.caterer_profile.id
#     ).first()
#
#     if not menu_item:
#         return jsonify({"msg": "Menu item not found"}), 404
#
#     # Soft delete
#     menu_item.is_active = False
#     db.session.commit()
#
#     return jsonify({"msg": "Menu item deleted successfully"}), 200


# ===== OPTIONAL: HARD DELETE ENDPOINT =====
@menu_bp.route("/items/<int:item_id>", methods=["DELETE"])
@jwt_required()
def hard_delete_menu_item(item_id):
    """
    Hard delete - permanently remove menu item from database
    Use with caution!
    """
    identity = get_jwt_identity()
    user_id = int(identity)

    user = User.query.get(user_id)
    if not user or user.role.value != "caterer" or not user.caterer_profile:
        return jsonify({"msg": "Caterer access required"}), 403

    menu_item = MenuItem.query.filter_by(
        id=item_id,
        caterer_id=user.caterer_profile.id
    ).first()

    if not menu_item:
        return jsonify({"msg": "Menu item not found"}), 404

    # Delete associated image file if exists
    if menu_item.image_url and not menu_item.image_url.startswith('http'):
        try:
            image_path = menu_item.image_url.replace('/static/', 'app/static/')
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            print(f"Error deleting image file: {e}")

    # Permanent delete from database
    db.session.delete(menu_item)
    db.session.commit()

    return jsonify({"msg": "Menu item permanently deleted"}), 200


# ===== CLIENT/PUBLIC ENDPOINTS =====

@menu_bp.route("/public/items", methods=["GET"])
def get_public_menu_items():
    """
    Get all active menu items for clients (public endpoint)
    Query params:
    - category: filter by category
    - dietary_tag: filter by dietary tag (gluten-free, vegan, etc.)
    - search: search in name/description
    """
    try:
        # Base query for active items
        query = MenuItem.query.filter_by(is_active=True)

        # Apply filters
        category = request.args.get("category")
        if category:
            query = query.filter_by(category=category)

        dietary_tag = request.args.get("dietary_tag")
        if dietary_tag:
            # Method 2: cast to text and search
            query = query.filter(db.cast(MenuItem.dietary_tags, db.Text).ilike(f'%"{dietary_tag}"%'))

        search = request.args.get("search")
        if search:
            query = query.filter(
                (MenuItem.name.ilike(f"%{search}%")) |
                (MenuItem.description.ilike(f"%{search}%"))
            )

        menu_items = query.all()

        # Organize by sections for frontend
        trending_items = [item for item in menu_items if item.is_trending]
        recommended_items = [item for item in menu_items if item.is_recommended]
        other_items = [item for item in menu_items if not item.is_trending and not item.is_recommended]

        return jsonify({
            "trending": [item.to_dict() for item in trending_items],
            "recommended": [item.to_dict() for item in recommended_items],
            "all_items": [item.to_dict() for item in other_items],
            "total": len(menu_items)
        }), 200

    except Exception as e:
        return jsonify({"msg": "Error fetching menu items", "error": str(e)}), 500


@menu_bp.route("/public/categories", methods=["GET"])
def get_categories():
    """
    Get all available menu categories
    """
    categories = db.session.query(MenuItem.category).filter_by(is_active=True).distinct().all()
    category_list = [cat[0] for cat in categories if cat[0]]

    return jsonify({"categories": category_list}), 200


@menu_bp.route("/public/items/<int:item_id>", methods=["GET"])
def get_public_menu_item(item_id):
    """
    Get a specific menu item details (public)
    """
    menu_item = MenuItem.query.filter_by(id=item_id, is_active=True).first()

    if not menu_item:
        return jsonify({"msg": "Menu item not found"}), 404

    return jsonify({"menu_item": menu_item.to_dict()}), 200