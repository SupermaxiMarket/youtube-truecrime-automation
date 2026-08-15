#!/usr/bin/env python3
"""
Module upload YouTube — Upload automatique via YouTube Data API v3.

Nécessite (une seule fois) :
  1. Aller sur https://console.cloud.google.com
  2. Créer un projet OU sélectionner un projet existant
  3. Activer "YouTube Data API v3" (APIs & Services → Library)
  4. Créer un écran de consentement OAuth (External, ajouter le scope youtube.upload)
  5. Créer des identifiants OAuth 2.0 → Desktop app
  6. Télécharger le JSON → le renommer client_secret.json
  7. Placer client_secret.json dans /root/projets/youtube-automation/

Premier lancement : ouvre l'URL affichée dans ton navigateur Windows,
connecte-toi au compte YouTube souhaité, copie le code d'auth et colle-le ici.
Le token est sauvegardé dans output/youtube_token.pickle pour les uploads suivants.
"""

import os
import sys
import pickle
import re
import subprocess

# ── Google API ──
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = "youtube_token.pickle"


def get_project_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_authenticated_service():
    """Authentifie via OAuth 2.0 (console flow pour WSL/headless)."""
    project_dir = get_project_dir()
    output_dir = os.path.join(project_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    token_path = os.path.join(output_dir, TOKEN_FILE)
    secret_path = os.path.join(project_dir, "client_secret.json")

    if not os.path.exists(secret_path):
        print("\n❌  Fichier client_secret.json introuvable !\n")
        print("Étapes à suivre (5 min la première fois) :\n")
        print("1. Ouvre https://console.cloud.google.com")
        print("2. Crée un projet (ou sélectionne un existant)")
        print("3. APIs & Services → Library → chercher 'YouTube Data API v3' → ACTIVER")
        print("4. APIs & Services → OAuth consent screen")
        print("   - Type: External")
        print("   - Ajoute le scope: .../auth/youtube.upload")
        print("   - Ajoute ton email comme test user")
        print("5. APIs & Services → Credentials → Create Credentials → OAuth client ID")
        print("   - Application type: Desktop app")
        print("   - Télécharge le JSON")
        print(f"6. Copie le fichier téléchargé ici :\n   {secret_path}\n")
        sys.exit(1)

    credentials = None

    if os.path.exists(token_path):
        with open(token_path, "rb") as token:
            credentials = pickle.load(token)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print("   ↻ Refresh du token OAuth...")
            credentials.refresh(Request())
        else:
            # WSL / headless → flow console (pas de navigateur intégré)
            flow = InstalledAppFlow.from_client_secrets_file(
                secret_path, SCOPES,
                redirect_uri="urn:ietf:wg:oauth:2.0:oob"
            )
            auth_url, _ = flow.authorization_url(prompt="consent")

            print("\n🔐  Authentification YouTube requise (première fois)\n")
            print("1. Ouvre ce lien dans ton navigateur Windows :\n")
            print(f"   {auth_url}\n")
            print("2. Connecte-toi au compte YouTube de la chaîne")
            print("3. Copie le code d'autorisation affiché")
            print("4. Colle-le ci-dessous :\n")

            code = input("   Code d'auth > ").strip()

            os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
            flow.fetch_token(code=code)
            credentials = flow.credentials

        os.makedirs(os.path.dirname(token_path), exist_ok=True)
        with open(token_path, "wb") as token:
            pickle.dump(credentials, token)
        print(f"   ✓ Token sauvegardé → {token_path}")

    return build("youtube", "v3", credentials=credentials)


def extract_metadata(script_text: str, title: str = "") -> dict:
    """Extrait description et tags depuis le script."""
    # Nettoyer pour la description
    clean = re.sub(r'\[IMAGE:[^\]]*\]', '', script_text)
    clean = re.sub(r'---.*?---', '', clean, flags=re.DOTALL)

    # Premiers paragraphes pour la description
    paragraphs = [p.strip() for p in clean.split('\n\n') if p.strip()]
    intro = '\n\n'.join(paragraphs[:3]) if paragraphs else clean[:500]

    description = f"""{title}

{intro}

━━━━━━━━━━━━━━━━━━━━━━
🔔 ABONNE-TOI pour plus d'histoires criminelles
👍 Like si tu veux la suite
💬 Ton avis en commentaire

#TrueCrime #CrimeStory #Documentaire #Enquete
"""

    # Tags
    tags = [
        "true crime", "crime", "enquête", "documentaire", "histoire vraie",
        "cold case", "affaire criminelle", "police", "investigation",
        "crime story", "mystère", "disparition", "meurtre", "thriller",
        "faits divers", "suisse", "vallée de joux"
    ]

    return {"description": description[:5000], "tags": tags}


def upload_video(video_path: str, title: str, script_text: str = "",
                 privacy: str = "unlisted", category_id: str = "27",
                 custom_description: str = None) -> dict:
    """
    Upload une vidéo sur YouTube.

    Args:
        video_path: Chemin absolu vers le .mp4
        title: Titre YouTube (max 100 chars)
        script_text: Texte du script pour générer description + tags
        privacy: public | unlisted | private
        category_id: 27=Education, 22=People, 24=Entertainment, 26=Howto
        custom_description: Description explicite (mode série, liens croisés)

    Returns:
        {"video_id": "...", "url": "https://youtube.com/watch?v=..."}
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Vidéo introuvable : {video_path}")

    file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
    print(f"\n📤  Upload YouTube — {os.path.basename(video_path)} ({file_size_mb:.0f} MB)")
    print(f"   Titre : {title[:80]}")
    print(f"   Confidentialité : {privacy}")

    youtube = get_authenticated_service()

    # Métadonnées
    if custom_description:
        meta = {
            "description": custom_description[:5000],
            "tags": extract_metadata(script_text, title)["tags"],
        }
    else:
        meta = extract_metadata(script_text, title)

    if len(title) > 100:
        title = title[:97] + "..."

    body = {
        "snippet": {
            "title": title,
            "description": meta["description"],
            "tags": meta["tags"],
            "categoryId": category_id,
            "defaultLanguage": "fr",
            "defaultAudioLanguage": "fr"
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
            "madeForKids": False
        }
    }

    # Planification de publication (publishAt) — nécessite privacy=private
    publish_at = os.environ.get("YOUTUBE_PUBLISH_AT")
    if publish_at:
        if privacy != "private":
            privacy = "private"
            body["status"]["privacyStatus"] = "private"
        body["status"]["publishAt"] = publish_at
        print(f"   ⏰ Publication planifiée : {publish_at}")

    # Upload resumable (5MB chunks, reprend si coupure)
    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        chunksize=1024 * 1024 * 5,
        resumable=True
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    print("   ↻ Upload en cours...")

    response = None
    last_progress = -1
    while response is None:
        try:
            status, response = request.next_chunk()
        except HttpError as e:
            if e.resp.status in [500, 502, 503, 504]:
                print(f"\n   ⚠️  Erreur serveur, nouvelle tentative...")
                continue
            raise

        if status:
            pct = int(status.progress() * 100)
            if pct != last_progress:
                print(f"   ↻ Upload... {pct}%", end="\r")
                last_progress = pct

    video_id = response["id"]
    url = f"https://youtube.com/watch?v={video_id}"
    print(f"\n   ✓ Upload terminé !")
    print(f"   🔗 {url}")

    # Upload miniature si dispo
    project_dir = get_project_dir()
    thumbs_dir = os.path.join(project_dir, "output", "thumbnails")
    if os.path.isdir(thumbs_dir):
        thumbs = sorted(
            [f for f in os.listdir(thumbs_dir) if f.endswith(('.jpg', '.png'))],
            key=lambda f: os.path.getmtime(os.path.join(thumbs_dir, f)),
            reverse=True
        )
        if thumbs:
            latest_thumb = os.path.join(thumbs_dir, thumbs[0])
            try:
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(latest_thumb, mimetype="image/jpeg")
                ).execute()
                print(f"   ✓ Miniature uploadée : {thumbs[0]}")
            except HttpError as e:
                print(f"   ⚠️  Miniature non uploadée : {e}")

    return {"video_id": video_id, "url": url}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python upload_youtube.py <video.mp4> <titre> [privacy]")
        print("       python upload_youtube.py video.mp4 \"Mon Titre\" unlisted")
        sys.exit(1)

    privacy = sys.argv[3] if len(sys.argv) > 3 else "unlisted"
    result = upload_video(sys.argv[1], sys.argv[2], privacy=privacy)
    print(f"\n✅  URL : {result['url']}")