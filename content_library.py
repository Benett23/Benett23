"""
Bibliothèque de versets bibliques et prières chrétiennes.
Organisée par thèmes pour la sélection thématique ou aléatoire.
"""

import random
from dataclasses import dataclass

THEMES = ["foi", "espoir", "amour", "paix", "force", "grâce", "louange", "guérison"]


@dataclass
class Verse:
    text: str
    reference: str
    theme: str


@dataclass
class Prayer:
    title: str
    text: str
    theme: str


VERSES: list[Verse] = [
    # Foi
    Verse(
        "Car c'est par la grâce que vous êtes sauvés, par le moyen de la foi. "
        "Et cela ne vient pas de vous, c'est le don de Dieu.",
        "Éphésiens 2:8",
        "foi",
    ),
    Verse(
        "La foi est une ferme assurance des choses qu'on espère, "
        "une démonstration de celles qu'on ne voit pas.",
        "Hébreux 11:1",
        "foi",
    ),
    Verse(
        "Jésus lui dit : Si tu peux croire, tout est possible à celui qui croit.",
        "Marc 9:23",
        "foi",
    ),
    Verse(
        "En effet, nous marchons par la foi et non par la vue.",
        "2 Corinthiens 5:7",
        "foi",
    ),
    # Espoir
    Verse(
        "Car je connais les projets que j'ai formés sur vous, dit l'Éternel, "
        "projets de paix et non de malheur, afin de vous donner un avenir et de l'espérance.",
        "Jérémie 29:11",
        "espoir",
    ),
    Verse(
        "Que le Dieu de l'espérance vous remplisse de toute joie et de toute paix "
        "dans la foi, pour que vous abondiez en espérance par la puissance du Saint-Esprit.",
        "Romains 15:13",
        "espoir",
    ),
    Verse(
        "L'Éternel est bon pour celui qui espère en lui, pour l'âme qui le cherche.",
        "Lamentations 3:25",
        "espoir",
    ),
    # Amour
    Verse(
        "Car Dieu a tant aimé le monde qu'il a donné son Fils unique, "
        "afin que quiconque croit en lui ne périsse point, mais qu'il ait la vie éternelle.",
        "Jean 3:16",
        "amour",
    ),
    Verse(
        "L'amour est patient, il est plein de bonté ; l'amour n'est point envieux ; "
        "l'amour ne se vante point, il ne s'enfle point d'orgueil.",
        "1 Corinthiens 13:4",
        "amour",
    ),
    Verse(
        "Nous l'aimons, parce qu'il nous a aimés le premier.",
        "1 Jean 4:19",
        "amour",
    ),
    Verse(
        "Aimez-vous les uns les autres ; comme je vous ai aimés, vous aussi, "
        "aimez-vous les uns les autres.",
        "Jean 13:34",
        "amour",
    ),
    # Paix
    Verse(
        "Je vous laisse la paix, je vous donne ma paix. "
        "Je ne vous donne pas comme le monde donne. "
        "Que votre cœur ne se trouble point, et ne s'alarme point.",
        "Jean 14:27",
        "paix",
    ),
    Verse(
        "Et la paix de Dieu, qui surpasse toute intelligence, "
        "gardera vos cœurs et vos pensées en Jésus-Christ.",
        "Philippiens 4:7",
        "paix",
    ),
    Verse(
        "L'Éternel est mon berger : je ne manquerai de rien. "
        "Il me fait reposer dans de verts pâturages.",
        "Psaume 23:1-2",
        "paix",
    ),
    # Force
    Verse(
        "Je puis tout par celui qui me fortifie.",
        "Philippiens 4:13",
        "force",
    ),
    Verse(
        "Il donne de la force à celui qui est fatigué, "
        "et il augmente la vigueur de celui qui tombe en défaillance.",
        "Ésaïe 40:29",
        "force",
    ),
    Verse(
        "Sois fort et courageux. Ne crains point et ne t'épouvante point, "
        "car l'Éternel, ton Dieu, est avec toi dans tout ce que tu entreprendras.",
        "Josué 1:9",
        "force",
    ),
    Verse(
        "L'Éternel est ma lumière et mon salut : de qui aurais-je crainte ?",
        "Psaume 27:1",
        "force",
    ),
    # Grâce
    Verse(
        "Ma grâce te suffit, car ma puissance s'accomplit dans la faiblesse.",
        "2 Corinthiens 12:9",
        "grâce",
    ),
    Verse(
        "Approchons-nous donc avec assurance du trône de la grâce, "
        "afin d'obtenir miséricorde et de trouver grâce, "
        "pour être secourus dans nos besoins.",
        "Hébreux 4:16",
        "grâce",
    ),
    # Louange
    Verse(
        "Louez l'Éternel ! Louez Dieu dans son sanctuaire ! "
        "Louez-le dans l'étendue, où éclate sa puissance !",
        "Psaume 150:1",
        "louange",
    ),
    Verse(
        "Réjouissez-vous toujours dans le Seigneur ; je le répète, réjouissez-vous.",
        "Philippiens 4:4",
        "louange",
    ),
    Verse(
        "Chantez à l'Éternel un cantique nouveau ! "
        "Car il a fait des merveilles.",
        "Psaume 98:1",
        "louange",
    ),
    # Guérison
    Verse(
        "L'Éternel est mon berger ; il guérit tous mes maux.",
        "Psaume 103:3",
        "guérison",
    ),
    Verse(
        "Mais lui, il était blessé pour nos péchés, "
        "brisé pour nos iniquités ; "
        "le châtiment qui nous donne la paix est tombé sur lui, "
        "et c'est par ses meurtrissures que nous sommes guéris.",
        "Ésaïe 53:5",
        "guérison",
    ),
    Verse(
        "Le Seigneur l'a relevé, et s'il a commis des péchés, "
        "ils lui seront pardonnés.",
        "Jacques 5:15",
        "guérison",
    ),
]


PRAYERS: list[Prayer] = [
    Prayer(
        title="Prière du matin",
        text=(
            "Seigneur, en ce nouveau jour que tu m'accordes, "
            "je te loue pour ta fidélité et ta grâce. "
            "Guide mes pas, éclaire mon chemin, "
            "et que tout ce que je fasse aujourd'hui "
            "soit à ta gloire. Amen."
        ),
        theme="louange",
    ),
    Prayer(
        title="Prière pour la paix",
        text=(
            "Père céleste, tu es le Prince de la Paix. "
            "Accorde-moi ta paix qui surpasse tout entendement. "
            "Que mon cœur ne soit pas troublé, "
            "que j'aie confiance en toi en toutes circonstances. "
            "Merci pour ta présence constante. Amen."
        ),
        theme="paix",
    ),
    Prayer(
        title="Prière de foi",
        text=(
            "Seigneur Jésus, augmente ma foi. "
            "Quand je doute, rappelle-moi que tu es fidèle. "
            "Aide-moi à te faire confiance de tout mon cœur "
            "et à ne pas m'appuyer sur ma propre intelligence. Amen."
        ),
        theme="foi",
    ),
    Prayer(
        title="Prière de force",
        text=(
            "Dieu Tout-Puissant, je suis faible, mais tu es fort. "
            "Renouvelle mes forces comme celles de l'aigle. "
            "Dans chaque épreuve, rappelle-moi que je puis tout "
            "par Celui qui me fortifie. Amen."
        ),
        theme="force",
    ),
    Prayer(
        title="Prière d'amour",
        text=(
            "Père, tu es amour. "
            "Remplis mon cœur de ton amour afin que je puisse "
            "aimer mon prochain comme tu m'as aimé. "
            "Que ta charité soit parfaite en moi. Amen."
        ),
        theme="amour",
    ),
    Prayer(
        title="Prière d'espoir",
        text=(
            "Seigneur, quand l'obscurité m'entoure, "
            "tu es ma lumière et mon espérance. "
            "Rappelle-moi que tu as de bons projets pour moi, "
            "un avenir et une espérance. "
            "Je place ma confiance en toi seul. Amen."
        ),
        theme="espoir",
    ),
    Prayer(
        title="Prière de guérison",
        text=(
            "Dieu guérisseur, toi qui es le même hier, aujourd'hui et éternellement, "
            "je viens à toi avec ma douleur. "
            "Pose ta main sur moi et guéris-moi "
            "selon ta volonté et ta bonté infinie. "
            "Je crois en ton pouvoir de guérison. Amen."
        ),
        theme="guérison",
    ),
    Prayer(
        title="Prière de grâce",
        text=(
            "Seigneur, je ne mérite rien, "
            "mais ta grâce est suffisante pour moi. "
            "Merci pour ton pardon, ta miséricorde renouvelée chaque matin. "
            "Aide-moi à marcher humblement avec toi. Amen."
        ),
        theme="grâce",
    ),
    Prayer(
        title="Prière de louange",
        text=(
            "Que toute ma vie soit une louange pour toi, Seigneur ! "
            "Tu es digne de tout honneur, de toute gloire. "
            "Je t'adore de tout mon cœur, de toute mon âme, "
            "de toutes mes forces. À toi soit la gloire pour toujours. Amen."
        ),
        theme="louange",
    ),
    Prayer(
        title="Prière du soir",
        text=(
            "Père, merci pour cette journée. "
            "Pardonne-moi pour mes fautes et mes manquements. "
            "Protège-moi cette nuit sous l'ombre de tes ailes. "
            "Je repose en paix, car tu veilles sur moi. Amen."
        ),
        theme="paix",
    ),
]


def get_random_verse(theme: str | None = None) -> Verse:
    """Retourne un verset aléatoire, filtré par thème si précisé."""
    pool = [v for v in VERSES if v.theme == theme] if theme else VERSES
    return random.choice(pool or VERSES)


def get_random_prayer(theme: str | None = None) -> Prayer:
    """Retourne une prière aléatoire, filtrée par thème si précisé."""
    pool = [p for p in PRAYERS if p.theme == theme] if theme else PRAYERS
    return random.choice(pool or PRAYERS)


def get_content_by_theme(theme: str) -> tuple[Verse, Prayer]:
    """Retourne un verset et une prière pour un thème donné."""
    return get_random_verse(theme), get_random_prayer(theme)
