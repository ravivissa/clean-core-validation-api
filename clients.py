from database import (
    get_client_by_api_key,
    get_all_clients,
    create_client,
    update_client_plan
)


def get_client_details(api_key: str):
    return get_client_by_api_key(api_key)


def list_clients():
    return get_all_clients()


def create_new_client(client_name: str, plan: str, max_usage: int):
    return create_client(client_name, plan, max_usage)


def upgrade_client_plan(api_key: str, plan: str, max_usage: int, is_paid: int):
    update_client_plan(api_key, plan, max_usage, is_paid)