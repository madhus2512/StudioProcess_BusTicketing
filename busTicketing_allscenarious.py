from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import random

# -------------------------------
# Initialize FastAPI
# -------------------------------
app = FastAPI(title="Bus Ticket Booking Workflow")

# -------------------------------
# Allowed / Mock Data
# -------------------------------
ALLOWED_PHONE_NUMBERS = {"7358174456", "7358174457"}
ALLOWED_CUSTOMERS = {
    "7358174456": {"name": "John Doe", "email": "john@example.com"},
    "7358174457": {"name": "Jane Smith", "email": "jane@example.com"}
}
ROUTES = {
    "Bangalore-Chennai": [
        {"bus_id": "B1001", "start_time": "09:00 AM", "available_seats": list(range(1, 11))},
        {"bus_id": "B1002", "start_time": "02:00 PM", "available_seats": list(range(1, 6))}
    ],
    "Chennai-Hyderabad": [
        {"bus_id": "B2001", "start_time": "08:30 AM", "available_seats": list(range(1, 8))}
    ]
}

# -------------------------------
# State Management (in-memory sessions)
# -------------------------------
SESSIONS = {}

# -------------------------------
# Pydantic Models
# -------------------------------
class PhoneNumber(BaseModel):
    phone_number: str

class RouteSearch(BaseModel):
    phone_number: str
    source: str
    destination: str

class SeatSelection(BaseModel):
    phone_number: str
    bus_id: str
    seat_number: int

class PassengerDetails(BaseModel):
    phone_number: str
    name: str
    age: int
    gender: str
    email: str

class Payment(BaseModel):
    phone_number: str
    card_number: str
    expiry_date: str
    cvv: str
    amount: float

# -------------------------------
# Welcome Message
# -------------------------------
@app.get("/welcome/")
def welcome():
    return {"message": "Welcome to XYZ Bus Booking Service! Let's start your booking."}

# -------------------------------
# Step 1: Validate Phone Number (with retry limit)
# -------------------------------
@app.post("/validate-phone/")
def validate_phone_number(phone: PhoneNumber):
    session = SESSIONS.setdefault(phone.phone_number, {"attempts": 0, "validated": False})

    if phone.phone_number in ALLOWED_PHONE_NUMBERS:
        session["validated"] = True
        session["attempts"] = 0  # reset attempts
        return {
            "message": "Phone number is valid.",
            "customer": ALLOWED_CUSTOMERS[phone.phone_number]
        }
    else:
        session["attempts"] += 1
        if session["attempts"] >= 2:
            return {"message": "Phone number invalid. Booking process failed!"}
        return {"message": "Invalid phone number. Please try again."}

# -------------------------------
# Step 2: Search Buses
# -------------------------------
@app.post("/search-buses/")
def search_buses(route: RouteSearch):
    session = SESSIONS.get(route.phone_number)
    if not session or not session.get("validated"):
        raise HTTPException(status_code=403, detail="Phone number not validated.")

    key = f"{route.source}-{route.destination}"
    if key not in ROUTES:
        return {"message": "No buses found for this route. Please try again."}
    return {"available_buses": ROUTES[key]}

# -------------------------------
# Step 3: Select Seat (with validation)
# -------------------------------
@app.post("/select-seat/")
def select_seat(selection: SeatSelection):
    session = SESSIONS.get(selection.phone_number)
    if not session or not session.get("validated"):
        raise HTTPException(status_code=403, detail="Phone number not validated.")

    for route_buses in ROUTES.values():
        for bus in route_buses:
            if bus["bus_id"] == selection.bus_id:
                if selection.seat_number in bus["available_seats"]:
                    bus["available_seats"].remove(selection.seat_number)
                    session["seat"] = selection.seat_number
                    return {
                        "message": "Seat booked temporarily.",
                        "bus_id": selection.bus_id,
                        "seat_number": selection.seat_number
                    }
                else:
                    return {"message": "Seat not available. Please select another seat."}
    return {"message": "Bus not found."}

# -------------------------------
# Step 4: Enter Passenger Details
# -------------------------------
@app.post("/enter-passenger/")
def enter_passenger(details: PassengerDetails):
    session = SESSIONS.get(details.phone_number)
    if not session or not session.get("validated"):
        raise HTTPException(status_code=403, detail="Phone number not validated.")

    session["passenger"] = details.dict()
    return {
        "message": "Passenger details recorded.",
        "passenger": details.dict()
    }

# -------------------------------
# Step 5: Payment (with failure handling)
# -------------------------------
@app.post("/make-payment/")
def make_payment(payment: Payment):
    session = SESSIONS.get(payment.phone_number)
    if not session or not session.get("validated"):
        raise HTTPException(status_code=403, detail="Phone number not validated.")

    if len(payment.card_number) != 16 or len(payment.cvv) != 3:
        return {"message": "Invalid card details. Payment failed!"}

    if payment.amount <= 0:
        return {"message": "Payment amount must be greater than zero."}

    confirmation_number = random.randint(100000, 999999)
    return {
        "message": "Payment successful! Your bus ticket is confirmed.",
        "amount_paid": payment.amount,
        "confirmation_number": confirmation_number,
        "ticket_status": "CONFIRMED",
        "passenger": session.get("passenger"),
        "seat_number": session.get("seat")
    }
