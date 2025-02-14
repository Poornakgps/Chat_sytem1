from fastapi import APIRouter, Request, File, UploadFile, Form, HTTPException, WebSocket, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from services.websocket import manager
from db.database import get_db_connection
from utils.qr_generator import generate_upi_qr
from typing import List, Optional
from routers.chat_utils import save_uploaded_files, get_chat_history, clear_chat

router = APIRouter(prefix="/seller", tags=["seller"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def seller_page(request: Request):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('''SELECT message, file_name, timestamp FROM seller_chat
                    ORDER BY timestamp''')
        chat_history = c.fetchall()
        return templates.TemplateResponse(
            "seller.html",
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
    order_status: Optional[str] = Form(None),
    bargain_status: Optional[str] = Form(None),
    payment_status: Optional[str] = Form(None),
    payment_qr_code: Optional[str] = Form(None)
):
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        file_names, file_names_str = await save_uploaded_files(files)
        
        c.execute('''
            INSERT INTO seller_chat 
            (message, file_name, order_status, bargain_status, payment_status, payment_qr_code)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (message, file_names_str, order_status, bargain_status, payment_status, payment_qr_code))
        
        conn.commit()
        
        c.execute("SELECT * FROM seller_chat ORDER BY chat_id DESC LIMIT 1")
        latest_entry = c.fetchone()
        print(f"Latest DB entry: {latest_entry}")

        await manager.broadcast({
            "sender": "seller",
            "message": message,
            "file_names": file_names,
            "order_status": order_status,
            "bargain_status": bargain_status,
            "payment_status": payment_status,
            "payment_qr_code": payment_qr_code
        })
        
        return {
            "status": "success",
            "saved_files": file_names,
            "message": message,
            "order_status": order_status,
            "bargain_status": bargain_status,
            "payment_status": payment_status,
            "payment_qr_code": payment_qr_code
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.post("/bargain_response")
async def bargain_response(response: bool = Form(...), amount: float = Form(...)):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        status = "approved" if response else "rejected"
        message = f"Bargain {status}"
        qr_code = None
        
        if response:
            message += f" - Final amount: ${amount}"
            qr_code = generate_upi_qr(amount)
            message += "\nPlease scan the QR code to make the payment."
            
            c.execute('''SELECT chat_id FROM buyer_chat
                        WHERE is_bargain = TRUE
                        ORDER BY timestamp DESC LIMIT 1''')
            result = c.fetchone()
            
            if result:
                chat_id = result[0]
                c.execute('''UPDATE buyer_chat
                            SET payment_status = 'pending'
                            WHERE chat_id = ?''', (chat_id,))
        
        c.execute('''INSERT INTO seller_chat
                    (message, bargain_status, payment_status, payment_qr_code)
                    VALUES (?, ?, ?, ?)''',
                    (message, status, "pending" if response else None, qr_code))
        conn.commit()
        
        response_data = {
            "sender": "seller",
            "type": "bargain_response",
            "approved": response,
            "amount": amount,
            "status": status
        }
        if response:
            response_data.update({
                "qr_code": qr_code,
                "payment_status": "pending"
            })
            
        await manager.broadcast(response_data)
        return {"status": "success"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.post("/confirm_payment")
async def confirm_payment(chat_id: int = Form(...)):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('''UPDATE seller_chat
                    SET payment_status = 'completed'
                    WHERE chat_id = ?''', (chat_id,))
        conn.commit()
        
        await manager.broadcast({
            "sender": "seller",
            "type": "payment_status",
            "chat_id": chat_id,
            "status": "completed"
        })
        return {"status": "success"}
    finally:
        conn.close()

@router.post("/clear_chat")
async def clear_seller_chat():
    return await clear_chat("seller_chat")

@router.get("/chat_history")
async def get_seller_chat_history(role: str = Query(..., description="User role (buyer/seller)")):
    return await get_chat_history(role)