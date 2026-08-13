#!/usr/bin/env python3
"""
Module vidéo — Assemble audio + images en vidéo YouTube.
Utilise ffmpeg pour le montage : transitions Ken Burns, audio, sous-titres.
"""

import json
import math
import os
import re
import subprocess
import yaml
from PIL import Image


def load_config():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(f"{base}/config.yaml") as f:
        return yaml.safe_load(f)


def get_image_duration(total_duration: float, num_images: int) -> float:
    """Calcule la durée par image pour couvrir la durée totale."""
    if num_images == 0:
        return total_duration
    return total_duration / num_images


def create_ken_burns_filter(image_path: str, duration: float,
                             zoom: float = 1.05, fps: int = 30) -> str:
    """
    Génère le filtre ffmpeg Ken Burns pour une image.
    Effet : zoom lent + léger mouvement.
    """
    w, h = 1920, 1080
    
    # Mouvement aléatoire basé sur le hash du fichier
    seed = abs(hash(image_path)) % 1000
    x_start = (seed % 10) / 100  # 0 à 0.09
    y_start = ((seed // 10) % 10) / 100  # 0 à 0.09
    
    # Effet Ken Burns : zoom + léger déplacement
    filter_str = (
        f"zoompan=z='min(zoom+0.0005,{zoom})':"
        f"d={int(duration*fps)}:"
        f"x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':"
        f"s={w}x{h}:fps={fps}"
    )
    return filter_str


def assemble_video(audio_path: str, image_paths: list,
                   output_path: str = None) -> str:
    """
    Assemble la vidéo : images + audio + transitions.
    Utilise ffmpeg avec filtre concat.
    """
    config = load_config()
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    if not output_path:
        output_path = f"{base}/output/videos/video_{os.urandom(4).hex()}.mp4"
    
    # Obtenir la durée de l'audio
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    audio_info = json.loads(result.stdout)
    audio_duration = float(audio_info["format"]["duration"])
    
    # Calculer le nombre d'images et leur durée
    num_images = len(image_paths)
    if num_images == 0:
        print("⚠️  Aucune image, création d'une image noire")
        img_path = "/tmp/black_frame.png"
        os.system(f"ffmpeg -y -f lavfi -i color=c=#0a0a14:s=1920x1080:d=1 -frames:v 1 {img_path} -hide_banner -loglevel error")
        image_paths = [img_path]
        num_images = 1
    
    img_duration = audio_duration / num_images
    
    print(f"🎬  Assemblage vidéo ({audio_duration:.0f}s audio, {num_images} images)...")
    
    # Créer un fichier de liste pour le concat
    concat_file = "/tmp/video_concat_list.txt"
    
    with open(concat_file, "w") as f:
        for i, img_path in enumerate(image_paths):
            f.write(f"file '{img_path}'\n")
            f.write(f"duration {img_duration:.2f}\n")
    
    # Commande ffmpeg principale
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-i", audio_path,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-r", str(config["video"]["fps"]),
        "-vf", (
            f"fps={config['video']['fps']},"
            f"scale=1920:1080:force_original_aspect_ratio=1,"
            f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=#0a0a14,"
            f"format=yuv420p"
        ),
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        "-hide_banner",
        "-loglevel", "warning",
        "-progress", "/tmp/ffmpeg_progress.txt",
        output_path
    ]
    
    subprocess.run(cmd, timeout=600)
    
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"   ✓ Vidéo assemblée : {size_mb:.0f}MB → {output_path}")
        return output_path
    else:
        raise RuntimeError(f"Échec de l'assemblage vidéo: {output_path}")


def add_subtitles(video_path: str, script_text: str, 
                  output_path: str = None) -> str:
    """
    Ajoute des sous-titres incrustés à la vidéo (style cinéma).
    """
    if not output_path:
        output_path = video_path.replace(".mp4", "_subtitled.mp4")
    
    # Nettoyer le script des balises IMAGE et métadonnées
    clean = re.sub(r'\[IMAGE:[^\]]*\]', '', script_text)
    clean = re.sub(r'---.*?---', '', clean, flags=re.DOTALL)
    clean = re.sub(r'\n\s*\n', '\n', clean).strip()
    
    # Écrire les sous-titres en SRT
    srt_path = "/tmp/subtitles.srt"
    lines = clean.split('\n')
    
    # Durée approximative par mot (2.5 mots/sec)
    total_words = len(clean.split())
    total_duration = total_words / 2.5  # secondes
    line_duration = total_duration / max(len(lines), 1)
    
    with open(srt_path, "w") as f:
        time = 0.0
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            # Sous-titres max 42 caractères par ligne
            words = line.split()
            chunks = []
            current = []
            for w in words:
                current.append(w)
                if len(' '.join(current)) > 42:
                    chunks.append(' '.join(current[:-1]))
                    current = [w]
            if current:
                chunks.append(' '.join(current))
            
            chunk_duration = line_duration / max(len(chunks), 1)
            
            for chunk in chunks:
                start_s = int(time)
                start_m = start_s // 60
                start_h = start_m // 60
                start_ms = int((time - start_s) * 1000)
                
                time += chunk_duration
                end_s = int(time)
                end_m = end_s // 60
                end_h = end_m // 60
                end_ms = int((time - end_s) * 1000)
                
                f.write(f"{i+1}\n")
                f.write(f"{start_h:02d}:{start_m%60:02d}:{start_s%60:02d},{start_ms:03d} "
                       f"--> {end_h:02d}:{end_m%60:02d}:{end_s%60:02d},{end_ms:03d}\n")
                f.write(f"{chunk}\n\n")
    
    # Incruster les sous-titres
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", (
            f"subtitles={srt_path}:force_style="
            f"'FontName=Georgia,FontSize=22,PrimaryColour=&H00FFFFFF,"
            f"OutlineColour=&H00000000,BorderStyle=1,Outline=1,"
            f"Shadow=0,MarginV=50,Alignment=2'"
        ),
        "-c:a", "copy",
        "-hide_banner",
        "-loglevel", "warning",
        output_path
    ]
    
    subprocess.run(cmd, timeout=600)
    
    if os.path.exists(output_path):
        print(f"   ✓ Sous-titres ajoutés : {output_path}")
        return output_path
    return video_path


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) >= 3:
        audio = sys.argv[1]
        images = sys.argv[2:] if len(sys.argv) > 2 else []
        video = assemble_video(audio, images)
        print(f"\n✔ Vidéo finale : {video}")
    else:
        print("Usage: python video.py <audio.mp3> <image1.jpg> [image2.jpg ...]")