import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

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
        df = pd.read_csv(csv_file)
        result = df[df['application_id'] == application_id]
        if result.empty:
            return f"The Application id for {application_id} is incorrect or does not exist, please re-enter the id or consult..."
        return f"The Application status for: {application_id} is {result['status'].iloc[0]}"
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
