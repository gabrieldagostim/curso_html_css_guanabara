from curl_cffi import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re # Importando regex para limpar o ID
SELLER_ID = "1669967510"
BASE_URL = f"https://lista.mercadolivre.com.br/_CustId_{SELLER_ID}"
OUTPUT_FILE = "historico_concorrente.csv"

def get_html_content(url):
    print(f"🕵️  Acessando: {url}...")
    try:
        response = requests.get(
            url, 
            impersonate="chrome110",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
                "Referer": "https://www.mercadolivre.com.br/"
            },
            timeout=15
        )
        if response.status_code == 200:
            return response.text
        return None
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return None

def extract_id_from_link(link):

    if not link: return "N/A"
    try:
        # Tenta achar o padrão MLB-123456 ou MLB123456
        match = re.search(r'MLB[-]?(\d+)', link)
        if match:
            return f"MLB{match.group(1)}"
        return "N/A"
    except:
        return "N/A"

def parse_items(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    items_data = []
    
    products = soup.find_all('li', class_='ui-search-layout__item')
    
    print(f"🔍 Analisando HTML... Encontrados {len(products)} blocos de produto.")

    for product in products:
        try:
            title = "Sem Título"
            link = ""
            price = 0.0

            title_tag = product.find('a', class_='poly-component__title')
            if not title_tag:
                 title_tag = product.find('h2', class_='poly-component__title')
            
            if title_tag:
                title = title_tag.text.strip()
                link = title_tag.get('href') if title_tag.name == 'a' else product.find('a')['href']

            if title == "Sem Título":
                title_tag = product.find('h2', class_='ui-search-item__title')
                if title_tag:
                    title = title_tag.text.strip()
                    link_tag = product.find('a', class_='ui-search-link')
                    link = link_tag['href'] if link_tag else ""

            # --- PREÇO ---
            price_container = product.find('div', class_='poly-price__current')
            if not price_container:
                price_container = product.find('div', class_='ui-search-price__second-line')
            
            if price_container:
                price_fraction = price_container.find('span', class_='andes-money-amount__fraction')
                if price_fraction:
                    price = float(price_fraction.text.strip().replace('.', ''))

            # Se falhou na estratégia acima, tenta busca genérica por preço
            if price == 0.0:
                 price_fraction = product.find('span', class_='andes-money-amount__fraction')
                 if price_fraction:
                    price = float(price_fraction.text.strip().replace('.', ''))

            items_data.append({
                "date": datetime.now().date(),
                "id": extract_id_from_link(link),
                "title": title,
                "price": price,
                "permalink": link
            })
        except Exception as e:
            print(f"Erro em um item: {e}") # Descomente para debug
            continue

    return pd.DataFrame(items_data)

def main():
    html = get_html_content(BASE_URL)
    
    if html:
        df = parse_items(html)
        
        if not df.empty:
            print(f"\n✅ Sucesso! {len(df)} produtos coletados.")
            print(df[['id', 'title', 'price']].head()) # Mostra resumo
            
            # Salvar
            # Modo append (se arquivo existir, adiciona no final)
            import os
            header = not os.path.exists(OUTPUT_FILE)
            df.to_csv(OUTPUT_FILE, mode='a', header=header, index=False)
            print(f"💾 Salvo em {OUTPUT_FILE}")
        else:
            print("⚠️ Página carregada, mas a estrutura do HTML mudou completamente.")
            # Dica: Se cair aqui, salve o HTML num arquivo debug.html para ler
            with open("debug.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("Verifique o arquivo debug.html")
    else:
        print("☠️ Falha no download.")

if __name__ == "__main__":
    main()