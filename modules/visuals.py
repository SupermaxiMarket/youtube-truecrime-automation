#!/usr/bin/env python3
"""
Module visuels — Télécharge de VRAIS clips vidéo depuis Pexels (gratuit).
Besoin d'une clé API Pexels (gratuite, 2min sur pexels.com/api).
"""

import json
import os
import re
import subprocess
import urllib.request
import urllib.parse
import yaml


# ── Mots-clés vidéo par thème ──
VIDEO_KEYWORDS = {
    "nuit": ["night city", "dark street", "night atmosphere", "rain night", "nocturnal"],
    "crime_scene": ["police lights", "crime scene", "emergency", "dark forest", "mystery"],
    "investigation": ["detective", "police station", "investigation", "office night", "documents"],
    "portrait": ["person silhouette", "mysterious person", "dark portrait", "face shadow"],
    "justice": ["courthouse", "justice", "courtroom", "lawyer", "judge"],
    "evidence": ["documents", "evidence", "magnifying glass", "fingerprint", "clues"],
    "conclusion": ["sunset", "dusk", "abandoned", "silence", "reflection"]
}


def load_config():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(f"{base}/config.yaml") as f:
        return yaml.safe_load(f)


def get_api_key():
    """Récupère la clé Pexels depuis .env ou variable d'environnement."""
    import os
    key = os.environ.get("PEXELS_API_KEY", "")
    if not key:
        # Chercher dans .env
        env_paths = ["/root/.hermes/.env", "/root/.env", "/root/projets/youtube-automation/.env"]
        for env_path in env_paths:
            if os.path.exists(env_path):
                with open(env_path) as f:
                    for line in f:
                        if line.startswith("PEXELS_API_KEY=") and not line.strip().startswith("#"):
                            key = line.strip().split("=", 1)[1].strip().strip("'\"")
                            return key
    return key


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


def search_pexels_video(query: str, api_key: str) -> list:
    """Cherche des clips vidéo sur Pexels."""
    params = urllib.parse.urlencode({
        "query": query,
        "per_page": 15,
        "orientation": "landscape",
        "size": "medium"
    })
    url = f"https://api.pexels.com/videos/search?{params}"
    
    req = urllib.request.Request(url, headers={
        "Authorization": api_key,
        "User-Agent": "Mozilla/5.0"
    })
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data.get("videos", [])
    except Exception as e:
        print(f"   ⚠️  Pexels search error: {e}")
        return []


def download_pexels_clip(pexels_video: dict, output_path: str) -> str:
    """Télécharge le clip en 720p (bon équilibre qualité/taille)."""
    # Priorité : 1280x720 HD > 1920x1080 > 960x540 > 640x360
    # Éviter le 4K (trop lourd)
    preferred = [
        (1280, 720),   # 720p HD - idéal
        (1920, 1080),  # 1080p - acceptable
        (960, 540),    # 540p - fallback
        (640, 360),    # 360p - dernier recours
    ]
    
    best = None
    for pw, ph in preferred:
        for vf in pexels_video.get("video_files", []):
            if vf.get("width") == pw and vf.get("height") == ph:
                best = vf
                break
        if best:
            break
    
    # Fallback : max 1080p
    if not best:
        for vf in pexels_video.get("video_files", []):
            w = vf.get("width", 0)
            if w <= 1920 and (not best or w > best.get("width", 0)):
                best = vf
    
    if not best:
        return None
    
    link = best.get("link")
    if not link:
        return None
    
    try:
        req = urllib.request.Request(link, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(output_path, "wb") as f:
                f.write(resp.read())
        
        if os.path.getsize(output_path) > 10000:
            return output_path
    except Exception as e:
        print(f"   ⚠️  Download failed: {e}")
    
    return None


def get_video_duration(video_path: str) -> float:
    """Récupère la durée d'un clip vidéo."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    try:
        return float(json.loads(result.stdout)["format"]["duration"])
    except:
        return 0.0


def extract_image_prompts(script: str) -> list:
    prompts = re.findall(r'\[IMAGE:\s*(.*?)\]', script)
    return [p.strip() for p in prompts if p.strip()]


def prepare_visuals(script_path: str, script_text: str = None) -> list:
    """
    Télécharge de vrais clips vidéo depuis Pexels pour chaque scène.
    """
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError(
            "❌ PEXELS_API_KEY manquante !\n\n"
            "Va sur https://www.pexels.com/api/ → Join Free → inscris-toi → reçois ta clé\n"
            "Puis ajoute-la dans /root/projets/youtube-automation/.env :\n"
            "  PEXELS_API_KEY=ta_clé_ici"
        )
    
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
        prompts = ["night city", "investigation", "mysterious person", "crime", "police", "evidence", "justice", "conclusion"]
    
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = f"{base}/output/visuals"
    os.makedirs(output_dir, exist_ok=True)
    
    clip_paths = []
    print(f"🎬 Téléchargement de {len(prompts)} clips vidéo Pexels...")
    
    for i, prompt in enumerate(prompts):
        theme = detect_theme(prompt)
        safe_name = re.sub(r'[^\w\s-]', '', prompt)[:25].strip().replace(' ', '_')
        filepath = f"{output_dir}/{i:02d}_{theme}_{safe_name}.mp4"
        
        # Si déjà téléchargé et valide, réutiliser
        if os.path.exists(filepath) and os.path.getsize(filepath) > 10000:
            clip_paths.append(filepath)
            dots = "•" * (i + 1) + " " * (len(prompts) - i - 1)
            print(f"   [{dots}] ♻️  {theme} - {prompt[:35]}... (cache)", end="\r")
            continue
        
        # Chercher un clip sur Pexels
        keywords = VIDEO_KEYWORDS.get(theme, ["mystery", "dark"])
        query = keywords[i % len(keywords)] if keywords else prompt
        
        videos = search_pexels_video(query, api_key)
        
        downloaded = None
        for video in videos:
            downloaded = download_pexels_clip(video, filepath)
            if downloaded:
                break
        
        if downloaded:
            clip_paths.append(filepath)
            status = "🎬"
        else:
            # Fallback : image statique transformée en clip (fondu)
            fallback_path = filepath.replace(".mp4", "_fallback.mp4")
            _create_fallback_clip(fallback_path, theme, i)
            clip_paths.append(fallback_path)
            status = "🎨"
        
        dots = "•" * (i + 1) + " " * (len(prompts) - i - 1)
        print(f"   [{dots}] {status} {theme} - {prompt[:35]}...", end="\r")
    
    print(f"\n   ✓ {len(clip_paths)} clips vidéo prêts")
    return clip_paths


def _create_fallback_clip(output_path: str, theme: str, seed: int):
    """Crée un clip de fallback avec un dégradé animé (léger mouvement)."""
    import numpy as np
    from PIL import Image
    
    colors = {
        "nuit": [(5, 5, 15), (10, 8, 20)],
        "crime_scene": [(15, 5, 5), (20, 8, 8)],
        "investigation": [(10, 10, 20), (15, 15, 30)],
        "justice": [(10, 10, 15), (18, 15, 22)],
        "evidence": [(5, 5, 10), (12, 8, 15)],
    }.get(theme, [(5, 5, 15), (10, 8, 20)])
    
    # Générer 30 frames d'un dégradé qui pulse doucement
    frames_dir = "/tmp/fallback_frames"
    os.makedirs(frames_dir, exist_ok=True)
    
    w, h = 1920, 1080
    rng = np.random.default_rng(seed)
    
    for frame in range(30):
        img = Image.new('RGB', (w, h), colors[0])
        draw = ImageDraw = __import__('PIL').ImageDraw.Draw(img)
        
        # Vague lente
        offset = (frame / 30) * 50
        for y in range(h):
            factor = (y + offset) / (h + 50)
            idx = min(int(factor * len(colors)), len(colors) - 1)
            c = colors[idx]
            draw.line([(0, y), (w, y)], fill=c)
        
        # Grain
        grain = rng.normal(0, 20, (h, w, 3)).astype(np.uint8)
        img_arr = np.array(img).astype(np.int16)
        img_arr = np.clip(img_arr + grain[:,:,0:1], 0, 255).astype(np.uint8)
        Image.fromarray(img_arr).save(f"{frames_dir}/{frame:04d}.png")
    
    # Assembler les frames en vidéo
    subprocess.run([
        "ffmpeg", "-y", "-v", "quiet",
        "-framerate", "30",
        "-i", f"{frames_dir}/%04d.png",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=1920:1080",
        "-t", "5",
        output_path
    ], timeout=30)


if __name__ == "__main__":
    import sys
    key = get_api_key()
    if key:
        print(f"✓ PEXELS_API_KEY trouvée: {key[:8]}...{key[-4:]}")
    else:
        print("❌ PEXELS_API_KEY manquante")
        print("Va sur https://www.pexels.com/api/ → Join Free → inscris-toi")
        print("Puis: echo 'PEXELS_API_KEY=ta_clé' > /root/projets/youtube-automation/.env")
    
    if len(sys.argv) > 1:
        paths = prepare_visuals(sys.argv[1])
        for p in paths:
            dur = get_video_duration(p)
            print(f"  • {os.path.basename(p)} ({dur:.1f}s)")