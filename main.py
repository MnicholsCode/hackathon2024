import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()
csv_file = 'data.csv'

class Message(BaseModel):
    message: str

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/status/{application_id}")
async def get_application_status(application_id: int):
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

@app.post("/echo")
def echo(message: Message):
    return {"message": message.message}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
