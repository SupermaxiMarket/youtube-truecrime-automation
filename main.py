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
                 resume_script: str = None,
                 external_script: str = None, external_title: str = None) -> dict:
    """Exécute le pipeline complet. external_script/title = mode série."""
    base = get_output_base()
    
    # Ajouter le dossier modules au path
    sys.path.insert(0, f"{base}/modules")
    
    result = {"topic": topic or "auto-généré"}
    
    # 1. SCRIPT
    if external_script and external_title:
        print(f"\n{'='*60}")
        print("📜 ÉTAPE 1/4 — Script fourni (mode série)")
        print(f"{'='*60}")
        script_text = external_script
        result["title"] = external_title
        from modules.script import save_script
        script_path = save_script(external_title, script_text)
        result["script"] = script_path
        print(f"   ✓ Titre : {result['title']}")
        print(f"   ✓ Script : {len(script_text)} chars")
    elif resume_script and os.path.exists(resume_script):
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
    
    # 2b. FOND SONORE AMBIENT (dark drone)
    config = load_config()
    if config.get("ambient", {}).get("enabled", True):
        print(f"\n{'='*60}")
        print("🌑 ÉTAPE 2b — Fond sonore dark ambient")
        print(f"{'='*60}")
        from modules.ambient import generate_ambient, mix_voice_with_ambient
        
        # Générer ou récupérer le fond (10 min cache)
        ambient_path = generate_ambient(720)  # 12 min, couvre toutes les vidéos
        
        # Mixer voix + fond
        ambient_vol = config.get("ambient", {}).get("volume", 0.10)
        mixed_audio = mix_voice_with_ambient(audio_path, ambient_path, ambient_vol)
        audio_path = mixed_audio
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


def upload_to_youtube(result: dict, privacy: str = "unlisted",
                      custom_description: str = None) -> dict:
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
    
    if custom_description:
        # Utiliser la description fournie + tags standard
        from modules.upload_youtube import get_authenticated_service
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        import os as _os
        upload_result = upload_video(
            video_path, title, script_text, privacy=privacy,
            custom_description=custom_description
        )
    else:
        upload_result = upload_video(video_path, title, script_text, privacy=privacy)
    result["youtube_url"] = upload_result["url"]
    result["youtube_id"] = upload_result["video_id"]
    return result


def run_series(topic: str = None, upload: bool = False,
               privacy: str = "unlisted",
               publish_at_parts: dict = None) -> dict:
    """Génère les 2 épisodes d'une affaire (mode série).

    Args:
        topic: Sujet spécifique (None = auto)
        upload: Uploader sur YouTube
        privacy: public | unlisted | private
        publish_at_parts: {"part1": "2026-08-18T12:00:00+02:00", "part2": ...}
            → planifie la publication automatique (privacy passe en private)
    """
    from modules.series import (
        generate_episode_scripts, load_state, save_state, build_descriptions
    )
    
    state = load_state()
    scripts = generate_episode_scripts(topic, state)
    
    print(f"\n{'#'*60}")
    print(f"🎬 SÉRIE : {scripts['topic']}")
    print(f"   Épisode {scripts['episode_nums']['part1']} (1/2) + Épisode {scripts['episode_nums']['part2']} (2/2)")
    print(f"{'#'*60}")
    
    result = {"topic": scripts["topic"], "episodes": []}
    urls = {}
    
    for part, label in [("part1", "Partie 1/2"), ("part2", "Partie 2/2")]:
        print(f"\n{'#'*60}")
        print(f"▶ {label} — Épisode {scripts['episode_nums'][part]}")
        print(f"{'#'*60}")
        
        ep_result = run_pipeline(
            external_script=scripts[part],
            external_title=scripts["titles"][part]
        )
        
        # Upload avec description croisée
        if upload and ep_result.get("video"):
            # Planification de publication si demandée
            if publish_at_parts and publish_at_parts.get(part):
                os.environ["YOUTUBE_PUBLISH_AT"] = publish_at_parts[part]
            descriptions = build_descriptions(scripts, urls)
            ep_result = upload_to_youtube(
                ep_result, privacy=privacy,
                custom_description=descriptions[part]
            )
            os.environ.pop("YOUTUBE_PUBLISH_AT", None)
            urls[part] = ep_result.get("youtube_url")
            print(f"\n   🔗 {ep_result.get('youtube_url')}")
        
        result["episodes"].append(ep_result)
    
    # Mettre à jour l'état de la série
    state["next_episode"] = scripts["episode_nums"]["part2"] + 1
    state["history"].append({
        "topic": scripts["topic"],
        "episodes": [scripts["episode_nums"]["part1"], scripts["episode_nums"]["part2"]],
        "date": datetime.now().isoformat(),
        "urls": urls
    })
    save_state(state)
    
    print(f"\n{'#'*60}")
    print(f"✅ SÉRIE TERMINÉE — Prochain épisode : {state['next_episode']}")
    print(f"{'#'*60}")
    
    result["status"] = "complete"
    result["state"] = state
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
    parser.add_argument("--series", action="store_true",
                       help="Mode série : 2 épisodes d'une affaire (1/2 + 2/2)")
    
    args = parser.parse_args()
    
    # Mode série : 2 épisodes
    if args.series:
        result = run_series(
            topic=args.topic,
            upload=args.upload,
            privacy=args.privacy
        )
        return result
    
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