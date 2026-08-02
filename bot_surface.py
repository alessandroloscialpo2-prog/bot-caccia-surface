import os
import requests
from bs4 import BeautifulSoup

# LINK OTTIMIZZATO: Versione che forza il layout di ricerca classico compatibile con BeautifulSoup
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
    print("Avvio scansione approfondita delle offerte...")
    
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
        
        # Cerchiamo in modo esteso tutti i contenitori di annunci possibili su eBay usando selettori alternativi
        annunci = soup.find_all('div', class_='s-item__info') or soup.select('.s-item__info') or soup.select('.s-item')
        print(f"Numero di blocchi grezzi individuati sulla pagina: {len(annunci)}")
        
        contatore_invii = 0
        
        for annuncio in annunci:
            titolo_elem = annuncio.find('span', role='heading') or annuncio.select_one('.s-item__title')
            prezzo_elem = annuncio.find('span', class_='s-item__price') or annuncio.select_one('.s-item__price')
            link_elem = annuncio.find('a', class_='s-item__link') or annuncio.select_one('.s-item__link')
            
            if not (titolo_elem and prezzo_elem and link_elem):
                continue
                
            titolo = titolo_elem.text.strip()
            prezzo = prezzo_elem.text.strip()
            link = link_elem['href']
            
            titolo_low = titolo.lower()
            
            # Filtri di esclusione
            if "shop on ebay" in titolo_low or "immagine" in titolo_low or titolo == "":
                continue
            if "solo tastiera" in titolo_low or "pellicola" in titolo_low or "caricabatterie" in titolo_low:
                continue
            if "tastiera" in titolo_low and "surface pro" not in titolo_low:
                continue
                
            msg = f"💻 *SURFACE TROVATO* 💻\n\n*Modello:* {titolo}\n*Prezzo:* {prezzo}\n[Vedi Annuncio]({link})"
            invia_notifica(msg)
            print(f"[{contatore_invii + 1}] Inviato con successo: {titolo} a {prezzo}")
            
            contatore_invii += 1
            if contatore_invii >= 3:
                break
                
        if contatore_invii == 0:
            print("La pagina conteneva blocchi HTML, ma nessuno ha superato i filtri sul testo.")
            
    except Exception as e:
        print(f"Errore generale nel ciclo: {e}")

if __name__ == "__main__":
    controlla_offerte()
