plans = {
    "FREE": {
        "price": 0,
        "currency": "INR",
        "max_usage": 5,
        "description": "Starter plan for evaluation and testing."
    },
    "PRO": {
        "price": 500,
        "currency": "INR",
        "max_usage": 100,
        "description": "Professional plan for regular business usage."
    },
    "ENTERPRISE": {
        "price": 2000,
        "currency": "INR",
        "max_usage": 1000,
        "description": "Enterprise plan for high-volume usage."
    }
}


def get_all_plans():
    return plans


def get_plan_details(plan_name: str):
    return plans.get(plan_name.upper())