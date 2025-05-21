"""
Service Registry Examples

This file provides practical examples of how to use the service registry
for service registration, discovery, and fallback handling.
"""

from utils.lib.service_registry import ServiceRegistry

#ai:section:start - Basic Service Registration
def example_register_service():
    """Example of registering a service"""
    # Create a sample service
    class PaymentService:
        def process_payment(self, payment_data):
            return True, "Payment processed"
    
    # Get registry instance
    registry = ServiceRegistry()
    
    # Register the service with version and module name
    registry.register('payment.example', PaymentService(), '1.0.0', 'payments')
    
    return "Service registered successfully"
#ai:section:end

#ai:section:start - Service Discovery
def example_discover_service():
    """Example of discovering and using a service"""
    registry = ServiceRegistry()
    
    # Get service by name
    payment_service = registry.get_service('payment.example')
    
    if payment_service:
        # Use the service
        success, message = payment_service.process_payment({
            'amount': 100.0,
            'account': '12345'
        })
        return f"Service call result: {success}, {message}"
    else:
        return "Service not found"
#ai:section:end

#ai:section:start - Fallback Behavior
def example_fallback_service():
    """Example of using fallback services"""
    registry = ServiceRegistry()
    
    # Register a fallback
    class FallbackService:
        def process_payment(self, payment_data):
            return True, "Payment processed by fallback"
    
    registry.register_fallback('payment.missing', FallbackService())
    
    # Try to get a service that doesn't exist in primary registry
    service = registry.get_service('payment.missing')
    
    if service:
        # This will use the fallback
        success, message = service.process_payment({'amount': 50.0})
        return f"Fallback result: {success}, {message}"
    else:
        return "No service or fallback found"
#ai:section:end

#ai:section:start - Module Activation/Deactivation
def example_module_activation():
    """Example of module activation and deactivation"""
    registry = ServiceRegistry()
    
    # Register services from a module
    class TransferService:
        def transfer(self, data):
            return True, "Transfer completed"
    
    class BalanceService:
        def get_balance(self, account_id):
            return 1000.0
    
    # Register services from the 'accounts' module
    registry.register('accounts.transfer', TransferService(), '1.0.0', 'accounts')
    registry.register('accounts.balance', BalanceService(), '1.0.0', 'accounts')
    
    # Deactivate the module
    deactivated = registry.deactivate_module('accounts')
    
    # Try to use a service (will return None)
    transfer_service = registry.get_service('accounts.transfer')
    
    # Reactivate the module
    activated = registry.activate_module('accounts')
    
    # Now the service is available again
    transfer_service = registry.get_service('accounts.transfer')
    
    return {
        "deactivated": deactivated,
        "activated": activated,
        "service_available": transfer_service is not None
    }
#ai:section:end

#ai:section:start - Versioned Services
def example_versioned_services():
    """Example of using versioned services"""
    registry = ServiceRegistry()
    
    # Register multiple versions of a service
    class PaymentV1:
        def process(self, data):
            return "v1 processed"
    
    class PaymentV2:
        def process(self, data):
            return "v2 processed with enhanced security"
    
    registry.register('payment.processor', PaymentV1(), '1.0.0', 'payments')
    registry.register('payment.processor', PaymentV2(), '2.0.0', 'payments')
    
    # Get latest version (default behavior)
    latest = registry.get_service('payment.processor')
    latest_result = latest.process({})
    
    # Get specific version
    v1 = registry.get_service('payment.processor', '1.0.0')
    v1_result = v1.process({})
    
    return {
        "latest_version_result": latest_result,
        "v1_result": v1_result
    }
#ai:section:end

# [ENTRY_POINT] - Execute examples if run directly
if __name__ == "__main__":
    print("Example 1:", example_register_service())
    print("Example 2:", example_discover_service())
    print("Example 3:", example_fallback_service())
    print("Example 4:", example_module_activation())
    print("Example 5:", example_versioned_services())
