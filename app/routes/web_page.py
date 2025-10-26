# app/routes/web_page
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import NewsletterSubscriber

landingPage_bp = Blueprint("landingPage", __name__)


@landingPage_bp.route("/subscribe", methods=["POST"])
def subscribe():
    """
    Subscribe to newsletter
    Accepts: { "email": "user@example.com" }
    Returns: success message
    """
    data = request.get_json() or {}
    email = data.get("email")

    if not email:
        return jsonify({"msg": "Email is required"}), 400

    # Basic email validation
    if "@" not in email or "." not in email:
        return jsonify({"msg": "Please provide a valid email address"}), 400

    # Check if already subscribed
    existing_subscriber = NewsletterSubscriber.query.filter_by(email=email).first()
    if existing_subscriber:
        if existing_subscriber.is_active:
            return jsonify({"msg": "This email is already subscribed to our newsletter"}), 409
        else:
            # Reactivate previously unsubscribed email
            existing_subscriber.is_active = True
            db.session.commit()
            return jsonify({"msg": "Successfully resubscribed to our newsletter"}), 200

    try:
        # Create new subscriber
        subscriber = NewsletterSubscriber(email=email)
        db.session.add(subscriber)
        db.session.commit()

        return jsonify({
            "msg": "Successfully subscribed to our newsletter!",
            "subscriber": subscriber.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Subscription failed", "error": str(e)}), 500


@landingPage_bp.route("/unsubscribe", methods=["POST"])
def unsubscribe():
    """
    Unsubscribe from newsletter
    Accepts: { "email": "user@example.com" }
    Returns: success message
    """
    data = request.get_json() or {}
    email = data.get("email")

    if not email:
        return jsonify({"msg": "Email is required"}), 400

    subscriber = NewsletterSubscriber.query.filter_by(email=email).first()
    if not subscriber:
        return jsonify({"msg": "Email not found in our newsletter list"}), 404

    if not subscriber.is_active:
        return jsonify({"msg": "This email is already unsubscribed"}), 409

    subscriber.is_active = False
    db.session.commit()

    return jsonify({"msg": "Successfully unsubscribed from our newsletter"}), 200


@landingPage_bp.route("/subscribers", methods=["GET"])
def get_subscribers():
    """
    Get all active subscribers (Admin only - optional)
    Returns: list of subscribers
    """
    subscribers = NewsletterSubscriber.query.filter_by(is_active=True).all()

    return jsonify({
        "subscribers": [subscriber.to_dict() for subscriber in subscribers],
        "total": len(subscribers)
    }), 200