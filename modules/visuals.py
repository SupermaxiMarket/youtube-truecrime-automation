#!/usr/bin/env python3
"""
Module visuels — Génération d'images cinématographiques locales.
Zéro API, zéro téléchargement. Optimisé numpy pour la vitesse.
"""

import os
import re
import random
import math
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont
import yaml


def load_config():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(f"{base}/config.yaml") as f:
        return yaml.safe_load(f)


# ── Thèmes visuels ──
THEMES = {
    "nuit": {
        "colors": [(5, 5, 15), (10, 8, 20), (15, 10, 25), (8, 8, 18)],
        "grain": 0.15, "vignette": 0.6, "blur": 2,
        "brightness": 0.4, "overlay": "none"
    },
    "crime_scene": {
        "colors": [(15, 5, 5), (20, 8, 8), (25, 10, 10), (10, 5, 5)],
        "grain": 0.2, "vignette": 0.7, "blur": 1,
        "brightness": 0.35, "overlay": "rouge"
    },
    "investigation": {
        "colors": [(10, 10, 20), (15, 15, 30), (20, 18, 35), (8, 8, 18)],
        "grain": 0.1, "vignette": 0.5, "blur": 1,
        "brightness": 0.5, "overlay": "none"
    },
    "portrait": {
        "colors": [(20, 15, 15), (30, 20, 20), (40, 25, 25), (15, 10, 10)],
        "grain": 0.08, "vignette": 0.4, "blur": 3,
        "brightness": 0.45, "overlay": "none"
    },
    "justice": {
        "colors": [(10, 10, 15), (18, 15, 22), (25, 20, 30), (12, 10, 18)],
        "grain": 0.05, "vignette": 0.5, "blur": 1,
        "brightness": 0.55, "overlay": "none"
    },
    "evidence": {
        "colors": [(5, 5, 10), (12, 8, 15), (18, 12, 20), (8, 6, 12)],
        "grain": 0.12, "vignette": 0.6, "blur": 1,
        "brightness": 0.5, "overlay": "rouge"
    },
    "conclusion": {
        "colors": [(5, 5, 10), (10, 8, 15), (15, 10, 18), (8, 6, 12)],
        "grain": 0.1, "vignette": 0.5, "blur": 2,
        "brightness": 0.35, "overlay": "none"
    }
}


def detect_theme(image_prompt: str) -> str:
    """Détecte le thème visuel à partir de la description."""
    p = image_prompt.lower()
    
    if any(w in p for w in ["nuit", "sombre", "pluie", "réverbère", "nocturne", "obscur", "lune"]):
        return "nuit"
    if any(w in p for w in ["crime", "ruban", "scène", "meurtre", "corps", "sang", "mort"]):
        return "crime_scene"
    if any(w in p for w in ["enquête", "bureau", "dossier", "commissariat", "policier", "interrogatoire"]):
        return "investigation"
    if any(w in p for w in ["portrait", "photo", "visage", "famille", "album", "identité"]):
        return "portrait"
    if any(w in p for w in ["justice", "tribunal", "audience", "juge", "procès", "palais", "avocat"]):
        return "justice"
    if any(w in p for w in ["preuve", "indice", "empreinte", "lettre", "anonyme", "fil", "tableau", "épingle"]):
        return "evidence"
    if any(w in p for w in ["crépuscule", "fin", "classé", "fermeture", "dossier", "poussière", "cimetière"]):
        return "conclusion"
    
    return "nuit"


def generate_background(width: int, height: int, theme: str, seed: int) -> Image.Image:
    """Génère un fond cinématographique avec numpy (vectorisé)."""
    rng = np.random.default_rng(seed)
    theme_data = THEMES.get(theme, THEMES["nuit"])
    colors = np.array(theme_data["colors"], dtype=np.float64)
    
    # Grille de coordonnées
    y, x = np.mgrid[0:height, 0:width]
    cx, cy = width // 2, height // 3
    dist = np.sqrt((x - cx)**2 + (y - cy)**2)
    max_dist = np.sqrt(cx**2 + cy**2)
    ratio = (dist / max_dist).clip(0, 1)
    
    # Interpolation entre les couleurs (vectorisée)
    n_colors = len(colors)
    idx = (ratio * (n_colors - 1)).astype(int)
    local_ratio = (ratio * (n_colors - 1) - idx)[..., None]
    
    c1 = colors[idx]
    c2_idx = np.minimum(idx + 1, n_colors - 1)
    c2 = colors[c2_idx]
    
    img_array = c1 + (c2 - c1) * local_ratio
    img_array = img_array.astype(np.uint8)
    
    # Dégradé vertical subtil
    v_grad = np.linspace(0, 0.15, height)[:, None, None]
    img_array = (img_array * (1 - v_grad)).astype(np.uint8)
    
    # Grain
    if theme_data["grain"] > 0:
        grain = rng.normal(0, 255 * theme_data["grain"], (height, width, 1))
        img_array = np.clip(img_array + grain, 0, 255).astype(np.uint8)
    
    # Vignette
    if theme_data["vignette"] > 0:
        vig = 1 - (dist / max_dist) * theme_data["vignette"]
        vig = vig[..., None]
        img_array = (img_array * vig).astype(np.uint8)
    
    # Overlay rouge
    if theme_data["overlay"] == "rouge":
        img_array[..., 0] = np.clip(img_array[..., 0] * 1.2, 0, 255).astype(np.uint8)
        img_array[..., 1] = (img_array[..., 1] * 0.8).astype(np.uint8)
        img_array[..., 2] = (img_array[..., 2] * 0.7).astype(np.uint8)
    
    # Brillance
    img_array = (img_array * theme_data["brightness"]).astype(np.uint8)
    
    return Image.fromarray(img_array)


def add_letterbox(img: Image.Image) -> Image.Image:
    """Ajoute des bandes noires (cinémascope)."""
    w, h = img.size
    draw = ImageDraw.Draw(img)
    bar_height = int(h * 0.08)
    draw.rectangle([(0, 0), (w, bar_height)], fill=(0, 0, 0))
    draw.rectangle([(0, h - bar_height), (w, h)], fill=(0, 0, 0))
    return img


def add_text_overlay(img: Image.Image, text: str) -> Image.Image:
    """Ajoute un texte contextuel discret."""
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 34)
    except:
        font = ImageFont.load_default()
    
    draw = ImageDraw.Draw(img)
    w, h = img.size
    text = text[:60]
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    margin = 12
    
    # Fond semi-transparent
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle(
        [(20, h - 62), (20 + tw + margin * 2, h - 16)],
        fill=(0, 0, 0, 160)
    )
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, overlay)
    img = img.convert('RGB')
    
    draw = ImageDraw.Draw(img)
    draw.text((20 + margin, h - 52), text, fill=(210, 210, 210), font=font)
    return img


def extract_image_prompts(script: str) -> list:
    """Extrait les descriptions [IMAGE: ...] du script."""
    prompts = re.findall(r'\[IMAGE:\s*(.*?)\]', script)
    return [p.strip() for p in prompts if p.strip()]


def prepare_visuals(script_path: str, script_text: str = None) -> list:
    """
    Génère toutes les images pour une vidéo.
    Zéro API, zéro téléchargement, numpy vectorisé.
    """
    if script_text is None:
        with open(script_path) as f:
            script_text = f.read()
    
    # Nettoyer les métadonnées
    if "---" in script_text:
        parts = script_text.split("---")
        if len(parts) >= 3:
            clean_script = "---".join(parts[2:])
        else:
            clean_script = parts[1] if len(parts) > 1 else parts[0]
    else:
        clean_script = script_text
    
    prompts = extract_image_prompts(clean_script)
    
    if not prompts:
        prompts = [
            "nuit, crime, silence",
            "enquête, dossier, bureau",
            "portrait, victime, identité",
            "crime scene, ruban, jaune",
            "investigation, police, interrogatoire",
            "evidence, preuve, indice",
            "justice, tribunal, audience",
            "conclusion, fin, classé"
        ]
    
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = f"{base}/output/visuals"
    os.makedirs(output_dir, exist_ok=True)
    
    image_paths = []
    print(f"🎨 Génération de {len(prompts)} visuels cinématographiques...")
    
    for i, prompt in enumerate(prompts):
        theme = detect_theme(prompt)
        seed = abs(hash(prompt)) % 10000
        safe_name = re.sub(r'[^\w\s-]', '', prompt)[:25].strip().replace(' ', '_')
        filename = f"{i:02d}_{theme}_{safe_name}.jpg"
        filepath = f"{output_dir}/{filename}"
        
        # Générer (vectorisé, rapide)
        img = generate_background(1920, 1080, theme, seed)
        
        # Flou
        blur = THEMES.get(theme, THEMES["nuit"])["blur"]
        if blur > 0:
            img = img.filter(ImageFilter.GaussianBlur(radius=blur))
        
        # Letterbox + texte
        img = add_letterbox(img)
        img = add_text_overlay(img, prompt[:50])
        
        img.save(filepath, 'JPEG', quality=92)
        image_paths.append(filepath)
        
        dots = "•" * (i + 1) + " " * (len(prompts) - i - 1)
        print(f"   [{dots}] {theme} - {prompt[:35]}...", end="\r")
    
    print(f"\n   ✓ {len(image_paths)} visuels générés")
    return image_paths


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        paths = prepare_visuals(sys.argv[1])
        for p in paths:
            print(f"  • {p}")
    else:
        print("Usage: python visuals.py <script_file>")