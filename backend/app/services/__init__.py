"""Domain service layer exports."""

from .user import (
    change_user_password,
    create_user,
    delete_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    list_users,
    update_user,
    update_user_profile,
    user_exists_with_username_or_email,
)
from .vehicle import (
    create_vehicle,
    delete_vehicle,
    get_expiring_vehicle_documents,
    get_vehicle_by_id,
    get_vehicle_by_registration_number,
    list_vehicles,
    store_vehicle_document,
    update_vehicle,
    update_vehicle_status,
)

__all__ = [
    "change_user_password",
    "create_user",
    "delete_user",
    "get_user_by_email",
    "get_user_by_id",
    "get_user_by_username",
    "list_users",
    "update_user",
    "update_user_profile",
    "user_exists_with_username_or_email",
    "create_vehicle",
    "delete_vehicle",
    "get_expiring_vehicle_documents",
    "get_vehicle_by_id",
    "get_vehicle_by_registration_number",
    "list_vehicles",
    "store_vehicle_document",
    "update_vehicle",
    "update_vehicle_status",
]
