import os
import requests
from bs4 import BeautifulSoup

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
        print(f"Errore invio: {e}")

def controlla_offerte():
    print("Controllo offerte Surface in corso...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        risposta = requests.get(URL_RICERCA, headers=headers, timeout=15)
        if risposta.status_code == 200:
            soup = BeautifulSoup(risposta.text, 'html.parser')
            
            # Cerchiamo tutti i possibili contenitori di annunci di eBay
            annunci = soup.find_all('div', class_='s-item__info') or soup.find_all('li', class_='s-item')
            
            trovato = False
            for annuncio in annunci:
                # Sistema di estrazione flessibile per i titoli
                titolo_elem = annuncio.find('span', role='heading') or annuncio.find('div', class_='s-item__title')
                prezzo_elem = annuncio.find('span', class_='s-item__price')
                link_elem = annuncio.find('a', class_='s-item__link')
                
                if titolo_elem and prezzo_elem and link_elem:
                    titolo = titolo_elem.text
                    prezzo = prezzo_elem.text
                    link = link_elem['href']
                    
                    # Filtri di pulizia avanzati per saltare gli accessori
                    titolo_low = titolo.lower()
                    if "shop on ebay" in titolo_low or "immagine" in titolo_low:
                        continue
                    if "solo tastiera" in titolo_low or "pellicola" in titolo_low or "caricabatterie" in titolo_low:
                        continue
                    if "tastiera" in titolo_low and "surface pro" not in titolo_low:
                        continue
                        
                    msg = f"💻 *SURFACE TROVATO (Filtro Attivo)* 💻\n\n*Modello:* {titolo}\n*Prezzo:* {prezzo}\n[Vedi Annuncio]({link})"
                    invia_notifica(msg)
                    print(f"Inviato con successo: {titolo} a {prezzo}")
                    trovato = True
                    break  # Ci fermiamo al primo annuncio valido trovato nella lista
            
            if not trovato:
                print("Nessun annuncio valido filtrato nei risultati analizzati.")
        else:
            print(f"Errore connessione: {risposta.status_code}")
    except Exception as e:
        print(f"Errore generale: {e}")

if __name__ == "__main__":
    controlla_offerte()
