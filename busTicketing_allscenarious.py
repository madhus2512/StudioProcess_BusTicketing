from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import random

app = FastAPI(title="Bus Ticket Booking")

# -------------------------------
# Dummy Data (with routes, buses, dates, seats)
# -------------------------------
ROUTES = [
    {"route_id": 1, "from": "Chennai", "to": "Bangalore"},
    {"route_id": 2, "from": "Bangalore", "to": "Hyderabad"},
    {"route_id": 3, "from": "Chennai", "to": "Coimbatore"},
]

BUS_DATA = {
    1: {
        "Chennai Express": {
            "2025-09-20": {"total_seats": 40, "booked_seats": [5, 8, 15]},
            "2025-09-21": {"total_seats": 40, "booked_seats": [10, 11]},
        },
        "Highway Rider": {
            "2025-09-20": {"total_seats": 40, "booked_seats": [1, 2, 3, 4]},
            "2025-09-21": {"total_seats": 40, "booked_seats": []},
        },
    },
    2: {
        "Hyd Volvo": {
            "2025-09-20": {"total_seats": 50, "booked_seats": [7, 9, 12]},
        },
        "Night Star": {
            "2025-09-20": {"total_seats": 50, "booked_seats": []},
        },
    },
    3: {
        "Coimbatore Deluxe": {
            "2025-09-20": {"total_seats": 45, "booked_seats": [5, 6]},
        },
        "GreenLine": {
            "2025-09-20": {"total_seats": 45, "booked_seats": []},
        },
    },
}

# Temporary store for booked tickets (before payment)
BOOKED_TICKETS = {}

# -------------------------------
# Pydantic Models
# -------------------------------
class RouteRequest(BaseModel):
    route_id: int

class SeatBookingRequest(BaseModel):
    route_id: int
    date: str
    bus_name: str
    seat_number: int
    passenger_name: str
    phone_number: str
    amount: float

class PaymentRequest(BaseModel):
    ticket_id: str
    card_number: str
    expiry_date: str
    cvv: str
    card_holder: str


# -------------------------------
# API 1: Get Routes
# -------------------------------
@app.get("/routes/")
def get_routes():
    return {"available_routes": ROUTES}


# -------------------------------
# API 2: Get Route Details (dates, buses, seats in one shot)
# -------------------------------
@app.post("/route-details/")
def route_details(req: RouteRequest):
    if req.route_id not in BUS_DATA:
        raise HTTPException(status_code=404, detail="Invalid route_id")

    route_info = {}
    for bus_name, schedules in BUS_DATA[req.route_id].items():
        route_info[bus_name] = {}
        for date, schedule in schedules.items():
            total = schedule["total_seats"]
            booked = schedule["booked_seats"]
            available = [s for s in range(1, total + 1) if s not in booked]

            route_info[bus_name][date] = {
                "total_seats": total,
                "booked_seats": booked,
                "available_seats": available
            }

    return {
        "route_id": req.route_id,
        "route_details": route_info
    }


# -------------------------------
# API 3: Book Seat (reserve seat, not yet paid)
# -------------------------------
@app.post("/book-seat/")
def book_seat(req: SeatBookingRequest):
    if req.route_id not in BUS_DATA:
        raise HTTPException(status_code=404, detail="Invalid route_id")
    if req.bus_name not in BUS_DATA[req.route_id]:
        raise HTTPException(status_code=404, detail="Bus not found on this route")
    if req.date not in BUS_DATA[req.route_id][req.bus_name]:
        raise HTTPException(status_code=404, detail="No schedule for this bus on given date")

    schedule = BUS_DATA[req.route_id][req.bus_name][req.date]

    if req.seat_number in schedule["booked_seats"]:
        raise HTTPException(status_code=400, detail="Seat already booked")

    if req.amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid amount")

    # Reserve seat
    schedule["booked_seats"].append(req.seat_number)

    # Generate ticket (not paid yet)
    ticket_id = f"TKT{random.randint(1000,9999)}"
    BOOKED_TICKETS[ticket_id] = {
        "passenger_name": req.passenger_name,
        "phone_number": req.phone_number,
        "bus_name": req.bus_name,
        "route_id": req.route_id,
        "date": req.date,
        "seat_number": req.seat_number,
        "amount": req.amount,
        "status": "Pending Payment"
    }

    return {
        "message": "Seat reserved! Please proceed to payment.",
        "ticket_id": ticket_id,
        "amount_due": req.amount
    }


# -------------------------------
# API 4: Make Payment (dummy)
# -------------------------------
@app.post("/make-payment/")
def make_payment(req: PaymentRequest):
    if req.ticket_id not in BOOKED_TICKETS:
        raise HTTPException(status_code=404, detail="Invalid ticket_id")

    ticket = BOOKED_TICKETS[req.ticket_id]

    # Dummy card validation
    if len(req.card_number) != 16 or not req.card_number.isdigit():
        raise HTTPException(status_code=400, detail="Invalid card number")
    if len(req.cvv) != 3 or not req.cvv.isdigit():
        raise HTTPException(status_code=400, detail="Invalid CVV")

    # Payment success (dummy)
    confirmation_number = random.randint(100000, 999999)
    ticket["status"] = "Paid"
    ticket["confirmation_number"] = confirmation_number
    ticket["card_holder"] = req.card_holder

    return {
        "message": "Payment Successful!",
        "ticket_id": req.ticket_id,
        "confirmation_number": confirmation_number,
        "details": ticket
    }

 
