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
import json
import torch
import torch.nn.functional as F
import clip
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

# Settings file path
SETTINGS_FILE = "settings.json"

# Get project root directory
ROOT_DIR = Path(__file__).parent.parent

# Mount frontend directory
app.mount("/static", StaticFiles(directory=str(ROOT_DIR / "frontend")), name="static")

def save_last_settings(query_path: str, folder_path: str, results=None):
    """Save the last used image, folder paths and results"""
    settings = {
        "last_query": query_path,
        "last_folder": folder_path,
        "last_results": results if results else [],
        "timestamp": time.time()
    }
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f)

def get_last_settings() -> Dict:
    """Get the last used settings"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error reading settings: {e}")
    return {"last_query": None, "last_folder": None, "timestamp": None}

@app.get("/")
async def read_root():
    return FileResponse(str(ROOT_DIR / "frontend/index.html"))

@app.get("/last-settings")
async def get_settings():
    """Get the last used settings"""
    return get_last_settings()

@app.get("/image/{path:path}")
async def get_image(path: str):
    """Serve image files safely"""
    try:
        return FileResponse(path)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Image not found")

@app.post("/select-image")
async def select_image():
    """Open native file selection dialog and return the selected file's info"""
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        file_path = filedialog.askopenfilename(
            parent=root,
            title='Select Image File',
            initialdir=os.path.expanduser("~"),
            filetypes=[('Image files', '*.jpg *.jpeg *.png *.gif')]
        )
        
        root.destroy()
        
        if file_path:
            folder_path = str(Path(file_path).parent)
            save_last_settings(file_path, folder_path)
            
            # Get image dimensions for proper sizing
            with Image.open(file_path) as img:
                width, height = img.size
                aspect_ratio = height / width
            
            return {
                "file_path": file_path,
                "folder_path": folder_path,
                "filename": os.path.basename(file_path),
                "width": width,
                "height": height,
                "aspect_ratio": aspect_ratio
            }
        return {"file_path": None, "folder_path": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search_images(
    folder: str = Form(...),
    min_score: float = Form(0.0),
    batch_size: int = Form(32),
    search_type: str = Form(...),
    query_path: str = Form(None),
    query_text: str = Form(None)
):
    try:
        print(f"Search request - Type: {search_type}, Folder: {folder}")
        
        if search_type not in ['image', 'text']:
            raise HTTPException(status_code=400, detail="Invalid search type")
        
        if search_type == 'image' and not query_path:
            raise HTTPException(status_code=400, detail="Query image path is required for image search")
        
        if search_type == 'text' and not query_text:
            raise HTTPException(status_code=400, detail="Query text is required for text search")

        # Get query embedding
        try:
            if search_type == 'image':
                query_embedding = get_image_embedding(query_path, model, preprocess)
            else:  # text search
                print(f"Processing text query: {query_text}")
                device = next(model.parameters()).device
                text = clip.tokenize([query_text]).to(device)
                with torch.no_grad():
                    query_embedding = model.encode_text(text)
                    query_embedding = F.normalize(query_embedding.squeeze(0), dim=0).cpu()
                print("Text embedding generated successfully")

            if query_embedding is None:
                raise HTTPException(status_code=400, detail="Failed to generate query embedding")
            
        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

        # Process folder path
        try:
            folder = os.path.abspath(folder)
            if not os.path.exists(folder):
                raise HTTPException(status_code=400, detail=f"Folder not found: {folder}")
            print(f"Searching in folder: {folder}")
        except Exception as e:
            print(f"Error with folder path: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid folder path: {str(e)}")
        
        # Search similar images
        try:
            results = search_similar_images(
                query_embedding,
                folder,
                model,
                preprocess,
                min_score=min_score,
                batch_size=batch_size,
                query_text=query_text if search_type == 'text' else None  # Pass query_text only for text search
            )
            print(f"Found {len(results)} results")
        except Exception as e:
            print(f"Error during image search: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error during search: {str(e)}")

        # Process results
        try:
            processed_results = []
            for result in results:
                with Image.open(result["path"]) as img:
                    width, height = img.size
                    aspect_ratio = height / width
                
                processed_results.append({
                    "path": result["path"],
                    "filename": os.path.basename(result["path"]),
                    "score": result["score"],
                    "description": result["description"],
                    "width": width,
                    "height": height,
                    "aspect_ratio": aspect_ratio
                })
            print("Results processed successfully")
        except Exception as e:
            print(f"Error processing results: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing results: {str(e)}")

        # Save settings
        try:
            save_last_settings(
                query_path if search_type == 'image' else None,
                folder,
                processed_results
            )
        except Exception as e:
            print(f"Error saving settings: {str(e)}")
            # Don't fail the request if settings save fails
            pass

        return JSONResponse({
            "query_path": query_path if search_type == 'image' else None,
            "results": processed_results
        })

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Unexpected error in search endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 