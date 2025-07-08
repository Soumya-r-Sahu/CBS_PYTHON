"""
Module repository implementation.
"""
from typing import Dict, List, Optional, Any
from django.db.models import Q
from dashboard.domain.entities.module import Module as ModuleEntity, ModuleStatus as ModuleStatusEntity, FeatureFlag as FeatureFlagEntity
from dashboard.application.interfaces.repositories import ModuleRepository
from dashboard.models import Module as ModuleModel, ModuleStatus, FeatureFlag as FeatureFlagModel


class DjangoModuleRepository(ModuleRepository):
    """Django implementation of the ModuleRepository interface."""

    def get_all_modules(self) -> List[ModuleEntity]:
        """Get all modules."""
        modules = ModuleModel.objects.all()
        return [self._to_entity(module) for module in modules]
    
    def get_module_by_id(self, module_id: str) -> Optional[ModuleEntity]:
        """Get a module by its ID."""
        try:
            module = ModuleModel.objects.get(id=module_id)
            return self._to_entity(module)
        except ModuleModel.DoesNotExist:
            return None
    
    def create_module(self, module: ModuleEntity) -> ModuleEntity:
        """Create a new module."""
        model = ModuleModel(
            id=module.id,
            name=module.name,
            version=module.version,
            status=module.status.value,
            description=module.description,
            dependencies=module.dependencies
        )
        model.save()
        
        # Create feature flags
        for feature_flag in module.features.values():
            FeatureFlagModel.objects.create(
                id=feature_flag.id or f"{module.id}_{feature_flag.name}",
                name=feature_flag.name,
                description=feature_flag.description,
                enabled=feature_flag.enabled,
                module=model,
                affects_endpoints=feature_flag.affects_endpoints
            )
        
        return self.get_module_by_id(module.id)
    
    def update_module(self, module: ModuleEntity) -> ModuleEntity:
        """Update an existing module."""
        try:
            model = ModuleModel.objects.get(id=module.id)
            model.name = module.name
            model.version = module.version
            model.status = module.status.value
            model.description = module.description
            model.dependencies = module.dependencies
            model.save()
            
            # Update feature flags
            # First, remove any feature flags that no longer exist
            existing_flags = FeatureFlagModel.objects.filter(module_id=module.id)
            existing_flag_ids = {flag.id for flag in existing_flags}
            new_flag_ids = {flag_id for flag_id in module.features.keys()}
            
            # Delete flags that are no longer in the entity
            for flag_id in existing_flag_ids - new_flag_ids:
                FeatureFlagModel.objects.get(id=flag_id).delete()
            
            # Create or update remaining flags
            for feature_flag in module.features.values():
                flag_id = feature_flag.id or f"{module.id}_{feature_flag.name}"
                flag, created = FeatureFlagModel.objects.update_or_create(
                    id=flag_id,
                    defaults={
                        'name': feature_flag.name,
                        'description': feature_flag.description,
                        'enabled': feature_flag.enabled,
                        'module': model,
                        'affects_endpoints': feature_flag.affects_endpoints
                    }
                )
            
            return self.get_module_by_id(module.id)
        except ModuleModel.DoesNotExist:
            return None
    
    def delete_module(self, module_id: str) -> bool:
        """Delete a module by its ID."""
        try:
            module = ModuleModel.objects.get(id=module_id)
            module.delete()
            return True
        except ModuleModel.DoesNotExist:
            return False
    
    def update_module_status(self, module_id: str, status: ModuleStatusEntity) -> Optional[ModuleEntity]:
        """Update a module's status."""
        try:
            module = ModuleModel.objects.get(id=module_id)
            module.status = status.value
            module.save()
            return self._to_entity(module)
        except ModuleModel.DoesNotExist:
            return None
    
    def get_modules_by_status(self, status: ModuleStatusEntity) -> List[ModuleEntity]:
        """Get all modules with a specific status."""
        modules = ModuleModel.objects.filter(status=status.value)
        return [self._to_entity(module) for module in modules]

    def _to_entity(self, model: ModuleModel) -> ModuleEntity:
        """Convert a Django model to a domain entity."""
        # Get feature flags for this module
        feature_flags = FeatureFlagModel.objects.filter(module=model)
        features = {}
        
        for flag in feature_flags:
            feature_entity = FeatureFlagEntity(
                id=flag.id,
                name=flag.name,
                description=flag.description,
                enabled=flag.enabled,
                module_id=model.id,
                affects_endpoints=flag.affects_endpoints
            )
            features[flag.id] = feature_entity
        
        return ModuleEntity(
            id=model.id,
            name=model.name,
            version=model.version,
            status=ModuleStatusEntity(model.status),
            description=model.description,
            dependencies=model.dependencies,
            features=features,
            last_modified=model.last_modified.isoformat() if model.last_modified else None
        )
