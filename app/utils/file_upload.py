# app/utils/file_upload.py
import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def save_menu_item_image(file):
    """Save uploaded image and return the file path"""
    if file and allowed_file(file.filename):
        # Generate unique filename
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{file_ext}"

        # Ensure upload directory exists
        upload_dir = current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads/menu_items')
        os.makedirs(upload_dir, exist_ok=True)

        # Save file
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)

        # Return relative URL for database storage
        return f"/static/uploads/menu_items/{filename}"

    return None