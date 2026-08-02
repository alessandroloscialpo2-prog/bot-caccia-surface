import os
import requests
from bs4 import BeautifulSoup
import re

# LINK OTTIMIZZATO: Categoria Tablet, max 1500€, ordinato per i più recenti
URL_RICERCA = "https://ebay.it"

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def invia_notifica(messaggio):
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": messaggio, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
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
        
        # Tecnica universale: cerchiamo tutti i link reali alle inserzioni di oggetti su eBay
        links_inserzioni = soup.find_all('a', href=re.compile(r'/itm/\d+'))
        print(f"Numero di collegamenti ad annunci reali individuati: {len(links_inserzioni)}")
        
        contatore_invii = 0
        link_salvati = set() # Evita di inviare due volte lo stesso annuncio se duplicato nella pagina
        
        for link_elem in links_inserzioni:
            link = link_elem['href'].split('?')[0] # Pulisce il link dai codici di tracciamento
            
            if link in link_salvati:
                continue
                
            # Cerchiamo il testo del titolo dentro il tag del link o nei tag figli
            titolo = link_elem.get_text().strip()
            
            # Se il testo del link è corto o vuoto, cerchiamo l'intestazione nel blocco circostante
            if len(titolo) < 10:
                blocco_padre = link_elem.find_parent('div') or link_elem.find_parent('li')
                if blocco_padre:
                    titolo_box = blocco_padre.find('span', role='heading') or blocco_padre.select_one('.s-item__title')
                    if titolo_box:
                        titolo = titolo_box.get_text().strip()
            
            # Rimuove le diciture fisse di inserzione di eBay
            if titolo.lower().startswith("nuova inserzione"):
                titolo = titolo[16:].strip()
                
            titolo_low = titolo.lower()
            
            # Filtri di pulizia ed esclusione
            if "shop on ebay" in titolo_low or titolo == "" or "immagine" in titolo_low or len(titolo) < 10:
                continue
            if "solo tastiera" in titolo_low or "pellicola" in titolo_low or "caricabatterie" in titolo_low:
                continue
                
            # Cerca il prezzo nel blocco dell'annuncio
            prezzo = "Vedi bando"
            blocco_padre = link_elem.find_parent('div') or link_elem.find_parent('li')
            if blocco_padre:
                prezzo_box = blocco_padre.find('span', class_='s-item__price') or blocco_padre.select_one('.s-item__price')
                if prezzo_box:
                    prezzo = prezzo_box.get_text().strip()
            
            link_salvati.add(link)
            
            # Invio effettivo a Telegram
            msg = f"💻 *SURFACE TROVATO* 💻\n\n*Modello:* {titolo}\n*Prezzo:* {prezzo}\n[Vedi Annuncio]({link})"
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
