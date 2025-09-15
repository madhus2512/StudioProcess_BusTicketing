from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List
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

BOOKINGS = {}   # booking_id → booking details
PASSENGERS = {} # booking_id → passenger details
SEATS = {}      # (bus_id, seat_number) → booking_id

# -------------------------------
# Pydantic Models
# -------------------------------
class SearchBus(BaseModel):
    source: str
    destination: str

class SelectBus(BaseModel):
    booking_id: str
    bus_id: str

class SelectSeat(BaseModel):
    booking_id: str
    seat_number: int

class PassengerDetails(BaseModel):
    booking_id: str
    name: str
    age: int
    gender: str

class Payment(BaseModel):
    booking_id: str
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

    # create temporary booking id
    booking_id = f"BK{random.randint(1000,9999)}"
    BOOKINGS[booking_id] = {"status": "Bus Search Done", "bus": None, "seat": None}

    return {"booking_id": booking_id, "available_buses": buses}

# -------------------------------
# 3. Choose Bus
# -------------------------------
@app.post("/choose-bus/")
def choose_bus(selection: SelectBus):
    if selection.booking_id not in BOOKINGS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking ID not found.")
    bus = next((bus for bus in AVAILABLE_BUSES if bus["bus_id"] == selection.bus_id), None)
    if not bus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bus not found.")
    BOOKINGS[selection.booking_id]["bus"] = bus
    BOOKINGS[selection.booking_id]["status"] = "Bus Selected"
    return {"message": "Bus selected successfully.", "booking_id": selection.booking_id, "bus": bus}

# -------------------------------
# 4. Select Seat
# -------------------------------
@app.post("/select-seat/")
def select_seat(selection: SelectSeat):
    if selection.booking_id not in BOOKINGS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking ID not found.")
    bus = BOOKINGS[selection.booking_id]["bus"]
    if not bus:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bus not yet chosen.")
    if selection.seat_number < 1 or selection.seat_number > bus["total_seats"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid seat number.")
    if SEATS.get((bus["bus_id"], selection.seat_number)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Seat already booked.")

    SEATS[(bus["bus_id"], selection.seat_number)] = selection.booking_id
    BOOKINGS[selection.booking_id]["seat"] = selection.seat_number
    BOOKINGS[selection.booking_id]["status"] = "Seat Selected"

    return {"message": "Seat selected successfully.", "booking_id": selection.booking_id, "seat_number": selection.seat_number}

# -------------------------------
# 5. Enter Passenger Details
# -------------------------------
@app.post("/enter-passenger/")
def enter_passenger(details: PassengerDetails):
    if details.booking_id not in BOOKINGS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking ID not found.")
    PASSENGERS[details.booking_id] = {
        "name": details.name,
        "age": details.age,
        "gender": details.gender
    }
    BOOKINGS[details.booking_id]["status"] = "Passenger Added"
    return {"message": "Passenger details saved successfully.", "booking_id": details.booking_id}

# -------------------------------
# 6. Make Payment
# -------------------------------
@app.post("/make-payment/")
def make_payment(payment: Payment):
    if payment.booking_id not in BOOKINGS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking ID not found.")
    if payment.amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment amount.")

    confirmation_number = f"TKT{random.randint(10000,99999)}"
    BOOKINGS[payment.booking_id]["status"] = "Payment Done"
    BOOKINGS[payment.booking_id]["confirmation_number"] = confirmation_number
    BOOKINGS[payment.booking_id]["journey_date"] = (datetime.now() + timedelta(days=1)).strftime("%d-%m-%Y")

    return {
        "message": "Payment successful. Ticket booked!",
        "booking_id": payment.booking_id,
        "confirmation_number": confirmation_number,
        "journey_date": BOOKINGS[payment.booking_id]["journey_date"]
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
    if booking_id not in BOOKINGS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking ID not found.")
    BOOKINGS[booking_id]["status"] = "Cancelled"
    return {"message": "Ticket cancelled successfully.", "booking_id": booking_id}
