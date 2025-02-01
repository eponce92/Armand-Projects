import os
import torch
import clip
from PIL import Image
import torch.nn.functional as F
from pathlib import Path
from typing import List, Dict, Union
import numpy as np

# Global cache for image embeddings
cache = {}


def load_model():
    """Load CLIP model and return model and preprocess function"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)
    model.eval()  # Set to evaluation mode
    return model, preprocess


def get_image_embedding(image_path: str, model: torch.nn.Module, preprocess) -> torch.Tensor:
    """Compute embedding for a single image with error handling"""
    try:
        device = next(model.parameters()).device
        image = Image.open(image_path).convert("RGB")
        image_input = preprocess(image).unsqueeze(0).to(device)
        
        with torch.no_grad():
            embedding = model.encode_image(image_input)
            
        return F.normalize(embedding.squeeze(0).cpu(), dim=0)
    except Exception as e:
        print(f"Error processing image {image_path}: {str(e)}")
        return None


def get_cached_embedding(image_path: str, model: torch.nn.Module, preprocess) -> Union[torch.Tensor, None]:
    """Return cached embedding if available, else compute and cache it"""
    try:
        mod_time = os.path.getmtime(image_path)
        key = (image_path, mod_time)
        
        if key in cache:
            return cache[key]
            
        embedding = get_image_embedding(image_path, model, preprocess)
        if embedding is not None:
            cache[key] = embedding
        return embedding
    except Exception as e:
        print(f"Error with cache for {image_path}: {str(e)}")
        return None


def process_image_batch(image_paths: List[str], model: torch.nn.Module, preprocess) -> List[Dict]:
    """Process a batch of images and return their embeddings"""
    batch_embeddings = []
    valid_paths = []
    
    for path in image_paths:
        embedding = get_cached_embedding(path, model, preprocess)
        if embedding is not None:
            batch_embeddings.append(embedding)
            valid_paths.append(path)
    
    return valid_paths, torch.stack(batch_embeddings) if batch_embeddings else None


def search_similar_images(
    query_embedding: torch.Tensor,
    folder: str,
    model: torch.nn.Module,
    preprocess,
    min_score: float = 0.0,
    batch_size: int = 32
) -> List[Dict]:
    """Search for similar images in folder and return results sorted by cosine similarity"""
    # Ensure query_embedding is normalized
    query_embedding = F.normalize(query_embedding, dim=0)
    
    # Gather image files
    image_files = []
    for ext in ['.jpg', '.jpeg', '.png', '.gif']:
        image_files.extend([str(f) for f in Path(folder).glob(f'**/*{ext}')])
    
    results = []
    
    # Process images in batches
    for i in range(0, len(image_files), batch_size):
        batch_files = image_files[i:i+batch_size]
        valid_paths, batch_embeddings = process_image_batch(batch_files, model, preprocess)
        
        if batch_embeddings is not None:
            # Calculate similarities
            similarities = F.cosine_similarity(query_embedding.unsqueeze(0), batch_embeddings)
            
            # Add results above minimum score
            for path, similarity in zip(valid_paths, similarities):
                score = similarity.item()
                if score >= min_score:
                    results.append({"path": path, "score": score})
    
    # Sort results by similarity (descending)
    results.sort(key=lambda x: x["score"], reverse=True)
    return results 