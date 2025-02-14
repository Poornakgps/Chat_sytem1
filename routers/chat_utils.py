import os
from fastapi import File, Form, HTTPException
from db.database import get_db_connection

async def save_uploaded_files(files):
    file_names = []
    
    if files and not isinstance(files, list):
        files = [files]
        
    if files:
        for file in files:
            if file and file.filename:
                upload_dir = "uploads"
                os.makedirs(upload_dir, exist_ok=True)
                
                file_name = os.path.join(upload_dir, file.filename)
                
                try:
                    contents = await file.read()
                    with open(file_name, "wb") as f:
                        f.write(contents)
                    file_names.append(file.filename)
                except Exception as e:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to save file {file.filename}: {str(e)}"
                    )
    
    return file_names, ",".join(file_names) if file_names else None

async def get_chat_history(role: str):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('''SELECT chat_id, message, file_name, timestamp, 'buyer' as sender, 
                    CASE WHEN is_bargain THEN 'bargain' ELSE NULL END as type,
                    bargain_amount as amount,
                    payment_status
                    FROM buyer_chat 
                    ORDER BY timestamp''')
        buyer_messages = c.fetchall()

        c.execute('''SELECT chat_id, message, file_name, timestamp, 'seller' as sender,
                    order_status,
                    bargain_status as type,
                    CASE WHEN bargain_status = 'approved' THEN 
                        (SELECT bargain_amount FROM buyer_chat WHERE is_bargain = TRUE 
                         ORDER BY timestamp DESC LIMIT 1)
                    ELSE NULL END as amount,
                    payment_status,
                    payment_qr_code
                    FROM seller_chat 
                    ORDER BY timestamp''')
        seller_messages = c.fetchall()

        all_messages = []
        for msg in buyer_messages + seller_messages:
            message_dict = {
                'id': msg[0],
                'message': msg[1],
                'timestamp': msg[3],
                'sender': msg[4]
            }
            
            if msg[2]: 
                if ',' in msg[2]:
                    message_dict['file_names'] = msg[2].split(',')
                else:
                    message_dict['file_name'] = msg[2]
            
            if msg[5]: 
                if msg[4] == 'seller' and msg[5]:
                    message_dict['order_status'] = msg[5]
                
            if msg[6]: 
                message_dict['type'] = msg[6]
                
            if msg[7]: 
                if msg[6] == 'bargain' or msg[6] == 'approved':
                    message_dict['amount'] = msg[7]
            
            if len(msg) > 8 and msg[8]:
                message_dict['payment_status'] = msg[8]
                
            if len(msg) > 9 and msg[9] and msg[4] == 'seller':
                message_dict['payment_qr_code'] = msg[9]

            all_messages.append(message_dict)

        all_messages.sort(key=lambda x: x['timestamp'])
        
        return all_messages

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chat history: {str(e)}")
    finally:
        conn.close()

async def clear_chat(table_name):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(f"SELECT file_name FROM {table_name} WHERE file_name IS NOT NULL")
        files = c.fetchall()
        
        c.execute(f"DELETE FROM {table_name}")
        c.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}'")
        conn.commit()
        
        deleted_files = []
        failed_files = []
        for file_tuple in files:
            file_name = file_tuple[0]
            if file_name:
                for fname in file_name.split(','):
                    file_path = f"uploads/{fname}"
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            deleted_files.append(fname)
                    except Exception as e:
                        failed_files.append({"file": fname, "error": str(e)})
        
        return {
            "message": f"{table_name} chat history cleared successfully",
            "details": {
                "deleted_files": deleted_files,
                "failed_files": failed_files
            }
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()