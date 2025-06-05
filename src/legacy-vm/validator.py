#!/usr/bin/env python3
"""
"Legacy" Item Code Validation Service
Simulates legacy business logic for item validation
Modern Python 3 on RHEL 8 (because life's too short for Python 2.7 dependency hell)
"""

import json
import re
import shutil
import os
from flask import Flask, request, jsonify
from datetime import datetime
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('legacy-validator')

# Add file handler
try:
    os.makedirs('/opt/validator/logs', exist_ok=True)
    file_handler = logging.FileHandler('/opt/validator/logs/validator.log')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
except Exception as e:
    logger.warning(f"Could not set up file logging: {e}")

app = Flask(__name__)

# "Legacy" business rules database (simulated)
LEGACY_RULES = {
    'prohibited_prefixes': ['XX', 'ZZ', 'TEST', 'TEMP', 'DEMO', 'SYS'],
    'prohibited_suffixes': ['000', '999', 'DEL', 'BAD'],
    'required_pattern': r'^[A-Z][A-Z0-9]{5}$',
    'special_codes': {
        'LEGACY': 'Reserved for legacy system migration',
        'SYSTEM': 'Reserved for system use',
        'ADMINS': 'Reserved for administrative functions'
    }
}

def validate_item_code(code):
    """
    "Legacy" validation logic with complex business rules
    (Actually modern Python 3 but pretending to be legacy!)
    """
    if not code:
        return False, "Item code cannot be empty"
    
    # Convert to uppercase for validation
    code = code.upper().strip()
    
    # Length check
    if len(code) != 6:
        return False, f"Item code must be exactly 6 characters, got {len(code)}"
    
    # Pattern check
    if not re.match(LEGACY_RULES['required_pattern'], code):
        return False, "Item code must start with letter and contain only alphanumeric characters"
    
    # Check prohibited prefixes
    for prefix in LEGACY_RULES['prohibited_prefixes']:
        if code.startswith(prefix):
            return False, f"Item code cannot start with prohibited prefix: {prefix}"
    
    # Check prohibited suffixes
    for suffix in LEGACY_RULES['prohibited_suffixes']:
        if code.endswith(suffix):
            return False, f"Item code cannot end with prohibited suffix: {suffix}"
    
    # Check special reserved codes
    if code in LEGACY_RULES['special_codes']:
        return False, f"Item code is reserved: {LEGACY_RULES['special_codes'][code]}"
    
    # "Legacy" checksum validation (simulated)
    checksum = sum(ord(c) for c in code) % 97
    if checksum < 10:
        return False, "Item code failed legacy checksum validation"
    
    # Simulate "legacy" database lookup delay
    time.sleep(0.1)
    
    return True, f"Item code {code} validated successfully by 'legacy' system"

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'legacy-validator',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'python_version': '3.8+ (Modern but pretending to be legacy!)',
        'os': 'RHEL 8',
        'note': 'This is a modern service simulating legacy behavior'
    })

@app.route('/validate', methods=['POST'])
def validate():
    """Main validation endpoint"""
    try:
        data = request.get_json()
        
        if not data or 'code' not in data:
            return jsonify({
                'valid': False,
                'message': 'Missing item code in request',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        code = data['code']
        logger.info(f"Validating item code: {code}")
        
        is_valid, message = validate_item_code(code)
        
        response = {
            'valid': is_valid,
            'message': message,
            'code': code.upper() if code else '',
            'timestamp': datetime.utcnow().isoformat(),
            'validator': 'modern-legacy-simulator-rhel8-python3'
        }
        
        logger.info(f"Validation result for {code}: {is_valid} - {message}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return jsonify({
            'valid': False,
            'message': f'Legacy validation service error: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/system', methods=['GET'])
def system_info():
    """System information endpoint for demo monitoring"""
    try:
        # Disk usage
        disk_usage = shutil.disk_usage('/')
        
        # Memory info
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
        
        mem_lines = meminfo.split('\n')
        mem_total = int([line for line in mem_lines if 'MemTotal' in line][0].split()[1]) * 1024
        mem_available_lines = [line for line in mem_lines if 'MemAvailable' in line]
        if mem_available_lines:
            mem_available = int(mem_available_lines[0].split()[1]) * 1024
        else:
            mem_free = int([line for line in mem_lines if 'MemFree' in line][0].split()[1]) * 1024
            mem_available = mem_free
        
        # Load average
        load_avg = os.getloadavg()
        
        return jsonify({
            'hostname': os.uname()[1],
            'uptime_hours': round(float(open('/proc/uptime').read().split()[0]) / 3600, 2),
            'disk': {
                'free_gb': round(disk_usage.free / (1024**3), 2),
                'total_gb': round(disk_usage.total / (1024**3), 2),
                'used_percent': round((disk_usage.used / disk_usage.total) * 100, 1)
            },
            'memory': {
                'total_gb': round(mem_total / (1024**3), 2),
                'available_gb': round(mem_available / (1024**3), 2),
                'used_percent': round((1 - mem_available / mem_total) * 100, 1)
            },
            'load_average': {
                '1min': load_avg[0],
                '5min': load_avg[1],
                '15min': load_avg[2]
            },
            'system_info': {
                'python_version': '3.8+',
                'os': 'RHEL 8',
                'message': 'Modern system simulating legacy behavior - much easier!'
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'error': f'Failed to get system info: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/info', methods=['GET'])
def info():
    """Service information"""
    return jsonify({
        'service': 'legacy-validator',
        'version': '1.0.0',
        'description': 'Modern service simulating legacy item validation (RHEL 8 + Python 3)',
        'stack': {
            'python': '3.8+',
            'os': 'RHEL 8',
            'flask': 'Modern version',
            'modernization_status': 'Actually modern, just simulating legacy behavior!'
        },
        'rules': {
            'code_length': 6,
            'pattern': 'Letter followed by 5 alphanumeric characters',
            'prohibited_prefixes': LEGACY_RULES['prohibited_prefixes'],
            'prohibited_suffixes': LEGACY_RULES['prohibited_suffixes']
        },
        'endpoints': {
            '/health': 'Health check',
            '/validate': 'POST - Validate item code',
            '/system': 'System monitoring info',
            '/info': 'Service information'
        }
    })

if __name__ == '__main__':
    logger.info("Starting 'Legacy' Item Validation Service")
    logger.info("RHEL 8 + Python 3 - Modern but simulating legacy behavior!")
    logger.info("Service will be available at http://0.0.0.0:8080")
    app.run(host='0.0.0.0', port=8080, debug=False)