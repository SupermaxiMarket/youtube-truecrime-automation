#!/usr/bin/env python3
"""
Module visuels — Photos réelles + filtres cinématographiques.
Utilise Picsum (gratuit, sans API) + effets dark. Fallback gradients si réseau HS.
"""

import os
import re
import random
import math
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont, ImageOps
import urllib.request
import yaml


def load_config():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(f"{base}/config.yaml") as f:
        return yaml.safe_load(f)


# ── Thèmes visuels (palettes pour fallback) ──
THEMES = {
    "nuit": {"grain": 0.1, "vignette": 0.35, "blur": 0.8, "brightness": 0.75, "contrast": 1.15, "saturation": 0.65},
    "crime_scene": {"grain": 0.15, "vignette": 0.4, "blur": 0.8, "brightness": 0.7, "contrast": 1.2, "saturation": 0.55},
    "investigation": {"grain": 0.08, "vignette": 0.3, "blur": 0.5, "brightness": 0.8, "contrast": 1.1, "saturation": 0.75},
    "portrait": {"grain": 0.06, "vignette": 0.25, "blur": 0.8, "brightness": 0.8, "contrast": 1.05, "saturation": 0.7},
    "justice": {"grain": 0.04, "vignette": 0.3, "blur": 0.5, "brightness": 0.85, "contrast": 1.1, "saturation": 0.85},
    "evidence": {"grain": 0.1, "vignette": 0.35, "blur": 0.5, "brightness": 0.75, "contrast": 1.15, "saturation": 0.6},
    "conclusion": {"grain": 0.08, "vignette": 0.35, "blur": 0.8, "brightness": 0.7, "contrast": 1.1, "saturation": 0.65}
}


def detect_theme(prompt: str) -> str:
    p = prompt.lower()
    if any(w in p for w in ["nuit", "sombre", "pluie", "réverbère", "nocturne", "obscur", "lune"]): return "nuit"
    if any(w in p for w in ["crime", "ruban", "scène", "meurtre", "corps", "sang", "mort"]): return "crime_scene"
    if any(w in p for w in ["enquête", "bureau", "dossier", "commissariat", "policier", "interrogatoire"]): return "investigation"
    if any(w in p for w in ["portrait", "photo", "visage", "famille", "album", "identité"]): return "portrait"
    if any(w in p for w in ["justice", "tribunal", "audience", "juge", "procès", "palais"]): return "justice"
    if any(w in p for w in ["preuve", "indice", "empreinte", "lettre", "anonyme", "fil", "tableau", "épingle"]): return "evidence"
    if any(w in p for w in ["crépuscule", "fin", "classé", "fermeture", "dossier", "poussière", "cimetière"]): return "conclusion"
    return "nuit"


def download_image(prompt: str, output_path: str, seed: int) -> bool:
    """Télécharge une photo depuis Picsum (gratuit, sans clé)."""
    urls = [
        f"https://picsum.photos/seed/{seed}/{1920}/{1080}",
        f"https://picsum.photos/{1920}/{1080}?random={seed}",
    ]
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                with open(output_path, 'wb') as f:
                    f.write(resp.read())
            if os.path.getsize(output_path) > 5000:
                return True
        except:
            continue
    return False


def generate_fallback_background(width: int, height: int, seed: int) -> Image.Image:
    """Génère un fond dégradé si le téléchargement échoue."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:height, 0:width]
    cx, cy = width // 2, height // 3
    dist = np.sqrt((x - cx)**2 + (y - cy)**2)
    max_dist = np.sqrt(cx**2 + cy**2)
    ratio = (dist / max_dist).clip(0, 1)
    
    colors = np.array([[5, 5, 15], [10, 8, 20], [15, 10, 25], [8, 8, 18]], dtype=np.float64)
    idx = (ratio * 3).astype(int)
    local_ratio = (ratio * 3 - idx)[..., None]
    c1 = colors[idx]
    c2 = colors[np.minimum(idx + 1, 3)]
    img_array = (c1 + (c2 - c1) * local_ratio).astype(np.uint8)
    
    grain = rng.normal(0, 30, (height, width, 1))
    img_array = np.clip(img_array + grain, 0, 255).astype(np.uint8)
    return Image.fromarray(img_array)


def apply_cinematic_style(img: Image.Image, theme: str) -> Image.Image:
    """Applique les filtres cinématographiques à une image réelle."""
    style = THEMES.get(theme, THEMES["nuit"])
    
    # Assombrir
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(style["brightness"])
    
    # Contraste
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(style["contrast"])
    
    # Désaturation
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(style["saturation"])
    
    # Flou subtil
    if style["blur"] > 0:
        img = img.filter(ImageFilter.GaussianBlur(radius=style["blur"]))
    
    # Vignette (coins sombres)
    w, h = img.size
    cx, cy = w // 2, h // 2
    max_dist = math.sqrt(cx**2 + cy**2)
    pixels = img.load()
    for y in range(h):
        for x in range(w):
            dist = math.sqrt((x - cx)**2 + (y - cy)**2)
            factor = 1 - (dist / max_dist) * style["vignette"]
            r, g, b = pixels[x, y]
            pixels[x, y] = (int(r * factor), int(g * factor), int(b * factor))
    
    # Letterbox
    draw = ImageDraw.Draw(img)
    bar = int(h * 0.07)
    draw.rectangle([(0, 0), (w, bar)], fill=(0, 0, 0))
    draw.rectangle([(0, h - bar), (w, h)], fill=(0, 0, 0))
    
    return img


def add_text(img: Image.Image, text: str) -> Image.Image:
    """Ajoute un texte contextuel discret."""
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 32)
    except:
        font = ImageFont.load_default()
    
    draw = ImageDraw.Draw(img)
    text = text[:55]
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    h = img.size[1]
    m = 10
    
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle([(20, h - 60), (20 + tw + m*2, h - 16)], fill=(0, 0, 0, 160))
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, overlay)
    img = img.convert('RGB')
    draw = ImageDraw.Draw(img)
    draw.text((20 + m, h - 50), text, fill=(210, 210, 210), font=font)
    return img


def extract_image_prompts(script: str) -> list:
    prompts = re.findall(r'\[IMAGE:\s*(.*?)\]', script)
    return [p.strip() for p in prompts if p.strip()]


def prepare_visuals(script_path: str, script_text: str = None) -> list:
    """Génère les visuels : photos réelles + filtres cinéma. Fallback gradients."""
    if script_text is None:
        with open(script_path) as f:
            script_text = f.read()
    
    if "---" in script_text:
        parts = script_text.split("---")
        clean_script = "---".join(parts[2:]) if len(parts) >= 3 else (parts[1] if len(parts) > 1 else parts[0])
    else:
        clean_script = script_text
    
    prompts = extract_image_prompts(clean_script)
    if not prompts:
        prompts = ["nuit, crime", "enquête", "portrait", "crime scene", "investigation", "preuve", "justice", "fin"]
    
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = f"{base}/output/visuals"
    os.makedirs(output_dir, exist_ok=True)
    
    image_paths = []
    print(f"📷 Téléchargement de {len(prompts)} photos + filtres cinéma...")
    
    for i, prompt in enumerate(prompts):
        theme = detect_theme(prompt)
        seed = abs(hash(prompt + str(i))) % 100000
        safe_name = re.sub(r'[^\w\s-]', '', prompt)[:25].strip().replace(' ', '_')
        filepath = f"{output_dir}/{i:02d}_{theme}_{safe_name}.jpg"
        
        if os.path.exists(filepath) and os.path.getsize(filepath) > 5000:
            img = Image.open(filepath).convert("RGB")
        else:
            # Télécharger une photo réelle
            ok = download_image(prompt, filepath, seed)
            if ok:
                img = Image.open(filepath).convert("RGB")
                img = img.resize((1920, 1080), Image.LANCZOS)
            else:
                # Fallback gradient
                img = generate_fallback_background(1920, 1080, seed)
        
        # Appliquer le style cinématographique
        img = apply_cinematic_style(img, theme)
        img = add_text(img, prompt[:50])
        img.save(filepath, 'JPEG', quality=92)
        image_paths.append(filepath)
        
        status = "📷" if os.path.getsize(filepath) > 50000 else "🎨"
        dots = "•" * (i + 1) + " " * (len(prompts) - i - 1)
        print(f"   [{dots}] {status} {theme} - {prompt[:35]}...", end="\r")
    
    print(f"\n   ✓ {len(image_paths)} visuels prêts")
    return image_paths


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        paths = prepare_visuals(sys.argv[1])
        for p in paths:
            print(f"  • {p}")
    else:
        print("Usage: python visuals.py <script_file>")