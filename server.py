from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import time

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

SIGNAL_STORE = {}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/create_offer")
async def create_offer(
    room_id: str = Form(...), offer: str = Form(...), password: str = Form(...)
):
    SIGNAL_STORE[room_id] = {
        "offer": offer,
        "password": password,
        "offerer_candidates": [],
        "answerer_candidates": [],
        "messages": [],
    }
    return {"status": "offer stored"}


@app.post("/get_offer")
async def get_offer(room_id: str = Form(...), password: str = Form(...)):
    data = SIGNAL_STORE.get(room_id)
    if not data:
        raise HTTPException(status_code=404, detail="Room not found")
    if data.get("password") != password:
        raise HTTPException(status_code=401, detail="Incorrect password")
    return {"offer": data.get("offer")}


@app.post("/send_answer")
async def send_answer(
    room_id: str = Form(...), answer: str = Form(...), password: str = Form(...)
):
    data = SIGNAL_STORE.get(room_id)
    if not data:
        raise HTTPException(status_code=404, detail="Room not found")
    if data.get("password") != password:
        raise HTTPException(status_code=401, detail="Incorrect password")
    SIGNAL_STORE[room_id]["answer"] = answer
    return {"status": "answer stored"}


@app.post("/get_answer")
async def get_answer(room_id: str = Form(...), password: str = Form(...)):
    data = SIGNAL_STORE.get(room_id)
    if not data:
        raise HTTPException(status_code=404, detail="Room not found")
    if data.get("password") != password:
        raise HTTPException(status_code=401, detail="Incorrect password")
    return {"answer": data.get("answer", None)}


@app.post("/add_ice")
async def add_ice(
    room_id: str = Form(...),
    role: str = Form(...),
    candidate: str = Form(...),
    password: str = Form(...),
):
    data = SIGNAL_STORE.get(room_id)
    if not data:
        raise HTTPException(status_code=404, detail="Room not found")
    if data.get("password") != password:
        raise HTTPException(status_code=401, detail="Incorrect password")
    SIGNAL_STORE.setdefault(room_id, {})
    SIGNAL_STORE[room_id].setdefault(f"{role}_candidates", []).append(candidate)
    return {"status": "candidate stored"}


@app.post("/get_ice")
async def get_ice(
    room_id: str = Form(...), role: str = Form(...), password: str = Form(...)
):
    data = SIGNAL_STORE.get(room_id)
    if not data:
        raise HTTPException(status_code=404, detail="Room not found")
    if data.get("password") != password:
        raise HTTPException(status_code=401, detail="Incorrect password")
    other_role = "offerer" if role == "answerer" else "answerer"
    candidates = SIGNAL_STORE.get(room_id, {}).get(f"{other_role}_candidates", [])
    return {"candidates": candidates}


@app.post("/send_message")
async def send_message(
    room_id: str = Form(...),
    user_id: str = Form(...),
    message: str = Form(...),
    password: str = Form(...),
):
    data = SIGNAL_STORE.get(room_id)
    if not data:
        raise HTTPException(status_code=404, detail="Room not found")
    if data.get("password") != password:
        raise HTTPException(status_code=401, detail="Incorrect password")
    SIGNAL_STORE[room_id].setdefault("messages", []).append(
        {
            "user_id": user_id,
            "message": message,
            "timestamp": int(time.time() * 1000),  # Store timestamp in milliseconds
        }
    )
    return {"status": "message stored"}


@app.post("/get_messages")
async def get_messages(
    room_id: str = Form(...), timestamp: int = Form(...), password: str = Form(...)
):
    data = SIGNAL_STORE.get(room_id)
    if not data:
        raise HTTPException(status_code=404, detail="Room not found")
    if data.get("password") != password:
        raise HTTPException(status_code=401, detail="Incorrect password")
    messages = [
        msg
        for msg in SIGNAL_STORE.get(room_id, {}).get("messages", [])
        if msg["timestamp"] > timestamp
    ]
    return {"messages": messages}
