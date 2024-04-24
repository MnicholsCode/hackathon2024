from typing import Optional
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
            return {"error": "Application not found"}
        return {"application_id": application_id, "status": result['status'].iloc[0]}
    except FileNotFoundError:
        return {"error": "Data file not found"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/echo")
def echo(message: Message):
    return {"message": message.message}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
