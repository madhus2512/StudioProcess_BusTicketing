from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, constr, conint
import random

# -------------------------------
# Initialize FastAPI
# -------------------------------
app = FastAPI(title="Bus Ticket Booking Workflow")

# Allow all origins (optional, helps testing in Postman/frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        {"bus_id": "CB1001", "start_time": "09:00 AM", "available_seats": list(range(1, 11))},
        {"bus_id": "CB1002", "start_time": "02:00 PM", "available_seats": list(range(1, 6))}
    ],
    "Chennai-Hyderabad": [
        {"bus_id": "CH2001", "start_time": "08:30 AM", "available_seats": list(range(1, 8))},
        {"bus_id": "CH2002", "start_time": "09:30 AM", "available_seats": list(range(1, 8))}
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
    phone_number: constr(strip_whitespace=True, min_length=10, max_length=10)

class RouteSearch(BaseModel):
    phone_number: constr(strip_whitespace=True, min_length=10, max_length=10)
    source: str
    destination: str

class SeatSelection(BaseModel):
    phone_number: constr(strip_whitespace=True, min_length=10, max_length=10)
    bus_id: str
    seat_number: conint(gt=0)

class PassengerDetails(BaseModel):
    phone_number: constr(strip_whitespace=True, min_length=10, max_length=10)
    name: str
    age: conint(gt=0)
    gender: str
    email: str

class Payment(BaseModel):
    phone_number: constr(strip_whitespace=True, min_length=10, max_length=10)
    card_number: constr(min_length=16, max_length=16)
    expiry_date: str
    cvv: constr(min_length=3, max_length=3)
    amount: float = Field(gt=0)

class CustomerRegistration(BaseModel):
    phone_number: constr(strip_whitespace=True, min_length=10, max_length=10)
    name: str
    email: str

# -------------------------------
# Welcome Message
# -------------------------------
@app.get("/welcome/")
def welcome():
    return {"message": "Welcome to Smartbots Bus Booking Service! Let's start your booking."}

# -------------------------------
# Step 1: Validate Phone Number
# -------------------------------
@app.post("/validate-phone/")
def validate_phone_number(phone: PhoneNumber):
    session = SESSIONS.setdefault(phone.phone_number, {"attempts": 0, "validated": False})

    if phone.phone_number in ALLOWED_PHONE_NUMBERS:
        session["validated"] = True
        session["attempts"] = 0
        return {
            "message": "Phone number is valid.",
            "customer": ALLOWED_CUSTOMERS.get(phone.phone_number, {})
        }
    else:
        session["attempts"] += 1
        if session["attempts"] >= 2:
            return {"message": "Phone number invalid. Booking process failed!"}
        return {"message": "Invalid phone number. Please try again."}

# -------------------------------
# Step 1.1: Validate Customer Name
# -------------------------------
@app.post("/validate-customer/")
def validate_customer(phone: PhoneNumber, name: str):
    session = SESSIONS.get(phone.phone_number)
    if not session or not session.get("validated"):
        raise HTTPException(status_code=403, detail="Phone number not validated.")

    customer = ALLOWED_CUSTOMERS.get(phone.phone_number)
    if customer and customer["name"].lower() == name.lower():
        return {"message": "Customer validated successfully.", "customer": customer}
    else:
        return {
            "message": "Customer not found. Please register with name, email, and phone number."
        }

# -------------------------------
# Step 1.2: Register New Customer
# -------------------------------
@app.post("/register-customer/")
def register_customer(customer: CustomerRegistration):
    if customer.phone_number in ALLOWED_CUSTOMERS:
        return {"message": "Customer already exists."}

    # Save into allowed customers
    ALLOWED_CUSTOMERS[customer.phone_number] = {
        "name": customer.name,
        "email": customer.email
    }
    # auto-mark validated
    SESSIONS[customer.phone_number] = {"validated": True}
    return {
        "message": "Customer registered successfully.",
        "customer": ALLOWED_CUSTOMERS[customer.phone_number]
    }

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
# Step 3: Select Seat
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
                    session["bus_id"] = selection.bus_id
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
# Step 5: Make Payment
# -------------------------------
@app.post("/make-payment/")
def make_payment(payment: Payment):
    session = SESSIONS.get(payment.phone_number)
    if not session or not session.get("validated"):
        raise HTTPException(status_code=403, detail="Phone number not validated.")

    confirmation_number = random.randint(100000, 999999)
    return {
        "message": "Payment successful! Your bus ticket is confirmed.",
        "amount_paid": payment.amount,
        "confirmation_number": confirmation_number,
        "ticket_status": "CONFIRMED",
        "passenger": session.get("passenger"),
        "bus_id": session.get("bus_id"),
        "seat_number": session.get("seat")
    }
