from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import random
from datetime import datetime, timedelta


app = FastAPI(title="Bus Ticket Booking API")

# -------------------------------
# Master Data
# -------------------------------
BUS_ROUTES = {
    "Garuda": ["Hyd - Bangalore", "Bangalore - Chennai"],
    "Volvo": ["Chennai - Mumbai", "Mumbai - Pune"],
    "GreenLines": ["Delhi - Agra", "Agra - Jaipur"],
    "AbhiBus": ["Chennai - Coimbatore", "Coimbatore - Trichy"]
}

# Temporary in-memory storage
TEMP_BOOKED_SEATS = {}
PASSENGER_BOOKINGS = {}
CONFIRMED_TICKETS = {}

# -------------------------------
# Pydantic Models
# -------------------------------
class OperatorSelection(BaseModel):
    operator_name: str


class RouteSelection(BaseModel):
    route_name: str


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
    card_number: str = Field(..., pattern=r"^\d{16}$")  # exactly 16 digits
    cvv: str = Field(..., pattern=r"^\d{3}$")           # exactly 3 digits
    expiry_date: str
    card_holder: str

# -------------------------------
# API 1: Get Bus Operators
# -------------------------------
@app.get("/buses/")
def get_buses():
    return {"available_buses": list(BUS_ROUTES.keys())}


# -------------------------------
# API 2: Get Bus Routes for Operator
# -------------------------------
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


# -------------------------------
# API 3: Get Available Dates for Route
# -------------------------------
@app.post("/route-dates/")
def get_dates(route: RouteSelection):
    today = datetime.today()
    # Generate next 5 days
    dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, 6)]
    return {"route": route.route_name, "available_dates": dates}


# -------------------------------
# API 4: Get Available Seats
# -------------------------------
@app.post("/available-seats/")
def get_seats(selection: DateSelection):
    route_key = f"{selection.date}"

    if route_key not in TEMP_BOOKED_SEATS:
        total_seats = 40
        booked_seats = random.sample(range(1, total_seats + 1), k=random.randint(0, 15))
        TEMP_BOOKED_SEATS[route_key] = booked_seats
    else:
        booked_seats = TEMP_BOOKED_SEATS[route_key]

    available_seats = [seat for seat in range(1, 41) if seat not in booked_seats]
    limited_seats = available_seats[:10]  # show only first 10

    return {
        "date": selection.date,
        "available_seats": limited_seats,
        "total_available": len(available_seats)
    }


# -------------------------------
# API 5: Add Passenger Info (NO seat restriction)
# -------------------------------
@app.post("/passenger-info/")
def add_passenger(info: PassengerInfo):
    # Generate a unique key per passenger entry
    booking_id = f"{info.date}_{info.seat_number}_{random.randint(1000,9999)}"

    PASSENGER_BOOKINGS[booking_id] = {
        "username": info.username,
        "phone_number": info.phone_number,
        "age": info.age,
        "seat_number": info.seat_number,
        "date": info.date
    }

    return {
        "message": "Passenger info successfully added (seat sharing allowed)!",
        "booking_id": booking_id,
        "booking_details": PASSENGER_BOOKINGS[booking_id]
    }


# -------------------------------
# API 6: Make Payment and Generate Ticket
# -------------------------------
@app.post("/make-payment/")
def make_payment(payment: PaymentInfo):
    # Match payment to any booking with same date & seat
    matching_booking = None
    for booking_id, data in PASSENGER_BOOKINGS.items():
        if data["date"] == payment.date and data["seat_number"] == payment.seat_number:
            matching_booking = (booking_id, data)
            break

    if not matching_booking:
        raise HTTPException(status_code=400, detail="No passenger info found for this seat and date")

    booking_id, passenger_data = matching_booking
    ticket_id = f"TKT{random.randint(1000, 9999)}"

    CONFIRMED_TICKETS[ticket_id] = {
        **passenger_data,
        "payment_status": "Paid",
        "card_holder": payment.card_holder,
        "ticket_id": ticket_id
    }

    return {
        "message": "Payment successful! Ticket generated.",
        "ticket": CONFIRMED_TICKETS[ticket_id]
    }


# -------------------------------
# API 7: View All Confirmed Tickets
# -------------------------------
@app.get("/confirmed-tickets/")
def get_confirmed_tickets():
    if not CONFIRMED_TICKETS:
        raise HTTPException(status_code=404, detail="No confirmed tickets found")
    return {"confirmed_tickets": CONFIRMED_TICKETS}


# -------------------------------
# API 8: View All Passenger Bookings (Admin)
# -------------------------------
@app.get("/passenger-bookings/")
def get_passenger_bookings():
    if not PASSENGER_BOOKINGS:
        raise HTTPException(status_code=404, detail="No passenger bookings found")
    return {"passenger_bookings": PASSENGER_BOOKINGS}
