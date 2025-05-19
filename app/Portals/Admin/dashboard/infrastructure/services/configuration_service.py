from typing import Dict, List, Optional, Any

from dashboard.application.interfaces.repositories import SystemConfigRepository
from dashboard.application.interfaces.services import ConfigurationService, AuditService
from dashboard.domain.entities.system_config import SystemConfig


class ConfigurationServiceImpl(ConfigurationService):
    """Implementation of the Configuration Service"""
    
    def __init__(
        self, 
        config_repository: SystemConfigRepository,
        audit_service: AuditService
    ):
        self.config_repository = config_repository
        self.audit_service = audit_service
    
    def get_all_configs(self) -> List[SystemConfig]:
        """Get all system configurations"""
        return self.config_repository.get_all_configs()
    
    def get_config_by_key(self, key: str) -> Optional[SystemConfig]:
        """Get system configuration by key"""
        return self.config_repository.get_config_by_key(key)
    
    def save_config(self, config: SystemConfig, user_id: str) -> SystemConfig:
        """Save a configuration"""
        saved_config = self.config_repository.save_config(config)
        
        # Log this action
        self.audit_service.log_action(
            user_id=user_id,
            action="SAVE_CONFIG",
            resource_type="SYSTEM_CONFIG",
            resource_id=saved_config.key,
            details=f"Updated system configuration: {saved_config.key}"
        )
        
        return saved_config
    
    def delete_config(self, key: str, user_id: str) -> bool:
        """Delete a configuration"""
        result = self.config_repository.delete_config(key)
        
        if result:
            # Log this action
            self.audit_service.log_action(
                user_id=user_id,
                action="DELETE_CONFIG",
                resource_type="SYSTEM_CONFIG",
                resource_id=key,
                details=f"Deleted system configuration: {key}"
            )
        
        return result
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key, with optional default"""
        config = self.config_repository.get_config_by_key(key)
        return config.value if config else default
    
    def update_multiple_configs(self, configs: Dict[str, Any], user_id: str) -> Dict[str, bool]:
        """Update multiple configurations at once"""
        results = {}
        
        for key, value in configs.items():
            config = self.config_repository.get_config_by_key(key)
            
            if config:
                config.value = value
                self.config_repository.save_config(config)
                results[key] = True
                
                # Log this action
                self.audit_service.log_action(
                    user_id=user_id,
                    action="UPDATE_CONFIG",
                    resource_type="SYSTEM_CONFIG",
                    resource_id=key,
                    details=f"Updated system configuration: {key}"
                )
            else:
                results[key] = False
        
        return results
