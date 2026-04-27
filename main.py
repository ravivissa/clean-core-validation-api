from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import traceback
from models import Invoice
from security import validate_api_key
from database import (
    init_db,
    seed_default_clients,
    save_validation_result,
    get_all_validation_history
)
from rules import rule_catalog
from validator import run_invoice_validation
from usage import increment_usage, get_usage, is_limit_exceeded, reset_usage
from clients import (
    get_client_details,
    list_clients,
    create_new_client,
    upgrade_client_plan
)
from plans import get_all_plans, get_plan_details
from payments import create_checkout_session, verify_stripe_event

app = FastAPI(
    title="CleanCore Validation API",
    description="Pre-posting invoice validation API for SAP-led landscapes.",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()
seed_default_clients()


class CreateClientRequest(BaseModel):
    client_name: str
    plan: str


class UpgradePlanRequest(BaseModel):
    api_key: str
    plan: str


class CheckoutRequest(BaseModel):
    api_key: str
    plan: str


class ResetUsageRequest(BaseModel):
    api_key: str


def enforce_usage_limit(x_api_key: Optional[str]):
    validate_api_key(x_api_key)

    client = get_client_details(x_api_key)
    if not client:
        raise HTTPException(status_code=403, detail="Client not found")

    if is_limit_exceeded(x_api_key, client["max_usage"]):
        raise HTTPException(
            status_code=429,
            detail=f"Usage limit exceeded for plan {client['plan']}"
        )

    return client


@app.get("/")
def home():
    return {"message": "CleanCore Validation API is running"}


@app.get("/plans")
def plans():
    return {
        "total_plans": len(get_all_plans()),
        "plans": get_all_plans()
    }


@app.post("/create-checkout-session")
def checkout(request: CheckoutRequest):
    existing_client = get_client_details(request.api_key)
    if not existing_client:
        raise HTTPException(status_code=404, detail="Client not found")

    plan_name = request.plan.upper()
    plan_details = get_plan_details(plan_name)

    if not plan_details:
        raise HTTPException(status_code=400, detail="Invalid plan")

    if plan_details["price"] <= 0:
        raise HTTPException(status_code=400, detail="Cannot create checkout for free plan")

    checkout_url = create_checkout_session(
        api_key=request.api_key,
        plan=plan_name,
        amount=plan_details["price"],
        currency=plan_details["currency"]
    )

    return {
        "checkout_url": checkout_url
    }


@app.post("/stripe-webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = verify_stripe_event(payload, sig_header)
    except Exception as e:
        print("STRIPE WEBHOOK VERIFY ERROR:", str(e))
        return {"received": False, "error": str(e)}

    print("STRIPE EVENT RECEIVED:", event["type"])

    if event["type"] == "checkout.session.completed":
        try:
            session = event["data"]["object"]

            metadata = session["metadata"] or {}
            api_key = metadata["api_key"] if "api_key" in metadata else None
            plan_name = metadata["plan"] if "plan" in metadata else None

            print("CHECKOUT SESSION ID:", session["id"])
            print("CHECKOUT METADATA:", metadata)
            print("API KEY FROM STRIPE:", api_key)
            print("PLAN FROM STRIPE:", plan_name)

            if not api_key or not plan_name:
                print("ERROR: Missing api_key or plan in Stripe metadata")
                return {"received": True, "message": "Missing metadata"}

            plan_name = str(plan_name).upper()
            plan_details = get_plan_details(plan_name)

            if not plan_details:
                print("ERROR: Invalid plan from Stripe:", plan_name)
                return {"received": True, "message": "Invalid plan"}

            existing_client = get_client_details(api_key)

            if not existing_client:
                print("ERROR: Client not found for API key:", api_key)
                return {"received": True, "message": "Client not found"}

            print("CLIENT BEFORE UPGRADE:", existing_client)

            upgrade_client_plan(
                api_key=api_key,
                plan=plan_name,
                max_usage=plan_details["max_usage"],
                is_paid=1
            )

            reset_usage(api_key)

            upgraded_client = get_client_details(api_key)
            print("CLIENT AFTER UPGRADE:", upgraded_client)

            return {
                "received": True,
                "message": "Client upgraded successfully",
                "client": upgraded_client
            }

        except Exception as e:
            print("STRIPE WEBHOOK PROCESSING ERROR:", str(e))
            print(traceback.format_exc())

            # Return 200 so Stripe does not keep retrying while we debug
            return {
                "received": True,
                "message": "Webhook processing failed but captured",
                "error": str(e)
            }

    return {"received": True}

@app.get("/payment-success")
def payment_success():
    return {
        "message": "Payment successful. Your plan will be upgraded automatically."
    }


@app.get("/payment-cancelled")
def payment_cancelled():
    return {
        "message": "Payment cancelled."
    }


@app.post("/create-client")
def create_client_api(request: CreateClientRequest):
    plan_name = request.plan.upper()
    plan_details = get_plan_details(plan_name)

    if not plan_details:
        raise HTTPException(status_code=400, detail="Invalid plan")

    client = create_new_client(
        client_name=request.client_name,
        plan=plan_name,
        max_usage=plan_details["max_usage"]
    )

    return {
        "message": "Client created successfully",
        "client": client,
        "pricing": {
            "price": plan_details["price"],
            "currency": plan_details["currency"],
            "description": plan_details["description"]
        }
    }


@app.post("/upgrade-plan")
def upgrade_plan_api(request: UpgradePlanRequest):
    plan_name = request.plan.upper()
    plan_details = get_plan_details(plan_name)

    if not plan_details:
        raise HTTPException(status_code=400, detail="Invalid plan")

    existing_client = get_client_details(request.api_key)
    if not existing_client:
        raise HTTPException(status_code=404, detail="Client not found")

    upgrade_client_plan(
        api_key=request.api_key,
        plan=plan_name,
        max_usage=plan_details["max_usage"],
        is_paid=1 if plan_name != "FREE" else 0
    )

    return {
        "message": "Plan upgraded successfully",
        "api_key": request.api_key,
        "old_plan": existing_client["plan"],
        "new_plan": plan_name,
        "max_usage": plan_details["max_usage"],
        "pricing": {
            "price": plan_details["price"],
            "currency": plan_details["currency"],
            "description": plan_details["description"]
        }
    }


@app.get("/clients")
def get_clients():
    clients = list_clients()
    return {
        "total_clients": len(clients),
        "clients": clients
    }


@app.get("/usage")
def usage(x_api_key: Optional[str] = Header(default=None)):
    client = validate_api_key(x_api_key)
    usage_count = get_usage(x_api_key)

    return {
        "api_key": x_api_key,
        "client_name": client["client_name"],
        "plan": client["plan"],
        "usage_count": usage_count,
        "max_usage": client["max_usage"],
        "remaining_usage": max(client["max_usage"] - usage_count, 0),
        "is_paid": client.get("is_paid", 0)
    }


@app.post("/reset-usage")
def reset(request: ResetUsageRequest):
    existing_client = get_client_details(request.api_key)
    if not existing_client:
        raise HTTPException(status_code=404, detail="Client not found")

    reset_usage(request.api_key)

    return {
        "message": "Usage reset successfully",
        "api_key": request.api_key,
        "client_name": existing_client["client_name"],
        "usage_count": 0,
        "max_usage": existing_client["max_usage"]
    }


@app.get("/rules")
def get_rules(x_api_key: Optional[str] = Header(default=None)):
    enforce_usage_limit(x_api_key)
    increment_usage(x_api_key)

    return {
        "api": "CleanCore Validation API",
        "total_rules": len(rule_catalog),
        "rules": rule_catalog
    }


@app.get("/sample-invoice")
def get_sample_invoice(x_api_key: Optional[str] = Header(default=None)):
    enforce_usage_limit(x_api_key)
    increment_usage(x_api_key)

    return {
        "invoice_number": "INV-9001",
        "supplier_id": "SUP-100",
        "po_number": "PO-1001",
        "header_amount": 200,
        "items": [
            {
                "line_no": 1,
                "po_line": 10,
                "quantity": 2,
                "unit_price": 100,
                "line_amount": 200
            }
        ]
    }


@app.get("/validation-history")
def get_validation_history(x_api_key: Optional[str] = Header(default=None)):
    enforce_usage_limit(x_api_key)
    increment_usage(x_api_key)

    history = get_all_validation_history()

    return {
        "total_records": len(history),
        "history": history
    }


@app.post("/validate-invoice")
def validate(invoice: Invoice, x_api_key: Optional[str] = Header(default=None)):
    enforce_usage_limit(x_api_key)
    increment_usage(x_api_key)

    result = run_invoice_validation(invoice)
    save_validation_result(result)

    return result