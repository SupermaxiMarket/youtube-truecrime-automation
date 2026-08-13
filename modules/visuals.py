#!/usr/bin/env python3
"""
Module visuels — Télécharge et prépare les images pour la vidéo.
Utilise Unsplash/Pexels (gratuit) + filtres cinématographiques.
"""

import json
import os
import re
import subprocess
import urllib.request
import urllib.parse
from PIL import Image, ImageFilter, ImageEnhance
import yaml


def load_config():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(f"{base}/config.yaml") as f:
        return yaml.safe_load(f)


def extract_image_prompts(script: str) -> list:
    """Extrait les descriptions [IMAGE: ...] du script."""
    prompts = re.findall(r'\[IMAGE:\s*(.*?)\]', script)
    return [p.strip() for p in prompts if p.strip()]


def download_unsplash_image(query: str, output_path: str, 
                            width: int = 1920, height: int = 1080) -> str:
    """
    Télécharge une image depuis Unsplash.
    Gratuit, sans compte pour usage basique.
    """
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return output_path

    # Construire l'URL de recherche
    params = urllib.parse.urlencode({
        'query': query,
        'orientation': 'landscape',
        'content_filter': 'high',
    })
    
    # Utiliser les images aléatoires d'Unsplash via Source
    # Fallback: Lorem Picsum (always available, no API key)
    urls = [
        f"https://picsum.photos/{width}/{height}?random={abs(hash(query)) % 1000}",
        f"https://picsum.photos/seed/{urllib.parse.quote(query)}/{width}/{height}",
    ]
    
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; YouTubeBot/1.0)'
            })
            with urllib.request.urlopen(req, timeout=15) as response:
                with open(output_path, 'wb') as f:
                    f.write(response.read())
            
            if os.path.getsize(output_path) > 1000:
                return output_path
        except Exception as e:
            print(f"   ⚠️  Failed to download from {url}: {e}")
            continue
    
    # Si tout échoue, créer une image par défaut
    return _create_fallback_image(output_path, width, height, query)


def _create_fallback_image(output_path: str, width: int, height: int, 
                           text: str = "") -> str:
    """Crée une image de fond sombre si le téléchargement échoue."""
    img = Image.new('RGB', (width, height), (10, 10, 20))
    # Ajouter un dégradé subtil
    for y in range(height):
        factor = y / height
        r = int(10 + factor * 20)
        g = int(10 + factor * 15)
        b = int(20 + factor * 10)
        for x in range(width):
            img.putpixel((x, y), (r, g, b))
    
    img.save(output_path, 'JPEG', quality=85)
    return output_path


def apply_cinematic_filter(image_path: str, style: str = "dark_cinematic") -> str:
    """Applique un filtre cinématographique dark à l'image."""
    img = Image.open(image_path)
    
    if style == "dark_cinematic":
        # Assombrir
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(0.6)
        # Baisser saturation
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(0.7)
        # Augmenter contraste
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.3)
        # Léger flou pour effet cinéma
        img = img.filter(ImageFilter.GaussianBlur(radius=1))
        # Ajouter une bande noire haut/bas (letterbox)
        w, h = img.size
        if h > 20:
            for y in range(20):
                for x in range(w):
                    img.putpixel((x, y), (0, 0, 0))
                    img.putpixel((x, h-1-y), (0, 0, 0))
    
    # S'assurer que la résolution est correcte
    img = img.resize((1920, 1080), Image.LANCZOS)
    
    # Écraser l'original
    img.save(image_path, 'JPEG', quality=90)
    return image_path


def prepare_visuals(script_path: str, script_text: str = None) -> list:
    """
    Prépare toutes les images pour une vidéo à partir du script.
    Retourne la liste des chemins d'images.
    """
    if script_text is None:
        with open(script_path) as f:
            script_text = f.read()
    
    config = load_config()
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = f"{base}/output/visuals"
    
    prompts = extract_image_prompts(script_text)
    if not prompts:
        # Ajouter des prompts par défaut
        prompts = [
            "crime scene dark night",
            "police investigation",
            "mysterious figure shadow",
            "abandoned building",
            "evidence board",
            "courtroom justice",
            "dark alleyway",
            "newspaper headline crime"
        ]
    
    image_paths = []
    print(f"🖼️  Préparation de {len(prompts)} visuels...")
    
    for prompt in prompts:
        safe_name = re.sub(r'[^\w\s-]', '', prompt)[:30].strip()
        safe_name = safe_name.replace(' ', '_')
        filename = f"{safe_name}_{os.urandom(4).hex()}.jpg"
        filepath = f"{output_dir}/{filename}"
        
        print(f"   → {prompt[:50]}...")
        download_unsplash_image(prompt, filepath)
        apply_cinematic_filter(filepath, config["visuals"]["style"])
        image_paths.append(filepath)
    
    print(f"   ✓ {len(image_paths)} visuels prêts")
    return image_paths


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        paths = prepare_visuals(sys.argv[1])
        for p in paths:
            print(f"  • {p}")
    else:
        print("Usage: python visuals.py <script_file>")