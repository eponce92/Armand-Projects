from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
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
from .clip_utils import (
    load_model,
    get_image_embedding,
    process_image_batch,
    tokenize_search_query,
    async_get_token_similarities
)
import uuid
from collections import defaultdict

app = FastAPI()

# Store search progress
search_progress = defaultdict(dict)

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

async def search_progress_generator(search_id: str):
    """Generate SSE events for search progress"""
    while True:
        if search_id in search_progress:
            progress = search_progress[search_id]
            if 'error' in progress:
                yield f"data: {json.dumps({'type': 'error', 'message': progress['error']})}\n\n"
                break
            elif 'done' in progress:
                yield f"data: {json.dumps({'type': 'complete', 'results': progress['results']})}\n\n"
                break
            else:
                yield f"data: {json.dumps({'type': 'progress', **progress})}\n\n"
        await asyncio.sleep(0.1)  # Check progress every 100ms

@app.get("/search-progress/{search_id}")
async def get_search_progress(search_id: str):
    """SSE endpoint for search progress updates"""
    return StreamingResponse(
        search_progress_generator(search_id),
        media_type="text/event-stream"
    )

async def process_search(
    search_id: str,
    folder: str,
    query_embedding: torch.Tensor,
    model,
    preprocess,
    min_score: float,
    batch_size: int,
    search_type: str,
    query_text: str = None,
    device = None
):
    """Asynchronous function to process search request"""
    try:
        results = []
        supported_formats = {'.jpg', '.jpeg', '.png', '.gif'}
        
        # Get total number of images first
        search_progress[search_id].update({'progress': 20, 'status': 'Scanning folder...'})
        image_files = []
        for root, _, files in os.walk(folder):
            image_files.extend([
                os.path.join(root, f) for f in files
                if os.path.splitext(f)[1].lower() in supported_formats
            ])
        
        total_images = len(image_files)
        processed_images = 0
        
        # Process images in batches
        for i in range(0, len(image_files), batch_size):
            batch_paths = image_files[i:i + batch_size]
            
            # Process batch concurrently
            valid_paths, batch_embeddings = await process_image_batch(batch_paths, model, preprocess)
            
            # Update progress after each batch
            processed_images += len(batch_paths)
            progress = int(30 + (processed_images / total_images * 60))
            search_progress[search_id].update({
                'progress': progress,
                'status': f'Processing images... ({processed_images}/{total_images})',
                'processed': processed_images,
                'total': total_images
            })
            
            if batch_embeddings is not None:
                # Calculate similarities for the batch
                similarities = F.cosine_similarity(batch_embeddings, query_embedding.unsqueeze(0))
                
                # Process results
                for path, similarity, img_embedding in zip(valid_paths, similarities, batch_embeddings):
                    score = (similarity.item() + 1) / 2
                    
                    if score >= min_score:
                        token_scores = []
                        description = ""
                        
                        if search_type == 'text':
                            # Get individual token similarities concurrently
                            tokens = tokenize_search_query(query_text)
                            token_similarities = await async_get_token_similarities(
                                img_embedding,
                                tokens,
                                model,
                                device
                            )
                            
                            description = ", ".join([f"{token} ({score:.1%})" for token, score in token_similarities])
                            token_scores = [score for _, score in token_similarities]
                            
                            if token_scores:
                                final_score = (score + sum(token_scores) / len(token_scores)) / 2
                            else:
                                final_score = score
                        else:
                            final_score = score
                            description = "Processing..."
                        
                        with Image.open(path) as img:
                            width, height = img.size
                            aspect_ratio = height / width
                        
                        results.append({
                            "path": path,
                            "filename": os.path.basename(path),
                            "score": final_score,
                            "description": description,
                            "width": width,
                            "height": height,
                            "aspect_ratio": aspect_ratio
                        })
        
        # Sort results by similarity score
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # Update progress with completion
        search_progress[search_id].update({
            'progress': 100,
            'status': 'Search complete!',
            'done': True,
            'results': results
        })
        
        # Save settings
        save_last_settings(
            None if search_type == 'text' else query_path,
            folder,
            results
        )
        
    except Exception as e:
        print(f"Error in background search task: {str(e)}")
        search_progress[search_id]['error'] = f"Error during search: {str(e)}"

@app.post("/search")
async def search_images(
    background_tasks: BackgroundTasks,
    folder: str = Form(...),
    min_score: float = Form(0.0),
    batch_size: int = Form(32),
    search_type: str = Form(...),
    query_path: str = Form(None),
    query_text: str = Form(None)
):
    search_id = str(uuid.uuid4())
    search_progress[search_id] = {'progress': 0, 'status': 'Initializing search...'}
    
    try:
        print(f"Search request - Type: {search_type}, Folder: {folder}")
        
        if search_type not in ['image', 'text']:
            raise HTTPException(status_code=400, detail="Invalid search type")
        
        if search_type == 'image' and not query_path:
            raise HTTPException(status_code=400, detail="Query image path is required for image search")
        
        if search_type == 'text' and not query_text:
            raise HTTPException(status_code=400, detail="Query text is required for text search")

        # Get query embedding
        search_progress[search_id].update({'progress': 10, 'status': 'Processing query...'})
        try:
            device = next(model.parameters()).device
            if search_type == 'image':
                query_embedding = get_image_embedding(query_path, model, preprocess)
            else:  # text search
                print(f"Processing text query: {query_text}")
                text = clip.tokenize([query_text]).to(device)
                with torch.no_grad():
                    query_embedding = model.encode_text(text)
                    query_embedding = F.normalize(query_embedding.squeeze(0), dim=0).cpu()
                print("Text embedding generated successfully")

            if query_embedding is None:
                raise HTTPException(status_code=400, detail="Failed to generate query embedding")
            
        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            search_progress[search_id]['error'] = f"Error processing query: {str(e)}"
            raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

        # Process folder path
        try:
            folder = os.path.abspath(folder)
            if not os.path.exists(folder):
                raise HTTPException(status_code=400, detail=f"Folder not found: {folder}")
            print(f"Searching in folder: {folder}")
        except Exception as e:
            print(f"Error with folder path: {str(e)}")
            search_progress[search_id]['error'] = f"Invalid folder path: {str(e)}"
            raise HTTPException(status_code=400, detail=f"Invalid folder path: {str(e)}")
        
        # Start background processing
        background_tasks.add_task(
            process_search,
            search_id=search_id,
            folder=folder,
            query_embedding=query_embedding,
            model=model,
            preprocess=preprocess,
            min_score=min_score,
            batch_size=batch_size,
            search_type=search_type,
            query_text=query_text,
            device=device
        )
        
        return {"search_id": search_id}
        
    except HTTPException as he:
        search_progress[search_id]['error'] = str(he.detail)
        raise he
    except Exception as e:
        print(f"Unexpected error in search endpoint: {str(e)}")
        search_progress[search_id]['error'] = f"Unexpected error: {str(e)}"
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        # Clean up progress after 5 minutes
        asyncio.create_task(cleanup_progress(search_id))

async def cleanup_progress(search_id: str):
    """Remove search progress after a delay"""
    await asyncio.sleep(300)  # 5 minutes
    if search_id in search_progress:
        del search_progress[search_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 