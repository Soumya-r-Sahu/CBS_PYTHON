#!/usr/bin/env python
"""
Employee Management API Server

This script runs a Flask server for the employee management
REST API in the HR-ERP system.
"""

import sys
import os
import logging
from pathlib import Path

# Ensure parent directory is in path
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import Flask
try:
    from flask import Flask, request, jsonify
except ImportError:
    print("Flask is required. Install it with: pip install flask")
    sys.exit(1)

# Import API controller
from hr_erp.employee_management.presentation.api import EmployeeApiController


# Create Flask app
app = Flask(__name__)

# Create API controller
controller = EmployeeApiController()


@app.route('/api/employees', methods=['GET'])
def get_all_employees():
    """Get all employees endpoint"""
    result = controller.get_all_employees()
    return jsonify(result)


@app.route('/api/employees/<employee_id>', methods=['GET'])
def get_employee(employee_id):
    """Get employee by ID endpoint"""
    result = controller.get_employee(employee_id)
    return jsonify(result)


@app.route('/api/employees', methods=['POST'])
def create_employee():
    """Create employee endpoint"""
    if not request.is_json:
        return jsonify({
            "status": "error", 
            "message": "Request must be JSON", 
            "data": None
        }), 400
        
    data = request.get_json()
    result = controller.create_employee(data)
    
    if result["status"] == "error":
        return jsonify(result), 400
        
    return jsonify(result), 201


@app.route('/api/employees/<employee_id>', methods=['PUT'])
def update_employee(employee_id):
    """Update employee endpoint"""
    if not request.is_json:
        return jsonify({
            "status": "error", 
            "message": "Request must be JSON", 
            "data": None
        }), 400
        
    data = request.get_json()
    result = controller.update_employee(employee_id, data)
    
    if result["status"] == "error" and "not found" in result["message"]:
        return jsonify(result), 404
    elif result["status"] == "error":
        return jsonify(result), 400
        
    return jsonify(result)


@app.route('/api/employees/<employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    """Delete employee endpoint"""
    result = controller.delete_employee(employee_id)
    
    if result["status"] == "error" and "not found" in result["message"]:
        return jsonify(result), 404
    elif result["status"] == "error":
        return jsonify(result), 500
        
    return jsonify(result), 204


def main():
    """Main entry point for the employee management API server"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)


if __name__ == '__main__':
    main()
