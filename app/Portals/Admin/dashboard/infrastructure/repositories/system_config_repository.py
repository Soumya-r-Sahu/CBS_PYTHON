"""
System configuration repository implementation.
"""
from typing import Dict, List, Optional, Any
from dashboard.domain.entities.system_config import SystemConfig as SystemConfigEntity, ConfigType as ConfigTypeEntity
from dashboard.application.interfaces.repositories import SystemConfigRepository
from dashboard.models import SystemConfig as SystemConfigModel, ConfigType


class DjangoSystemConfigRepository(SystemConfigRepository):
    """Django implementation of the SystemConfigRepository interface."""

    def get_all_configs(self) -> List[SystemConfigEntity]:
        """Get all system configurations."""
        configs = SystemConfigModel.objects.all()
        return [self._to_entity(config) for config in configs]
    
    def get_config_by_id(self, config_id: str) -> Optional[SystemConfigEntity]:
        """Get a system configuration by its ID."""
        try:
            config = SystemConfigModel.objects.get(id=config_id)
            return self._to_entity(config)
        except SystemConfigModel.DoesNotExist:
            return None
    
    def get_configs_by_module(self, module_id: str) -> List[SystemConfigEntity]:
        """Get all system configurations for a specific module."""
        configs = SystemConfigModel.objects.filter(module_id=module_id)
        return [self._to_entity(config) for config in configs]
    
    def get_config_by_key(self, key: str) -> Optional[SystemConfigEntity]:
        """Get a system configuration by its key."""
        try:
            config = SystemConfigModel.objects.get(key=key)
            return self._to_entity(config)
        except SystemConfigModel.DoesNotExist:
            return None
    
    def create_config(self, config: SystemConfigEntity) -> SystemConfigEntity:
        """Create a new system configuration."""
        model = SystemConfigModel(
            id=config.id,
            key=config.key,
            value=config.value,
            type=config.type.value,
            module_id=config.module_id,
            description=config.description,
            is_sensitive=config.is_sensitive,
            allowed_values=config.allowed_values,
            modified_by_id=config.modified_by_id if config.modified_by_id else None
        )
        model.save()
        return self._to_entity(model)
    
    def update_config(self, config: SystemConfigEntity) -> SystemConfigEntity:
        """Update an existing system configuration."""
        try:
            model = SystemConfigModel.objects.get(id=config.id)
            model.key = config.key
            model.value = config.value
            model.type = config.type.value
            model.module_id = config.module_id
            model.description = config.description
            model.is_sensitive = config.is_sensitive
            model.allowed_values = config.allowed_values
            model.modified_by_id = config.modified_by_id if config.modified_by_id else None
            model.save()
            return self._to_entity(model)
        except SystemConfigModel.DoesNotExist:
            return None
    
    def delete_config(self, config_id: str) -> bool:
        """Delete a system configuration by its ID."""
        try:
            config = SystemConfigModel.objects.get(id=config_id)
            config.delete()
            return True
        except SystemConfigModel.DoesNotExist:
            return False
    
    def _to_entity(self, model: SystemConfigModel) -> SystemConfigEntity:
        """Convert a Django model to a domain entity."""
        return SystemConfigEntity(
            id=model.id,
            key=model.key,
            value=model.value,
            type=ConfigTypeEntity(model.type),
            module_id=model.module.id if model.module else None,
            description=model.description,
            is_sensitive=model.is_sensitive,
            allowed_values=model.allowed_values,
            modified_by_id=str(model.modified_by.id) if model.modified_by else None,
            last_modified=model.last_modified.isoformat() if model.last_modified else None
        )
