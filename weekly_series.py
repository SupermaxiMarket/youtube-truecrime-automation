#!/usr/bin/env python3
"""
Job hebdomadaire — Série "Crimes & Ténèbres".
À exécuter le mardi à 06:00 :
  → génère une affaire en 2 épisodes
  → upload + planifie Partie 1 : mardi 12:00
  → upload + planifie Partie 2 : jeudi 12:00

Usage:
    python3 weekly_series.py [--topic "sujet"] [--now] [--dry-run]

Options:
    --now       Ignore la règle mardi/jeudi : publie P1 demain 12h, P2 +2j
    --dry-run   Affiche les dates calculées sans rien faire
"""

import argparse
import os
import sys
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)


def compute_publish_times(now: datetime, force: bool = False):
    """
    Calcule les 2 dates de publication (heure suisse).

    Règle normale : mardi 12:00 (P1) et jeudi 12:00 (P2).
    Si on n'est pas mardi (mode --now/retard), on prend demain 12h et J+2 12h.
    """
    if force or now.weekday() != 1:  # pas mardi → mode rattrapage
        p1 = (now + timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)
        p2 = (now + timedelta(days=2)).replace(hour=12, minute=0, second=0, microsecond=0)
    else:
        p1 = now.replace(hour=12, minute=0, second=0, microsecond=0)
        p2 = (now + timedelta(days=2)).replace(hour=12, minute=0, second=0, microsecond=0)

    # Format RFC 3339 avec offset local (WSL configuré Europe/Zurich)
    return {
        "part1": p1.astimezone().isoformat(timespec="seconds"),
        "part2": p2.astimezone().isoformat(timespec="seconds"),
    }


def main():
    parser = argparse.ArgumentParser(description="Job hebdomadaire série True Crime")
    parser.add_argument("--topic", type=str, help="Sujet spécifique")
    parser.add_argument("--now", action="store_true",
                        help="Publier demain/J+2 (ignore la règle mardi)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Afficher les dates sans exécuter")
    args = parser.parse_args()

    now = datetime.now().astimezone()
    publish = compute_publish_times(now, force=args.now)

    print(f"{'='*60}")
    print(f"📅 PLANIFICATION SÉRIE — {now.strftime('%A %d.%m.%Y %H:%M')}")
    print(f"{'='*60}")
    print(f"   Partie 1 : {publish['part1']}")
    print(f"   Partie 2 : {publish['part2']}")
    print(f"{'='*60}")

    if args.dry_run:
        print("   (dry-run — aucune exécution)")
        return

    from main import run_series

    result = run_series(
        topic=args.topic,
        upload=True,
        privacy="private",  # private + publishAt = planification auto
        publish_at_parts=publish,
    )

    print(f"\n✅ JOB HEBDOMADAIRE TERMINÉ")
    if result.get("episodes"):
        for ep in result["episodes"]:
            print(f"   → {ep.get('title', '?')} : {ep.get('youtube_url', 'non uploadé')}")

    return result


if __name__ == "__main__":
    main()