from database import get_usage_count, increment_usage_count, reset_usage_count


def increment_usage(api_key: str):
    return increment_usage_count(api_key)


def get_usage(api_key: str):
    return get_usage_count(api_key)


def reset_usage(api_key: str):
    return reset_usage_count(api_key)


def is_limit_exceeded(api_key: str, max_usage: int):
    return get_usage(api_key) >= max_usage