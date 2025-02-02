import os
import torch
import clip
from PIL import Image
import torch.nn.functional as F
from pathlib import Path
from typing import List, Dict, Union, Tuple
import numpy as np
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Global cache for image embeddings
cache = {}

# Global thread pool executor for image processing
thread_pool = ThreadPoolExecutor(max_workers=4)  # Adjust based on your CPU cores


def load_model():
    """Load CLIP model and return model and preprocess function"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)
    model.eval()  # Set to evaluation mode
    return model, preprocess


def analyze_image_content(image_path: str, model: torch.nn.Module, preprocess) -> str:
    """Analyze image content using CLIP"""
    try:
        device = next(model.parameters()).device
        image = Image.open(image_path).convert("RGB")
        image_input = preprocess(image).unsqueeze(0).to(device)
        
        # Categories for image analysis
        categories = [
            "a photograph", "digital art", "a painting", "a sketch",
            "landscape photo", "portrait photo", "abstract art", "still life",
            "black and white", "colorful", "high contrast", "soft lighting",
            "nature scene", "urban scene", "indoor scene", "outdoor scene",
            "close-up shot", "wide angle shot", "aerial view", "macro photography",
            "night scene", "daylight scene", "sunset scene", "sunrise scene",
            "architecture", "people", "animals", "plants",
            "water", "mountains", "sky", "buildings",
            "vintage style", "modern style", "minimalist", "detailed",
            "texture", "pattern", "symmetrical", "asymmetrical"
        ]
        
        text = clip.tokenize(categories).to(device)
        
        with torch.no_grad():
            image_features = model.encode_image(image_input)
            text_features = model.encode_text(text)
            
            # Calculate similarities
            similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
            
            # Get top 5 matches
            values, indices = similarity[0].topk(5)
            
            # Create description
            descriptions = [categories[idx] for idx in indices]
            scores = [float(val) for val in values]
            
            # Format top matches with confidence scores
            formatted_desc = [f"{desc} ({score:.1f}%)" for desc, score in zip(descriptions, scores)]
            return ", ".join(formatted_desc)
            
    except Exception as e:
        print(f"Error analyzing image {image_path}: {str(e)}")
        return "unknown content"


def get_image_embedding(image_path: str, model: torch.nn.Module, preprocess) -> Union[torch.Tensor, None]:
    """Get embedding for a single image"""
    try:
        image = Image.open(image_path).convert('RGB')
        image_input = preprocess(image).unsqueeze(0).to(next(model.parameters()).device)
        with torch.no_grad():
            image_features = model.encode_image(image_input)
            image_features = F.normalize(image_features.squeeze(0), dim=0)
        return image_features.cpu()
    except Exception as e:
        print(f"Error processing image {image_path}: {str(e)}")
        return None


async def async_get_image_embedding(image_path: str, model: torch.nn.Module, preprocess) -> Union[torch.Tensor, None]:
    """Asynchronous wrapper for get_image_embedding"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        thread_pool,
        get_image_embedding,
        image_path,
        model,
        preprocess
    )


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


async def process_image_batch(batch_paths: List[str], model: torch.nn.Module, preprocess) -> Tuple[List[str], torch.Tensor]:
    """Process a batch of images concurrently"""
    # Create tasks for all images in the batch
    embedding_tasks = [
        async_get_image_embedding(path, model, preprocess)
        for path in batch_paths
    ]
    
    # Process all embeddings concurrently
    embeddings = await asyncio.gather(*embedding_tasks)
    
    # Filter out failed embeddings and keep track of valid paths
    valid_embeddings = []
    valid_paths = []
    
    for path, embedding in zip(batch_paths, embeddings):
        if embedding is not None:
            valid_embeddings.append(embedding)
            valid_paths.append(path)
    
    if not valid_embeddings:
        return [], None
    
    # Stack valid embeddings
    return valid_paths, torch.stack(valid_embeddings)


def tokenize_search_query(query: str) -> List[str]:
    """
    Tokenize the search query into meaningful words
    Remove common stop words and special characters
    """
    # Basic stop words list - can be expanded
    stop_words = {'a', 'an', 'the', 'of', 'in', 'on', 'at', 'for', 'to', 'with'}
    
    # Convert to lowercase and split
    words = query.lower().split()
    
    # Remove stop words and clean tokens
    tokens = []
    for word in words:
        # Clean the word of special characters
        word = re.sub(r'[^\w\s]', '', word)
        if word and word not in stop_words:
            tokens.append(word)
    
    return tokens


def get_token_similarities(image_embedding: torch.Tensor, tokens: List[str], model) -> List[Tuple[str, float]]:
    """
    Calculate similarity scores between image embedding and each token
    Returns list of (token, similarity_score) tuples
    """
    device = next(model.parameters()).device
    similarities = []
    
    for token in tokens:
        # Tokenize and encode the text
        text = clip.tokenize([token]).to(device)
        with torch.no_grad():
            text_features = model.encode_text(text)
            text_features = F.normalize(text_features.squeeze(0), dim=0)
        
        # Calculate similarity
        similarity = torch.dot(image_embedding.to(device), text_features.to(device))
        similarity_score = (similarity.item() + 1) / 2  # Normalize to 0-1 range
        similarities.append((token, similarity_score))
    
    # Sort by similarity score in descending order
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities


async def async_get_token_similarities(
    image_embedding: torch.Tensor,
    tokens: List[str],
    model: torch.nn.Module,
    device
) -> List[Tuple[str, float]]:
    """Asynchronous function to get token similarities"""
    similarities = []
    
    # Process tokens in parallel
    async def process_token(token: str) -> Tuple[str, float]:
        text = clip.tokenize([token]).to(device)
        with torch.no_grad():
            text_features = model.encode_text(text)
            text_features = F.normalize(text_features.squeeze(0), dim=0)
            similarity = torch.dot(image_embedding.to(device), text_features.to(device))
            similarity_score = (similarity.item() + 1) / 2
        return token, similarity_score
    
    # Create tasks for all tokens
    similarity_tasks = [process_token(token) for token in tokens]
    
    # Process all similarities concurrently
    similarities = await asyncio.gather(*similarity_tasks)
    
    # Sort by similarity score in descending order
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities


def search_similar_images(query_embedding: torch.Tensor, folder_path: str, model, preprocess, min_score: float = 0.0, batch_size: int = 32, query_text: str = None) -> List[Dict]:
    """Search for similar images in the folder"""
    results = []
    supported_formats = {'.jpg', '.jpeg', '.png', '.gif'}
    
    # Get query tokens if text query is provided
    query_tokens = tokenize_search_query(query_text) if query_text else []

    for root, _, files in os.walk(folder_path):
        image_paths = [
            os.path.join(root, f) for f in files
            if os.path.splitext(f)[1].lower() in supported_formats
        ]
        
        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i:i + batch_size]
            batch_embeddings = []
            valid_paths = []
            
            for img_path in batch_paths:
                embedding = get_image_embedding(img_path, model, preprocess)
                if embedding is not None:
                    batch_embeddings.append(embedding)
                    valid_paths.append(img_path)
            
            if not batch_embeddings:
                continue
                
            # Stack embeddings and calculate similarities
            batch_embeddings = torch.stack(batch_embeddings)
            similarities = F.cosine_similarity(batch_embeddings, query_embedding.unsqueeze(0))
            
            # Process results
            for path, similarity in zip(valid_paths, similarities):
                score = (similarity.item() + 1) / 2  # Normalize to 0-1 range
                
                if score >= min_score:
                    # Get token-based description if query text is provided
                    if query_tokens:
                        token_similarities = get_token_similarities(batch_embeddings[valid_paths.index(path)], query_tokens, model)
                        description = ", ".join([f"{token} ({score:.1%})" for token, score in token_similarities])
                    else:
                        # Fallback to basic description
                        description = "a photograph (1.0%), a sketch (0.0%), digital art (0.0%), landscape photo (0.0%), a painting (0.0%)"
                    
                    results.append({
                        "path": path,
                        "score": score,
                        "description": description
                    })
    
    # Sort results by similarity score
    results.sort(key=lambda x: x["score"], reverse=True)
    return results 