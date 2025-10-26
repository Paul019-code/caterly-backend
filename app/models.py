# app/models.py
# from .extensions import db
# from werkzeug.security import generate_password_hash, check_password_hash
# from datetime import datetime
# import enum
# from sqlalchemy.dialects.postgresql import JSON
#
#
# class UserRole(enum.Enum):
#     CLIENT = "client"
#     CATERER = "caterer"
#     ADMIN = "admin"
#
#
# class User(db.Model):
#     __tablename__ = "users"
#     id = db.Column(db.Integer, primary_key=True)
#     email = db.Column(db.String(120), unique=True, nullable=False, index=True)
#     password_hash = db.Column(db.String(255), nullable=False)
#     role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.CLIENT)
#     phone_number = db.Column(db.String(20))  # ADD THIS FIELD
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#
#     caterer_profile = db.relationship("CatererProfile", back_populates="user", uselist=False)
#     customer_profile = db.relationship("CustomerProfile", back_populates="user", uselist=False)  # ADD THIS
#     orders = db.relationship("Order", back_populates="client", lazy="dynamic")
#
#     def set_password(self, password):
#         self.password_hash = generate_password_hash(password)
#
#     def check_password(self, password):
#         return check_password_hash(self.password_hash, password)
#
#
# # ADD THIS NEW MODEL FOR CUSTOMERS
# class CustomerProfile(db.Model):
#     __tablename__ = "customer_profiles"
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
#     full_name = db.Column(db.String(150), nullable=False)
#     address = db.Column(db.String(255), nullable=False)
#
#     user = db.relationship("User", back_populates="customer_profile")
#
#
# class CatererProfile(db.Model):
#     __tablename__ = "caterer_profiles"
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
#     business_name = db.Column(db.String(150))
#     phone = db.Column(db.String(30))
#     address = db.Column(db.String(255))
#     details = db.Column(JSON, default={})
#
#     user = db.relationship("User", back_populates="caterer_profile")
#     menu_items = db.relationship("MenuItem", back_populates="caterer", lazy="dynamic")
#
#
# # ... rest of your existing models (MenuItem, Order, OrderItem) remain the same ...
#
#
# class MenuItem(db.Model):
#     __tablename__ = "menu_items"
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(150), nullable=False)
#     description = db.Column(db.Text)
#     price = db.Column(db.Numeric(10,2), nullable=False)
#     image_url = db.Column(db.String(500))  # For food images
#     category = db.Column(db.String(100))  # e.g., "Trending Now", "Recommendations"
#     dietary_tags = db.Column(JSON)  # ["gluten-free", "vegan", "vegetarian"]
#     preparation_time = db.Column(db.Integer)  # Minutes
#     is_active = db.Column(db.Boolean, default=True)
#     is_trending = db.Column(db.Boolean, default=False)  # For "Trending Now" section
#     is_recommended = db.Column(db.Boolean, default=False)  # For "Recommendations" section
#     caterer_id = db.Column(db.Integer, db.ForeignKey("caterer_profiles.id"))
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#
#     caterer = db.relationship("CatererProfile", back_populates="menu_items")
#
#     def to_dict(self):
#         return {
#             "id": self.id,
#             "name": self.name,
#             "description": self.description,
#             "price": float(self.price) if self.price else 0,
#             "image_url": self.image_url,
#             "category": self.category,
#             "dietary_tags": self.dietary_tags or [],
#             "preparation_time": self.preparation_time,
#             "is_active": self.is_active,
#             "is_trending": self.is_trending,
#             "is_recommended": self.is_recommended,
#             "caterer_id": self.caterer_id,
#             "caterer_business_name": self.caterer.business_name if self.caterer else None,
#             "created_at": self.created_at.isoformat() if self.created_at else None
#         }
#
#
# class OrderStatus(enum.Enum):
#     PENDING = "pending"
#     CONFIRMED = "confirmed"
#     PREPARING = "preparing"
#     OUT_FOR_DELIVERY = "out_for_delivery"
#     COMPLETED = "completed"
#     CANCELLED = "cancelled"
#
#
# class Order(db.Model):
#     __tablename__ = "orders"
#     id = db.Column(db.Integer, primary_key=True)
#     client_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
#     caterer_id = db.Column(db.Integer, db.ForeignKey("caterer_profiles.id"), nullable=False)
#     total_amount = db.Column(db.Numeric(10,2), nullable=False)
#     status = db.Column(db.Enum(OrderStatus), default=OrderStatus.PENDING)
#     notes = db.Column(db.Text)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#
#     client = db.relationship("User", back_populates="orders")
#     order_items = db.relationship("OrderItem", back_populates="order", lazy="dynamic")
#
#
# class OrderItem(db.Model):
#     __tablename__ = "order_items"
#     id = db.Column(db.Integer, primary_key=True)
#     order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
#     menu_item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), nullable=False)
#     quantity = db.Column(db.Integer, default=1)
#     unit_price = db.Column(db.Numeric(10,2))
#     customization = db.Column(db.Text)
#
#     order = db.relationship("Order", back_populates="order_items")
#
#
# class NewsletterSubscriber(db.Model):
#     __tablename__ = "newsletter_subscribers"
#
#     id = db.Column(db.Integer, primary_key=True)
#     email = db.Column(db.String(120), unique=True, nullable=False, index=True)
#     subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
#     is_active = db.Column(db.Boolean, default=True)
#
#     def to_dict(self):
#         return {
#             "id": self.id,
#             "email": self.email,
#             "subscribed_at": self.subscribed_at.isoformat(),
#             "is_active": self.is_active
#         }


# app/models.py
from .extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import enum
from sqlalchemy.dialects.postgresql import JSON


class UserRole(enum.Enum):
    CLIENT = "client"
    CATERER = "caterer"
    ADMIN = "admin"


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.CLIENT)
    phone_number = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    caterer_profile = db.relationship("CatererProfile", back_populates="user", uselist=False)
    customer_profile = db.relationship("CustomerProfile", back_populates="user", uselist=False)
    orders = db.relationship("Order", back_populates="client", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class CustomerProfile(db.Model):
    __tablename__ = "customer_profiles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.String(255), nullable=False)

    user = db.relationship("User", back_populates="customer_profile")


class CatererProfile(db.Model):
    __tablename__ = "caterer_profiles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    business_name = db.Column(db.String(150))
    phone = db.Column(db.String(30))
    address = db.Column(db.String(255))
    details = db.Column(JSON, default={})

    user = db.relationship("User", back_populates="caterer_profile")
    menu_items = db.relationship("MenuItem", back_populates="caterer", lazy="dynamic")


class MenuItem(db.Model):
    __tablename__ = "menu_items"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    image_url = db.Column(db.String(500))
    category = db.Column(db.String(100))
    dietary_tags = db.Column(JSON)
    preparation_time = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    is_trending = db.Column(db.Boolean, default=False)
    is_recommended = db.Column(db.Boolean, default=False)
    caterer_id = db.Column(db.Integer, db.ForeignKey("caterer_profiles.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    caterer = db.relationship("CatererProfile", back_populates="menu_items")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price) if self.price else 0,
            "image_url": self.image_url,
            "category": self.category,
            "dietary_tags": self.dietary_tags or [],
            "preparation_time": self.preparation_time,
            "is_active": self.is_active,
            "is_trending": self.is_trending,
            "is_recommended": self.is_recommended,
            "caterer_id": self.caterer_id,
            "caterer_business_name": self.caterer.business_name if self.caterer else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# ENHANCED OrderStatus with catering-specific statuses
class OrderStatus(enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    OUT_FOR_DELIVERY = "out_for_delivery"
    COMPLETED = "completed"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# ENHANCED Order model with catering features
class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False, index=True)  # ADDED
    client_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    caterer_id = db.Column(db.Integer, db.ForeignKey("caterer_profiles.id"), nullable=False)

    # Catering-specific fields
    event_name = db.Column(db.String(200))  # ADDED - for catering orders
    event_date = db.Column(db.Date)  # ADDED - for catering orders
    event_time = db.Column(db.Time)  # ADDED - for catering orders
    delivery_address = db.Column(db.Text)  # ENHANCED - for detailed catering delivery
    delivery_instructions = db.Column(db.Text)  # ADDED
    guest_count = db.Column(db.Integer)  # ADDED - for catering orders
    special_requirements = db.Column(JSON)  # ADDED - ["vegetarian", "nut-free", "gluten-free"]

    # Financial fields
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    estimated_total = db.Column(db.Numeric(10, 2))  # ADDED - for catering quotes
    final_total = db.Column(db.Numeric(10, 2))  # ADDED - actual final amount
    deposit_paid = db.Column(db.Numeric(10, 2), default=0)  # ADDED

    # Status & timestamps
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.PENDING)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # ADDED
    confirmed_at = db.Column(db.DateTime)  # ADDED
    delivery_date = db.Column(db.DateTime)  # ADDED

    client = db.relationship("User", back_populates="orders")
    caterer = db.relationship("CatererProfile", backref=db.backref("orders", lazy="dynamic"))
    order_items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan", lazy="dynamic")

    def is_catering_order(self):
        """Check if this is a catering order (has event details)"""
        return bool(self.event_name and self.event_date and self.guest_count)


# ENHANCED OrderItem model with catering features
class OrderItem(db.Model):
    __tablename__ = "order_items"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Numeric(10, 2))
    customization = db.Column(db.Text)
    servings_per_unit = db.Column(db.Integer, default=1)  # ADDED - for catering (e.g., 1 tray serves 10 people)
    special_instructions = db.Column(db.Text)  # ADDED - for catering-specific instructions

    order = db.relationship("Order", back_populates="order_items")
    menu_item = db.relationship("MenuItem", backref=db.backref("order_items", lazy="dynamic"))  # ADD THIS LINE

    def total_price(self):
        """Calculate total price for this order item"""
        return float(self.unit_price * self.quantity) if self.unit_price else 0

    def total_servings(self):
        """Calculate total servings for catering orders"""
        return self.quantity * self.servings_per_unit


class NewsletterSubscriber(db.Model):
    __tablename__ = "newsletter_subscribers"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "subscribed_at": self.subscribed_at.isoformat(),
            "is_active": self.is_active
        }