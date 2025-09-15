from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
import random
from datetime import datetime, timedelta

# -------------------------------
# Initialize FastAPI
# -------------------------------
app = FastAPI(title="Bus Ticket Booking API")

# -------------------------------
# Mock Data
# -------------------------------
AVAILABLE_BUSES = [
    {"bus_id": "B1001", "source": "Bangalore", "destination": "Chennai", "start_time": "08:00", "total_seats": 5},
    {"bus_id": "B1002", "source": "Bangalore", "destination": "Hyderabad", "start_time": "09:30", "total_seats": 5},
    {"bus_id": "B1003", "source": "Chennai", "destination": "Coimbatore", "start_time": "07:15", "total_seats": 5},
]

SEATS = {}  # (bus_id, seat_number) -> booking_id
TEMP_SELECTIONS = {}  # temporary storage before payment

BOOKINGS = {}  # booking_id -> booking details

# -------------------------------
# Pydantic Models
# -------------------------------
class SearchBus(BaseModel):
    source: str
    destination: str

class ChooseBus(BaseModel):
    session_id: str
    bus_id: str

class SelectSeat(BaseModel):
    session_id: str
    seat_number: int

class PassengerDetails(BaseModel):
    session_id: str
    name: str
    age: int
    gender: str

class Payment(BaseModel):
    session_id: str
    amount: float

# -------------------------------
# 1. Welcome Endpoint
# -------------------------------
@app.get("/welcome/")
def welcome():
    return {"message": "Welcome to Bus Ticket Booking Service!"}

# -------------------------------
# 2. Search Buses
# -------------------------------
@app.post("/search-bus/")
def search_bus(search: SearchBus):
    buses = [bus for bus in AVAILABLE_BUSES if bus["source"] == search.source and bus["destination"] == search.destination]
    if not buses:
        return {"message": "No buses found for this route. Please try again."}

    # Create a temporary session ID for this booking process
    session_id = f"SS{random.randint(1000,9999)}"
    TEMP_SELECTIONS[session_id] = {"bus": None, "seat": None, "passenger": None}

    return {"session_id": session_id, "available_buses": buses}

# -------------------------------
# 3. Choose Bus
# -------------------------------
@app.post("/choose-bus/")
def choose_bus(selection: ChooseBus):
    session = TEMP_SELECTIONS.get(selection.session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    bus = next((bus for bus in AVAILABLE_BUSES if bus["bus_id"] == selection.bus_id), None)
    if not bus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bus not found.")

    session["bus"] = bus
    return {"message": "Bus selected successfully.", "session_id": selection.session_id, "bus": bus}

# -------------------------------
# 4. Select Seat
# -------------------------------
@app.post("/select-seat/")
def select_seat(selection: SelectSeat):
    session = TEMP_SELECTIONS.get(selection.session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    bus = session["bus"]
    if not bus:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bus not yet chosen.")

    if selection.seat_number < 1 or selection.seat_number > bus["total_seats"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid seat number.")
    if SEATS.get((bus["bus_id"], selection.seat_number)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Seat already booked.")

    session["seat"] = selection.seat_number
    return {"message": "Seat selected successfully.", "session_id": selection.session_id, "seat_number": selection.seat_number}

# -------------------------------
# 5. Enter Passenger Details
# -------------------------------
@app.post("/enter-passenger/")
def enter_passenger(details: PassengerDetails):
    session = TEMP_SELECTIONS.get(details.session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    session["passenger"] = {
        "name": details.name,
        "age": details.age,
        "gender": details.gender
    }
    return {"message": "Passenger details saved successfully.", "session_id": details.session_id}

# -------------------------------
# 6. Make Payment & Generate Booking ID
# -------------------------------
@app.post("/make-payment/")
def make_payment(payment: Payment):
    session = TEMP_SELECTIONS.get(payment.session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    if payment.amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment amount.")

    # Ensure bus, seat, and passenger details are filled
    if not session.get("bus") or not session.get("seat") or not session.get("passenger"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incomplete booking details.")

    # Mark seat as booked
    bus_id = session["bus"]["bus_id"]
    seat_number = session["seat"]
    if SEATS.get((bus_id, seat_number)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Seat already booked.")

    booking_id = f"BK{random.randint(10000,99999)}"
    confirmation_number = f"TKT{random.randint(10000,99999)}"

    # Save booking permanently
    BOOKINGS[booking_id] = {
        "status": "Payment Done",
        "bus": session["bus"],
        "seat": seat_number,
        "passenger": session["passenger"],
        "confirmation_number": confirmation_number,
        "journey_date": (datetime.now() + timedelta(days=1)).strftime("%d-%m-%Y")
    }

    # Update seat mapping
    SEATS[(bus_id, seat_number)] = booking_id

    # Clear temporary session
    TEMP_SELECTIONS.pop(payment.session_id)

    return {
        "message": "Payment successful. Ticket booked!",
        "booking_id": booking_id,
        "confirmation_number": confirmation_number,
        "journey_date": BOOKINGS[booking_id]["journey_date"]
    }

# -------------------------------
# 7. Check Ticket Status
# -------------------------------
@app.get("/check-status/{booking_id}")
def check_status(booking_id: str):
    if booking_id not in BOOKINGS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking ID not found.")
    return BOOKINGS[booking_id]

# -------------------------------
# 8. Cancel Ticket
# -------------------------------
@app.post("/cancel-ticket/{booking_id}")
def cancel_ticket(booking_id: str):
    booking = BOOKINGS.get(booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking ID not found.")

    booking["status"] = "Cancelled"
    # Free the seat
    bus_id = booking["bus"]["bus_id"]
    seat_number = booking["seat"]
    SEATS.pop((bus_id, seat_number), None)

    return {"message": "Ticket cancelled successfully.", "booking_id": booking_id}
