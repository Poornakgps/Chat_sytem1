import os
from fastapi import UploadFile, HTTPException
from typing import Optional
import secrets
from datetime import datetime
    
class FileService:
    UPLOAD_DIR = "static/uploads"
    
    @classmethod
    def initialize(cls):
        try:
            os.makedirs(cls.UPLOAD_DIR, exist_ok=True)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create upload directory: {str(e)}")
    
    @classmethod
    async def save_file(cls, file: UploadFile) -> Optional[str]:
            if not file or not file.filename:
                return None
            
            try:
                file_extension = os.path.splitext(file.filename)[-1].lower()
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                random_hash = secrets.token_hex(4)
                unique_filename = f"{timestamp}_{random_hash}{file_extension}"

                file_path = os.path.join(cls.UPLOAD_DIR, unique_filename)
                
                os.makedirs(cls.UPLOAD_DIR, exist_ok=True)

                with open(file_path, "wb") as buffer:
                    buffer.write(await file.read())

                return unique_filename
            except OSError as e: 
                raise HTTPException(status_code=500, detail=f"OS error while saving file: {str(e)}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    @classmethod
    def remove_file(cls, file_name: str) -> bool:
        if not file_name:
            return False
            
        try:
            file_path = os.path.join(cls.UPLOAD_DIR, file_name)
            
            if not os.path.exists(file_path):
                return False
            
            os.remove(file_path)
            return True
        except PermissionError:
            raise HTTPException(status_code=403, detail="Permission denied: Cannot delete file")
        except OSError as e:
            raise HTTPException(status_code=500, detail=f"OS error while deleting file: {str(e)}")
    
    @classmethod
    def clear_uploads(cls):
        try:
            if not os.path.exists(cls.UPLOAD_DIR):
                raise HTTPException(status_code=404, detail="Upload directory does not exist")

            for file_name in os.listdir(cls.UPLOAD_DIR):
                file_path = os.path.join(cls.UPLOAD_DIR, file_name)
                
                if os.path.isfile(file_path):
                    os.remove(file_path)

        except PermissionError:
            raise HTTPException(status_code=403, detail="Permission denied: Cannot clear uploads")
        except OSError as e:
            raise HTTPException(status_code=500, detail=f"OS error while clearing uploads: {str(e)}")
