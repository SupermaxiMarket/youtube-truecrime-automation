#!/usr/bin/env python3
"""
Module TTS — Synthèse vocale française de qualité.
Utilise edge-tts (Microsoft Edge TTS, gratuit, voix françaises naturelles).
"""

import asyncio
import json
import os
import re
import subprocess
import sys


def text_to_speech(text: str, voice: str = "fr-FR-DeniseNeural",
                   rate: str = "+0%", pitch: str = "+0Hz",
                   output_path: str = None) -> str:
    """
    Convertit un texte en fichier audio WAV.
    Utilise edge-tts en ligne de commande.
    """
    if not output_path:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_path = f"{base}/output/audio/voice_{os.urandom(4).hex()}.mp3"

    # Nettoyer le texte — garder la narration, enlever les balises [IMAGE:]
    clean_text = re.sub(r'\[IMAGE:[^\]]*\]', '', text)
    clean_text = re.sub(r'---.*?---', '', clean_text, flags=re.DOTALL)
    clean_text = clean_text.strip()

    # Écrire le texte dans un fichier temporaire (edge-tts peut lire depuis stdin)
    temp_file = "/tmp/tts_input.txt"
    with open(temp_file, "w") as f:
        f.write(clean_text)

    cmd = [
        "edge-tts",
        "--voice", voice,
        "--rate", rate,
        "--pitch", pitch,
        "-f", temp_file,
        "--write-media", output_path
    ]

    print(f"🎙️  Génération voix ({voice})...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        raise RuntimeError(f"edge-tts failed: {result.stderr}")

    # Vérifier que le fichier existe et a une taille non nulle
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        duration = get_audio_duration(output_path)
        print(f"   ✓ Voix générée : {os.path.basename(output_path)} ({duration:.1f}s)")
        return output_path
    else:
        raise RuntimeError(f"Fichier audio vide ou manquant: {output_path}")


def get_audio_duration(filepath: str) -> float:
    """Récupère la durée d'un fichier audio via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", filepath
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    try:
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except:
        return 0.0


def list_voices():
    """Liste les voix françaises disponibles."""
    result = subprocess.run(["edge-tts", "--list-voices"], capture_output=True, text=True, timeout=30)
    voices = [l for l in result.stdout.split("\n") if "FR-" in l]
    for v in voices:
        print(v)
    return voices


if __name__ == "__main__":
    if "--list-voices" in sys.argv:
        list_voices()
    elif len(sys.argv) > 1:
        # Lire le fichier script et générer l'audio
        script_path = sys.argv[1]
        with open(script_path) as f:
            content = f.read()
        # Enlever les métadonnées
        if "---" in content:
            content = "---".join(content.split("---")[2:])
        output = text_to_speech(content)
        print(f"\n✔ Audio prêt : {output}")
    else:
        print("Usage: python voice.py <script_file>")
        print("       python voice.py --list-voices")