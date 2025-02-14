from fastapi import APIRouter, Request, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import os
from main1 import manager

buyer_router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Create uploads directory if it doesn't exist
os.makedirs("static/uploads", exist_ok=True)

# Serve buyer page
@buyer_router.get("/buyer", response_class=HTMLResponse)
async def buyer_page(request: Request):
    try:
        # Get chat history for initial load
        conn = sqlite3.connect('chat.db')
        c = conn.cursor()
        c.execute('''SELECT message, file_name, timestamp FROM buyer_chat 
                     ORDER BY timestamp''')
        chat_history = c.fetchall()
        conn.close()
        
        return templates.TemplateResponse(
            "buyer.html",
            {
                "request": request,
                "chat_history": chat_history
            }
        )
    except Exception as e:
        print(f"Error loading buyer page: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def safe_file_save(file: UploadFile, file_name: str) -> bool:
    try:
        file_path = f"static/uploads/{file_name}"
        os.makedirs("static/uploads", exist_ok=True)
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())
        return True
    except Exception as e:
        print(f"Error saving file: {e}")
        return False

# Send message
@buyer_router.post("/buyer/send_message")
async def send_message(message: str = Form(...), file: UploadFile = File(None)):
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    
    try:
        file_name = None
        if file:
            file_name = file.filename
            if not safe_file_save(file, file_name):
                raise HTTPException(status_code=500, detail="Failed to save file")
        
        c.execute('''INSERT INTO buyer_chat (message, file_name)
                     VALUES (?, ?)''', (message, file_name))
        
        conn.commit()
        
        await manager.broadcast({
            "sender": "buyer",
            "message": message,
            "file_name": file_name
        })
        
        return {"status": "success"}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Send bargain request
@buyer_router.post("/buyer/bargain")
async def send_bargain(amount: float = Form(...)):
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    
    try:
        c.execute('''INSERT INTO buyer_chat (message, is_bargain, bargain_amount)
                     VALUES (?, TRUE, ?)''', (f"Bargain request: ${amount}", amount))
        
        conn.commit()
        
        await manager.broadcast({
            "sender": "buyer",
            "type": "bargain",
            "amount": amount
        })
        
        return {"status": "success"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()