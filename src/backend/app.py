#!/usr/bin/env python3
"""
OpenShift Service Mesh Inventory Demo - Backend API
A Flask application demonstrating Service Mesh integration with PostgreSQL and legacy VM services.
"""

import os
import logging
import requests
import re
from datetime import datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Database configuration from environment variables
DB_HOST = os.getenv('DB_HOST', 'postgres-service')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'inventory')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

# Service Mesh configuration
LEGACY_SERVICE_URL = os.getenv('LEGACY_SERVICE_URL', 'http://legacy-service:8080')
USE_MOCK_VALIDATION = os.getenv('USE_MOCK_VALIDATION', 'false').lower() == 'true'

# Flask configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# Initialize database
db = SQLAlchemy(app)

# Database Models
class Item(db.Model):
    """Inventory item model"""
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert item to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'quantity': self.quantity,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f'<Item {self.code}: {self.name}>'

# Health Check Endpoints
@app.route('/health')
def health():
    """Health check endpoint for Kubernetes liveness probe"""
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'inventory-backend',
        'version': '1.0.0'
    }

@app.route('/ready')
def ready():
    """Readiness check endpoint for Kubernetes readiness probe"""
    try:
        # Test database connection
        db.session.execute(text('SELECT 1'))
        db.session.commit()
        
        return {
            'status': 'ready',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            'status': 'not ready',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }, 503

@app.route('/info')
def info():
    """Service information endpoint"""
    return {
        'service': 'inventory-backend',
        'version': '1.0.0',
        'description': 'OpenShift Service Mesh Inventory Demo Backend',
        'features': {
            'service_mesh': True,
            'database': 'postgresql',
            'legacy_integration': not USE_MOCK_VALIDATION,
            'mock_validation': USE_MOCK_VALIDATION
        },
        'configuration': {
            'database_host': DB_HOST,
            'legacy_service_url': LEGACY_SERVICE_URL if not USE_MOCK_VALIDATION else 'mock',
            'cors_enabled': True
        }
    }

# Validation Functions
def mock_validate_item_code(code):
    """Mock validation service for testing without VM"""
    logger.info(f"Using mock validation for item code: {code}")
    
    # Basic validation rules
    if not code:
        return False, "Code cannot be empty"
    
    if len(code) != 6:
        return False, "Code must be exactly 6 characters"
    
    if not code[0].isalpha():
        return False, "Code must start with a letter"
    
    if not code.isalnum():
        return False, "Code must contain only letters and numbers"
    
    # Reserved prefixes (simulate legacy business rules)
    reserved_prefixes = ['XX', 'ZZ', 'TEST', 'TEMP', 'DEMO']
    for prefix in reserved_prefixes:
        if code.startswith(prefix):
            return False, f"Code cannot start with reserved prefix: {prefix}"
    
    # Simulate some business logic
    if code.endswith('000'):
        return False, "Code cannot end with '000' (reserved for system use)"
    
    return True, "Valid item code (mock validation)"

def legacy_validate_item_code(code):
    """Validate item code using legacy VM service through Service Mesh"""
    try:
        logger.info(f"Validating item code {code} with legacy service at {LEGACY_SERVICE_URL}")
        
        # Call legacy service through Service Mesh
        response = requests.post(
            f'{LEGACY_SERVICE_URL}/validate',
            json={'code': code},
            timeout=10,
            headers={
                'Content-Type': 'application/json',
                'X-Service-Mesh': 'true'
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Legacy validation result: {result}")
            return result.get('valid', False), result.get('message', 'Unknown validation result')
        else:
            logger.error(f"Legacy service returned status {response.status_code}: {response.text}")
            return False, f"Validation service error: HTTP {response.status_code}"
            
    except requests.exceptions.Timeout:
        logger.error("Legacy validation service timeout")
        return False, "Validation service timeout - please try again"
    except requests.exceptions.ConnectionError:
        logger.error(f"Cannot connect to legacy service at {LEGACY_SERVICE_URL}")
        return False, "Cannot connect to validation service"
    except requests.exceptions.RequestException as e:
        logger.error(f"Legacy validation request failed: {e}")
        return False, f"Validation service error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error in legacy validation: {e}")
        return False, "Unexpected validation error"

def validate_item_code(code):
    """Main validation function - routes to mock or legacy service"""
    if USE_MOCK_VALIDATION:
        return mock_validate_item_code(code)
    else:
        return legacy_validate_item_code(code)

# API Routes
@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    """Get all inventory items"""
    try:
        logger.info("Fetching inventory items")
        
        # Get query parameters for pagination and filtering
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search', '').strip()
        
        # Build query
        query = Item.query
        
        # Apply search filter if provided
        if search:
            query = query.filter(
                db.or_(
                    Item.code.ilike(f'%{search}%'),
                    Item.name.ilike(f'%{search}%')
                )
            )
        
        # Apply pagination and ordering
        items = query.order_by(Item.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = {
            'items': [item.to_dict() for item in items.items],
            'pagination': {
                'page': items.page,
                'pages': items.pages,
                'per_page': items.per_page,
                'total': items.total
            }
        }
        
        logger.info(f"Returned {len(items.items)} items (page {page} of {items.pages})")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Failed to fetch inventory: {e}")
        return jsonify({'error': 'Failed to fetch inventory'}), 500

@app.route('/api/inventory', methods=['POST'])
def add_item():
    """Add new inventory item"""
    try:
        data = request.get_json()
        logger.info(f"Adding new item: {data}")
        
        # Validate request data
        if not data or not all(k in data for k in ['code', 'name', 'quantity']):
            return jsonify({
                'error': 'Missing required fields: code, name, quantity'
            }), 400
        
        # Extract and validate fields
        code = data['code'].strip().upper()
        name = data['name'].strip()
        quantity = data['quantity']
        
        # Basic validation
        if not code or not name:
            return jsonify({'error': 'Code and name cannot be empty'}), 400
        
        if not isinstance(quantity, int) or quantity < 0:
            return jsonify({'error': 'Quantity must be a non-negative integer'}), 400
        
        if len(code) > 10:
            return jsonify({'error': 'Item code cannot exceed 10 characters'}), 400
        
        if len(name) > 100:
            return jsonify({'error': 'Item name cannot exceed 100 characters'}), 400
        
        # Check if item already exists
        existing_item = Item.query.filter_by(code=code).first()
        if existing_item:
            return jsonify({
                'error': f'Item with code {code} already exists',
                'existing_item': existing_item.to_dict()
            }), 409
        
        # Validate item code with legacy service (or mock)
        is_valid, validation_message = validate_item_code(code)
        if not is_valid:
            logger.warning(f"Item code validation failed for {code}: {validation_message}")
            return jsonify({'error': f'Invalid item code: {validation_message}'}), 400
        
        # Create new item
        new_item = Item(code=code, name=name, quantity=quantity)
        db.session.add(new_item)
        db.session.commit()
        
        logger.info(f"Successfully added new item: {code} - {name} (qty: {quantity})")
        return jsonify(new_item.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to add item: {e}")
        return jsonify({'error': 'Failed to add item'}), 500

@app.route('/api/inventory/<int:item_id>', methods=['GET'])
def get_item(item_id):
    """Get specific inventory item"""
    try:
        item = Item.query.get_or_404(item_id)
        return jsonify(item.to_dict())
    except Exception as e:
        logger.error(f"Failed to fetch item {item_id}: {e}")
        return jsonify({'error': 'Item not found'}), 404

@app.route('/api/inventory/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    """Update inventory item"""
    try:
        item = Item.query.get_or_404(item_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update allowed fields
        if 'name' in data:
            item.name = data['name'].strip()
        if 'quantity' in data:
            if not isinstance(data['quantity'], int) or data['quantity'] < 0:
                return jsonify({'error': 'Quantity must be a non-negative integer'}), 400
            item.quantity = data['quantity']
        
        item.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Updated item {item_id}: {item.code}")
        return jsonify(item.to_dict())
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to update item {item_id}: {e}")
        return jsonify({'error': 'Failed to update item'}), 500

@app.route('/api/inventory/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    """Delete inventory item"""
    try:
        item = Item.query.get_or_404(item_id)
        item_code = item.code
        
        db.session.delete(item)
        db.session.commit()
        
        logger.info(f"Deleted item {item_id}: {item_code}")
        return jsonify({'message': f'Item {item_code} deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to delete item {item_id}: {e}")
        return jsonify({'error': 'Failed to delete item'}), 500

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

# Database initialization
def create_tables():
    """Create database tables if they don't exist"""
    try:
        with app.app_context():
            db.create_all()
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

# Application startup
if __name__ == '__main__':
    # Create database tables
    create_tables()
    
    # Log startup information
    logger.info("Starting OpenShift Service Mesh Inventory Demo Backend")
    logger.info(f"Database: postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    logger.info(f"Legacy service: {LEGACY_SERVICE_URL}")
    logger.info(f"Mock validation: {USE_MOCK_VALIDATION}")
    
    # Start Flask development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    )