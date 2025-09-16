from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import random

app = FastAPI(title="Bus Ticket Booking")

# -------------------------------
# Master Route List
# -------------------------------
ALL_ROUTES = [
    {"from": "Chennai", "to": "Bangalore"},
    {"from": "Bangalore", "to": "Hyderabad"},
    {"from": "Chennai", "to": "Coimbatore"},
    {"from": "Hyderabad", "to": "Vizag"},
    {"from": "Delhi", "to": "Agra"},
    {"from": "Mumbai", "to": "Pune"},
    {"from": "Chennai", "to": "Madurai"},
    {"from": "Kolkata", "to": "Bhubaneswar"},
    {"from": "Trichy", "to": "Chennai"},
    {"from": "Goa", "to": "Bangalore"}
]

# -------------------------------
# Bus Data
# -------------------------------
BUS_DATA = {
    1: {"Chennai Express": {"2025-09-20": {"total_seats": 40, "booked_seats": [5, 8, 15]},
                            "2025-09-21": {"total_seats": 40, "booked_seats": [10, 11]}},
        "Highway Rider": {"2025-09-20": {"total_seats": 40, "booked_seats": [1, 2, 3, 4]},
                          "2025-09-21": {"total_seats": 40, "booked_seats": []}}},
    2: {"Hyd Volvo": {"2025-09-20": {"total_seats": 50, "booked_seats": [7, 9, 12]},
                      "2025-09-21": {"total_seats": 50, "booked_seats": [1, 2]}},
        "Night Star": {"2025-09-20": {"total_seats": 50, "booked_seats": []},
                       "2025-09-21": {"total_seats": 50, "booked_seats": [5]}}},
    3: {"Coimbatore Deluxe": {"2025-09-20": {"total_seats": 45, "booked_seats": [5, 6]},
                              "2025-09-21": {"total_seats": 45, "booked_seats": [1]}},
        "GreenLine": {"2025-09-20": {"total_seats": 45, "booked_seats": []},
                      "2025-09-21": {"total_seats": 45, "booked_seats": [2, 3]}}},
}

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
# API 1: Get Numbered Routes
# -------------------------------
@app.get("/routes/")
def get_routes():
    numbered_routes = [{"route_number": i+1, "from": route["from"], "to": route["to"]}
                       for i, route in enumerate(ALL_ROUTES)]
    return {"available_routes": numbered_routes}

# -------------------------------
# API 2: Get Route Details (Simplified)
# -------------------------------
@app.post("/route-details/")
def route_details(req: RouteRequest):
    route_number = req.route_id
    if route_number not in BUS_DATA:
        raise HTTPException(status_code=404, detail="Invalid route_id")

    result = {"route_number": route_number, "buses": []}

    for bus_name, schedules in BUS_DATA[route_number].items():
        bus_info = {"bus_name": bus_name, "schedules": []}
        for date, schedule in schedules.items():
            available_seats = schedule["total_seats"] - len(schedule["booked_seats"])
            bus_info["schedules"].append({"date": date, "available_seats": available_seats})
        result["buses"].append(bus_info)

    return result

# -------------------------------
# API 3: Book Seat
# -------------------------------
@app.post("/book-seat/")
def book_seat(req: SeatBookingRequest):
    route_number = req.route_id
    if route_number not in BUS_DATA:
        raise HTTPException(status_code=404, detail="Invalid route_id")
    if req.bus_name not in BUS_DATA[route_number]:
        raise HTTPException(status_code=404, detail="Bus not found")
    if req.date not in BUS_DATA[route_number][req.bus_name]:
        raise HTTPException(status_code=404, detail="No schedule on this date")

    schedule = BUS_DATA[route_number][req.bus_name][req.date]

    if req.seat_number in schedule["booked_seats"]:
        raise HTTPException(status_code=400, detail="Seat already booked")
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    schedule["booked_seats"].append(req.seat_number)

    ticket_id = f"TKT{random.randint(1000, 9999)}"
    BOOKED_TICKETS[ticket_id] = {
        "passenger_name": req.passenger_name,
        "phone_number": req.phone_number,
        "bus_name": req.bus_name,
        "route_id": route_number,
        "date": req.date,
        "seat_number": req.seat_number,
        "amount": req.amount,
        "status": "Pending Payment"
    }

    return {"message": "Seat reserved! Please proceed to payment.", "ticket_id": ticket_id, "amount_due": req.amount}

# -------------------------------
# API 4: Make Payment
# -------------------------------
@app.post("/make-payment/")
def make_payment(req: PaymentRequest):
    if req.ticket_id not in BOOKED_TICKETS:
        raise HTTPException(status_code=404, detail="Invalid ticket_id")

    ticket = BOOKED_TICKETS[req.ticket_id]

    if len(req.card_number) != 16 or not req.card_number.isdigit():
        raise HTTPException(status_code=400, detail="Invalid card number")
    if len(req.cvv) != 3 or not req.cvv.isdigit():
        raise HTTPException(status_code=400, detail="Invalid CVV")

    confirmation_number = random.randint(100000, 999999)
    ticket["status"] = "Paid"
    ticket["confirmation_number"] = confirmation_number
    ticket["card_holder"] = req.card_holder

    return {"message": "Payment Successful!", "ticket_id": req.ticket_id, "confirmation_number": confirmation_number, "details": ticket}
