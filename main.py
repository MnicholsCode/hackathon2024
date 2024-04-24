import pandas as pd
from secrets import token_hex
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator, root_validator
from datetime import datetime

app = FastAPI()
csv_file = 'data.csv'

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

@app.get("/status/{application_id}")
async def get_application_status(application_id: str):
    try:
        # Load data into python
        df = pd.read_csv(csv_file)
        # Find the match on the application id
        result = df[df['application_id'] == application_id]
        # Get submission date from application
        submission_date = result['submission_date'].iloc[0]
        # Get our as_of_date
        as_of_date = datetime.now().strftime("%m%d%Y")
        # Get applications status
        status = result['status'].iloc[0]
        # Check if the id is empty
        if result.empty:
            return f"The Application id for {application_id} is incorrect or does not exist, please re-enter the id or consult..."
        
        # Setup output string for bot
        output_string = f"As of {as_of_date}. The applications status for ID:{application_id} is {status}, which was submitted on {submission_date}"
        return output_string

    except FileNotFoundError:
        return "Data file does not exist."
    
    except Exception as e:
        return {"error": str(e)}

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
