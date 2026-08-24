from .models import ActivityLog


def log_activity(user, action, entity_type, entity_id=None, entity_name='', details=None):
    ActivityLog.objects.create(
        user_id=user.id,
        user_name=user.name,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        details=details or {},
    )
