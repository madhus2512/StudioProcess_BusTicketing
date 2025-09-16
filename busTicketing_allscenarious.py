from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import random

app = FastAPI(title="Bus Ticket Booking API")

# -------------------------------
# Bus Operators and Routes
# -------------------------------
BUS_ROUTES = {
    "Garuda": ["Hyd - Bangalore", "Bangalore - Chennai"],
    "Volvo": ["Chennai - Mumbai", "Mumbai - Pune"],
    "GreenLines": ["Delhi - Agra", "Agra - Jaipur"],
    "AbhiBus": ["Chennai - Coimbatore", "Coimbatore - Trichy"]
}


# -------------------------------
# Pydantic Models
# -------------------------------
class DateSelection(BaseModel):
    date: str


class SeatSelection(BaseModel):
    date: str
    seat_number: int


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


# -------------------------------
# Pre-selected Operator & Route
# -------------------------------
PRE_SELECTED_OPERATOR = "Volvo"
PRE_SELECTED_ROUTE = "Chennai - Mumbai"

# Temporary storage
TEMP_BOOKED_SEATS = {}
PASSENGER_BOOKINGS = {}
CONFIRMED_TICKETS = {}


# -------------------------------
# API: Get Available Seats
# -------------------------------
@app.post("/available-seats/")
def get_seats(selection: DateSelection):
    route_key = f"{PRE_SELECTED_ROUTE}_{selection.date}"

    if route_key not in TEMP_BOOKED_SEATS:
        total_seats = 40
        booked_seats = random.sample(range(1, total_seats + 1), k=random.randint(0, 15))
        TEMP_BOOKED_SEATS[route_key] = booked_seats
    else:
        booked_seats = TEMP_BOOKED_SEATS[route_key]

    available_seats = [seat for seat in range(1, 41) if seat not in booked_seats]

    return {
        "operator": PRE_SELECTED_OPERATOR,
        "route": PRE_SELECTED_ROUTE,
        "date": selection.date,
        "available_seats": available_seats
    }


# -------------------------------
# API: Select Seat
# -------------------------------
@app.post("/select-seat/")
def select_seat(selection: SeatSelection):
    route_key = f"{PRE_SELECTED_ROUTE}_{selection.date}"

    if route_key not in TEMP_BOOKED_SEATS:
        raise HTTPException(status_code=400, detail="Check available seats first")

    if selection.seat_number in TEMP_BOOKED_SEATS[route_key]:
        raise HTTPException(status_code=400, detail="Seat already booked")

    TEMP_BOOKED_SEATS[route_key].append(selection.seat_number)

    return {
        "message": f"Seat {selection.seat_number} successfully selected!",
        "operator": PRE_SELECTED_OPERATOR,
        "route": PRE_SELECTED_ROUTE,
        "date": selection.date,
        "selected_seat": selection.seat_number
    }


# -------------------------------
# API: Add Passenger Info
# -------------------------------
@app.post("/passenger-info/")
def add_passenger(info: PassengerInfo):
    route_key = f"{PRE_SELECTED_ROUTE}_{info.date}_{info.seat_number}"

    if route_key in PASSENGER_BOOKINGS:
        raise HTTPException(status_code=400, detail="Passenger info already added for this seat")

    PASSENGER_BOOKINGS[route_key] = {
        "username": info.username,
        "phone_number": info.phone_number,
        "age": info.age,
        "operator": PRE_SELECTED_OPERATOR,
        "route": PRE_SELECTED_ROUTE,
        "seat_number": info.seat_number,
        "date": info.date
    }

    return {
        "message": "Passenger info successfully added!",
        "booking_details": PASSENGER_BOOKINGS[route_key]
    }


# -------------------------------
# API: Make Payment and Generate Ticket
# -------------------------------
@app.post("/make-payment/")
def make_payment(payment: PaymentInfo):
    route_key = f"{PRE_SELECTED_ROUTE}_{payment.date}_{payment.seat_number}"

    if route_key not in PASSENGER_BOOKINGS:
        raise HTTPException(status_code=400, detail="Passenger info not added for this seat")

    # Simulate card validation
    if len(payment.card_number) != 16 or not payment.card_number.isdigit():
        raise HTTPException(status_code=400, detail="Invalid card number")
    if len(payment.cvv) != 3 or not payment.cvv.isdigit():
        raise HTTPException(status_code=400, detail="Invalid CVV")

    # Generate ticket ID
    ticket_id = f"TKT{random.randint(1000, 9999)}"

    CONFIRMED_TICKETS[ticket_id] = {
        **PASSENGER_BOOKINGS[route_key],
        "payment_status": "Paid",
        "card_holder": payment.card_holder,
        "ticket_id": ticket_id
    }

    return {
        "message": "Payment successful! Ticket generated.",
        "ticket": CONFIRMED_TICKETS[ticket_id]
    }
