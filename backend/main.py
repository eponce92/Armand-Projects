from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from PIL import Image
import io
import base64
from pathlib import Path
import asyncio
from typing import List, Dict
import time
import tkinter as tk
from tkinter import filedialog

from .clip_utils import load_model, get_image_embedding, search_similar_images

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model globally
model, preprocess = load_model()

# Create necessary directories
os.makedirs("temp", exist_ok=True)
os.makedirs("temp/thumbnails", exist_ok=True)

# Mount static directories
app.mount("/static", StaticFiles(directory="temp"), name="static")
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

def create_thumbnail(image_path: str, max_size: int = 800) -> str:
    """Create a high-quality thumbnail for an image and return its path"""
    try:
        thumb_path = os.path.join("temp/thumbnails", f"thumb_{os.path.basename(image_path)}")
        if os.path.exists(thumb_path):
            return thumb_path

        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Calculate aspect ratio
            aspect = img.width / img.height
            if aspect > 1:
                new_width = max_size
                new_height = int(max_size / aspect)
            else:
                new_height = max_size
                new_width = int(max_size * aspect)
            
            # High quality resize
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            img.save(thumb_path, "JPEG", quality=85, optimize=True)
        return thumb_path
    except Exception as e:
        print(f"Error creating thumbnail for {image_path}: {str(e)}")
        return image_path

@app.get("/")
async def read_root():
    return FileResponse("frontend/index.html")

@app.get("/list-folder")
async def list_folder(folder_path: str) -> Dict:
    """List all images in a folder"""
    try:
        image_files = []
        for ext in ['.jpg', '.jpeg', '.png', '.gif']:
            image_files.extend(Path(folder_path).glob(f'**/*{ext}'))
        return {"files": [str(f) for f in image_files]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/select-folder")
async def select_folder():
    """Open native folder selection dialog and return the selected path"""
    try:
        # Create a new root window for each dialog
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        root.attributes('-topmost', True)  # Make sure dialog stays on top
        
        folder_path = filedialog.askdirectory(
            parent=root,
            title='Select Folder with Images',
            initialdir=os.path.expanduser("~")  # Start from user's home directory
        )
        
        root.destroy()  # Clean up the window
        
        if folder_path:
            return {"folder_path": folder_path}
        else:
            return {"folder_path": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search_images(
    query: UploadFile = File(...),
    folder: str = Form(...),
    min_score: float = Form(0.0),
    batch_size: int = Form(32)
):
    try:
        # Save query image
        file_location = f"temp/{query.filename}"
        with open(file_location, "wb") as f:
            content = await query.read()
            f.write(content)

        # Create thumbnail for query image
        query_thumb = create_thumbnail(file_location)
        
        # Get query embedding
        query_embedding = get_image_embedding(file_location, model, preprocess)
        
        # Search similar images
        results = search_similar_images(
            query_embedding,
            folder,
            model,
            preprocess,
            min_score=min_score,
            batch_size=batch_size
        )

        # Process results to include thumbnails
        processed_results = []
        for result in results:
            thumb_path = create_thumbnail(result["path"])
            processed_results.append({
                "path": result["path"],
                "thumbnail": f"/static/thumbnails/thumb_{os.path.basename(result['path'])}",
                "score": result["score"]
            })

        return JSONResponse({
            "query_thumbnail": f"/static/thumbnails/thumb_{query.filename}",
            "results": processed_results
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 