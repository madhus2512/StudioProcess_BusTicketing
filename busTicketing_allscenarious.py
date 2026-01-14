from fastapi import FastAPI
from pydantic import BaseModel, Field
import random
from datetime import datetime, timedelta

app = FastAPI(title="Bus Ticket Booking API")

# -------------------------------------------------
# Master Data
# -------------------------------------------------
BUS_ROUTES = {
    "Garuda": ["Hyd - Bangalore", "Bangalore - Chennai"],
    "Volvo": ["Chennai - Mumbai", "Mumbai - Pune"],
    "GreenLines": ["Delhi - Agra", "Agra - Jaipur"],
    "AbhiBus": ["Chennai - Coimbatore", "Coimbatore - Trichy"]
}

TEMP_BOOKED_SEATS = {}
PASSENGER_BOOKINGS = {}
CONFIRMED_TICKETS = {}

# -------------------------------------------------
# Pydantic Models
# -------------------------------------------------

class OperatorSelection(BaseModel):
    operator_name: str

class RouteSelection(BaseModel):
    route_name: str

class DateSelection(BaseModel):
    date: str

class PassengerInfo(BaseModel):
    date: str
    seat_number: int
    username: str
    phone_number: str = Field(..., min_length=10, max_length=15)
    age: int = Field(..., gt=0)

class PaymentInfo(BaseModel):
    date: str
    seat_number: int
    card_number: str
    cvv: str
    expiry_date: str
    card_holder: str

class TicketRequest(BaseModel):
    ticket_id: str

# -------------------------------------------------
# API 1: Get Bus Operators
# -------------------------------------------------
@app.get("/buses/")
def get_buses():
    return {"available_buses": list(BUS_ROUTES.keys())}

# -------------------------------------------------
# API 2: Get Bus Routes
# -------------------------------------------------
@app.post("/bus-routes/")
def get_routes(op: OperatorSelection):
    if op.operator_name not in BUS_ROUTES:
        return {
            "operator": op.operator_name,
            "routes": [],
            "message": "No operator found"
        }

    return {
        "operator": op.operator_name,
        "routes": BUS_ROUTES[op.operator_name],
        "message": "Operator found"
    }

# -------------------------------------------------
# API 3: Get Available Dates
# -------------------------------------------------
@app.post("/route-dates/")
def get_dates(route: RouteSelection):
    today = datetime.today()
    dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, 6)]
    return {
        "route": route.route_name,
        "available_dates": dates
    }

# -------------------------------------------------
# API 4: Get Available Seats
# -------------------------------------------------
@app.post("/available-seats/")
def get_seats(selection: DateSelection):
    if selection.date not in TEMP_BOOKED_SEATS:
        TEMP_BOOKED_SEATS[selection.date] = random.sample(range(1, 41), random.randint(0, 15))

    booked = TEMP_BOOKED_SEATS[selection.date]
    available = [s for s in range(1, 41) if s not in booked]

    return {
        "date": selection.date,
        "available_seats": available[:10],
        "total_available": len(available)
    }

# -------------------------------------------------
# API 5: Add Passenger Info
# -------------------------------------------------
@app.post("/passenger-info/")
def add_passenger(info: PassengerInfo):
    key = f"{info.date}_{info.seat_number}"

    if key in PASSENGER_BOOKINGS:
        return {
            "message": "Passenger already exists"
        }

    PASSENGER_BOOKINGS[key] = info.dict()

    return {
        "message": "Passenger info added successfully"
    }

# -------------------------------------------------
# API 6: Make Payment & Generate Ticket
# -------------------------------------------------
@app.post("/make-payment/")
def make_payment(payment: PaymentInfo):
    key = f"{payment.date}_{payment.seat_number}"

    if key not in PASSENGER_BOOKINGS:
        return {
            "message": "Passenger info not found"
        }

    ticket_id = f"TKT{random.randint(1000, 9999)}"

    CONFIRMED_TICKETS[ticket_id] = {
        **PASSENGER_BOOKINGS[key],
        "payment_status": "Paid",
        "card_holder": payment.card_holder,
        "ticket_id": ticket_id
    }

    return {
        "message": "Payment successful",
        "ticket_id": ticket_id
    }

# =================================================
# 🔹 Ticket ID Based APIs (FLAT RESPONSE)
# =================================================

# -------------------------------------------------
# API 7: Get Ticket Details (FLAT)
# -------------------------------------------------
@app.post("/ticket/details")
def get_ticket_details(req: TicketRequest):
    ticket = CONFIRMED_TICKETS.get(req.ticket_id)

    if not ticket:
        return {
            "message": "Ticket not found",
            "ticket_id": req.ticket_id
        }

    return {
        "message": "Ticket found",
        "ticket_id": req.ticket_id,
        "username": ticket["username"],
        "phone_number": ticket["phone_number"],
        "age": ticket["age"],
        "seat_number": ticket["seat_number"],
        "date": ticket["date"],
        "payment_status": ticket["payment_status"],
        "card_holder": ticket["card_holder"]
    }

# -------------------------------------------------
# API 8: Get Passenger Details (FLAT)
# -------------------------------------------------
@app.post("/ticket/passenger")
def get_passenger_details(req: TicketRequest):
    ticket = CONFIRMED_TICKETS.get(req.ticket_id)

    if not ticket:
        return {
            "message": "Ticket not found",
            "ticket_id": req.ticket_id
        }

    return {
        "message": "Passenger details found",
        "ticket_id": req.ticket_id,
        "username": ticket["username"],
        "phone_number": ticket["phone_number"],
        "age": ticket["age"],
        "seat_number": ticket["seat_number"],
        "date": ticket["date"]
    }

# -------------------------------------------------
# API 9: Cancel Ticket (FLAT)
# -------------------------------------------------
@app.post("/ticket/cancel")
def cancel_ticket(req: TicketRequest):
    ticket = CONFIRMED_TICKETS.pop(req.ticket_id, None)

    if not ticket:
        return {
            "message": "Ticket not found or already cancelled",
            "ticket_id": req.ticket_id,
            "cancelled": False
        }

    key = f"{ticket['date']}_{ticket['seat_number']}"
    PASSENGER_BOOKINGS.pop(key, None)

    return {
        "message": "Ticket cancelled successfully",
        "ticket_id": req.ticket_id,
        "cancelled": True,
        "refund_status": "Initiated"
    }
