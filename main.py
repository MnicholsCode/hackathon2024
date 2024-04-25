from sqlalchemy import Column, String, Date, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import sqlalchemy as sa
from typing import Optional

import pandas as pd
from secrets import token_hex
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
import uuid

app = FastAPI()
csv_file = "data.csv"
bob_file = "book_of_business.csv"
# Database setup
database_url = "postgresql://hackathon_24_postgres_db_user:miFahcbAg3EBV51UntwSvo6bnekAMo0m@dpg-cokqhdud3nmc739jrqj0-a/hackathon_24_postgres_db"
engine = create_engine(database_url)
session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def generate_unique_id():
    """
    Function to create a unique id
    """
    return token_hex(3)

def get_db():
    """
    Function to set up database session
    """
    db = session_local()
    try:
        yield db
    finally:
        db.close()


class Order(BaseModel):
    item: str
    qty: str
    address: str



# Pydantic model for input validation
class Application(BaseModel):
    first_name: str 
    last_name: str 
    dob: str 
    address: Optional[str] = None 
    plan_choice: str

# SQLAlchemy model for database
class ApplicationDB(Base):
    __tablename__ = "applications"
    application_id = Column(String, primary_key=True, default=generate_unique_id)
    status = Column(String, default="Pending")
    first_name = Column(String)
    last_name = Column(String)
    submission_data = Column(String, default=datetime.now().strftime("%m/%d/%Y"))
    dob = Column(String)
    address = Column(String, default="N/A")

@app.on_event("startup")
def startup_event():
    # Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/commissions")
async def get_commissions():
    base_amount = 640
    total_commissions = 0
    df = pd.read_csv(bob_file)
    for __, row in df.iterrows():
        total_commissions += row["count"] * row["commission_rate"] * base_amount
    total_commissions = int(round(total_commissions, 0))
    return f"Your commissions total ${total_commissions:,}"


@app.get("/status/{application_id}")
async def get_application_status(application_id: str, db: Session=Depends(get_db)):
    try:
        # Query the database for the application
        application = db.query(ApplicationDB).filter(ApplicationDB.application_id == application_id).first()
        
        # Check if the application is found
        if not application:
            return f"{application_id} is not found. Please check and try again."
        
        # Prepare the data
        submission_date = application.submission_date.strftime("%m/%d/%Y") if application.submission_date else "Date not available"
        as_of_date = datetime.now().strftime("%m/%d/%Y")
        status = application.status

        # Setup output string for bot
        return f"As of {as_of_date}, the status for {application_id} is '{status}'.  It was submitted on {submission_date}"

    except Exception as e:
        return str(e)


@app.post("/add")
async def add_application(application_data: Application, db: Session = Depends(get_db)):
    new_application = ApplicationDB(
        first_name=application_data.first_name,
        last_name=application_data.last_name,
        dob=application_data.dob,
        address=application_data.address,
        plan_choice=application_data.plan_choice
    )
    db.add(new_application)
    db.commit()
    db.refresh(new_application)  # Refresh to load the auto-generated fields like application_id

    # Return a message indicating success along with the application_id
    return f"The application is submitted. The id is {new_application.application_id}. Write this down to track the status."
    

@app.get("/book_of_business")
def book_of_business():
    df = pd.read_csv(bob_file)
    # Get the total number of members
    total = sum(df["count"])
    # Start the book of business narative
    text = f"You have {total} members in your book of business.  The breakout is as follows:"
    # Aggregate the data up by plan
    df = df.groupby(["plan"])["count"].sum().reset_index()
    # Loop over the aggregated data
    for __, row in df.iterrows():
        # Add to the narative
        text = text + "<br/> " + row["plan"] + ": " + str(row["count"])
    # Return the narative
    return text


@app.post("/order")
def order_stuff(order: Order):
    # Do we need to add a s to the item(s)?
    s = "s"  # Assume yes
    if order.qty == "1":
        s = ""
    # Create a fake order id
    order_id = str(uuid.uuid4())
    # Return a plausible confirmation message
    return f"Your order for {order.qty} {order.item}{s} to be delivered to {order.address} was submitted.  The order number is: {order_id}."


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
