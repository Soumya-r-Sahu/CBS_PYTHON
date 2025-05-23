# Deploy Clean Architecture Templates to All Modules
#
# This script copies the Clean Architecture template files to all relevant modules
# and performs basic customization of the templates for each module.
#
# Usage: python deploy_clean_architecture_templates.py

import os
import shutil
from datetime import datetime

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # Go up one directory
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
GUIDE_TEMPLATE_PATH = os.path.join(TEMPLATES_DIR, 'CLEAN_ARCHITECTURE_GUIDE_TEMPLATE.md')
PROGRESS_TEMPLATE_PATH = os.path.join(TEMPLATES_DIR, 'CLEAN_ARCHITECTURE_PROGRESS_TEMPLATE.md')

# List of modules to deploy to
MODULES = [
    'core_banking',
    'payments',
    'treasury',
    'digital_channels',
    'crm',
    'risk_compliance',
    'hr_erp',
    'security'
]

# Module-specific components (just a sample, to be expanded)
MODULE_COMPONENTS = {
    'core_banking': ['Accounts', 'Transactions', 'Customers', 'Products', 'Services'],
    'payments': ['Transfers', 'Cards', 'Mobile Payments', 'Payment Gateways', 'Reconciliation'],
    'treasury': ['Liquidity', 'Investments', 'Forex', 'Money Markets', 'Securities'],
    'digital_channels': ['Web Banking', 'Mobile Banking', 'API Gateway', 'ATM Interface', 'User Experience'],
    'crm': ['Customer Management', 'Campaign Management', 'Lead Management', 'Analytics', 'Reporting'],
    'risk_compliance': ['Risk Assessment', 'Compliance Management', 'Regulatory Reporting', 'Fraud Detection', 'Monitoring'],
    'hr_erp': ['Employee Management', 'Leave Management', 'Performance Management', 'Recruitment', 'Training'],
    'security': ['Authentication', 'Authorization', 'Encryption', 'Audit', 'Threat Management']
}

# Custom module guidelines (just a sample, to be expanded)
MODULE_GUIDELINES = {
    'core_banking': ['Maintain ACID compliance for all transaction operations', 
                    'Implement double-entry accounting principles', 
                    'Ensure audit trail for all account modifications'],
                    
    'payments': ['Implement idempotent transaction processing',
               'Follow PCI-DSS requirements for all card operations',
               'Provide comprehensive transaction receipts'],
               
    'treasury': ['Implement risk calculations based on Basel standards', 
               'Support multi-currency operations natively',
               'Maintain real-time position tracking'],
               
    'digital_channels': ['Implement responsive design patterns for all UIs',
                       'Support offline operation modes where possible',
                       'Maintain consistent branding across all channels'],
                       
    'crm': ['Ensure GDPR compliance for all customer data',
          'Implement customer segmentation capabilities',
          'Support multi-channel campaign management'],
          
    'risk_compliance': ['Implement configurable rule engines',
                      'Support regulatory report generation',
                      'Maintain audit trails for all risk assessments'],
                      
    'hr_erp': ['Support configurable workflow approvals',
             'Implement secure document management',
             'Provide flexible reporting capabilities'],
             
    'security': ['Implement defense in depth strategies',
               'Support multi-factor authentication',
               'Follow least privilege principles']
}

def deploy_templates():
    """Deploy templates to all specified modules"""
    
    print(f"Deploying Clean Architecture templates to {len(MODULES)} modules...")
    print(f"Base directory: {BASE_DIR}")
    
    now = datetime.now().strftime("%Y-%m-%d")
    
    # First ensure template directory exists
    if not os.path.exists(TEMPLATES_DIR):
        print(f"Creating templates directory: {TEMPLATES_DIR}")
        os.makedirs(TEMPLATES_DIR)
    
    # Check if template files exist, if not print an error
    if not os.path.exists(GUIDE_TEMPLATE_PATH):
        print(f"Error: Template file not found: {GUIDE_TEMPLATE_PATH}")
        return
    
    if not os.path.exists(PROGRESS_TEMPLATE_PATH):
        print(f"Error: Template file not found: {PROGRESS_TEMPLATE_PATH}")
        return
    
    for module in MODULES:
        module_path = os.path.join(BASE_DIR, module)
        
        if not os.path.exists(module_path):
            print(f"Warning: Module path {module_path} not found. Skipping.")
            continue
            
        print(f"Processing module: {module} at {module_path}")
            
        # Create guide file
        guide_path = os.path.join(module_path, 'CLEAN_ARCHITECTURE_GUIDE.md')
        progress_path = os.path.join(module_path, 'CLEAN_ARCHITECTURE_PROGRESS.md')
        
        # Read template content
        try:
            with open(GUIDE_TEMPLATE_PATH, 'r') as f:
                guide_content = f.read()
            
            with open(PROGRESS_TEMPLATE_PATH, 'r') as f:
                progress_content = f.read()
        except Exception as e:
            print(f"Error reading template files: {e}")
            continue
        
        # Customize content
        guide_content = guide_content.replace('[MODULE_NAME]', module.replace('_', ' ').title())
        progress_content = progress_content.replace('[MODULE_NAME]', module.replace('_', ' ').title())
        
        # Replace components
        components = MODULE_COMPONENTS.get(module, ['Component1', 'Component2', 'Component3', 'Component4', 'Component5'])
        for i, component in enumerate(components):
            if i < 5:  # Only replace up to 5 components
                progress_content = progress_content.replace(f'[Component{i+1}]', component)
        
        # Replace guidelines
        guidelines = MODULE_GUIDELINES.get(module, ['Guideline 1', 'Guideline 2', 'Guideline 3'])
        for i, guideline in enumerate(guidelines):
            if i < 3:  # Only replace up to 3 guidelines
                guide_content = guide_content.replace(f'[Guideline {i+1}]', guideline)
        
        # Add "TEMPORARY FILE" marking
        guide_content = "# TEMPORARY FILE - TO BE CUSTOMIZED\n\n" + guide_content
        progress_content = "# TEMPORARY FILE - TO BE CUSTOMIZED\n\n" + progress_content
        
        # Write customized content
        try:
            with open(guide_path, 'w') as f:
                f.write(guide_content)
            
            with open(progress_path, 'w') as f:
                f.write(progress_content)
            
            print(f"✅ Deployed templates to {module}")
        except Exception as e:
            print(f"Error writing files for module {module}: {e}")
    
    print("Deployment complete!")

if __name__ == "__main__":
    deploy_templates()
