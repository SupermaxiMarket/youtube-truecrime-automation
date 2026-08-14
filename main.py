#!/usr/bin/env python3
"""
Pipeline YouTube Automatisé — True Crime façon thriller.
Orchestrateur principal : script → voix → visuels → vidéo → miniature.

Usage:
    python main.py                          # Chaîne complète, sujet auto-généré
    python main.py --topic "titre sujet"     # Sujet spécifique
    python main.py --script-only             # Génère juste le script
    python main.py --resume <script_file>    # Reprend à partir d'un script existant
"""

import argparse
import os
import subprocess
import sys
import yaml
from datetime import datetime


def load_config():
    base = os.path.dirname(os.path.abspath(__file__))
    with open(f"{base}/config.yaml") as f:
        return yaml.safe_load(f)


def get_output_base():
    return os.path.dirname(os.path.abspath(__file__))


def run_pipeline(topic: str = None, script_only: bool = False,
                 resume_script: str = None) -> dict:
    """Exécute le pipeline complet."""
    base = get_output_base()
    
    # Ajouter le dossier modules au path
    sys.path.insert(0, f"{base}/modules")
    
    result = {"topic": topic or "auto-généré"}
    
    # 1. SCRIPT
    if resume_script and os.path.exists(resume_script):
        print(f"\n{'='*60}")
        print("📜 ÉTAPE 1/4 — Reprise du script existant")
        print(f"{'='*60}")
        with open(resume_script) as f:
            script_text = f.read()
        script_path = resume_script
        print(f"   ✓ Script chargé : {script_path}")
    else:
        print(f"\n{'='*60}")
        print("📜 ÉTAPE 1/4 — Génération du script")
        print(f"{'='*60}")
        from modules.script import generate_script, save_script
        topic_gen, script_text = generate_script(topic)
        result["title"] = topic_gen
        script_path = save_script(topic_gen, script_text)
        result["script"] = script_path
        
        print(f"   ✓ Titre : {result['title']}")
        print(f"   ✓ Script : {len(script_text)} chars")
    
    if script_only:
        result["status"] = "script_ready"
        return result
    
    # 2. VOIX
    print(f"\n{'='*60}")
    print("🎙️  ÉTAPE 2/4 — Synthèse vocale")
    print(f"{'='*60}")
    from modules.voice import text_to_speech
    
    # Nettoyer le script des métadonnées
    if "---" in script_text:
        parts = script_text.split("---")
        if len(parts) >= 3:
            clean_text = "---".join(parts[2:])
        else:
            clean_text = parts[1] if len(parts) > 1 else parts[0]
    else:
        clean_text = script_text
    
    audio_path = text_to_speech(clean_text)
    result["audio"] = audio_path
    
    # 3. VISUELS (clips vidéo Pexels)
    print(f"\n{'='*60}")
    print("🎬 ÉTAPE 3/4 — Téléchargement clips vidéo")
    print(f"{'='*60}")
    from modules.visuals import prepare_visuals
    video_clips = prepare_visuals(script_path, script_text)
    result["clips"] = video_clips
    
    # 4. VIDÉO (assemblage avec vrais clips)
    print(f"\n{'='*60}")
    print("🎬 ÉTAPE 4/4 — Assemblage vidéo")
    print(f"{'='*60}")
    from modules.video import assemble_video
    video_path = assemble_video(audio_path, video_clips)
    result["video"] = video_path
    
    # 5. MINIATURE (à partir du premier clip)
    print(f"\n{'='*60}")
    print("🖼️  ÉTAPE FINALE — Création miniature")
    print(f"{'='*60}")
    from modules.thumbnail import create_thumbnail
    first_frame = "/tmp/thumb_frame.jpg"
    subprocess.run([
        "ffmpeg", "-y", "-v", "quiet",
        "-ss", "0:01", "-i", video_clips[0],
        "-frames:v", "1", "-q:v", "3", first_frame
    ], timeout=10)
    thumb_path = create_thumbnail(result.get("title", "True Crime"), 
                                   first_frame if os.path.exists(first_frame) else None)
    result["thumbnail"] = thumb_path
    
    # Résumé final
    print(f"\n{'='*60}")
    print(f"✅ PIPELINE TERMINÉ !")
    print(f"{'='*60}")
    print(f"   Titre     : {result.get('title', 'N/A')}")
    print(f"   Script    : {result.get('script', 'N/A')}")
    print(f"   Audio     : {result.get('audio', 'N/A')}")
    print(f"   Visuels   : {len(result.get('clips', []))} clips")
    print(f"   Vidéo     : {result.get('video', 'N/A')}")
    print(f"   Miniature : {result.get('thumbnail', 'N/A')}")
    video_size = os.path.getsize(video_path) / (1024*1024) if os.path.exists(video_path) else 0
    print(f"   Taille    : {video_size:.0f} MB")
    print(f"{'='*60}")
    
    result["status"] = "complete"
    return result


def upload_to_youtube(result: dict, privacy: str = "unlisted") -> dict:
    """Upload la vidéo produite sur YouTube."""
    from modules.upload_youtube import upload_video
    
    video_path = result.get("video")
    title = result.get("title", "True Crime")
    # Charger le script pour la description
    script_text = ""
    script_path = result.get("script")
    if script_path and os.path.exists(script_path):
        with open(script_path) as f:
            script_text = f.read()
    
    upload_result = upload_video(video_path, title, script_text, privacy=privacy)
    result["youtube_url"] = upload_result["url"]
    result["youtube_id"] = upload_result["video_id"]
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline YouTube True Crime automatisé",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python main.py
  python main.py --topic "L'Affaire du Pont du Diable — Deux Disparus Sans Traces"
  python main.py --script-only
  python main.py --resume output/scripts/20260812_143000_L_affaire_du_pont.txt
  python main.py --upload                         # Génère + upload
  python main.py --upload --privacy public       # Upload en public
        """
    )
    parser.add_argument("--topic", type=str, help="Sujet de la vidéo")
    parser.add_argument("--script-only", action="store_true",
                       help="Générer uniquement le script")
    parser.add_argument("--resume", type=str,
                       help="Reprendre à partir d'un script existant")
    parser.add_argument("--upload", action="store_true",
                       help="Uploader sur YouTube après génération")
    parser.add_argument("--privacy", type=str, default="unlisted",
                       choices=["public", "unlisted", "private"],
                       help="Confidentialité YouTube (défaut: unlisted)")
    
    args = parser.parse_args()
    
    result = run_pipeline(
        topic=args.topic,
        script_only=args.script_only,
        resume_script=args.resume
    )
    
    # Upload YouTube si demandé
    if args.upload and result.get("video"):
        result = upload_to_youtube(result, privacy=args.privacy)
    
    return result


if __name__ == "__main__":
    main()