#!/usr/bin/env python3
"""
Générateur de scripts à partir de la BDD de sujets réels mondiaux.
Remplace le template fictif par des faits vérifiés pour la chaîne "Dark Chronicles".
Bilingue FR/EN.
"""

import os
import random
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Charger la BDD
import sys
sys.path.insert(0, BASE)
from data.subjects import SUBJECTS, CATEGORIES, DEFAULT_TAGS


SERIES_NAME_FR = "Chroniques des Ténèbres"
SERIES_NAME_EN = "Dark Chronicles"

CLIFFHANGERS_FR = [
    "Mais ce que les enquêteurs allaient découvrir dans les jours suivants allait tout remettre en question. Une découverte si troublante qu'elle a failli faire basculer l'affaire à jamais. La suite, dans la partie 2.",
    "Et puis, ce témoignage inattendu. Une voix que personne n'attendait. Ce que cette voix allait révéler... personne n'était prêt à l'entendre. La partie 2 est déjà disponible.",
    "Le dossier semblait enterré. Mais dans l'ombre, la vérité attendait son heure. Et elle allait frapper plus fort que tout ce qu'on avait imaginé. Rendez-vous dans la partie 2.",
    "Ce n'était que la partie émergée de l'iceberg. Derrière cette façade de mystère se cachait une vérité encore plus sombre. La partie 2 vous attend.",
]

CLIFFHANGERS_EN = [
    "But what investigators would discover in the following days would turn everything upside down. A discovery so disturbing it nearly broke the case forever. The conclusion, in part 2.",
    "And then, that unexpected testimony. A voice no one expected. What that voice would reveal... no one was ready to hear. Part 2 is already available.",
    "The case seemed buried. But in the shadows, the truth was waiting. And it would strike harder than anyone imagined. Part 2 awaits.",
    "This was just the tip of the iceberg. Behind this veil of mystery lay a truth darker than anyone dreamed. Part 2 is waiting for you.",
]

TEASERS_FR = [
    "La semaine prochaine dans Chroniques des Ténèbres : {next_title}. Une histoire qui va vous glacer le sang. Abonnez-vous pour ne pas la rater.",
    "Rendez-vous la semaine prochaine pour une nouvelle plongée dans les ténèbres : {next_title}. Activez la cloche.",
    "L'histoire ne s'arrête pas là. La semaine prochaine : {next_title}. Abonnez-vous dès maintenant.",
]

TEASERS_EN = [
    "Next week on Dark Chronicles: {next_title}. A story that will chill you to the bone. Subscribe so you don't miss it.",
    "Join us next week for another dive into darkness: {next_title}. Hit the bell.",
    "The story doesn't end here. Next week: {next_title}. Subscribe now.",
]

RECAPS_FR = [
    "Dans l'épisode précédent : {period}, {country}. {teaser_line} Et au moment où tout semblait perdu, un élément nouveau a tout bouleversé. Voici la suite.",
]
RECAPS_EN = [
    "In the previous episode: {period}, {country}. {teaser_line} And just when all seemed lost, a new element changed everything. Here is the conclusion.",
]

OUTROS_FR = [
    "Merci d'avoir suivi ce dossier jusqu'au bout. Si cette histoire vous a marqué, laissez un pouce bleu, partagez-la, et dites-nous en commentaire ce que vous en pensez. On se retrouve la semaine prochaine.",
    "Ce dossier est maintenant refermé. Mais d'autres attendent. Abonnez-vous, activez la cloche, et rejoignez-nous la semaine prochaine.",
]
OUTROS_EN = [
    "Thank you for following this case to the end. If this story moved you, leave a thumbs up, share it, and tell us in the comments what you think. See you next week.",
    "This case is now closed. But more await. Subscribe, hit the bell, and join us next week.",
]


def _pick(items, lang="fr"):
    """Choisit aléatoirement selon la langue si dispo, sinon prend la liste."""
    if isinstance(items, dict):
        return random.choice(items.get(lang, items.get("fr", [])))
    return random.choice(items)


def _llm_narrate(subj: dict, facts: list, lang: str, part: str, series: str,
                 ep_num: int, next_title: str = "") -> str:
    """
    Transforme les faits vérifiés en narration thriller via Gemini (gratuit).
    Les faits sont sacrés : le LLM ne doit RIEN inventer.
    Fallback template si l'API échoue.
    """
    import requests as _req
    import json as _json

    # Charger la clé Google (dernière occurrence valide, ignore les placeholders)
    api_key = None
    for env_path in ["/root/.hermes/.env", "/root/.env"]:
        try:
            with open(env_path) as f:
                for line in f:
                    if line.startswith("GOOGLE_API_KEY"):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        # Ignorer les placeholders et ne garder que les vraies clés
                        if val.startswith("AIza") and "your_" not in val:
                            api_key = val  # garde la dernière valide
        except FileNotFoundError:
            continue
        if api_key:
            break

    if not api_key:
        return None

    cat_labels = {
        "crime": {"fr": "une affaire criminelle célèbre", "en": "a famous criminal case"},
        "disparition": {"fr": "une disparition mystérieuse", "en": "a mysterious disappearance"},
        "catastrophe": {"fr": "une catastrophe historique", "en": "a historic disaster"},
        "mystere": {"fr": "un mystère inexpliqué", "en": "an unexplained mystery"},
    }
    cat = cat_labels.get(subj["category"], cat_labels["mystere"]).get(lang, "")

    if lang == "fr":
        system = (
            "Tu es le narrateur d'une chaîne YouTube documentaire thriller "
            "'Chroniques des Ténèbres'. Ton style : tension, phrases courtes, "
            "rythme cinématographique, aucune fioriture. "
            "RÈGLE ABSOLUE : tu écris UNIQUEMENT à partir des faits fournis. "
            "Tu ne modifies JAMAIS les noms, dates, lieux, chiffres. "
            "Tu n'inventes AUCUN fait, AUCUN dialogue, AUCUN détail non fourni. "
            "Tu peux ajouter du style, du suspense, des questions rhétoriques, "
            "mais chaque phrase factuelle doit provenir des faits donnés."
        )
        if part == "part1":
            user = (
                f"Sujet : {subj['title_fr']} ({cat}). "
                f"Écris la PARTIE 1 d'une narration vidéo en français : "
                f"1) une accroche dramatique de 2-3 phrases sur {subj['title_fr']}, "
                f"2) le contexte ({subj['period']}, {subj['country']}), "
                f"3) le développement des 4 premiers faits ci-dessous, chacun enrichi "
                f"par des transitions et du suspense, "
                f"4) une montée en tension finale se terminant par un cliffhanger "
                f"du type « la suite dans la partie 2 ». "
                f"Longueur : 1100-1300 mots. Utilise des paragraphes séparés par des lignes vides.\n\n"
                f"FAITS (à respecter à la lettre) :\n"
                + "\n".join(f"- {f}" for f in facts[:4])
            )
        else:
            user = (
                f"Sujet : {subj['title_fr']} ({cat}). "
                f"Écris la PARTIE 2 (le dénouement) d'une narration vidéo en français : "
                f"1) un récapitulatif de 2-3 phrases de la partie 1, "
                f"2) le développement des faits restants ci-dessous, enrichis par du suspense, "
                f"3) une réflexion finale et un appel à l'abonnement. "
                f"Longueur : 900-1100 mots. Paragraphes séparés par des lignes vides.\n\n"
                f"FAITS (à respecter à la lettre) :\n"
                + "\n".join(f"- {f}" for f in facts[4:])
            )
    else:
        system = (
            "You are the narrator of a thriller documentary YouTube channel "
            "'Dark Chronicles'. Style: tension, short sentences, cinematic pacing, no fluff. "
            "ABSOLUTE RULE: you write ONLY from the provided facts. "
            "NEVER alter names, dates, places, numbers. "
            "NEVER invent any fact, dialogue, or unprovided detail. "
            "You may add style, suspense, rhetorical questions, "
            "but every factual sentence must come from the given facts."
        )
        if part == "part1":
            user = (
                f"Subject: {subj['title_en']} ({cat}). "
                f"Write PART 1 of a video narration in English: "
                f"1) a dramatic 2-3 sentence hook about {subj['title_en']}, "
                f"2) the context ({subj['period']}, {subj['country']}), "
                f"3) the development of the first 4 facts below, each enriched "
                f"with transitions and suspense, "
                f"4) a final build-up ending with a cliffhanger like "
                f"'the conclusion in part 2'. "
                f"Length: 1100-1300 words. Paragraphs separated by blank lines.\n\n"
                f"FACTS (respect them to the letter):\n"
                + "\n".join(f"- {f}" for f in facts[:4])
            )
        else:
            user = (
                f"Subject: {subj['title_en']} ({cat}). "
                f"Write PART 2 (the conclusion) of a video narration in English: "
                f"1) a 2-3 sentence recap of part 1, "
                f"2) the development of the remaining facts below, enriched with suspense, "
                f"3) a final reflection and a call to subscribe. "
                f"Length: 900-1100 words. Paragraphs separated by blank lines.\n\n"
                f"FACTS (respect them to the letter):\n"
                + "\n".join(f"- {f}" for f in facts[4:])
            )

    try:
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        resp = _req.post(
            url,
            headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": system + "\n\n" + user}]}],
                "generationConfig": {
                    "maxOutputTokens": 4000,
                    "temperature": 0.8,
                },
            },
            timeout=120,
        )
        data = resp.json()
        if "candidates" in data:
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            if len(text.split()) > 300:
                return text
            print(f"   ⚠️  Réponse Gemini trop courte ({len(text.split())} mots, "
                  f"finish={data['candidates'][0].get('finishReason')}), fallback template")
        else:
            print(f"   ⚠️  Gemini erreur API : {_json.dumps(data)[:200]}")
        return None
    except Exception as e:
        print(f"   ⚠️  LLM indisponible ({type(e).__name__}), fallback template")
        return None


def generate_episode_scripts_real(subject_id: str = None, lang: str = "fr",
                                   state: dict = None) -> dict:
    """
    Génère les 2 scripts d'une affaire RÉELLE à partir de la BDD.

    Args:
        subject_id: ID du sujet dans la BDD, ou None pour aléatoire
        lang: "fr" ou "en"
        state: état de la série

    Returns:
        dict avec part1, part2, titles, episode_nums
    """
    if subject_id:
        subj = SUBJECTS[subject_id]
    else:
        # Aléatoire, en évitant les sujets déjà traités
        used = set()
        if state:
            used = {h.get("subject_id", "") for h in state.get("history", [])}
        available = [k for k in SUBJECTS if k not in used] or list(SUBJECTS.keys())
        subject_id = random.choice(available)
        subj = SUBJECTS[subject_id]

    facts = subj["facts_fr"] if lang == "fr" else subj["facts_en"]
    title = subj[f"title_{lang}"]
    cat_fr = CATEGORIES.get(subj["category"], subj["category"])

    series = SERIES_NAME_FR if lang == "fr" else SERIES_NAME_EN
    cliffhangers = CLIFFHANGERS_FR if lang == "fr" else CLIFFHANGERS_EN
    recaps_tpl = RECAPS_FR if lang == "fr" else RECAPS_EN
    outros = OUTROS_FR if lang == "fr" else OUTROS_EN
    teasers = TEASERS_FR if lang == "fr" else TEASERS_EN

    ep1 = (state or {}).get("next_episode", 1)
    ep2 = ep1 + 1

    # Prochain sujet pour le teaser
    remaining = [k for k in SUBJECTS if k != subject_id]
    next_title = SUBJECTS[random.choice(remaining)][f"title_{lang}"]

    # ── GÉNÉRATION LLM (narration riche) avec fallback template ──
    series = SERIES_NAME_FR if lang == "fr" else SERIES_NAME_EN

    narration1 = _llm_narrate(subj, facts, lang, "part1", series, ep1)
    narration2 = _llm_narrate(subj, facts, lang, "part2", series, ep2)

    if narration1 and narration2:
        # Préfixer avec l'intro de série
        if lang == "fr":
            intro1 = (f"[IMAGE: Logo {series}, ambiance sombre, fumée, lumière dramatique]\n"
                      f"{series}. Saison {1 if ep1 <= 30 else 2}, épisode {ep1}.\n\n")
            intro2 = (f"[IMAGE: Logo {series}, ambiance sombre, fumée, lumière dramatique]\n"
                      f"{series}. Saison {1 if ep2 <= 30 else 2}, épisode {ep2}.\n\n")
        else:
            intro1 = (f"[IMAGE: {series} logo, dark atmosphere, smoke, dramatic lighting]\n"
                      f"{series}. Season {1 if ep1 <= 30 else 2}, Episode {ep1}.\n\n")
            intro2 = (f"[IMAGE: {series} logo, dark atmosphere, smoke, dramatic lighting]\n"
                      f"{series}. Season {1 if ep2 <= 30 else 2}, Episode {ep2}.\n\n")
        part1_text = intro1 + narration1
        part2_text = intro2 + narration2
    else:
        # Fallback template (facts bruts)
        part1_text, part2_text = _template_fallback(subj, facts, lang, series, ep1, ep2)

    # ── TITRES YOUTUBE ──
    if lang == "fr":
        titles = {
            "part1": f"{title} — ÉPISODE {ep1} (1/2) | {series}",
            "part2": f"{title} — ÉPISODE {ep2} (2/2) Le Dénouement | {series}",
        }
    else:
        titles = {
            "part1": f"{title} — EPISODE {ep1} (1/2) | {series}",
            "part2": f"{title} — EPISODE {ep2} (2/2) The Conclusion | {series}",
        }

    return {
        "subject_id": subject_id,
        "topic": title,
        "category": subj["category"],
        "part1": part1_text,
        "part2": part2_text,
        "titles": titles,
        "episode_nums": {"part1": ep1, "part2": ep2},
    }


def _template_fallback(subj, facts, lang, series, ep1, ep2):
    """Fallback : faits bruts + cliffhanger si le LLM est indisponible."""
    img = "[IMAGE: Dark night scene, cinematic atmosphere, shadows]"
    if lang == "fr":
        ch = "Chroniques des Ténèbres"
        p1 = [f"[IMAGE: Logo {series}, ambiance sombre, fumée, lumière dramatique]",
              f"{series}. Saison 1, épisode {ep1}.", "",
              img, f"{subj['period']}. {subj['country']}. {facts[0]}", "",
              img, facts[1], "",
              img, facts[2], "",
              img, facts[3] if len(facts) > 3 else facts[2], "",
              img, random.choice(CLIFFHANGERS_FR), "",
              "[IMAGE: Écran noir, texte 'À SUIVRE']",
              f"La suite dans l'épisode {ep2}, déjà disponible."]
        p2 = [f"[IMAGE: Logo {series}, ambiance sombre, fumée, lumière dramatique]",
              f"{series}. Saison 1, épisode {ep2}.", "",
              img, "Dans l'épisode précédent, l'affaire nous a laissés sans réponse. Voici la vérité.", "",
              img, facts[4] if len(facts) > 4 else facts[3], "",
              img, facts[5] if len(facts) > 5 else facts[-1], "",
              img, facts[6] if len(facts) > 6 else facts[-1], "",
              img, random.choice(OUTROS_FR)]
    else:
        p1 = [f"[IMAGE: {series} logo, dark atmosphere, smoke, dramatic lighting]",
              f"{series}. Season 1, Episode {ep1}.", "",
              img, f"{subj['period']}. {subj['country']}. {facts[0]}", "",
              img, facts[1], "",
              img, facts[2], "",
              img, facts[3] if len(facts) > 3 else facts[2], "",
              img, random.choice(CLIFFHANGERS_EN), "",
              "[IMAGE: Black screen, 'TO BE CONTINUED']",
              f"The conclusion in episode {ep2}, already available."]
        p2 = [f"[IMAGE: {series} logo, dark atmosphere, smoke, dramatic lighting]",
              f"{series}. Season 1, Episode {ep2}.", "",
              img, "In the previous episode, the case left us without answers. Here is the truth.", "",
              img, facts[4] if len(facts) > 4 else facts[3], "",
              img, facts[5] if len(facts) > 5 else facts[-1], "",
              img, facts[6] if len(facts) > 6 else facts[-1], "",
              img, random.choice(OUTROS_EN)]
    return "\n".join(p1), "\n".join(p2)


def get_voice_for_lang(lang: str) -> str:
    """Retourne la voix edge-tts pour une langue donnée."""
    voices = {
        "fr": "fr-FR-DeniseNeural",
        "en": "en-US-ChristopherNeural",
    }
    return voices.get(lang, "fr-FR-DeniseNeural")


if __name__ == "__main__":
    for lang in ["fr", "en"]:
        r = generate_episode_scripts_real(lang=lang)
        print(f"\n{'='*60}")
        print(f"LANG: {lang} | {r['topic']}")
        print(f"EP{r['episode_nums']['part1']} : {r['titles']['part1']}")
        print(f"Partie 1 : {len(r['part1'].split())} mots")
        print(f"Partie 2 : {len(r['part2'].split())} mots")
        print("--- PARTIE 1 (extrait) ---")
        print(r["part1"][:300])