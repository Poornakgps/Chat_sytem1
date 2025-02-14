from fastapi import APIRouter, Request, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from main1 import manager
import qrcode
import base64
from io import BytesIO

seller_router = APIRouter()
templates = Jinja2Templates(directory="templates")

def generate_upi_qr(amount: float, upi_id: str = "poornachandra1479@oksbi") -> str:
    # Create UPI payment URL
    upi_url = f"upi://pay?pa={upi_id}&am={amount}&cu=INR"
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(upi_url)
    qr.make(fit=True)
    
    # Create QR image
    qr_image = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 string
    buffered = BytesIO()
    qr_image.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    return f"data:image/png;base64,{qr_base64}"

# Serve seller page
@seller_router.get("/seller", response_class=HTMLResponse)
async def seller_page(request: Request):
    return templates.TemplateResponse("seller.html", {"request": request})

# Send message
@seller_router.post("/seller/send_message")
async def send_message(message: str = Form(...), file: UploadFile = File(None)):
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    
    file_name = None
    if file:
        file_name = file.filename
        file_path = f"static/uploads/{file_name}"
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
    
    c.execute('''INSERT INTO seller_chat (message, file_name)
                 VALUES (?, ?)''', (message, file_name))
    
    conn.commit()
    conn.close()
    
    await manager.broadcast({
        "sender": "seller",
        "message": message,
        "file_name": file_name
    })

# Update order status
@seller_router.post("/seller/update_status")
async def update_status(status: str = Form(...), tracking: str = Form(None)):
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    
    message = f"Order status updated to: {status}"
    if tracking:
        message += f"\nTracking number: {tracking}"
    
    c.execute('''INSERT INTO seller_chat (message, order_status, tracking_number)
                 VALUES (?, ?, ?)''', (message, status, tracking))
    
    conn.commit()
    conn.close()
    
    await manager.broadcast({
        "sender": "seller",
        "type": "status_update",
        "status": status,
        "tracking": tracking
    })

# Handle bargain response
@seller_router.post("/seller/bargain_response")
async def bargain_response(response: bool = Form(...), amount: float = Form(...)):
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    
    try:
        status = "approved" if response else "rejected"
        message = f"Bargain {status}"
        qr_code = None
        
        if response:
            message += f" - Final amount: ${amount}"
            qr_code = generate_upi_qr(amount)
            message += "\nPlease scan the QR code to make the payment."
            
            # First, get the latest bargain request's chat_id
            c.execute('''SELECT chat_id FROM buyer_chat 
                        WHERE is_bargain = TRUE 
                        ORDER BY timestamp DESC LIMIT 1''')
            result = c.fetchone()
            
            if result:
                chat_id = result[0]
                # Now update that specific record
                c.execute('''UPDATE buyer_chat 
                           SET payment_status = 'pending'
                           WHERE chat_id = ?''', (chat_id,))
        
        # Insert seller's response
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
            response_data["qr_code"] = qr_code
            response_data["payment_status"] = "pending"
        
        await manager.broadcast(response_data)
        return {"status": "success"}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

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

    
def update_seller_chat_table():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('''ALTER TABLE seller_chat ADD COLUMN IF NOT EXISTS bargain_status TEXT''')
    c.execute('''ALTER TABLE seller_chat ADD COLUMN IF NOT EXISTS payment_status TEXT''')
    conn.commit()
    conn.close()

@seller_router.post("/seller/confirm_payment")
async def confirm_payment(chat_id: int = Form(...)):
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    
    c.execute('''UPDATE seller_chat 
                 SET payment_status = 'completed'
                 WHERE chat_id = ?''', (chat_id,))
    
    conn.commit()
    conn.close()
    
    await manager.broadcast({
        "sender": "seller",
        "type": "payment_status",
        "chat_id": chat_id,
        "status": "completed"
    })