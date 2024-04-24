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
        # Check if the id is empty
        if result.empty:
            return f"{application_id} is not found.  Please check and try again."
        # Get submission date from application
        submission_date = result['submission_date'].iloc[0]
        # Get our as_of_date
        as_of_date = datetime.now().strftime("%m%d%Y")
        # Get applications status
        status = result['status'].iloc[0]
        # Setup output string for bot
        return f"As of {as_of_date}, the status for {application_id} is {status}.  It was submitted on {submission_date}"

    except FileNotFoundError:
        return "Data file does not exist."
    
    except Exception as e:
        return str(e)

@app.post("/echo")
def echo(message: Message):
    return {"message": message.message}


@app.get("/book_of_business")
def book_of_business():
    df = pd.read_csv("book_of_business.csv")
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
