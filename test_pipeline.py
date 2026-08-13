#!/usr/bin/env python3
"""Test du pipeline complet avec un vrai script généré."""
import sys
import os

sys.path.insert(0, 'modules')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import glob

# Récupérer le dernier script généré
scripts = sorted(glob.glob("output/scripts/*.txt"))
if not scripts:
    print("❌ Aucun script trouvé")
    sys.exit(1)

script_path = scripts[-1]
print(f"=== SCRIPT: {os.path.basename(script_path)} ===")

with open(script_path) as f:
    script_text = f.read()

# Récupérer le titre
title = None
for line in script_text.split('\n'):
    if line.startswith("TITLE:"):
        title = line.replace("TITLE:", "").strip()
        break

# Nettoyer les métadonnées
if "---" in script_text:
    parts = script_text.split("---")
    if len(parts) >= 3:
        clean_text = "---".join(parts[2:])
    else:
        clean_text = parts[1] if len(parts) > 1 else parts[0]
else:
    clean_text = script_text

words = len(clean_text.split())
print(f"Titre : {title}")
print(f"Longueur : {words} mots (~{words//150} min de vidéo)")
print(f"Image prompts : {clean_text.count('[IMAGE:')}")

# 1. VOIX
from voice import text_to_speech
print("\n=== ÉTAPE 1: VOIX ===")
audio = text_to_speech(clean_text, voice="fr-FR-HenriNeural", rate="+5%")
print(f"Audio : {os.path.basename(audio)}")

# 2. VISUELS
from visuals import prepare_visuals
print("\n=== ÉTAPE 2: VISUELS ===")
images = prepare_visuals(script_path, script_text)
print(f"Images : {len(images)}")

# 3. VIDÉO
from video import assemble_video
print("\n=== ÉTAPE 3: VIDÉO ===")
video = assemble_video(audio, images)
print(f"Vidéo : {os.path.basename(video)}")

# 4. MINIATURE
from thumbnail import create_thumbnail
print("\n=== ÉTAPE 4: MINIATURE ===")
thumb = create_thumbnail(title or "True Crime Suisse", images[0] if images else None)
print(f"Miniature : {os.path.basename(thumb)}")

# 5. SOUS-TITRES
from video import add_subtitles
print("\n=== ÉTAPE 5: SOUS-TITRES ===")
subtitled = add_subtitles(video, clean_text)
print(f"Sous-titres : {os.path.basename(subtitled)}")

# Résumé
print("\n" + "="*60)
print("✅ TEST PIPELINE COMPLET RÉUSSI")
print("="*60)
print(f"  Script    : {script_path}")
print(f"  Audio     : {audio}")
print(f"  Images    : {len(images)}")
print(f"  Vidéo     : {video}")
print(f"  Sous-titré: {subtitled}")
print(f"  Miniature : {thumb}")
print(f"  Taille    : {os.path.getsize(video)/(1024*1024):.0f} MB")