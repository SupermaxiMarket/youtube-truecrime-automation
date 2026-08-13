#!/usr/bin/env python3
"""
Module de génération de scripts — Version longue pour YouTube.
Génère des scripts true crime de 1200-1500 mots (8-10 min de vidéo).
"""

import os
import random
import re
from datetime import datetime


# ── Banque de sujets ──
SUJETS = [
    "L'Affaire du Disparu du Jura — Un Cold Case Suisse",
    "Le Tueur de la Vallée de Joux — Crimes dans le Silence",
    "L'Affaire des Faux-Monnayeurs de La Chaux-de-Fonds",
    "Le Disparu du Creux-du-Van — Suicide ou Meurtre ?",
    "La Nuit du Crime de Delémont — Une Affaire Classée",
    "L'Énigme de la Ferme Abandonnée — Rubigen, 1987",
    "Le Serpent de Porrentruy — Un Escroc Tombé du Ciel",
    "L'Affaire du Col de la Vue des Alpes — Trafic d'Influence",
    "La Disparition de la Gare de Bâle — Sans Laisser de Traces",
    "Le Cimetière des Oubliés — Fosse Commune dans le Jura",
    "L'Affaire des Trois Pendus — Coïncidence ou Tueur en Série ?",
    "Le Réseau de la Bernina — Trafic International dans les Alpes",
    "La Veuve Noire de Neuchâtel — Trois Maris, Trois Morts",
    "L'Incendie du Chalet — Une Famille Disparue dans les Flammes",
    "Le Fantôme du Crêt-du-Locle — Légende ou Crime Parfait ?",
    "L'Affaire des Écoutes de la Place — Scandale d'Espionnage",
    "Le Tueur à la Corde — Meurtres en Série dans le Jura Bernois",
    "La Disparue du Lac de Joux — Noyade ou Assassinat ?",
    "L'Affaire du Notaire de Saignelégier — Héritage et Trahison",
    "Les Oubliés de la Douane — Contrebande et Silence d'État",
    "Le Crime du Presbytère — Un Prêtre, un Secret, un Meurtre",
    "L'Affaire du Courtier en Vins — Escroquerie et Disparition",
    "Les Nuits de la Saint-Jean — Rituels et Disparitions",
    "Le Tueur de l'Horloge — Meurtres en Série en Suisse Alémanique",
    "La Disparition du Train de Nuit — Genève-Zurich, 1995",
    "L'Affaire des Enfants du Mont-Tendre — Une Secte dans le Jura",
    "Le Parfumeur de la Rue des Terreaux — Meurtre au Marché de Noël",
    "La Banque des Secrets — Scandale Financier et Mort Mystérieuse",
    "Les Ombres du Château de Joux — Prisons et Évasions",
    "L'Affaire du Glacier — Corps Retrouvé 50 Ans Plus Tard",
]


# ── Données narratives ──
LIEUX = [
    "un village du Jura suisse", "une petite ville de l'Arc jurassien",
    "un hameau perdu dans les montagnes neuchâteloises",
    "la banlieue tranquille de La Chaux-de-Fonds",
    "une commune du Jura bernois", "la vallée de Joux",
    "les rives du lac de Neuchâtel", "une zone industrielle de Bâle",
    "un quartier résidentiel de Delémont", "la vieille ville de Porrentruy",
    "un chalet isolé sur les hauteurs du Jura",
    "un hôtel désaffecté de la région des Franches-Montagnes",
    "les rues pavées de Neuchâtel", "la périphérie de Bienne",
    "un village viticole du canton de Vaud",
]

VICTIMES = [
    "Marc Dupuis", "Sophie Berger", "Hans Müller", "Marie-Claire Dubois",
    "Pierre-André Favre", "Elisabeth Koller", "Jean-Luc Charrière",
    "Catherine Monnet", "Thomas Wenger", "Isabelle Girard",
    "Frédéric Kuonen", "Nathalie Glauser", "Daniel Bregy", "Sandra Python",
    "Bernard Rossier", "Monique Theytaz", "Georges Grandjean",
]

PROFESSIONS = [
    "agriculteur", "commerçant", "banquier", "institutrice", "médecin",
    "horloger", "notaire", "artisan", "infirmière", "avocat",
    "petit entrepreneur", "fonctionnaire", "architecte", "bijoutier",
    "professeur de musique", "bibliothécaire", "journaliste",
]

DESCRIPTIONS = [
    "un homme discret, presque invisible",
    "une femme que tout le monde appréciait",
    "un solitaire au grand cœur",
    "quelqu'un qui ne faisait pas de vagues",
    "un personnage haut en couleur",
    "un homme d'affaires respecté",
    "une mère de famille dévouée",
    "un retraité paisible",
    "un jeune homme prometteur",
    "une femme indépendante et secrète",
    "un père de famille exemplaire",
    "une artiste talentueuse mais tourmentée",
]

REBONDISSEMENTS = [
    "un second corps a été découvert à cinq kilomètres du premier",
    "une lettre anonyme est arrivée au commissariat, trois ans après les faits",
    "l'ADN a révélé que la victime n'était pas celle que l'on croyait",
    "un témoin s'est finalement présenté, après des années de silence",
    "les relevés téléphoniques ont montré un appel passé à 4h du matin",
    "la victime avait changé d'identité six mois avant sa mort",
    "une caméra de surveillance oubliée par tous avait tout filmé",
    "le principal suspect avait un alibi en béton, mais ce n'était pas le bon",
    "l'assurance-vie avait été souscrite la veille du meurtre",
    "le corps portait une marque que seule la famille pouvait connaître",
    "un relevé bancaire a révélé des transactions impossibles",
    "les empreintes digitales ne correspondent à aucun fichier connu",
]

QUESTIONS_FINALES = [
    "le crime parfait existe-t-il vraiment ?",
    "peut-on vraiment connaître ceux qui vivent à côté de chez nous ?",
    "jusqu'où peut aller la soif de vengeance ?",
    "quand la justice échoue, qui reste-t-il pour punir ?",
    "la vérité rend-elle toujours libre, ou parfois prisonnier ?",
    "certains mystères méritent-ils de rester enfouis ?",
    "que reste-t-il de nous quand on a tout perdu ?",
    "le mal peut-il vraiment se cacher derrière un visage ordinaire ?",
]


# ── Sections narratives étendues ──
def gen_accroche():
    return random.choice([
        "Il est des nuits qui ne s'oublient jamais. Des nuits où le silence pèse plus lourd que tous les mots. Des nuits où le destin bascule sans prévenir, et où rien, plus jamais, ne sera comme avant.",
        "Quand la police a reçu l'appel, il était exactement 3h17 du matin. À cette heure-là, les appels ne sont jamais de bonnes nouvelles. Mais personne n'imaginait encore à quel point cette nuit allait marquer l'histoire judiciaire du canton.",
        "Certaines affaires commencent par un corps. D'autres par une absence. Celle-ci commence par un silence. Un silence si profond, si complet, qu'il a mis des jours à être remarqué. Et quand on a enfin compris, il était trop tard.",
        "Le dossier était classé depuis vingt-trois ans. Poussiéreux, oublié, rangé tout en bas d'une armoire métallique dans les sous-sols du palais de justice. Jusqu'à ce qu'un jeune inspecteur, curieux, décide de l'ouvrir. Ce qu'il a découvert l'a glacé.",
        "On dit que la vérité finit toujours par éclater. Mais parfois, elle met des décennies à sortir de l'ombre. Parfois, elle ne sort jamais. Et parfois, ceux qui la cherchent auraient mieux fait de la laisser enterrée.",
    ])


def gen_contexte(annee, lieu, saison):
    return random.choice([
        f"{annee}. {lieu}. Un endroit où tout le monde se connaît, où les portes ne ferment pas à clé, où les voisins se saluent dans la rue. Le genre de village où il ne se passe jamais rien. Jusqu'à ce jour.",
        f"Les faits remontent à {annee}. {lieu} n'était pas encore ce qu'elle est devenue aujourd'hui. Une petite communauté tranquille, sans histoire, où le taux de criminalité se limitait à quelques larcins et une ou deux bagarres du samedi soir. Jusqu'à cette affaire.",
        f"C'était un {saison} comme les autres à {lieu}. Les gens vaquaient à leurs occupations, insouciants. Les enfants jouaient dans les rues, les marchés battaient leur plein. Personne ne se doutait que le pire était à venir.",
        f"{lieu}, {annee}. La région était connue pour ses paysages à couper le souffle, ses forêts profondes et ses lacs d'émeraude. Pas pour ses crimes. Pourtant, cette année-là, tout a basculé. Et les habitants comprendraient vite que le mal peut frapper n'importe où.",
    ])


def gen_personnage(victime, age, profession, description):
    return random.choice([
        f"La victime s'appelait {victime}. {age} ans, {profession} de son état. {description}. Le genre de personne qu'on croise tous les jours dans la rue sans vraiment la voir. Rien ne laissait présager un tel destin.",
        f"{victime} était {description}. Voisins, collègues, famille : tous disaient la même chose. Un homme sans histoire, une vie sans éclat. Et pourtant, quelqu'un en avait décidé autrement. La question est : pourquoi ?",
        f"Qui était vraiment {victime} ? Derrière les apparences d'une vie ordinaire se cachait {description}. Un détail que les enquêteurs allaient mettre des semaines à découvrir. Un détail qui allait tout changer.",
        f"À {age} ans, {victime} menait une vie que beaucoup auraient pu envier. {profession}, respecté, apprécié de tous. {description}. Mais derrière cette façade lisse, des fissures commençaient à apparaître. Des fissures que quelqu'un a su exploiter.",
    ])


def gen_enquete():
    return random.choice([
        "Les enquêteurs ont rapidement compris qu'ils ne faisaient pas face à un crime ordinaire. Les indices ne collaient pas. Le mobile n'existait pas. L'arme du crime restait introuvable. Chaque piste explorée les menait à une impasse. Comme si le meurtrier avait tout prévu, tout calculé, jusqu'au moindre détail.",
        "La police a passé des semaines à explorer toutes les pistes. Des dizaines de témoins entendus, des centaines d'heures de vidéosurveillance passées au crible, des relevés d'empreintes dans tout le périmètre. Chaque fois qu'elle croyait toucher au but, le fil se brisait. Et le temps passait.",
        "Ce qui a frappé les enquêteurs, dès les premières heures, c'est l'absence de logique. Dans un crime, tout a une raison. L'argent, la passion, la vengeance. Ici, rien. Pas de mobile apparent. Pas de suspect évident. Pas de témoin. Le vide absolu.",
        "L'autopsie a révélé l'inimaginable. Ce n'était pas un crime passionnel, ni un vol qui a mal tourné. C'était autre chose. Quelque chose de froid, de méthodique, de calculé. Le médecin légiste a noté des détails qui ne collaient pas avec un crime impulsif. Le meurtrier connaissait son métier.",
    ])


def gen_rebondissement(rebondissement):
    return random.choice([
        f"Mais l'affaire a pris un tournant inattendu quand {rebondissement}. La police pensait tenir la vérité. Elle n'avait encore rien vu. Ce rebondissement allait relancer l'enquête de façon spectaculaire.",
        f"Tout a basculé le jour où {rebondissement}. Un détail que tout le monde avait négligé, enterré sous des tonnes de paperasse. Une pièce du puzzle qui ne collait pas, et que personne n'avait voulu voir. Jusqu'à ce jour.",
        f"C'est là que l'enquête a pris une direction complètement inattendue : {rebondissement}. Les policiers ont dû tout revoir, tout remettre en question. Leurs certitudes, leurs hypothèses, leur compréhension même de l'affaire. Tout volait en éclats.",
        f"Et puis, il y a eu {rebondissement}. Un élément qui allait faire voler en éclats toutes les certitudes. Les enquêteurs ont compris qu'ils s'étaient trompés dès le début. Qu'ils avaient cherché au mauvais endroit, dans la mauvaise direction. Il fallait tout reprendre à zéro.",
    ])


def gen_climax(lieu, duree):
    return random.choice([
        f"Le procès a duré {duree}. Les jurés ont entendu des témoignages qui ont glacé la salle d'audience. Des experts, des témoins, des proches. Chaque jour apportait son lot de révélations. Mais la vérité, elle, restait insaisissable, comme une ombre qui glisse entre les doigts.",
        f"Après des mois d'enquête acharnée, la vérité a éclaté au grand jour. Elle était plus terrible que tout ce qu'on avait imaginé. Plus complexe, plus sombre, plus humaine. Dans le box des accusés, l'homme semblait presque ordinaire. Presque.",
        f"Le dénouement a eu lieu là où personne ne l'attendait. {lieu}. Le lieu du crime était aussi le lieu de la vérité. Une ultime perquisition, un dernier témoignage, et tout s'est mis en place. Comme les pièces d'un puzzle que personne n'avait su assembler.",
        f"La salle d'audience retenait son souffle. Le verdict allait tomber. {duree} de procédures, de débats, de confrontations. Tout cela pour arriver à ce moment précis. Le juge a prononcé les mots que personne n'attendait. Et dans le public, quelqu'un a pleuré.",
    ])


def gen_conclusion(affaire, nb_ans, lieu, question_finale):
    return random.choice([
        f"Aujourd'hui, l'affaire {affaire} reste l'une des plus troublantes du canton. {nb_ans} ans après, des questions demeurent sans réponse. Des doutes subsistent. Et la question que tout le monde se pose est : {question_finale}",
        f"Le dossier est clos. Mais pour ceux qui ont vécu cette affaire de près, la cicatrice ne s'est jamais refermée. {nb_ans} ans plus tard, certains habitants de {lieu} évitent encore de passer devant la maison. La mémoire est plus longue que la justice.",
        f"La justice a rendu son verdict. Mais la vraie question, celle qui hante encore les enquêteurs et les proches, est : {question_finale} Un mystère qui restera peut-être à jamais sans réponse.",
        f"Les archives disent que l'affaire est résolue. Les habitants, eux, ne sont pas si sûrs. {nb_ans} ans après, les nuits d'hiver, certains jurent encore voir une lumière à la fenêtre. Une ombre qui se déplace. La vérité a-t-elle vraiment été découverte ? {question_finale}",
    ])


def gen_image(description):
    return f"[IMAGE: {description}]"


def generate_script(topic: str = None) -> tuple:
    """Génère un script true crime de 1200-1500 mots."""
    if not topic:
        topic = random.choice(SUJETS)
    
    # Générer les variables narratives
    annee = random.randint(1970, 2015)
    lieu = random.choice(LIEUX)
    victime = random.choice(VICTIMES)
    age = random.randint(22, 67)
    profession = random.choice(PROFESSIONS)
    description = random.choice(DESCRIPTIONS)
    rebondissement = random.choice(REBONDISSEMENTS)
    nb_ans = datetime.now().year - annee
    duree = f"{random.randint(3, 18)} mois" if random.random() > 0.3 else f"{random.randint(1, 5)} ans"
    saison = random.choice(["printemps", "été", "automne", "hiver"])
    question_finale = random.choice(QUESTIONS_FINALES)
    
    # Construire les sections
    sections = []
    
    heures = [f"{h}h{random.choice(['00','15','30','45'])}" for h in [random.randint(6,10), random.randint(12,14), random.randint(17,20), random.randint(21,23)]]
    lieu_rencontre = random.choice(["la sortie du village", "l'arrêt de bus", "le café du centre", "la poste", "le parking du supermarché", "la gare", "le bureau de tabac", "le pont de la rivière"])
    
    # === ACTE I : L'AVANT (3-4 min) ===
    sections.append(gen_image(f"Rue sombre sous la pluie, réverbères qui clignotent, ambiance nocturne, film noir"))
    sections.append(gen_accroche())
    sections.append("")
    
    sections.append(gen_image(f"{lieu}, paysage du Jura suisse, brume matinale, forêts, lacs"))
    sections.append(gen_contexte(annee, lieu, saison))
    sections.append("")
    
    sections.append(gen_image(f"Portrait de {victime}, photo d'identité, cadre doré, ambiance années {annee}"))
    sections.append(gen_personnage(victime, age, profession, description))
    sections.append("")
    
    sections.append(gen_image(f"Portrait de famille, album photo, souvenirs, maison de {victime}, intérieur chaleureux"))
    sections.append(f"Les proches de {victime.split()[0]} décrivent une personne attachée à ses habitudes. Chaque matin, le même rituel : lever à {heures[0]}, petit-déjeuner, puis départ pour le travail. {profession} depuis {random.randint(8, 30)} ans. Des collègues discrets, des voisins serviables. Rien qui ne sorte de l'ordinaire. Et c'est précisément cela qui rend sa disparition si troublante. Quand des gens bien comme il faut disparaissent, c'est que quelque chose a terriblement mal tourné.")
    sections.append("")
    
    # === ACTE II : LA DISPARITION (3-4 min) ===
    sections.append(gen_image(f"Scène de crime, ruban jaune, forêt dense, lampes torches, nuit"))
    sections.append(f"Ce jour-là, {victime.split()[0]} a été vu pour la dernière fois. C'était un {random.choice(['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi'])} {random.choice(['ordinaire', 'comme les autres', 'banal', 'sans particularité'])}. Un témoin l'a croisé vers {heures[1]} à {lieu_rencontre}. Il semblait normal, peut-être un peu pressé. Rien dans son comportement ne laissait penser que quelque chose n'allait pas. Ce serait la dernière fois que quelqu'un le voyait vivant.")
    sections.append("")
    
    sections.append(gen_image(f"Téléphone qui sonne dans un commissariat vide, nuit, éclairage au néon"))
    sections.append(f"C'est un proche qui a donné l'alerte. {victime.split()[0]} ne s'est pas présenté à un rendez-vous, n'a pas répondu aux appels. La première réaction des policiers, c'est l'attentisme. Les adultes disparaissent parfois volontairement, disent-ils. Mais les proches insistent. {victime.split()[0]} n'est pas du genre à partir sans prévenir. Jamais.")
    sections.append("")
    
    sections.append(gen_image(f"Bureau d'enquêteur, dossier étalé, café froid, lampes de bureau, nuit"))
    sections.append(gen_enquete())
    sections.append("")
    
    sections.append(gen_image(f"Interrogatoire, salle vide, table métallique, lumière crue"))
    sections.append(f"Les policiers ont interrogé des dizaines de personnes. La famille, les collègues, les voisins, les commerçants du quartier. Chaque témoignage apportait son lot d'informations, mais rien qui ne permettait de progresser. {victime.split()[0]} était quelqu'un de bien, disaient-ils tous. Un homme sans histoire. Et c'était bien là le problème.")
    sections.append("")
    
    sections.append(gen_image(f"Horloge qui tourne, aiguilles qui s'affolent, salle d'interrogatoire vide"))
    sections.append(gen_rebondissement(rebondissement))
    sections.append("")
    
    sections.append(gen_image(f"Tableau d'enquête, photos reliées par des fils rouges, épingles, indices"))
    sections.append(f"Les semaines ont passé. Les mois. L'affaire commençait à refroidir, comme une braise que plus personne n'alimente. Les médias en parlaient moins. Les enquêteurs étaient épuisés, frustrés, à bout. Et puis, un matin, un appel. Une voix au bout du fil. Un témoin qui n'avait pas parlé jusque-là, par peur, par oubli, par indifférence peut-être. Et tout a recommencé.")
    sections.append("")
    
    sections.append(gen_image(f"Cimetière sous la pluie, pierres tombales, silhouette solitaire, ambiance mélancolique"))
    sections.append(f"Le nouveau témoignage relançait l'enquête sur des bases totalement différentes. Ce n'était plus un crime crapuleux, ni un différend personnel. C'était plus profond, plus ancien, plus sombre. Les enquêteurs ont dû remonter le fil du passé de {victime.split()[0]}, explorer des zones d'ombre que personne n'avait envisagées. Et plus ils creusaient, plus le portrait se complexifiait.")
    sections.append("")
    
    sections.append(gen_image(f"Lettre anonyme, papier jauni, écriture tremblée, enveloppe timbrée, mystère"))
    sections.append(f"Un détail en particulier a retenu l'attention des enquêteurs. {victime.split()[0]} avait reçu plusieurs lettres anonymes dans les mois précédant sa disparition. Des lettres que les proches avaient écartées, les jugeant sans importance. Mais après relecture, elles prenaient un sens nouveau, inquiétant. Quelqu'un avait voulu faire peur à {victime.split()[0]}. Quelqu'un qui connaissait ses habitudes, ses horaires, ses faiblesses.")
    sections.append("")
    
    sections.append(gen_image(f"Scène de nuit, lampes torches dans les bois, enquêteurs en combinaison, brouillard"))
    sections.append(f"Il a fallu organiser des battues. Des dizaines de bénévoles, des chiens renifleurs, un hélicoptère. Les forêts du Jura ont été passées au peigne fin, mètre par mètre. Les lacs ont été sondés. Les grottes explorées. Rien. Comme si la terre avait avalé {victime.split()[0]} sans laisser de trace. Les semaines passaient, et l'espoir s'amenuisait.")
    sections.append("")
    
    sections.append(gen_image(f"Bureau de juge, livres de droit, balance de justice, lumière tamisée, paperasse"))
    sections.append(f"Du côté de la justice, le dossier prenait une ampleur inattendue. Le juge d'instruction avait été saisi, les moyens débloqués. Des experts en criminologie étaient appelés en renfort. Le profil de la victime était passé au crible : ses comptes bancaires, ses appels téléphoniques, ses déplacements, ses relations. Rien n'était laissé au hasard. Et pourtant, l'étau peinait à se resserrer. Le ou les coupables semblaient avoir une longueur d'avance, comme s'ils connaissaient parfaitement les méthodes d'enquête.")
    sections.append("")
    
    # === ACTE III : LA VÉRITÉ (3-4 min) ===
    sections.append(gen_image(f"Salle d'audience, bois sombre, lumière tamisée, bancs vides, silence"))
    sections.append(f"Le parquet a décidé de rouvrir le dossier. De nouveaux moyens, de nouvelles méthodes. Les progrès de la science, l'ADN, les analyses téléphoniques, la géolocalisation. Tout ce qui n'existait pas au moment des faits allait peut-être permettre de faire la lumière sur cette affaire. Les avocats des parties civiles, eux, retenaient leur souffle. Après tant d'années, la vérité allait-elle enfin éclater ?")
    sections.append("")
    
    sections.append(gen_image(f"Palais de justice, façade imposante, ciel gris, jour d'hiver, foule"))
    sections.append(gen_climax(lieu, duree))
    sections.append("")
    
    sections.append(gen_image(f"Portrait de {victime}, encadré, bougie, hommage, intérieur feutré"))
    sections.append(f"Ce qui s'est joué dans ce procès, c'est bien plus que la culpabilité d'un accusé. C'est la question de savoir si la justice peut vraiment réparer l'irréparable. {nb_ans} ans après les faits, les proches de {victime.split()[0]} attendent toujours des réponses. Et le verdict, quel qu'il soit, ne leur rendra jamais ce qu'ils ont perdu.")
    sections.append("")
    
    sections.append(gen_image(f"Crépuscule sur {lieu}, dernières lueurs du jour, silence, campagne"))
    sections.append(gen_conclusion(topic, nb_ans, lieu, question_finale))
    sections.append("")
    
    sections.append(gen_image(f"Fermeture de dossier, étiquette 'Classé', poussière, lumière rasante, fin"))
    sections.append("")
    
    # Assembler
    script = "\n".join(sections)
    
    return topic, script


def save_script(topic: str, script: str) -> str:
    """Sauvegarde le script dans output/scripts/."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    date = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = re.sub(r'[^\w\s-]', '', topic)[:40].strip()
    filename = f"{date}_{safe_topic}.txt"
    path = f"{base}/output/scripts/{filename}"

    metadata = f"""TITLE: {topic}
DATE: {datetime.now().strftime('%Y-%m-%d %H:%M')}
STATUS: draft
GENRE: true_crime
MODE: template_long
---
"""
    with open(path, "w") as f:
        f.write(metadata + script)

    print(f"📝 Script sauvegardé : {path}")
    return path


if __name__ == "__main__":
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else None
    topic, script = generate_script(topic)
    word_count = len(script.split())
    est_duration = word_count / 150  # ~150 mots/min
    print("\n" + "="*60)
    print(f"📜 {topic}")
    print("="*60)
    print(script)
    print("="*60)
    path = save_script(topic, script)
    print(f"\n✔ Script prêt : {path}")
    print(f"📝 {word_count} mots, ~{est_duration:.0f} min de vidéo")