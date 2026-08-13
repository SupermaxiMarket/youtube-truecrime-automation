#!/usr/bin/env python3
"""
Module miniature — Génère des thumbnails YouTube accrocheuses.
Style : dark, cinématographique, texte contrasté.
"""

import os
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter


def create_thumbnail(title: str, image_path: str = None,
                     output_path: str = None) -> str:
    """
    Crée une miniature YouTube (1280x720) style true crime.
    
    Style : fond sombre, sujet central désaturé, titre rouge/blanc,
    effet cinéma, bande noire haut/bas (letterbox).
    """
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    if not output_path:
        output_path = f"{base}/output/thumbnails/thumb_{os.urandom(4).hex()}.jpg"
    
    # Dimensions YouTube
    w, h = 1280, 720
    
    # 1. Créer le fond
    if image_path and os.path.exists(image_path):
        img = Image.open(image_path).convert("RGB")
        img = img.resize((w, h), Image.LANCZOS)
        # Assombrir fortement
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(0.3)
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(0.5)
        # Flou
        img = img.filter(ImageFilter.GaussianBlur(radius=3))
    else:
        # Fond par défaut : dégradé sombre
        img = Image.new('RGB', (w, h), (8, 8, 16))
        draw = ImageDraw.Draw(img)
        for y in range(h):
            factor = y / h
            r = int(8 + factor * 15)
            g = int(8 + factor * 10)
            b = int(16 + factor * 15)
            draw.rectangle([(0, y), (w, y+1)], fill=(r, g, b))
    
    draw = ImageDraw.Draw(img)
    
    # 2. Bandes noires (letterbox style)
    draw.rectangle([(0, 0), (w, 40)], fill=(0, 0, 0))
    draw.rectangle([(0, h-40), (w, h)], fill=(0, 0, 0))
    
    # 3. Bordure fine rouge en haut
    draw.rectangle([(0, 38), (w, 42)], fill=(180, 20, 20))
    
    # 4. Texte principal
    # Découper le titre en lignes (max ~25 caractères par ligne)
    words = title.split()
    lines = []
    current = ""
    for word in words:
        if len(current + " " + word) <= 28:
            current += " " + word if current else word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    
    # Police (essayer plusieurs chemins)
    font_paths = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ]
    
    font = None
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, 52)
                break
            except:
                continue
    
    if not font:
        font = ImageFont.load_default()
    
    # Dessiner chaque ligne centrée
    y_pos = 280
    for i, line in enumerate(lines[:4]):  # max 4 lignes
        # Ombre portée
        shadow_color = (0, 0, 0)
        
        # Calculer la taille du texte
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x_pos = (w - text_w) // 2
        
        # Ombre
        draw.text((x_pos+3, y_pos+3), line, fill=shadow_color, font=font)
        
        # Texte principal (blanc)
        draw.text((x_pos, y_pos), line, fill=(255, 255, 255), font=font)
        
        y_pos += 62
    
    # 5. Barre rouge en bas du texte
    draw.rectangle([(w//2 - 60, y_pos + 10), (w//2 + 60, y_pos + 14)], fill=(180, 20, 20))
    
    # 6. Petit texte "CRIMES & TÉNÈBRES" en bas
    try:
        small_font = ImageFont.truetype(font_paths[0], 18)
    except:
        small_font = ImageFont.load_default()
    
    watermark = "CRIMES & TÉNÈBRES"
    bbox = draw.textbbox((0, 0), watermark, font=small_font)
    tw = bbox[2] - bbox[0]
    draw.text(((w - tw) // 2, h - 100), watermark, fill=(180, 20, 20, 200), font=small_font)
    
    # Sauvegarder
    img.save(output_path, 'JPEG', quality=92)
    
    print(f"🖼️  Miniature créée : {output_path}")
    return output_path


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        title = sys.argv[1]
        img = sys.argv[2] if len(sys.argv) > 2 else None
        path = create_thumbnail(title, img)
        print(f"✔ Miniature : {path}")
    else:
        print("Usage: python thumbnail.py \"Titre de la vidéo\" [image.jpg]")