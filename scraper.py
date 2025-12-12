import requests
from bs4 import BeautifulSoup
import json
import re

# --- CONFIGURATION MISE A JOUR ---
# Le lien exact que tu m'as donné
PATCH_VERSION = "25-22"
URL = f"https://www.leagueoflegends.com/fr-fr/news/game-updates/patch-{PATCH_VERSION}-notes/"

HEADERS = {
    # User Agent mis à jour pour 2025 pour éviter d'être bloqué
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
}

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def scrape_patch_notes(url):
    print(f"🔄 Connexion au Patch 25.24 : {url}")
    
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Erreur critique : {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # DEBUG : Vérifions le titre pour être sûr qu'on est sur la bonne page
    print(f"📄 Titre détecté : {soup.title.string if soup.title else 'Pas de titre'}")

    # STRATÉGIE AGRESSIVE : 
    # Au lieu de chercher un conteneur 'div' précis qui change tout le temps,
    # on cherche le noeud <article>. Si pas là, on cherche le conteneur principal par contenu.
    
    content_root = soup.find('article')
    
    if not content_root:
        # Fallback : On cherche la div qui contient le mot "Champions" dans un H2
        # C'est souvent le point d'ancrage le plus fiable.
        print("⚠️ Balise <article> non trouvée, recherche par contenu...")
        h2_champions = soup.find('h2', string=re.compile(r'Champions', re.IGNORECASE))
        if h2_champions:
            # On remonte au parent qui contient tout le patch
            content_root = h2_champions.find_parent('div')
        else:
            # Dernier recours : on prend le conteneur principal de style Riot
            content_root = soup.find('div', class_=re.compile(r'style__Wrapper'))

    if not content_root:
        print("❌ ECHEC : Impossible de localiser le texte du patch. Riot a peut-être changé le rendu (React/JS).")
        # DEBUG AVANCE : Afficher les classes des divs pour comprendre
        divs = soup.find_all('div', class_=True)
        print(f"   (Info Debug : {len(divs)} divs trouvées sur la page. Le site charge peut-être en JS pur.)")
        return []

    print("✅ Contenu localisé. Extraction des données...")

    chunks = []
    current_section = "Intro / Systèmes"
    current_content = []
    
    # On capture tout ce qui est pertinent
    tags = content_root.find_all(['h2', 'h3', 'h4', 'p', 'li'])

    for element in tags:
        text = clean_text(element.get_text())
        if not text: continue
        
        # Ignorer les textes de navigation (Skins, Retour en haut, etc)
        if text.lower() in ["retour en haut", "sommaire", "partager"]:
            continue

        tag_name = element.name

        # DÉTECTION : Si c'est un gros titre (H2) ou un nom de perso (H3)
        if tag_name in ['h2', 'h3']:
            # On clôture la section précédente
            if current_content:
                full_text = " ".join(current_content)
                if len(full_text) > 20: # Filtre le bruit
                    chunks.append({
                        "patch_version": PATCH_VERSION,
                        "entity": current_section,
                        "content": full_text,
                        "url": url
                    })
            
            # Nouvelle section
            current_section = text
            current_content = []
        else:
            current_content.append(text)

    # Sauvegarder la fin
    if current_content:
        chunks.append({
            "patch_version": PATCH_VERSION,
            "entity": current_section,
            "content": " ".join(current_content),
            "url": url
        })

    print(f"🎉 Succès ! {len(chunks)} sections extraites.")
    return chunks

if __name__ == "__main__":
    data = scrape_patch_notes(URL)
    
    if data:
        filename = f"patches_json/patch_{PATCH_VERSION}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"💾 Fichier créé : {filename}")