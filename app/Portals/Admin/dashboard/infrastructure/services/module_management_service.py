"""
Module management service implementation.
"""
from typing import Dict, List, Optional, Any
from dashboard.domain.entities.module import Module, ModuleStatus
from dashboard.application.interfaces.services import ModuleManagementService
from dashboard.application.interfaces.repositories import ModuleRepository
from dashboard.domain.entities.audit_log import AuditLog, AuditLogAction, AuditLogSeverity
from dashboard.application.interfaces.repositories import AuditLogRepository


class ModuleManagementServiceImpl(ModuleManagementService):
    """Implementation of the ModuleManagementService interface."""
    
    def __init__(
        self, 
        module_repository: ModuleRepository,
        audit_log_repository: AuditLogRepository
    ):
        self.module_repository = module_repository
        self.audit_log_repository = audit_log_repository
    
    def toggle_module(self, module_id: str, enabled: bool, user_id: str = None) -> Module:
        """Enable or disable a module."""
        module = self.module_repository.get_module_by_id(module_id)
        if not module:
            raise ValueError(f"Module with ID {module_id} not found")
        
        # Update module status based on enabled flag
        new_status = ModuleStatus.ACTIVE if enabled else ModuleStatus.DEACTIVATED
        
        # Check if we can make this status change
        if module.status == new_status:
            # No change needed
            return module
        
        # Update module status
        updated_module = self.module_repository.update_module_status(module_id, new_status)
        
        # Log the action
        if user_id:
            action = AuditLogAction.ENABLE if enabled else AuditLogAction.DISABLE
            self.audit_log_repository.create_log(
                AuditLog(
                    user_id=user_id,
                    action=action,
                    resource_type="module",
                    resource_id=module_id,
                    severity=AuditLogSeverity.INFO,
                    details={
                        "old_status": module.status.value,
                        "new_status": new_status.value
                    },
                    success=True
                )
            )
        
        return updated_module
    
    def check_dependencies(self, module_id: str) -> Dict[str, bool]:
        """Check if all dependencies for a module are satisfied."""
        module = self.module_repository.get_module_by_id(module_id)
        if not module:
            raise ValueError(f"Module with ID {module_id} not found")
        
        # Initialize result dictionary
        dependency_status = {}
        
        # Check each dependency
        for dep_id in module.dependencies:
            dependency = self.module_repository.get_module_by_id(dep_id)
            if not dependency:
                dependency_status[dep_id] = False
            else:
                # A dependency is satisfied if it's ACTIVE
                dependency_status[dep_id] = dependency.status == ModuleStatus.ACTIVE
        
        return dependency_status
    
    def restart_module(self, module_id: str, user_id: str = None) -> bool:
        """Restart a module."""
        module = self.module_repository.get_module_by_id(module_id)
        if not module:
            raise ValueError(f"Module with ID {module_id} not found")
        
        # Check if we can restart this module (it should be active or failed)
        if module.status not in [ModuleStatus.ACTIVE, ModuleStatus.FAILED]:
            raise ValueError(f"Cannot restart module with status {module.status}")
        
        # In a real implementation, we would need to actually restart the module
        # For now, we'll just simulate it by setting the status to ACTIVE
        updated_module = self.module_repository.update_module_status(module_id, ModuleStatus.ACTIVE)
        
        # Log the action
        if user_id:
            self.audit_log_repository.create_log(
                AuditLog(
                    user_id=user_id,
                    action=AuditLogAction.RESTART,
                    resource_type="module",
                    resource_id=module_id,
                    severity=AuditLogSeverity.INFO,
                    details={
                        "old_status": module.status.value,
                        "new_status": ModuleStatus.ACTIVE.value
                    },
                    success=True
                )
            )
        
        return updated_module is not None
    
    def install_module(self, module_data: Dict[str, Any], user_id: str = None) -> Module:
        """Install a new module."""
        # Create a new module with INSTALLED status
        module = Module(
            id=module_data.get("id"),
            name=module_data.get("name"),
            version=module_data.get("version"),
            status=ModuleStatus.INSTALLED,
            dependencies=module_data.get("dependencies", []),
            description=module_data.get("description")
        )
        
        created_module = self.module_repository.create_module(module)
        
        # Log the action
        if user_id:
            self.audit_log_repository.create_log(
                AuditLog(
                    user_id=user_id,
                    action=AuditLogAction.CREATE,
                    resource_type="module",
                    resource_id=created_module.id,
                    severity=AuditLogSeverity.INFO,
                    details={
                        "name": created_module.name,
                        "version": created_module.version
                    },
                    success=True
                )
            )
        
        return created_module
    
    def uninstall_module(self, module_id: str, user_id: str = None) -> bool:
        """Uninstall a module."""
        module = self.module_repository.get_module_by_id(module_id)
        if not module:
            raise ValueError(f"Module with ID {module_id} not found")
        
        # Check if we can uninstall this module (it should not be ACTIVE)
        if module.status == ModuleStatus.ACTIVE:
            raise ValueError("Cannot uninstall an active module. Deactivate it first.")
        
        # Delete the module
        result = self.module_repository.delete_module(module_id)
        
        # Log the action
        if result and user_id:
            self.audit_log_repository.create_log(
                AuditLog(
                    user_id=user_id,
                    action=AuditLogAction.DELETE,
                    resource_type="module",
                    resource_id=module_id,
                    severity=AuditLogSeverity.INFO,
                    details={
                        "name": module.name,
                        "version": module.version
                    },
                    success=True
                )
            )
        
        return result
