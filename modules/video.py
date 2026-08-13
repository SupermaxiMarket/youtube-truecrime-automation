#!/usr/bin/env python3
"""
Module vidéo — Assemble des clips vidéo réels + audio en vidéo YouTube.
Normalise chaque clip (résolution/fps/codec identiques) puis concatène.
"""

import json
import os
import re
import subprocess
import yaml


def load_config():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(f"{base}/config.yaml") as f:
        return yaml.safe_load(f)


def normalize_clip(input_path: str, output_path: str, 
                   width: int = 1920, height: int = 1080, fps: int = 30) -> bool:
    """
    Normalise un clip : même résolution, même fps, même codec, timestamps réinitialisés.
    Étape indispensable avant le concat de clips hétérogènes.
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        "-vf", (
            f"scale={width}:{height}:force_original_aspect_ratio=1,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=#0a0a14,"
            f"fps={fps},"
            f"setpts=PTS-STARTPTS,"
            f"format=yuv420p"
        ),
        "-an",  # pas d'audio sur les clips (on garde que la voix)
        "-hide_banner", "-loglevel", "error",
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return os.path.exists(output_path) and os.path.getsize(output_path) > 1000


def get_duration(filepath: str) -> float:
    """Récupère la durée d'un fichier vidéo/audio."""
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", filepath]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    try:
        return float(json.loads(result.stdout)["format"]["duration"])
    except:
        return 0.0


def assemble_video(audio_path: str, video_clips: list,
                   output_path: str = None) -> str:
    """
    Assemble la vidéo : normalise les clips, concatène, ajoute l'audio.
    """
    config = load_config()
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    if not output_path:
        output_path = f"{base}/output/videos/video_{os.urandom(4).hex()}.mp4"
    
    audio_duration = get_duration(audio_path)
    num_clips = len(video_clips)
    if num_clips == 0:
        raise RuntimeError("Aucun clip vidéo fourni")
    
    print(f"🎬  Assemblage ({audio_duration:.0f}s audio, {num_clips} clips)...")
    
    # 1. Normaliser chaque clip (indispensable pour le concat)
    norm_dir = "/tmp/norm_clips"
    os.makedirs(norm_dir, exist_ok=True)
    normalized = []
    
    print("   ↻ Normalisation des clips...")
    for i, clip in enumerate(video_clips):
        out = f"{norm_dir}/clip_{i:03d}.mp4"
        if not os.path.exists(out) or os.path.getsize(out) < 1000:
            ok = normalize_clip(clip, out)
            if not ok:
                print(f"   ⚠️  Clip {i} normalisation échouée, skip")
                continue
        normalized.append(out)
        print(f"   ↻ clip {i+1}/{num_clips}...", end="\r")
    
    if not normalized:
        raise RuntimeError("Aucun clip normalisé")
    
    print(f"   ✓ {len(normalized)} clips normalisés")
    
    # 2. Durée totale des clips
    clips_duration = sum(get_duration(c) for c in normalized)
    print(f"   Durée clips: {clips_duration:.0f}s / audio: {audio_duration:.0f}s")
    
    # 3. Si besoin, répéter les clips pour couvrir l'audio (avec fondu enchaîné)
    if clips_duration < audio_duration:
        # Faire un fondu enchaîné entre clips pour boucle fluide
        repeat_times = int(audio_duration / clips_duration) + 1
        print(f"   ↻ Boucle {repeat_times}x pour couvrir l'audio...")
        
        # Construire le filtre concat avec crossfade
        loop_dir = "/tmp/loop_clips"
        os.makedirs(loop_dir, exist_ok=True)
        
        # Concat simple (copie) - les clips sont maintenant homogènes
        concat_list = "/tmp/concat_all.txt"
        with open(concat_list, "w") as f:
            for _ in range(repeat_times):
                for c in normalized:
                    f.write(f"file '{c}'\n")
        
        temp_loop = f"{loop_dir}/looped.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_list,
            "-c", "copy",
            "-hide_banner", "-loglevel", "error",
            temp_loop
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if os.path.exists(temp_loop) and os.path.getsize(temp_loop) > 1000:
            normalized = [temp_loop]
            clips_duration = get_duration(temp_loop)
    
    # 4. Concaténer (maintenant homogène → concat -c copy OK)
    concat_list = "/tmp/concat_final.txt"
    with open(concat_list, "w") as f:
        for c in normalized:
            f.write(f"file '{c}'\n")
    
    temp_video = "/tmp/concat_video.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list,
        "-c", "copy",
        "-hide_banner", "-loglevel", "error",
        temp_video
    ]
    subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    
    if not os.path.exists(temp_video) or os.path.getsize(temp_video) < 1000:
        raise RuntimeError("Échec du concat des clips")
    
    # 5. Ajouter l'audio + couper à la durée de l'audio
    cmd = [
        "ffmpeg", "-y",
        "-i", temp_video,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-movflags", "+faststart",
        "-hide_banner", "-loglevel", "error",
        output_path
    ]
    subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        final_dur = get_duration(output_path)
        print(f"   ✓ Vidéo finale : {size_mb:.0f}MB, {final_dur:.0f}s → {output_path}")
        return output_path
    else:
        raise RuntimeError(f"Échec de l'assemblage vidéo: {output_path}")


def add_subtitles(video_path: str, script_text: str,
                  output_path: str = None) -> str:
    """Ajoute des sous-titres incrustés à la vidéo."""
    if not output_path:
        output_path = video_path.replace(".mp4", "_subtitled.mp4")
    
    clean = re.sub(r'\[IMAGE:[^\]]*\]', '', script_text)
    clean = re.sub(r'---.*?---', '', clean, flags=re.DOTALL)
    clean = re.sub(r'\n\s*\n', '\n', clean).strip()
    
    srt_path = "/tmp/subtitles.srt"
    lines = clean.split('\n')
    total_words = len(clean.split())
    total_duration = total_words / 2.5
    line_duration = total_duration / max(len(lines), 1)
    
    with open(srt_path, "w") as f:
        time = 0.0
        for i, line in enumerate(lines):
            if not line.strip():
                continue
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
        "-hide_banner", "-loglevel", "error",
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
        clips = sys.argv[2:]
        video = assemble_video(audio, clips)
        print(f"\n✔ Vidéo finale : {video}")
    else:
        print("Usage: python video.py <audio.mp3> <clip1.mp4> [clip2.mp4 ...]")