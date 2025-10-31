# app/utils/google_oauth.py
import requests
from flask import current_app, jsonify
import uuid
from app.models import User, CustomerProfile, CatererProfile, UserRole, db
from datetime import datetime


class GoogleOAuth:
    @staticmethod
    def get_google_provider_cfg():
        return requests.get(current_app.config['GOOGLE_DISCOVERY_URL']).json()

    @staticmethod
    def verify_google_token(token):
        """
        Verify Google ID token and return user info
        """
        try:
            # Get Google's provider configuration
            google_provider_cfg = GoogleOAuth.get_google_provider_cfg()
            token_endpoint = google_provider_cfg["token_endpoint"]

            # Verify the token
            token_url = "https://oauth2.googleapis.com/tokeninfo"
            params = {'id_token': token}
            response = requests.get(token_url, params=params)

            if response.status_code == 200:
                user_info = response.json()

                # Verify the token is for our app
                if user_info['aud'] != current_app.config['GOOGLE_CLIENT_ID']:
                    return None, "Invalid token audience"

                return user_info, None
            else:
                return None, "Invalid token"

        except Exception as e:
            current_app.logger.error(f"Google token verification error: {str(e)}")
            return None, "Token verification failed"

    @staticmethod
    def find_or_create_user(google_user_info, role="client"):
        """
        Find existing user or create new user from Google info
        """
        try:
            email = google_user_info['email']

            # Check if user already exists
            user = User.query.filter_by(email=email).first()

            if user:
                # User exists, return the user
                return user, False  # False means user already existed
            else:
                # Create new user
                new_user = User(
                    email=email,
                    role=UserRole(role),
                    created_at=datetime.utcnow()
                )

                # Generate a random password for OAuth users
                # They'll always use Google login, so this is just for the database
                new_user.set_password(str(uuid.uuid4()))

                db.session.add(new_user)
                db.session.flush()

                # Create profile based on role
                if role == "client":
                    profile = CustomerProfile(
                        user_id=new_user.id,
                        full_name=google_user_info.get('name', ''),
                        address="To be updated"  # User can update later
                    )
                else:  # caterer
                    profile = CatererProfile(
                        user_id=new_user.id,
                        business_name=google_user_info.get('name', ''),
                        address="To be updated"
                    )

                db.session.add(profile)
                db.session.commit()

                return new_user, True  # True means new user was created

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating user from Google: {str(e)}")
            raise e
