from fastapi import APIRouter, Request, File, UploadFile, Form, HTTPException, WebSocket, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from services.websocket import manager
from db.database import get_db_connection
from typing import List, Optional
import os
from routers.chat_utils import save_uploaded_files, get_chat_history, clear_chat

router = APIRouter(prefix="/buyer", tags=["buyer"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def buyer_page(request: Request):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('''SELECT message, file_name, timestamp FROM buyer_chat
                    ORDER BY timestamp''')
        chat_history = c.fetchall()
        return templates.TemplateResponse(
            "buyer.html",
            {"request": request, "chat_history": chat_history}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.post("/send_message")
async def send_message(
    message: str = Form(...),
    files: List[UploadFile] = File(None),
    is_bargain: bool = Form(False),
    bargain_amount: Optional[float] = Form(None),
    payment_status: str = Form("pending")
):
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        file_names, file_names_str = await save_uploaded_files(files)
        c.execute('''
            INSERT INTO buyer_chat 
            (message, file_name, is_bargain, bargain_amount, payment_status)
            VALUES (?, ?, ?, ?, ?)
        ''', (message, file_names_str, is_bargain, bargain_amount, payment_status))
        
        conn.commit()
        
        c.execute("SELECT * FROM buyer_chat ORDER BY chat_id DESC LIMIT 1")
        latest_entry = c.fetchone()
        print(f"Latest DB entry: {latest_entry}")
        
        await manager.broadcast({
            "sender": "buyer",
            "message": message,
            "file_names": file_names,
            "is_bargain": is_bargain,
            "bargain_amount": bargain_amount,
            "payment_status": payment_status
        })
        
        return {
            "status": "success",
            "saved_files": file_names,
            "message": message,
            "is_bargain": is_bargain,
            "bargain_amount": bargain_amount,
            "payment_status": payment_status
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.post("/bargain")
async def send_bargain(amount: float = Form(...)):
    conn = get_db_connection()
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

@router.post("/clear_chat")
async def clear_buyer_chat():
    return await clear_chat("buyer_chat")

@router.get("/chat_history")
async def get_buyer_chat_history(role: str = Query(..., description="User role (buyer/seller)")):
    return await get_chat_history(role)


# @router.post("/update_status")
# async def update_status(order_id: str, status: str):
#     if order_id in orders:
#         orders[order_id]["status"] = status
#         message = json.dumps({
#             "type": "status_update",
#             "order_id": order_id,
#             "status": status
#         })
#         # Send the update to both buyer and seller if they're connected
#         if buyer_ws:
#             try:
#                 await buyer_ws.send_text(message)
#             except Exception:
#                 pass  # Ignore if the WebSocket fails
#         if seller_ws:
#             try:
#                 await seller_ws.send_text(message)
#             except Exception:
#                 pass  # Ignore if the WebSocket fails
#         return {"message": "Status updated"}
#     return {"error": "Order not found"}

# @router.get("/order_status")
# async def get_order_status():
#     conn = get_db_connection()
#     c = conn.cursor()
#     try:
#         c.execute('SELECT order_status FROM seller_chat ORDER BY timestamp DESC LIMIT 1')
#         result = c.fetchone()
#         latest_status = result[0] if result else "Unknown"
#         return {"status": latest_status}
#     finally:
#         conn.close()