# main.py
import os
from app import create_app
from flask import send_from_directory


app = create_app()


@app.route('/static/uploads/menu_items/<filename>')
def serve_menu_item_image(filename):
    return send_from_directory('app/static/uploads/menu_items', filename)


# Create upload directory if it doesn't exist
os.makedirs('app/static/uploads/menu_items', exist_ok=True)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
