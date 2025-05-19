"""
Customer Controller for Mobile Banking API

Handles customer account management and profile operations
"""

from flask import Blueprint, request, jsonify
from integration_interfaces.api.middleware.authentication import token_required
from integration_interfaces.api.middleware.error_handler import APIException
from database.python.connection import DatabaseConnection


# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
# Create blueprint
customer_api = Blueprint('customer_api', __name__)

# Initialize database connection
db_connection = DatabaseConnection()

@customer_api.route('/profile', methods=['GET'])
@token_required
def get_customer_profile(current_user):
    """
    Get profile information for the authenticated customer
    """
    try:
        conn = db_connection.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            """
            SELECT customer_id, first_name, last_name, email, phone, address, city,
                   state, pin_code, customer_type, customer_segment, kyc_status
            FROM customers
            WHERE customer_id = %s
            """,
            (current_user['customer_id'],)
        )
        
        customer = cursor.fetchone()
        
        if not customer:
            raise APIException(
                "Customer profile not found", 
                "PROFILE_NOT_FOUND", 
                404
            )
        
        return jsonify({
            'status': 'success',
            'data': {
                'profile': customer
            }
        }), 200
        
    except APIException as e:
        raise e
    except Exception as e:
        # Log the error
        print(f"Get Profile Error: {str(e)}")
        raise APIException(
            "Failed to fetch customer profile", 
            "FETCH_PROFILE_FAILED", 
            500
        )
    finally:
        cursor.close()
        conn.close()


@customer_api.route('/profile/contact', methods=['PUT'])
@token_required
def update_contact_info(current_user):
    """
    Update contact information for the customer
    
    Request body:
    {
        "email": "string",
        "phone": "string",
        "address": "string",
        "city": "string",
        "state": "string",
        "pin_code": "string"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            raise APIException(
                "Missing request body", 
                "MISSING_DATA", 
                400
            )
            
        # Collect fields to update
        update_fields = {}
        
        for field in ['email', 'phone', 'address', 'city', 'state', 'pin_code']:
            if field in data:
                update_fields[field] = data[field]
                
        if not update_fields:
            raise APIException(
                "No fields provided for update", 
                "NO_UPDATES", 
                400
            )
            
        # Build dynamic SQL for updates
        sql = "UPDATE customers SET "
        values = []
        
        for field, value in update_fields.items():
            sql += f"{field} = %s, "
            values.append(value)
            
        sql += "updated_at = NOW() WHERE customer_id = %s"
        values.append(current_user['customer_id'])
        
        conn = db_connection.get_connection()
        cursor = conn.cursor()
        
        # Execute update
        cursor.execute(sql, values)
        conn.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Contact information updated successfully'
        }), 200
        
    except APIException as e:
        conn.rollback()
        raise e
    except Exception as e:
        conn.rollback()
        # Log the error
        print(f"Update Contact Error: {str(e)}")
        raise APIException(
            "Failed to update contact information", 
            "UPDATE_CONTACT_FAILED", 
            500
        )
    finally:
        cursor.close()
        conn.close()


@customer_api.route('/beneficiaries', methods=['GET'])
@token_required
def get_beneficiaries(current_user):
    """
    Get saved beneficiaries for the customer
    """
    try:
        conn = db_connection.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            """
            SELECT b.id, b.beneficiary_name, b.account_number, b.ifsc_code,
                   b.bank_name, b.is_favorite, b.created_at
            FROM beneficiaries b
            JOIN customers c ON b.customer_id = c.id
            WHERE c.customer_id = %s
            ORDER BY b.is_favorite DESC, b.beneficiary_name ASC
            """,
            (current_user['customer_id'],)
        )
        
        beneficiaries = cursor.fetchall()
        
        # Format dates
        for ben in beneficiaries:
            if 'created_at' in ben and ben['created_at']:
                ben['created_at'] = ben['created_at'].strftime('%Y-%m-%d')
        
        return jsonify({
            'status': 'success',
            'data': {
                'beneficiaries': beneficiaries
            }
        }), 200
        
    except Exception as e:
        # Log the error
        print(f"Get Beneficiaries Error: {str(e)}")
        raise APIException(
            "Failed to fetch beneficiaries", 
            "FETCH_BENEFICIARIES_FAILED", 
            500
        )
    finally:
        cursor.close()
        conn.close()


@customer_api.route('/beneficiaries', methods=['POST'])
@token_required
def add_beneficiary(current_user):
    """
    Add a new beneficiary
    
    Request body:
    {
        "beneficiary_name": "string",
        "account_number": "string",
        "ifsc_code": "string",
        "bank_name": "string",
        "is_favorite": boolean
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            raise APIException(
                "Missing request body", 
                "MISSING_DATA", 
                400
            )
            
        # Validate required fields
        required_fields = ['beneficiary_name', 'account_number', 'ifsc_code']
        for field in required_fields:
            if field not in data:
                raise APIException(
                    f"Missing required field: {field}", 
                    "MISSING_FIELD", 
                    400
                )
                
        conn = db_connection.get_connection()
        cursor = conn.cursor()
        
        # Get customer ID from customer_id
        cursor.execute(
            """
            SELECT id FROM customers
            WHERE customer_id = %s
            """,
            (current_user['customer_id'],)
        )
        
        result = cursor.fetchone()
        if not result:
            raise APIException(
                "Customer not found", 
                "CUSTOMER_NOT_FOUND", 
                404
            )
            
        customer_id = result[0]
        
        # Check if beneficiary already exists
        cursor.execute(
            """
            SELECT id FROM beneficiaries
            WHERE customer_id = %s AND account_number = %s
            """,
            (customer_id, data['account_number'])
        )
        
        if cursor.fetchone():
            raise APIException(
                "Beneficiary with this account number already exists", 
                "DUPLICATE_BENEFICIARY", 
                400
            )
            
        # Add beneficiary
        cursor.execute(
            """
            INSERT INTO beneficiaries
            (customer_id, beneficiary_name, account_number, ifsc_code, bank_name, is_favorite, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """,
            (
                customer_id,
                data['beneficiary_name'],
                data['account_number'],
                data['ifsc_code'],
                data.get('bank_name', 'SBI'),
                data.get('is_favorite', False)
            )
        )
        
        conn.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Beneficiary added successfully'
        }), 201
        
    except APIException as e:
        conn.rollback()
        raise e
    except Exception as e:
        conn.rollback()
        # Log the error
        print(f"Add Beneficiary Error: {str(e)}")
        raise APIException(
            "Failed to add beneficiary", 
            "ADD_BENEFICIARY_FAILED", 
            500
        )
    finally:
        cursor.close()
        conn.close()
