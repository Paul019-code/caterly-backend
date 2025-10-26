# routes/order_routes.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_, and_
import uuid
from datetime import datetime

from app.models import db, User, Order, OrderItem, MenuItem, CatererProfile, CustomerProfile, OrderStatus, UserRole

order_bp = Blueprint('order', __name__)


def generate_order_number():
    return f"ORD-{uuid.uuid4().hex[:8].upper()}"


def generate_catering_order_number():
    return f"CAT-{uuid.uuid4().hex[:8].upper()}"


@order_bp.route('/', methods=['GET'])
@jwt_required()
def get_orders():
    """Get orders for the current user (client or caterer) with filtering"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        order_type = request.args.get('type')  # 'regular' or 'catering'

        # Base query
        if user.role == UserRole.CLIENT:
            query = Order.query.filter_by(client_id=current_user_id)
        elif user.role == UserRole.CATERER:
            query = Order.query.filter_by(caterer_id=user.caterer_profile.id)
        else:  # ADMIN
            query = Order.query

        # Filter by status
        if status:
            query = query.filter_by(status=OrderStatus(status))

        # Filter by order type
        if order_type == 'catering':
            query = query.filter(Order.event_name.isnot(None))
        elif order_type == 'regular':
            query = query.filter(Order.event_name.is_(None))

        orders = query.order_by(Order.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        orders_data = []
        for order in orders.items:
            # Get caterer business name safely
            caterer = CatererProfile.query.get(order.caterer_id)

            order_data = {
                'id': order.id,
                'order_number': order.order_number,
                'status': order.status.value,
                'total_amount': float(order.total_amount),
                'estimated_total': float(order.estimated_total) if order.estimated_total else None,
                'created_at': order.created_at.isoformat(),
                'is_catering': order.is_catering_order(),
                'caterer_business_name': caterer.business_name if caterer else None,
                'client_email': order.client.email if order.client else None
            }

            # Add catering-specific fields
            if order.is_catering_order():
                order_data.update({
                    'event_name': order.event_name,
                    'event_date': order.event_date.isoformat() if order.event_date else None,
                    'event_time': order.event_time.strftime('%H:%M') if order.event_time else None,
                    'guest_count': order.guest_count
                })

            orders_data.append(order_data)

        return jsonify({
            'orders': orders_data,
            'total': orders.total,
            'pages': orders.pages,
            'current_page': page
        }), 200

    except Exception as e:
        current_app.logger.error(f'Error fetching orders: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@order_bp.route('/', methods=['POST'])
@jwt_required()
def create_order():
    """
    Create a new order - supports both regular and catering orders

    REGULAR ORDER (Step-by-step form):
    {
        "caterer_id": 1,
        "order_type": "regular",
        "client_info": {
            "full_name": "John Doe",
            "email": "john@example.com",
            "phone_number": "123-456-7890"
        },
        "order_items": [
            {"menu_item_id": 1, "quantity": 2, "customization": "No onions"}
        ],
        "delivery_location": "123 Main St, City",
        "dietary_requirements": ["vegetarian", "gluten-free"],
        "notes": "Additional instructions"
    }

    CATERING ORDER (Bulk order):
    {
        "caterer_id": 1,
        "order_type": "catering",
        "event_name": "Company Meeting",
        "event_type": "corporate",  // wedding, birthday, corporate, etc.
        "event_date": "2025-11-15",
        "event_time": "12:00",
        "delivery_location": "123 Main St, City",
        "guest_count": 50,
        "special_requirements": ["vegetarian", "nut-free"],
        "client_info": {
            "full_name": "John Doe",
            "email": "john@example.com",
            "phone_number": "123-456-7890"
        },
        "order_items": [
            {
                "menu_item_id": 1,
                "quantity": 5,
                "servings_per_unit": 10,
                "special_instructions": "No spicy sauce"
            }
        ],
        "notes": "Additional catering notes"
    }
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        # Validate required fields
        if 'caterer_id' not in data or 'order_items' not in data:
            return jsonify({'error': 'Missing required fields: caterer_id and order_items'}), 400

        # Validate caterer exists
        caterer = CatererProfile.query.get(data['caterer_id'])
        if not caterer:
            return jsonify({'error': 'Caterer not found'}), 404

        # Determine order type
        order_type = data.get('order_type', 'regular')  # Default to regular

        # Calculate total and validate menu items
        total_amount = 0
        order_items_data = []

        for item in data['order_items']:
            if 'menu_item_id' not in item or 'quantity' not in item:
                return jsonify({'error': 'Each order item must have menu_item_id and quantity'}), 400

            menu_item = MenuItem.query.filter_by(
                id=item['menu_item_id'],
                caterer_id=data['caterer_id']
            ).first()

            if not menu_item:
                return jsonify({'error': f'Menu item not found for this caterer: {item["menu_item_id"]}'}), 404

            if not menu_item.is_active:
                return jsonify({'error': f'Menu item not available: {menu_item.name}'}), 400

            quantity = item['quantity']
            unit_price = float(menu_item.price)
            item_total = unit_price * quantity

            total_amount += item_total

            order_items_data.append({
                'menu_item': menu_item,
                'quantity': quantity,
                'unit_price': unit_price,
                'customization': item.get('customization', ''),
                'servings_per_unit': item.get('servings_per_unit', 1),
                'special_instructions': item.get('special_instructions', '')
            })

        # Create comprehensive notes based on order type
        if order_type == 'regular':
            # Regular order notes format
            client_info = data.get('client_info', {})
            notes_parts = [
                f"CLIENT: {client_info.get('full_name', '')}",
                f"EMAIL: {client_info.get('email', '')}",
                f"PHONE: {client_info.get('phone_number', '')}",
                f"DELIVERY: {data.get('delivery_location', '')}",
                f"DIETARY: {', '.join(data.get('dietary_requirements', []))}",
                f"NOTES: {data.get('notes', '')}"
            ]
            notes = "\n".join([part for part in notes_parts if part.split(': ')[1]])
        else:
            # Catering order notes format
            client_info = data.get('client_info', {})
            notes_parts = [
                f"EVENT: {data.get('event_name', '')}",
                f"TYPE: {data.get('event_type', '')}",
                f"DATE: {data.get('event_date', '')} at {data.get('event_time', '')}",
                f"GUESTS: {data.get('guest_count', '')}",
                f"DELIVERY: {data.get('delivery_location', '')}",
                f"CLIENT: {client_info.get('full_name', '')}",
                f"EMAIL: {client_info.get('email', '')}",
                f"PHONE: {client_info.get('phone_number', '')}",
                f"REQUIREMENTS: {', '.join(data.get('special_requirements', []))}",
                f"NOTES: {data.get('notes', '')}"
            ]
            notes = "\n".join([part for part in notes_parts if part.split(': ')[1]])

        # Create order
        order = Order(
            order_number=generate_catering_order_number() if order_type == 'catering' else generate_order_number(),
            client_id=current_user_id,
            caterer_id=data['caterer_id'],
            total_amount=total_amount,
            estimated_total=total_amount,
            status=OrderStatus.PENDING,
            notes=notes
        )

        # Add catering-specific fields if this is a catering order
        if order_type == 'catering':
            order.event_name = data.get('event_name')
            order.event_date = datetime.strptime(data['event_date'], '%Y-%m-%d').date() if data.get(
                'event_date') else None
            order.event_time = datetime.strptime(data['event_time'], '%H:%M').time() if data.get('event_time') else None
            order.delivery_address = data.get('delivery_location', '')
            order.guest_count = data.get('guest_count')
            order.special_requirements = data.get('special_requirements', [])

        db.session.add(order)
        db.session.flush()

        # Create order items
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=item_data['menu_item'].id,
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                customization=item_data['customization'],
                servings_per_unit=item_data['servings_per_unit'],
                special_instructions=item_data['special_instructions']
            )
            db.session.add(order_item)

        db.session.commit()

        # Prepare response
        response_data = {
            'message': 'Order created successfully',
            'order': {
                'id': order.id,
                'order_number': order.order_number,
                'order_type': order_type,
                'total_amount': float(order.total_amount),
                'status': order.status.value,
                'caterer_business_name': caterer.business_name
            }
        }

        # Add catering-specific response data
        if order_type == 'catering':
            response_data['order'].update({
                'event_name': order.event_name,
                'event_date': order.event_date.isoformat() if order.event_date else None,
                'event_time': order.event_time.strftime('%H:%M') if order.event_time else None,
                'guest_count': order.guest_count
            })

        return jsonify(response_data), 201

    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': 'Invalid date or time format'}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating order: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@order_bp.route('/calculate-total', methods=['POST'])
def calculate_order_total():
    """
    Calculate order total before submission
    Useful for showing estimated total in the UI
    """
    try:
        data = request.get_json()

        if 'order_items' not in data or 'caterer_id' not in data:
            return jsonify({'error': 'Missing required fields: caterer_id and order_items'}), 400

        total_amount = 0
        items_breakdown = []

        for item in data['order_items']:
            if 'menu_item_id' not in item or 'quantity' not in item:
                continue

            menu_item = MenuItem.query.filter_by(
                id=item['menu_item_id'],
                caterer_id=data['caterer_id'],
                is_active=True
            ).first()

            if menu_item:
                quantity = item['quantity']
                unit_price = float(menu_item.price)
                item_total = unit_price * quantity
                total_amount += item_total

                items_breakdown.append({
                    'menu_item_id': menu_item.id,
                    'name': menu_item.name,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'item_total': item_total
                })

        return jsonify({
            'estimated_total': total_amount,
            'items_breakdown': items_breakdown,
            'item_count': len(items_breakdown)
        }), 200

    except Exception as e:
        current_app.logger.error(f'Error calculating order total: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@order_bp.route('/<int:order_id>/details', methods=['GET', 'PATCH'])
@jwt_required()
def order_details(order_id):
    """
    GET: Get order details in a format suitable for the step-by-step form
    PATCH: Update order status (for caterers and admins)
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        # Find order with access control
        if user.role == UserRole.CLIENT:
            order = Order.query.filter_by(id=order_id, client_id=current_user_id).first()
        elif user.role == UserRole.CATERER:
            order = Order.query.filter_by(
                id=order_id,
                caterer_id=user.caterer_profile.id
            ).first()
        else:  # ADMIN
            order = Order.query.get(order_id)

        if not order:
            return jsonify({'error': 'Order not found'}), 404

        # Handle GET request - Get order details
        if request.method == 'GET':
            # Get caterer business name safely
            caterer = CatererProfile.query.get(order.caterer_id)
            caterer_business_name = caterer.business_name if caterer else None

            # Parse notes to extract client info (for regular orders)
            client_info = {}
            dietary_requirements = []
            delivery_location = ""

            if order.notes:
                for line in order.notes.split('\n'):
                    if line.startswith('CLIENT:'):
                        client_info['full_name'] = line.replace('CLIENT:', '').strip()
                    elif line.startswith('EMAIL:'):
                        client_info['email'] = line.replace('EMAIL:', '').strip()
                    elif line.startswith('PHONE:'):
                        client_info['phone_number'] = line.replace('PHONE:', '').strip()
                    elif line.startswith('DELIVERY:'):
                        delivery_location = line.replace('DELIVERY:', '').strip()
                    elif line.startswith('DIETARY:'):
                        dietary_str = line.replace('DIETARY:', '').strip()
                        if dietary_str:
                            dietary_requirements = [req.strip() for req in dietary_str.split(',')]

            order_data = {
                'id': order.id,
                'order_number': order.order_number,
                'order_type': 'catering' if order.is_catering_order() else 'regular',
                'status': order.status.value,
                'total_amount': float(order.total_amount),
                'estimated_total': float(order.estimated_total) if order.estimated_total else None,
                'final_total': float(order.final_total) if order.final_total else None,
                'deposit_paid': float(order.deposit_paid) if order.deposit_paid else 0,
                'created_at': order.created_at.isoformat(),
                'updated_at': order.updated_at.isoformat() if order.updated_at else None,
                'caterer_business_name': caterer_business_name,
                'client_info': client_info,
                'delivery_location': delivery_location,
                'dietary_requirements': dietary_requirements,
                'order_items': []
            }

            # Add catering-specific fields
            if order.is_catering_order():
                order_data.update({
                    'event_name': order.event_name,
                    'event_date': order.event_date.isoformat() if order.event_date else None,
                    'event_time': order.event_time.strftime('%H:%M') if order.event_time else None,
                    'delivery_address': order.delivery_address,
                    'delivery_instructions': order.delivery_instructions,
                    'guest_count': order.guest_count,
                    'special_requirements': order.special_requirements or [],
                    'confirmed_at': order.confirmed_at.isoformat() if order.confirmed_at else None,
                    'delivery_date': order.delivery_date.isoformat() if order.delivery_date else None
                })

            # Add order items
            for item in order.order_items:
                # Get menu item details safely
                menu_item = MenuItem.query.get(item.menu_item_id)

                item_data = {
                    'id': item.id,
                    'menu_item_id': item.menu_item_id,
                    'menu_item_name': menu_item.name if menu_item else "Unknown Item",
                    'menu_item_description': menu_item.description if menu_item else "",
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'customization': item.customization,
                    'item_total': float(item.quantity * item.unit_price)
                }

                if order.is_catering_order():
                    item_data.update({
                        'servings_per_unit': item.servings_per_unit,
                        'special_instructions': item.special_instructions,
                        'total_servings': item.total_servings()
                    })

                order_data['order_items'].append(item_data)

            return jsonify(order_data), 200

        # Handle PATCH request - Update order status
        elif request.method == 'PATCH':
            # Only caterers and admins can update order status
            if user.role == UserRole.CLIENT:
                return jsonify({'error': 'Unauthorized to update order status'}), 403

            data = request.get_json()

            if not data:
                return jsonify({'error': 'No data provided'}), 400

            # Track what was updated for response
            updated_fields = []

            # Update status if provided
            if 'status' in data:
                try:
                    new_status = OrderStatus(data['status'])
                    old_status = order.status
                    order.status = new_status
                    order.updated_at = datetime.utcnow()
                    updated_fields.append('status')

                    # Set confirmed_at if status changed to CONFIRMED
                    if new_status == OrderStatus.CONFIRMED and old_status != OrderStatus.CONFIRMED:
                        order.confirmed_at = datetime.utcnow()
                        updated_fields.append('confirmed_at')

                    # Set delivery_date if status changed to OUT_FOR_DELIVERY
                    if new_status == OrderStatus.OUT_FOR_DELIVERY and not order.delivery_date:
                        order.delivery_date = datetime.utcnow()
                        updated_fields.append('delivery_date')

                except ValueError:
                    return jsonify({'error': 'Invalid status value'}), 400

            # Update financial fields if provided (caterers only)
            if user.role in [UserRole.CATERER, UserRole.ADMIN]:
                if 'final_total' in data:
                    order.final_total = data['final_total']
                    order.updated_at = datetime.utcnow()
                    updated_fields.append('final_total')

                if 'deposit_paid' in data:
                    order.deposit_paid = data['deposit_paid']
                    order.updated_at = datetime.utcnow()
                    updated_fields.append('deposit_paid')

            # Update catering-specific fields if provided
            if order.is_catering_order():
                if 'delivery_instructions' in data and user.role in [UserRole.CATERER, UserRole.ADMIN]:
                    order.delivery_instructions = data['delivery_instructions']
                    order.updated_at = datetime.utcnow()
                    updated_fields.append('delivery_instructions')

            db.session.commit()

            return jsonify({
                'message': 'Order updated successfully',
                'updated_fields': updated_fields,
                'order': {
                    'id': order.id,
                    'order_number': order.order_number,
                    'status': order.status.value,
                    'final_total': float(order.final_total) if order.final_total else None,
                    'deposit_paid': float(order.deposit_paid) if order.deposit_paid else 0,
                    'updated_at': order.updated_at.isoformat()
                }
            }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error in order details: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500
# Keep all the other existing endpoints from previous version:
# - get_orders (with filtering)
# - update_order_status
# - update_order
# - get_order_stats
