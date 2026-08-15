#!/usr/bin/env python3
"""
Module series — Gestion de la série YouTube "Crimes & Ténèbres".
Une affaire = 2 épisodes :
  - Partie 1 (mardi)   : le mystère, l'enquête → CLIFFHANGER
  - Partie 2 (jeudi)   : la résolution → TEASER du prochain dossier

Structure de rétention : le spectateur qui finit la partie 1 DOIT voir la partie 2.
"""

import json
import os
import random
from datetime import datetime

from modules.script import (
    SUJETS, LIEUX, VICTIMES, PROFESSIONS, DESCRIPTIONS,
    gen_accroche, gen_contexte, gen_personnage, gen_enquete,
    gen_rebondissement, gen_climax, gen_conclusion,
)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_PATH = f"{BASE}/output/series_state.json"
SERIES_NAME = "Crimes & Ténèbres"


# ── État de la série ──
def load_state() -> dict:
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            return json.load(f)
    return {"season": 1, "next_episode": 1, "history": []}


def save_state(state: dict):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


# ── Éléments de série ──
CLIFFHANGERS = [
    "Mais ce que les enquêteurs allaient découvrir quarante-huit heures plus tard allait tout remettre en question. Une découverte si troublante qu'elle a failli faire basculer l'affaire à jamais. Une découverte qui a donné froid dans le dos à tous ceux qui l'ont vue. La suite, dans la partie 2.",
    "Et puis, ce matin-là, un appel a changé la donne. Au bout du fil, une voix que personne n'attendait. Ce que cette voix allait révéler... personne n'était prêt à l'entendre. Personne. La partie 2 est déjà en ligne. Ne la ratez pas.",
    "Le dossier semblait mort. Enterré. Oublié. Mais dans l'ombre, quelqu'un continuait d'observer. Quelqu'un qui connaissait la vérité. Et ce quelqu'un a décidé que le moment était venu de parler. Ce qu'il allait dire allait faire l'effet d'une bombe. La vérité éclate dans la partie 2.",
    "Alors que les enquêteurs s'apprêtaient à refermer le dossier, un détail infime a tout fait basculer. Un détail que des dizaines d'yeux avaient vu sans le voir. Un détail qui ouvrait une porte que l'on croyait verrouillée à jamais. Derrière cette porte... la partie 2 vous attend.",
    "La nuit est tombée sur cette affaire. Mais comme chacun sait, c'est dans les ténèbres que les secrets finissent toujours par remonter. Et celui qui allait remonter à la surface était plus noir que tout ce que la région avait connu. Rendez-vous dans la partie 2.",
]


def gen_recap(victime, annee, lieu, rebondissement):
    return random.choice([
        f"Dans l'épisode précédent : {annee}, {lieu}. {victime} disparaissait sans laisser de traces. Une enquête qui piétinait, des témoignages contradictoires, un village entier sous le choc. Et puis, {rebondissement}. Un élément qui allait tout bouleverser.",
        f"Vous vous souvenez : {victime}, {annee}. Une disparition que rien n'expliquait. Des mois d'enquête infructueuse. Des lettres anonymes. Des battues dans les forêts du Jura. Et au moment où tout semblait perdu, {rebondissement}. Voici la suite.",
        f"L'épisode précédent s'est arrêté sur une révélation : {rebondissement}. Mais ce n'était que la partie émergée de l'iceberg. Ce que {victime} cachait, ce que {lieu} a voulu oublier... tout allait remonter à la surface.",
    ])


def gen_teaser(next_topic):
    return random.choice([
        f"La semaine prochaine, dans {SERIES_NAME} : {next_topic}. Une affaire qui a marqué la Suisse. Abonnez-vous dès maintenant pour ne pas rater le premier épisode.",
        f"Mais l'histoire ne s'arrête pas là. Dès la semaine prochaine : {next_topic}. Un dossier brûlant, des secrets enfouis. Activez la cloche pour être prévenu de la sortie.",
        f"Rendez-vous la semaine prochaine pour un nouveau dossier : {next_topic}. Et croyez-moi, celui-là va vous glacer le sang. Abonnez-vous.",
    ])


def gen_intro_serie(episode_num):
    return random.choice([
        f"{SERIES_NAME}. Saison {1 if episode_num <= 30 else 2}, épisode {episode_num}.",
        f"Bienvenue dans {SERIES_NAME}. Épisode {episode_num}.",
        f"{SERIES_NAME} vous présente l'épisode {episode_num}.",
    ])


def gen_outro_part1(episode_num):
    return random.choice([
        f"La suite de cette affaire, dans l'épisode {episode_num + 1}, déjà disponible sur la chaîne. Ne manquez pas le dénouement.",
        f"Cette histoire est loin d'être terminée. L'épisode {episode_num + 1} révèle tout. Cliquez dès maintenant.",
        f"Vous ne devinerez jamais la fin. Épisode {episode_num + 1}, juste à côté. Regardez-le avant la suite.",
    ])


def gen_outro_part2():
    return random.choice([
        "Merci d'avoir suivi ce dossier jusqu'au bout. Si cette histoire vous a marqué, laissez un pouce bleu, partagez-la, et dites-nous en commentaire ce que vous en pensez. On se retrouve la semaine prochaine.",
        "Ce dossier est maintenant refermé. Mais d'autres attendent. Abonnez-vous, activez la cloche, et rejoignez-nous la semaine prochaine pour une nouvelle plongée dans les ténèbres.",
        "La vérité a été dite. L'affaire est close. Mais dans les archives, d'autres dossiers attendent de sortir de l'ombre. À la semaine prochaine.",
    ])


# ── Génération des 2 parties ──
def generate_episode_scripts(topic: str = None, state: dict = None) -> dict:
    """
    Génère les scripts des 2 épisodes d'une affaire.

    Returns:
        {
            "topic": "Titre de l'affaire",
            "part1": "script partie 1",
            "part2": "script partie 2",
            "titles": {"part1": "...", "part2": "..."},
            "episode_nums": {"part1": N, "part2": N+1},
        }
    """
    if state is None:
        state = load_state()

    if not topic:
        # Ne pas réutiliser un sujet déjà traité
        used = {h.get("topic", "") for h in state.get("history", [])}
        available = [s for s in SUJETS if s not in used] or SUJETS
        topic = random.choice(available)

    ep1 = state["next_episode"]
    ep2 = ep1 + 1

    # Variables narratives partagées entre les 2 parties
    annee = random.randint(1970, 2015)
    lieu = random.choice(LIEUX)
    victime = random.choice(VICTIMES)
    age = random.randint(22, 67)
    profession = random.choice(PROFESSIONS)
    description = random.choice(DESCRIPTIONS)
    rebondissement = random.choice(gen_rebondissement.__globals__["REBONDISSEMENTS"])
    nb_ans = datetime.now().year - annee
    duree = f"{random.randint(3, 18)} mois" if random.random() > 0.3 else f"{random.randint(1, 5)} ans"
    saison = random.choice(["printemps", "été", "automne", "hiver"])
    prenom = victime.split()[0]

    # ============================================================
    # PARTIE 1 — LE MYSTÈRE (~1100 mots)
    # ============================================================
    heures = [f"{h}h{random.choice(['00','15','30','45'])}" for h in [random.randint(6,10), random.randint(12,14), random.randint(17,20)]]
    lieu_rencontre = random.choice(["la sortie du village", "l'arrêt de bus", "le café du centre", "la poste", "le parking du supermarché", "la gare", "le bureau de tabac", "le pont de la rivière"])
    cliffhanger = random.choice(CLIFFHANGERS)

    p1 = []
    p1.append(f"[IMAGE: Logo {SERIES_NAME}, ambiance sombre, fumée, lumière dramatique]")
    p1.append(gen_intro_serie(ep1))
    p1.append("")
    p1.append(f"[IMAGE: Rue sombre sous la pluie, réverbères qui clignotent, ambiance nocturne, film noir]")
    p1.append(gen_accroche())
    p1.append("")
    p1.append(f"[IMAGE: {lieu}, paysage du Jura suisse, brume matinale, forêts, lacs]")
    p1.append(gen_contexte(annee, lieu, saison))
    p1.append("")
    p1.append(f"[IMAGE: Portrait de {victime}, photo d'identité, cadre doré, ambiance années {annee}]")
    p1.append(gen_personnage(victime, age, profession, description))
    p1.append("")
    p1.append(f"[IMAGE: Portrait de famille, album photo, souvenirs, maison de {victime}, intérieur chaleureux]")
    p1.append(f"Les proches de {prenom} décrivent une personne attachée à ses habitudes. Chaque matin, le même rituel : lever à {heures[0]}, petit-déjeuner, puis départ pour le travail. {profession} depuis {random.randint(8, 30)} ans. Des collègues discrets, des voisins serviables. Rien qui ne sorte de l'ordinaire. Et c'est précisément cela qui rend sa disparition si troublante. Quand des gens bien comme il faut disparaissent, c'est que quelque chose a terriblement mal tourné.")
    p1.append("")
    p1.append(f"[IMAGE: Scène de crime, ruban jaune, forêt dense, lampes torches, nuit]")
    p1.append(f"Ce jour-là, {prenom} a été vu pour la dernière fois. C'était un {random.choice(['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi'])} {random.choice(['ordinaire', 'comme les autres', 'banal'])}. Un témoin l'a croisé vers {heures[1]} à {lieu_rencontre}. Il semblait normal, peut-être un peu pressé. Rien dans son comportement ne laissait penser que quelque chose n'allait pas. Ce serait la dernière fois que quelqu'un le voyait vivant.")
    p1.append("")
    p1.append(f"[IMAGE: Téléphone qui sonne dans un commissariat vide, nuit, éclairage au néon]")
    p1.append(f"C'est un proche qui a donné l'alerte. {prenom} ne s'est pas présenté à un rendez-vous, n'a pas répondu aux appels. La première réaction des policiers, c'est l'attentisme. Les adultes disparaissent parfois volontairement, disent-ils. Mais les proches insistent. {prenom} n'est pas du genre à partir sans prévenir. Jamais.")
    p1.append("")
    p1.append(f"[IMAGE: Bureau d'enquêteur, dossier étalé, café froid, lampes de bureau, nuit]")
    p1.append(gen_enquete())
    p1.append("")
    p1.append(f"[IMAGE: Interrogatoire, salle vide, table métallique, lumière crue]")
    p1.append(f"Les policiers ont interrogé des dizaines de personnes. La famille, les collègues, les voisins, les commerçants du quartier. Chaque témoignage apportait son lot d'informations, mais rien qui ne permettait de progresser. {prenom} était quelqu'un de bien, disaient-ils tous. Une personne sans histoire. Et c'était bien là le problème.")
    p1.append("")
    p1.append(f"[IMAGE: Horloge qui tourne, aiguilles qui s'affolent, salle d'interrogatoire vide]")
    p1.append(gen_rebondissement(rebondissement))
    p1.append("")
    p1.append(f"[IMAGE: Tableau d'enquête, photos reliées par des fils rouges, épingles, indices]")
    p1.append(f"Les semaines ont passé. Les mois. L'affaire commençait à refroidir, comme une braise que plus personne n'alimente. Les médias en parlaient moins. Les enquêteurs étaient épuisés, frustrés, à bout. Et puis, un matin, un appel. Une voix au bout du fil. Un témoin qui n'avait pas parlé jusque-là, par peur, par oubli, par indifférence peut-être. Et tout a recommencé.")
    p1.append("")
    p1.append(f"[IMAGE: Lettre anonyme, papier jauni, écriture tremblée, enveloppe timbrée, mystère]")
    p1.append(f"Un détail en particulier a retenu l'attention des enquêteurs. {prenom} avait reçu plusieurs lettres anonymes dans les mois précédant sa disparition. Des lettres que les proches avaient écartées, les jugeant sans importance. Mais après relecture, elles prenaient un sens nouveau, inquiétant. Quelqu'un avait voulu faire peur à {prenom}. Quelqu'un qui connaissait ses habitudes, ses horaires, ses faiblesses.")
    p1.append("")
    p1.append(f"[IMAGE: Village sous le choc, habitants réunis, discussions de comptoir, commérages]")
    p1.append(f"Dans le village, la rumeur s'est répandue comme une traînée de poudre. Les commérages allaient bon train, les hypothèses les plus folles circulaient. Chacun y allait de sa théorie : une fugue, un enlèvement, un règlement de comptes. L'angoisse, elle, était palpable. On fermait les portes à double tour, on surveillait les enfants de plus près. Le mal était entré dans la vallée, et plus personne ne se sentait en sécurité.")
    p1.append("")
    p1.append(f"[IMAGE: Journalistes, caméras, micros, conférence de presse, flashs]")
    p1.append(f"Les médias s'en sont mêlés. Les journaux locaux d'abord, puis la presse nationale. L'affaire faisait la une, alimentée par le mystère et le silence des autorités. Des journalistes caméraient devant le domicile de {prenom}, interrogeaient les voisins, fouillaient le passé. Chaque jour, de nouvelles révélations, vraies ou fausses, entretenaient la tension. La famille, elle, vivait un cauchemar médiatique.")
    p1.append("")
    p1.append(f"[IMAGE: Scène de nuit, lampes torches dans les bois, enquêteurs en combinaison, brouillard]")
    p1.append(f"Il a fallu organiser des battues. Des dizaines de bénévoles, des chiens renifleurs, un hélicoptère. Les forêts du Jura ont été passées au peigne fin, mètre par mètre. Les lacs ont été sondés. Les grottes explorées. Rien. Comme si la terre avait avalé {prenom} sans laisser de trace. Les semaines passaient, et l'espoir s'amenuisait.")
    p1.append("")
    p1.append(f"[IMAGE: Nuit noire, une silhouette s'éloigne dans le brouillard, suspense]")
    p1.append(cliffhanger)
    p1.append("")
    p1.append(f"[IMAGE: Écran noir, texte 'À SUIVRE', suspense]")
    p1.append(gen_outro_part1(ep1))

    # ============================================================
    # PARTIE 2 — LA RÉSOLUTION (~1100 mots)
    # ============================================================
    next_topic = random.choice([s for s in SUJETS if s != topic])
    teaser = gen_teaser(next_topic)
    mobile = random.choice([
        f"une dette que {prenom} avait contractée des années plus tôt et que tout le monde avait oubliée. Sauf une personne.",
        f"une vieille histoire de famille, un héritage contesté, des jalousies qui couvaient depuis des générations.",
        f"un secret professionnel. {prenom} avait vu quelque chose qu'il n'aurait jamais dû voir.",
        f"une liaison ancienne, terminée dans la douleur, dont personne ne connaissait l'existence.",
        f"un passé que {prenom} croyait avoir enterré, mais qui refaisait surface au pire moment.",
    ])

    p2 = []
    p2.append(f"[IMAGE: Logo {SERIES_NAME}, ambiance sombre, fumée, lumière dramatique]")
    p2.append(gen_intro_serie(ep2))
    p2.append("")
    p2.append(f"[IMAGE: Flashback, images du village sous la pluie, plans rapides]")
    p2.append(gen_recap(victime, annee, lieu, rebondissement))
    p2.append("")
    p2.append(f"[IMAGE: Bureau de juge, livres de droit, balance de justice, lumière tamisée]")
    p2.append(f"Le parquet a décidé de rouvrir le dossier. De nouveaux moyens, de nouvelles méthodes. Les progrès de la science, l'ADN, les analyses téléphoniques, la géolocalisation. Tout ce qui n'existait pas au moment des faits allait peut-être permettre de faire la lumière sur cette affaire. Les avocats des parties civiles, eux, retenaient leur souffle. Après tant d'années, la vérité allait-elle enfin éclater ?")
    p2.append("")
    p2.append(f"[IMAGE: Laboratoire médico-légal, microscope, échantillons, lumière froide]")
    p2.append(f"Et c'est la science qui a parlé en premier. Les nouvelles techniques d'analyse ont permis d'exploiter des prélèvements que l'on croyait perdus. Une trace infime, invisible à l'œil nu, conservée des années dans un scellé poussiéreux. Les experts ont travaillé des semaines, dans le secret le plus total. Et quand le résultat est tombé, personne n'en a cru ses yeux.")
    p2.append("")
    p2.append(f"[IMAGE: Tableau d'enquête, photos de suspects, lignes rouges, théories]")
    p2.append(f"Le résultat a orienté les enquêteurs vers une piste que personne n'avait sérieusement explorée. Des suspects que l'on avait écartés trop vite, des alibis qui se fissuraient, des contradictions dans des témoignages vieux de plusieurs années. Lentement, le filet se resserrait. Mais chaque avancée soulevait une nouvelle question, chaque réponse cachait un nouveau mystère.")
    p2.append("")
    p2.append(f"[IMAGE: Interrogatoire, face à face tendu, lumière crue, silence pesant]")
    p2.append(f"Les confrontations ont été éprouvantes. Des heures d'interrogatoire, des voix qui se brisent, des aveux qui ne viennent pas. Les enquêteurs savaient qu'ils touchaient au but, mais il leur manquait la pièce maîtresse du puzzle. Et puis, un soir, tout a basculé. Un détail dans une déposition. Une phrase prononcée trop vite. Et le château de cartes s'est effondré.")
    p2.append("")
    p2.append(f"[IMAGE: Salle d'audience, bois sombre, lumière tamisée, bancs vides, silence]")
    p2.append(f"Le mobile, lui, était d'une banalité effrayante : {mobile} Et c'est cette banalité qui a rendu le crime si difficile à élucider. Les enquêteurs cherchaient un monstre, une folie, quelque chose d'extraordinaire. Ils ont trouvé un être humain, terriblement ordinaire, rongé par une rancœur que personne n'avait su voir.")
    p2.append("")
    p2.append(f"[IMAGE: Rapport d'expert, schémas, profil psychologique, annotations]")
    p2.append(f"Les experts en criminologie ont dressé un profil troublant. L'auteur des faits ne correspondait pas au portrait attendu. Ni impulsif, ni désorganisé. Au contraire : méthodique, calculateur, capable de garder son sang-froid dans les situations les plus extrêmes. Un profil qui évoquait davantage le prédateur patient que le criminel passionnel. Et c'est ce sang-froid qui, pendant toutes ces années, lui avait permis de passer entre les mailles du filet.")
    p2.append("")
    p2.append(f"[IMAGE: Avocat, costume sombre, bureau feutré, dossiers empilés]")
    p2.append(f"La défense, elle, a joué sa carte maîtresse : le doute. Pendant des semaines, les avocats ont martelé l'absence de preuves directes, les zones grises de l'enquête, les erreurs des premières heures. Chaque élément à charge était contesté, décortiqué, retourné. Le procès s'est transformé en un combat d'usure, où chaque mot pesait, où chaque silence comptait.")
    p2.append("")
    p2.append(f"[IMAGE: Palais de justice, façade imposante, ciel gris, foule, caméras]")
    p2.append(gen_climax(lieu, duree))
    p2.append("")
    p2.append(f"[IMAGE: Portrait de {victime}, encadré, bougie, hommage, intérieur feutré]")
    p2.append(f"Ce qui s'est joué dans ce procès, c'est bien plus que la culpabilité d'un accusé. C'est la question de savoir si la justice peut vraiment réparer l'irréparable. {nb_ans} ans après les faits, les proches de {prenom} attendent toujours des réponses. Et le verdict, quel qu'il soit, ne leur rendra jamais ce qu'ils ont perdu.")
    p2.append("")
    p2.append(f"[IMAGE: Le village aujourd'hui, vie quotidienne, soleil bas, mélancolie]")
    p2.append(f"Le village, lui, a mis des années à se remettre. Les habitants évitent certains sujets, certains lieux, certains regards. Les plus anciens se souviennent encore de ce jour où tout a basculé. Les plus jeunes, eux, n'en connaissent que les rumeurs. Mais une chose est certaine : cette affaire a changé {lieu} à jamais.")
    p2.append("")
    p2.append(f"[IMAGE: Crépuscule sur {lieu}, dernières lueurs du jour, silence, campagne]")
    p2.append(gen_conclusion(topic, nb_ans, lieu, random.choice(gen_conclusion.__globals__["QUESTIONS_FINALES"])))
    p2.append("")
    p2.append(f"[IMAGE: Écran noir, silhouette qui approche, suspense, 'PROCHAIN ÉPISODE']")
    p2.append(teaser)
    p2.append("")
    p2.append(f"[IMAGE: Logo {SERIES_NAME}, fondu noir]")
    p2.append(gen_outro_part2())

    # Titres YouTube
    titre_court = topic.split(" — ")[0]
    titles = {
        "part1": f"{titre_court} — ÉPISODE {ep1} (1/2) | {SERIES_NAME}",
        "part2": f"{titre_court} — ÉPISODE {ep2} (2/2) Le Dénouement | {SERIES_NAME}",
    }

    return {
        "topic": topic,
        "part1": "\n".join(p1),
        "part2": "\n".join(p2),
        "titles": titles,
        "episode_nums": {"part1": ep1, "part2": ep2},
    }


def build_descriptions(result: dict, urls: dict = None) -> dict:
    """
    Génère les descriptions YouTube des 2 épisodes avec liens croisés.

    Args:
        result: dict de generate_episode_scripts()
        urls: {"part1": "https://...", "part2": "https://..."} si déjà uploadé

    Returns:
        {"part1": "description", "part2": "description"}
    """
    topic = result["topic"]
    ep1 = result["episode_nums"]["part1"]
    ep2 = result["episode_nums"]["part2"]

    d1 = f"""🔍 {topic} — Partie 1/2

Dans cet épisode : une disparition inexplicable, un village sous le choc, et une enquête qui piétine. Jusqu'au détail qui va tout faire basculer...

🎬 Épisode {ep1} — {SERIES_NAME}

━━━━━━━━━━━━━━━━━━━━━━
⏭️ LA SUITE DANS L'ÉPISODE {ep2} :"""
    if urls and urls.get("part2"):
        d1 += f"\n👉 {urls['part2']}"
    else:
        d1 += f"\n👉 Déjà disponible sur la chaîne — clique sur le logo !"

    d1 += f"""

🔔 ABONNE-TOI : 2 épisodes par semaine (mardi & jeudi)
👍 Like si tu veux la suite
💬 Théories en commentaire !

#TrueCrime #Série #CrimeStory #Documentaire #Enquête #Suisse
"""

    d2 = f"""🔍 {topic} — Partie 2/2 — LE DÉNOUEMENT

L'épisode précédent nous a laissés sur un cliffhanger. Aujourd'hui : la vérité éclate enfin.

🎬 Épisode {ep2} — {SERIES_NAME}

━━━━━━━━━━━━━━━━━━━━━━
📺 L'ÉPISODE {ep1} (Partie 1) :"""
    if urls and urls.get("part1"):
        d2 += f"\n👉 {urls['part1']}"
    else:
        d2 += f"\n👉 Sur la chaîne"

    d2 += f"""

🔔 ABONNE-TOI : 2 épisodes par semaine (mardi & jeudi)
👍 Like si la vérité t'a surpris
💬 Dis-moi en commentaire si tu avais deviné !

#TrueCrime #Série #CrimeStory #Documentaire #Enquête #Suisse
"""

    return {"part1": d1, "part2": d2}


if __name__ == "__main__":
    result = generate_episode_scripts()
    print(f"\n{'='*60}")
    print(f"SÉRIE : {result['topic']}")
    print(f"{'='*60}")
    print(f"Épisode {result['episode_nums']['part1']} : {result['titles']['part1']}")
    print(f"Épisode {result['episode_nums']['part2']} : {result['titles']['part2']}")
    print(f"\nPartie 1 : {len(result['part1'].split())} mots")
    print(f"Partie 2 : {len(result['part2'].split())} mots")
    print("\n--- PARTIE 1 (extrait) ---")
    print(result["part1"][:500])
    print("\n--- PARTIE 2 (extrait) ---")
    print(result["part2"][:500])