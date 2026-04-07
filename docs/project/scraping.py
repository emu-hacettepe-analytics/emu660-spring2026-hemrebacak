import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
import re

def clean_name(name):
    name = str(name).replace('\xa0', ' ')
    return re.sub(r'\s+', ' ', name).strip()

def parse_market_value(val_str):
    if not isinstance(val_str, str):
        return 0.0
    
    val_str = str(val_str).lower().replace('€', '').replace('\xa0', ' ').strip()
    if not val_str or val_str == '-':
        return 0.0
        
    try:
        val_str = val_str.replace(',', '.')
        match = re.search(r'[\d\.]+', val_str)
        if not match:
            return 0.0
            
        clean_num_str = match.group().rstrip('.')
        if not clean_num_str:
            return 0.0
            
        num = float(clean_num_str)
        
        if 'milyar' in val_str or 'mlr' in val_str or 'bn' in val_str:
            return num * 1000000000.0
        elif 'mil' in val_str or 'm' in val_str:
            return num * 1000000.0
        elif 'bin' in val_str or 'k' in val_str or 'th' in val_str:
            return num * 1000.0
        else:
            return num
            
    except Exception as e:
        return 0.0

def get_transfermarkt_squad_data(html_source, year):
    soup = BeautifulSoup(html_source, 'html.parser')
    table = soup.find('table', class_='items')
    data = []
    
    if table and table.find('tbody'):
        main_tbody = table.find('tbody', recursive=False) or table.find('tbody')
        rows = main_tbody.find_all('tr', recursive=False)
        
        for row in rows:
            cols = row.find_all('td', recursive=False)
            
            if len(cols) >= 7:
                try:
                    takim_cell = row.find('td', class_='hauptlink')
                    takim_adi = clean_name(takim_cell.text) if takim_cell else clean_name(cols[1].text)
                    
                    kadro_text = cols[2].text.strip()
                    kadro_sayisi = int(kadro_text) if kadro_text.isdigit() else 0
                    
                    yas_text = cols[3].text.replace(',', '.').strip()
                    ortalama_yas = float(yas_text) if yas_text and yas_text != '-' else 0.0
                    
                    yabanci_text = cols[4].text.strip()
                    yabanci_sayisi = int(yabanci_text) if yabanci_text.isdigit() else 0
                    
                    ortalama_deger = parse_market_value(cols[-2].text)
                    toplam_deger = parse_market_value(cols[-1].text)
                    
                    data.append({
                        'Takim': takim_adi,
                        'Sezon': f"{year}-{year+1}",
                        'Kadro_Sayisi': kadro_sayisi,
                        'Ortalama_Yas': ortalama_yas,
                        'Yabanci_Oyuncu_Sayisi': yabanci_sayisi,
                        'Ortalama_Piyasa_Degeri_Euro': ortalama_deger,
                        'Toplam_Piyasa_Degeri_Euro': toplam_deger
                    })
                except Exception as e:
                    pass
    return data

def get_transfermarkt_standings(html_source, year):
    soup = BeautifulSoup(html_source, 'html.parser')
    table = soup.find('table', class_='items')
    data = []
    
    if table and table.find('tbody'):
        rows = table.find('tbody').find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 10:
                try:
                    
                    takim_link = cols[2].find('a')
                    takim_adi = clean_name(takim_link.text) if takim_link else clean_name(cols[2].text)
                    
                    galibiyet_text = cols[4].text.strip()
                    galibiyet = int(galibiyet_text) if galibiyet_text.isdigit() else 0
                    
                    beraberlik_text = cols[5].text.strip()
                    beraberlik = int(beraberlik_text) if beraberlik_text.isdigit() else 0
                    
                    maglubiyet_text = cols[6].text.strip()
                    maglubiyet = int(maglubiyet_text) if maglubiyet_text.isdigit() else 0
                    
                    goller = cols[7].text.strip()
                    atilan_gol = int(goller.split(':')[0]) if ':' in goller else 0
                    yenilen_gol = int(goller.split(':')[1]) if ':' in goller else 0
                    
                    averaj_text = cols[8].text.strip()
                    averaj = int(averaj_text) if averaj_text.lstrip('-+').isdigit() else 0
                    
                    puan_text = cols[9].text.strip()
                    puan = int(puan_text) if puan_text.isdigit() else 0
                    
                    data.append({
                        'Takim': takim_adi,
                        'Sezon': f"{year}-{year+1}",
                        'Galibiyet': galibiyet,
                        'Beraberlik': beraberlik,
                        'Maglubiyet': maglubiyet,
                        'Atilan_Gol': atilan_gol,
                        'Yenilen_Gol': yenilen_gol,
                        'Averaj': averaj,
                        'Puan': puan
                    })
                except Exception as e:
                    pass
    return data

if __name__ == "__main__":
    baslangic_yili = 2004
    bitis_yili = 2024
    
    tum_kadro_verileri = []
    tum_puan_verileri = []
    
    print("Tarayıcı başlatılıyor...")
    
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options, version_main=146)
    driver.maximize_window()
    
    try:
        for yil in range(baslangic_yili, bitis_yili + 1):
            
            # --- 1. KADRO VERİSİNİ ÇEK ---
            url_kadro = f"https://www.transfermarkt.com.tr/super-lig/startseite/wettbewerb/TR1/plus/1?saison_id={yil}"
            print(f"\n[{yil}-{yil+1}] Kadro sayfasına gidiliyor...")
            driver.get(url_kadro)
            time.sleep(random.uniform(4.0, 6.0)) 
            
            html_kadro = driver.page_source
            kadro_verisi = get_transfermarkt_squad_data(html_kadro, yil)
            
            # --- 2. PUAN DURUMU VERİSİNİ ÇEK ---
            url_puan = f"https://www.transfermarkt.com.tr/super-lig/tabelle/wettbewerb/TR1/saison_id/{yil}"
            print(f"[{yil}-{yil+1}] Puan durumu sayfasına gidiliyor...")
            driver.get(url_puan)
            time.sleep(random.uniform(4.0, 6.0))
            
            html_puan = driver.page_source
            puan_verisi = get_transfermarkt_standings(html_puan, yil)
            
            # --- DF OLUŞTUR VE LİSTEYE EKLE ---
            df_kadro = pd.DataFrame(kadro_verisi)
            df_puan = pd.DataFrame(puan_verisi)
            
            print(f" -> Başarılı: Kadro {len(df_kadro)} Satır | Puan Durumu {len(df_puan)} Satır Çekildi")
            
            if not df_kadro.empty:
                tum_kadro_verileri.append(df_kadro)
            if not df_puan.empty:
                tum_puan_verileri.append(df_puan)

        # --- TÜM SEZONLAR BİTTİĞİNDE KAYDET ---
        print("\nVeri çekme işlemi tamamlandı. CSV dosyaları oluşturuluyor...")
        script_klasoru = os.path.dirname(os.path.abspath(__file__))
        
        if tum_kadro_verileri:
            df_kadro_final = pd.concat(tum_kadro_verileri, ignore_index=True)
            yol_kadro = os.path.join(script_klasoru, 'superlig_kadro_verileri.csv')
            df_kadro_final.to_csv(yol_kadro, index=False, encoding='utf-8-sig')
            print(f"[*] Kadro Verileri Kaydedildi: {yol_kadro} ({len(df_kadro_final)} Satır)")
            
        if tum_puan_verileri:
            df_puan_final = pd.concat(tum_puan_verileri, ignore_index=True)
            yol_puan = os.path.join(script_klasoru, 'superlig_puan_durumu_verileri.csv')
            df_puan_final.to_csv(yol_puan, index=False, encoding='utf-8-sig')
            print(f"[*] Puan Durumu Verileri Kaydedildi: {yol_puan} ({len(df_puan_final)} Satır)")
            
    finally:
        try:
            driver.quit()
        except:
            pass
