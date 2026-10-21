from fastapi import FastAPI, Body, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Optional
from fastapi import FastAPI, Body, HTTPException, Response

app = FastAPI()

deliveries = {}
next_id = 1

STATUSES = ["created", "in_transit", "delivered"]
# שגיאות בפורמט {"error": "..."} במקום {"detail": "..."}
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse({"error": str(exc.detail)}, status_code=exc.status_code)


# גוף חסר או לא תקין: 400 במקום 422
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse({"error": "Invalid request body"}, status_code=400)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/deliveries", status_code=201)
def create_delivery(data: dict = Body(...)):
    global next_id
    recipient = data.get("recipient")
    address = data.get("address")

    if not isinstance(recipient, str) or not recipient.strip():
        raise HTTPException(400, "recipient must be a non-empty string")
    if not isinstance(address, str) or not address.strip():
        raise HTTPException(400, "address must be a non-empty string")

    delivery = {
        "id": next_id,
        "recipient": recipient,
        "address": address,
        "status": "created",
    }
    deliveries[next_id] = delivery
    next_id += 1
    return delivery

@app.get("/deliveries")
def list_deliveries(status: Optional[str] = None):
    if status is None:
        return list(deliveries.values())
    if status not in STATUSES:
        raise HTTPException(400, "unknown status")
    return [d for d in deliveries.values() if d["status"] == status]


@app.get("/deliveries/{delivery_id}")
def get_delivery(delivery_id: int):
    if delivery_id not in deliveries:
        raise HTTPException(404, "delivery not found")
    return deliveries[delivery_id]

@app.patch("/deliveries/{delivery_id}/status")
def update_status(delivery_id: int, data: dict = Body(...)):
    if delivery_id not in deliveries:
        raise HTTPException(404, "delivery not found")

    new_status = data.get("status")
    if new_status not in STATUSES:
        raise HTTPException(400, "unknown status")

    delivery = deliveries[delivery_id]
    current_index = STATUSES.index(delivery["status"])
    new_index = STATUSES.index(new_status)

    if new_index != current_index + 1:
        raise HTTPException(409, "invalid status transition")

    delivery["status"] = new_status
    return delivery

@app.delete("/deliveries/{delivery_id}")
def delete_delivery(delivery_id: int):
    if delivery_id not in deliveries:
        raise HTTPException(404, "delivery not found")

    if deliveries[delivery_id]["status"] != "created":
        raise HTTPException(409, "only deliveries with status created can be deleted")

    del deliveries[delivery_id]
    return Response(status_code=204)