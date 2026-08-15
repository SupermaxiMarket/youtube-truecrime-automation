#!/usr/bin/env python3
"""
Module ambient — Génère un fond sonore dark ambient via ffmpeg.
Brown noise filtré + reverb = drone atmosphérique pour true crime.
Zéro dépendance externe, génération en ~5 secondes.
"""

import os
import subprocess
import yaml


def load_config():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(f"{base}/config.yaml") as f:
        return yaml.safe_load(f)


def generate_ambient(duration_seconds: int = 600, output_path: str = None) -> str:
    """
    Génère une piste dark ambient de fond.

    Args:
        duration_seconds: Durée en secondes (défaut 10 min, assez pour couvrir 12 min de vidéo)
        output_path: Chemin de sortie .wav

    Returns:
        Chemin du fichier audio généré
    """
    config = load_config()
    ambient_cfg = config.get("ambient", {})
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if not output_path:
        cache_dir = f"{base}/output/audio"
        os.makedirs(cache_dir, exist_ok=True)
        output_path = f"{cache_dir}/ambient_dark_{duration_seconds}s.wav"

    # Utiliser le cache si la piste existe déjà
    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        print(f"   ✓ Fond sonore réutilisé depuis le cache : {output_path}")
        return output_path

    volume = ambient_cfg.get("volume", 0.5)
    
    print(f"   ↻ Génération fond dark ambient ({duration_seconds}s)...")

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"anoisesrc=d={duration_seconds}:c=brown:a={volume}",
        "-af",
        # lowpass → que les basses (grave, oppressant)
        "lowpass=f=180,"
        # highpass → enlève les infra-basses inaudibles
        "highpass=f=25,"
        # reverb → espace, profondeur
        "aecho=0.8:0.6:60:0.4,"
        # deuxième couche de reverb plus longue
        "aecho=0.9:0.5:80:0.3,"
        # normaliser le volume
        "volume=0.6",
        "-ac", "2",
        "-ar", "44100",
        "-hide_banner", "-loglevel", "error",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"   ✓ Fond sonore généré : {output_path} ({size_mb:.1f} MB)")
        return output_path
    else:
        raise RuntimeError(f"Échec génération ambient: {result.stderr}")


def mix_voice_with_ambient(voice_path: str, ambient_path: str,
                            ambient_volume: float = 0.12,
                            output_path: str = None) -> str:
    """
    Mixe la voix off avec le fond sonore ambient.

    Args:
        voice_path: Chemin du fichier voix (MP3)
        ambient_path: Chemin du fond sonore (WAV)
        ambient_volume: Volume du fond (0-1, défaut 12%)
        output_path: Chemin de sortie

    Returns:
        Chemin du fichier audio mixé
    """
    if not output_path:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_path = voice_path.replace(".mp3", "_mixed.mp3")

    # Récupérer la durée de la voix
    import json
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", voice_path]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    voice_dur = float(json.loads(result.stdout)["format"]["duration"])

    print(f"   ↻ Mixage voix + fond sonore ({ambient_volume*100:.0f}%)...")

    cmd = [
        "ffmpeg", "-y",
        "-i", voice_path,
        "-stream_loop", "-1", "-i", ambient_path,
        "-t", str(voice_dur + 3),
        "-filter_complex",
        f"[1:a]volume={ambient_volume},afade=t=out:st={voice_dur}:d=3[a];"
        f"[0:a][a]amix=inputs=2:duration=first:dropout_transition=2,"
        f"volume=1.2",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        "-ac", "2",
        "-hide_banner", "-loglevel", "error",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        size_kb = os.path.getsize(output_path) / 1024
        print(f"   ✓ Audio mixé : {output_path} ({size_kb:.0f} KB)")
        return output_path
    else:
        raise RuntimeError(f"Échec mixage audio: {result.stderr}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2:
        voice = sys.argv[1]
        ambient = generate_ambient(600)
        mixed = mix_voice_with_ambient(voice, ambient)
        print(f"\n✓ Mix final : {mixed}")
    else:
        # Test : juste générer le fond
        path = generate_ambient(30)
        print(f"✓ Test ambient : {path}")