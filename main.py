import pandas as pd
from secrets import token_hex
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator, root_validator
from datetime import datetime

app = FastAPI()
csv_file = "data.csv"
bob_file = "book_of_business.csv"


def generate_unique_application_id():
    """
    Function to create a unique id
    """
    df = pd.read_csv(csv_file)
    while True:
        new_id = token_hex(2)  # Generates a random 4-char hex string (2 bytes)
        if new_id not in df['application_id'].values:
            return new_id

class Application(BaseModel):
    application_id: str = None
    status: str = "Pending"
    first_name: str = "Missing"
    last_name: str = "Missing"
    submission_date: str = None
    dob: str = "Missing"
    address: str = "Missing"
    city: str = "Missing"
    state: str = "Missing"
    zip: str = "00000"
    plan_choice: str = "Missing"

    @root_validator(pre=True)
    def set_application_id(cls, values):
        if values.get('application_id') is None:
            values['application_id'] = generate_unique_application_id()
        if values.get('submission_date') is None:
            values['submission_date'] = datetime.now().strftime("%m/%d/%Y")
        return values

    @validator('city', pre=True, always=True)
    def capitalize_city(cls, v):
        return v.title() if v else 'Missing'

    @validator('state', pre=True, always=True)
    def uppercase_state(cls, v):
        return v.upper() if v else 'Missing'


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
    total_commissions = int(round(total_commissions,0))
    return f"Your commissions total ${total_commissions:,}"


@app.get("/status/{application_id}")
async def get_application_status(application_id: str):
    try:
        # Load data into python
        df = pd.read_csv(csv_file, dtype=str)
        # Find the match on the application id
        result = df[df["application_id"] == application_id]
        # Check if the id is empty
        if result.empty:
            return f"{application_id} is not found.  Please check and try again."
        # Get submission date from application
        submission_date = result["submission_date"].iloc[0]
        # Get our as_of_date
        as_of_date = datetime.now().strftime("%m/%d/%Y")
        # Get applications status
        status = result["status"].iloc[0]
        # Setup output string for bot
        return f"As of {as_of_date}, the status for {application_id} is {status}.  It was submitted on {submission_date}"

    except FileNotFoundError:
        return "Data file does not exist."

    except Exception as e:
        return str(e)

@app.post("/add")
async def add_application(application: Application):
    try:
        # Load in data
        df = pd.read_csv(csv_file)
        
        # Check if the DataFrame is empty to handle the first entry scenario
        if not df.empty and application.application_id in df['application_id'].values:
            raise HTTPException(status_code=400, detail="A rare ID conflict occurred, please try submitting again.")
        
        # Grab data from user input, create df and save to the csv
        new_data_df = pd.DataFrame([application.dict()])
        df = pd.concat([df, new_data_df], ignore_index=True)
        df.to_csv(csv_file, index=False)
        # Grab create id
        id = application.application_id

        return f"The application is submitted. The id is {id}. Write this down to track the status."
    
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Data file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        text = text + "\n " + row["plan"] + ": " + str(row["count"])
    # Return the narative
    return text


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
