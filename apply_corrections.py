#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, sys

p = 'roman_tome1_extracted.txt'
s = open(p, encoding='utf-8').read()

def rep(old, new, count=1):
    global s
    c = s.count(old)
    if c != count:
        print(f'FAIL expected={count} found={c}: {old[:70]!r}')
        sys.exit(1)
    s = s.replace(old, new)

# ---------- 1. Residu hors-fiction entre Ch.28 et Ch.29 ----------
rep("Voici la version réécrite du Chapitre 25, nettoyée selon les conseils de votre éditeur.\n"
    "Les explications sur-exprimées ont été supprimées pour faire confiance au lecteur, le style est plus sobre, "
    "les lourdeurs de tournure ont été corrigées, et la fin s'appuie désormais sur une pure image sensorielle "
    "plutôt que sur une morale.\n", "")

# normaliser les lignes vides entre l'en-tete du Ch.29 et son sous-titre
rep("CHAPITRE 29\n\n\nUne chambre pleine de vie", "CHAPITRE 29\nUne chambre pleine de vie")

# ---------- 2. Chronologie Ch.22-23 : corrections ciblees ----------
# Ch.23 : supprimer la reference prematuree a la perte de cheveux / aux traitements
rep("Le foulard sur mon crâne. Les cernes que le fond de teint ne masque plus vraiment. "
    "Les mains, plus fines qu'avant, qui ne savent plus rester immobiles.",
    "Le foulard autour de mon cou. Les cernes que le fond de teint ne masque plus vraiment. "
    "Les mains, plus nerveuses qu'avant, qui ne savent plus rester immobiles.")
rep("Je m'attendais à une femme fatiguée, un visage creusé par les traitements, un foulard un peu de travers.",
    "Je m'attendais à une femme fatiguée, un visage creusé par l'épuisement, un foulard un peu de travers.")
# Ch.24 : le carnet donne devient un second carnet (continuite, pas une premiere fois)
rep("— Léa... qu'est-ce que c'est ?", "— Léa... tu m'en as déjà offert un.")
rep("— Je voudrais que tu aies un endroit à toi.",
    "— Celui-là est pour ce qui commence maintenant. Je voudrais que tu aies un endroit à toi pour la suite.")

# ---------- 3. Mentor : Adrien renomme Daniel ; Ch.30 corrige ----------
rep("Adrien", "Daniel", count=14)
rep("— J'ai une boutique d'herboristerie rue des Ursulines.",
    "— Je m'occupe du cercle de parole dans la boutique d'herboristerie de la rue des Ursulines.")

# ---------- 4. Boutique de Claire : nouveau local ----------
rep("Le GPS m'annonce deux minutes de trajet lorsque je reconnais la petite rue pavée "
    "où Claire a décidé d'ouvrir sa pâtisserie.",
    "Le GPS m'annonce deux minutes de trajet lorsque je reconnais la petite rue pavée "
    "où Claire vient d'installer sa pâtisserie — après des années dans son premier local, "
    "elle a signé pour cette vitrine plus grande, et l'inauguration d'aujourd'hui en est la première page.")

# ---------- 10. Ch.2 : citation du Pr Tournier ----------
rep("« cerveau laser, mais amies-distraction publique »",
    "« un cerveau laser, mais une distraction publique : ses amies »")

# ---------- 11. Espaces manquantes ----------
rep("Clic.Clac.", "Clic. Clac.")
rep("m'arrive.Mais je peux", "m'arrive. Mais je peux")
rep("chiffres.Pas de réunions.Pas de délais.", "chiffres. Pas de réunions. Pas de délais.")
rep("feuilles blanches.Des pinceaux.Des pots de peinture.Des craies grasses.De l’argile.",
    "feuilles blanches. Des pinceaux. Des pots de peinture. Des craies grasses. De l’argile.")

# ---------- 8. Renommer 2 des 3 Sophie ----------
rep("C’est Sophie, l’éducatrice.", "C’est Sonia, l’éducatrice.")
rep("Sophie hésite.", "Sonia hésite.")
rep("Lorsqu’il franchit la porte, Sophie lève les yeux.", "Lorsqu’il franchit la porte, Sonia lève les yeux.")
rep("Sophie, du service juridique, me sourit.", "Sandra, du service juridique, me sourit.")

# ---------- 9. Harmonisation des sous-titres de chapitres (format : ligne dediee) ----------
subs = [
    ("CHAPITRE 10 — LE MEILLEUR INVESTISSEMENT", "CHAPITRE 10\nLe meilleur investissement"),
    ("CHAPITRE 11 — LA REINE DU MARCHÉ", "CHAPITRE 11\nLa reine du marché"),
    ("CHAPITRE 14 — LE TOUR DE SIMON", "CHAPITRE 14\nLe tour de Simon"),
    ("CHAPITRE 18 — CEUX QUI ÉTAIENT LÀ AVANT MOI", "CHAPITRE 18\nCeux qui étaient là avant moi"),
    ("CHAPITRE 19 — Ce que je ne contrôle plus", "CHAPITRE 19\nCe que je ne contrôle plus"),
    ("Chapitre 20 — L’odeur du café", "CHAPITRE 20\nL’odeur du café"),
    ("CHAPITRE 21 — Avant que tout ne bascule", "CHAPITRE 21\nAvant que tout ne bascule"),
    ("CHAPITRE 23 — Les couleurs qui ne mentent pas", "CHAPITRE 23\nLes couleurs qui ne mentent pas"),
    ("CHAPITRE 26 — La peur dans les yeux de mon frère de bureau", "CHAPITRE 26\nLa peur dans les yeux de mon frère de bureau"),
    ("CHAPITRE 27 — Le temps autrement", "CHAPITRE 27\nLe temps autrement"),
    ("CHAPITRE 28 — Avant que tout ne s'effondre", "CHAPITRE 28\nAvant que tout ne s'effondre"),
    ("CHAPITRE 30 — Les petites rébellions", "CHAPITRE 30\nLes petites rébellions"),
    ("CHAPITRE 32 — Ce que le miroir ne cache plus", "CHAPITRE 32\nCe que le miroir ne cache plus"),
    ("CHAPITRE 33 — Là où la vie continue", "CHAPITRE 33\nLà où la vie continue"),
    ("CHAPITRE 34 — Ce qui reste", "CHAPITRE 34\nCe qui reste"),
    ("CHAPITRE 35 — Ce qu’on transmet", "CHAPITRE 35\nCe qu’on transmet"),
    ("CHAPITRE 37 — La lumière revient", "CHAPITRE 37\nLa lumière revient"),
    ("CHAPITRE 38 — Ce qui reste à vivre", "CHAPITRE 38\nCe qui reste à vivre"),
    ("CHAPITRE 39 — La vie devant moi", "CHAPITRE 39\nLa vie devant moi"),
]
for old, new in subs:
    rep(old + "\n", new + "\n")

# ---------- 6. Guillemets droits -> guillemets francais ----------
rep('Quand tu dis "intéressant", ça veut dire mauvais.',
    'Quand tu dis « intéressant », ça veut dire mauvais.')
rep('tu as dit : "C\'est une expérience culinaire intéressante."',
    'tu as dit : « C\'est une expérience culinaire intéressante. »')
rep('Quelque chose comme : "Je vais très bien, j\'ai juste besoin de travailler encore trois heures '
    'avant de préparer la réunion de demain."',
    'Quelque chose comme : « Je vais très bien, j\'ai juste besoin de travailler encore trois heures '
    'avant de préparer la réunion de demain. »')
rep('dire quelque chose comme "au printemps prochain", même approximatif',
    'dire quelque chose comme « au printemps prochain », même approximatif')
rep('c\'est parce qu\'il faut "inviter"... comme dans une facture ?',
    'c\'est parce qu\'il faut « inviter »... comme dans une facture ?')

# ---------- 5. Apostrophes droites -> apostrophes courbes ----------
n_apos = s.count("'")
s = s.replace("'", "’")

open(p, 'w', encoding='utf-8').write(s)

print("OK. apostrophes droites converties:", n_apos)
