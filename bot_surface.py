import os
import requests
from bs4 import BeautifulSoup
import re

# LINK DEFINITIVO: Categoria Tablet, Microsoft Surface Pro 7, max 500€
URL_RICERCA = "https://ebay.it"

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def invia_notifica(messaggio):
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": messaggio}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            print(f"Errore Telegram Status: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Errore invio Telegram: {e}")

def controlla_offerte():
    print("Avvio scansione profonda tramite link diretti...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        risposta = requests.get(URL_RICERCA, headers=headers, timeout=15)
        if risposta.status_code != 200:
            print(f"Errore connessione: {risposta.status_code}")
            return
            
        soup = BeautifulSoup(risposta.text, 'html.parser')
        
        # Estrazione universale tramite i link reali delle inserzioni
        links_inserzioni = soup.find_all('a', href=re.compile(r'/itm/\d+'))
        print(f"Numero di collegamenti ad annunci reali individuati: {len(links_inserzioni)}")
        
        contatore_invii = 0
        link_salvati = set()
        
        for link_elem in links_inserzioni:
            # Estrae l'indirizzo internet dell'annuncio
            link_completo = link_elem['href']
            # Pulisce l'indirizzo dai parametri di tracciamento superflui di eBay
            raw_link = link_completo.split('?')[0] if '?' in link_completo else link_completo
            
            if raw_link in link_salvati:
                continue
                
            titolo = link_elem.get_text().strip()
            
            if len(titolo) < 10:
                blocco_padre = link_elem.find_parent('div') or link_elem.find_parent('li')
                if blocco_padre:
                    titolo_box = blocco_padre.find('span', role='heading') or blocco_padre.select_one('.s-item__title')
                    if titolo_box:
                        titolo = titolo_box.get_text().strip()
            
            if titolo.lower().startswith("nuova inserzione"):
                titolo = titolo[16:].strip()
                
            titolo_low = titolo.lower()
            
            # Filtri di isolamento per evitare pubblicità o accessori vuoti
            if "shop on ebay" in titolo_low or titolo == "" or "immagine" in titolo_low or len(titolo) < 10:
                continue
            if "solo tastiera" in titolo_low or "pellicola" in titolo_low or "caricabatterie" in titolo_low:
                continue
                
            prezzo = "Vedi su eBay"
            blocco_padre = link_elem.find_parent('div') or link_elem.find_parent('li')
            if blocco_padre:
                prezzo_box = blocco_padre.find('span', class_='s-item__price') or blocco_padre.select_one('.s-item__price')
                if prezzo_box:
                    prezzo = prezzo_box.get_text().strip()
            
            link_salvati.add(raw_link)
            
            # Formattazione del testo semplificata salvando la stringa dell'indirizzo internet corretta
            msg = f"SURFACE TROVATO\n\nModello: {titolo}\nPrezzo: {prezzo}\nLink: {raw_link}"
            invia_notifica(msg)
            print(f"[{contatore_invii + 1}] Inviato con successo: {titolo}")
            
            contatore_invii += 1
            if contatore_invii >= 3:
                break
                
        if contatore_invii == 0:
            print("Nessun link ha superato i filtri di pulizia del testo.")
            
    except Exception as e:
        print(f"Errore nel motore di scansione link: {e}")

if __name__ == "__main__":
    controlla_offerte()
