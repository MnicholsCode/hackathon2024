from sqlalchemy import Column, String, Date, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, validates
import sqlalchemy as sa
from typing import Optional, List

import pandas as pd
from secrets import token_hex
from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel, validator, ValidationError
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

    # Validate for name
    @validator('first_name', 'last_name', pre=True)
    def capitalize_name(cls, v):
        return v.title()
    
# Pydantic model for application update
class ApplicationUpdate(BaseModel):
    application_id: str
    field_name: str
    new_value: str

    @validator('field_name')
    def validate_field_name(cls, v):
        # Fields allowed to change
        allowed_fields = {'first_name', 'last_name', 'address', 'city','dob', 'plan_choice', 'status', 'submission_date'}
        # Validation for field choices
        if v not in allowed_fields:
            raise ValueError("This field cannot be updated or does not exist.")
        return v

# SQLAlchemy model for database
class ApplicationDB(Base):
    __tablename__ = "fake_application"
    application_id = Column(String, primary_key=True, default=generate_unique_id)
    status = Column(String, default="Pending")
    first_name = Column(String)
    last_name = Column(String)
    submission_date = Column(String, default=datetime.now().strftime("%m/%d/%Y %I:%M%p"))
    dob = Column(String)
    address = Column(String, default="N/A")
    plan_choice = Column(String)
    
    # Validation for name
    @validates('first_name', 'last_name')
    def validate_name(self, key, name):
        return name.title()
    
# Pydantic model to correspond with sql alchemy model
class ApplicationResponse(BaseModel):
    application_id: str
    status: str
    first_name: str
    last_name: str
    submission_date: str
    dob: str
    address: str
    plan_choice: str

    class Config:
        from_attributes = True


@app.on_event("startup")
def startup_event():
    # Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    return {"message": "Hello World"}

# Get commissions
@app.get("/commissions")
async def get_commissions():
    base_amount = 640
    total_commissions = 0
    df = pd.read_csv(bob_file)
    for __, row in df.iterrows():
        total_commissions += row["count"] * row["commission_rate"] * base_amount
    total_commissions = int(round(total_commissions, 0))
    return f"Your commissions total ${total_commissions:,}"

# Get Status for application
@app.get("/status/{application_id}")
async def get_application_status(application_id: str, db: Session=Depends(get_db)):
    try:
        # Query the database for the application
        application = db.query(ApplicationDB).filter(func.lower(ApplicationDB.application_id) == application_id.lower()).first()
        
        # Check if the application is found
        if not application:
            return f"{application_id} is not found. Please check and try again."
        
        # Prepare the data
        submission_date = application.submission_date
        as_of_date = datetime.now().strftime("%m/%d/%Y %I:%M%p")
        status = application.status

        # Setup output string for bot
        return f"As of {as_of_date}, the status for {application_id} is '{status}'.  It was submitted on {submission_date}"

    except Exception as e:
        return str(e)

# Search the database for the application using first and last name
@app.get("/search-by-name", response_model=str)
async def fetch_applications_by_name(first_name: str, last_name: str, db: Session = Depends(get_db)):
    applications = db.query(ApplicationDB).filter(
        func.lower(ApplicationDB.first_name) == first_name.lower(),
        func.lower(ApplicationDB.last_name) == last_name.lower()
    ).all()

    if not applications:
        return "No applications found with the provided names."

    response = "\n".join(
        f"Application ID: {app.application_id}, Name: {app.first_name} {app.last_name}, Status: {app.status}, Address: {app.address}, Submitted on: {app.submission_date}, DOB: {app.dob}, Plan Choice: {app.plan_choice}"
        for app in applications
    )
    return response

# Add an application to the database
@app.post("/add")
async def add_application(application_data: Application, db: Session = Depends(get_db)):
    try:
        new_application = ApplicationDB(
            first_name=application_data.first_name,
            last_name=application_data.last_name,
            dob=application_data.dob,
            address=application_data.address,
            plan_choice=application_data.plan_choice
        )
        db.add(new_application)
        db.commit()
    
        # Return a message indicating success along with the application_id
        return f"The application is submitted. The id is {new_application.application_id}. Write this down to track the status."
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Update certain fields in the application
@app.put("/update-application")
async def update_application(update_data: ApplicationUpdate, db: Session = Depends(get_db)):
    # Fetch the existing application
    application = db.query(ApplicationDB).filter(ApplicationDB.application_id == update_data.application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Check if the field exists and update it
    if hasattr(application, update_data.field_name):
        setattr(application, update_data.field_name, update_data.new_value)
        db.commit()
        return f"Updated {update_data.field_name} successfully."
    else:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid field name")

# Display all applications depending on their status    
@app.get("/applications/status/", response_model=List[ApplicationResponse])
async def get_applications_by_status(status: str = Query(..., enum=["Pending", "Reviewed", "Completed"]), db: Session = Depends(get_db)):
    applications = db.query(ApplicationDB).filter(func.lower(ApplicationDB.status) == status.lower()).all()
    if not applications:
        raise HTTPException(status_code=404, detail="No applications found with the specified status")
    return applications

# Book of business
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

# Place an order
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
