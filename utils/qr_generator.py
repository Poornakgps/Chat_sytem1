import qrcode
import base64
from io import BytesIO

def generate_upi_qr(amount: float, upi_id: str = "poornachandra1479@oksbi") -> str:
    upi_url = f"upi://pay?pa={upi_id}&am={amount}&cu=INR"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(upi_url)
    qr.make(fit=True)
    
    qr_image = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    qr_image.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    return f"data:image/png;base64,{qr_base64}"
