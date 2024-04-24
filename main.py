from typing import Optional

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}

# @app.get("/echo")
# def echo(message: Optional[str] = None):
#     if message:
#         return {"message": message}
#     return {"message": "No message provided"}
