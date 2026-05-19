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

def map_position(pos_text):
    pos_clean = pos_text.lower().replace('\xa0', ' ').strip()
    
    mevki_sozlugu = {
        'kaleci': 'Kaleci',
        'stoper': 'Defans',
        'sağ bek': 'Defans',
        'sol bek': 'Defans',
        'libero': 'Defans',
        'merkez orta saha': 'Orta Saha',
        'önlibero': 'Orta Saha',
        'on numara': 'Orta Saha',
        'orta saha': 'Orta Saha',
        'sağ orta saha': 'Orta Saha',
        'sol orta saha': 'Orta Saha',
        'sağ kanat': 'Forvet',
        'sol kanat': 'Forvet',
        'santrafor': 'Forvet',
        'ikinci forvet': 'Forvet',
        'forvet arkası': 'Forvet',
        'forvet': 'Forvet'
    }
    
    if pos_clean in mevki_sozlugu:
        return mevki_sozlugu[pos_clean]
        
    if 'kaleci' in pos_clean: return 'Kaleci'
    if 'bek' in pos_clean or 'stoper' in pos_clean or 'defans' in pos_clean: return 'Defans'
    if 'saha' in pos_clean or 'önlibero' in pos_clean or 'numara' in pos_clean: return 'Orta Saha'
    if 'forvet' in pos_clean or 'kanat' in pos_clean or 'santrafor' in pos_clean: return 'Forvet'
    if 'libero' in pos_clean: return 'Defans'
    
    return 'Bilinmiyor'

def safe_get(driver, url, max_retries=3):
    for i in range(max_retries):
        try:
            driver.get(url)
            return True
        except Exception as e:
            print(f"      [!] Bağlantı zaman aşımı. Sayfa tekrar deneniyor ({i+1}/{max_retries})...")
            time.sleep(3)
    return False

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
                    
                    club_id = None
                    if takim_cell:
                        a_tag = takim_cell.find('a')
                        if a_tag and 'href' in a_tag.attrs:
                            match = re.search(r'/verein/(\d+)', a_tag['href'])
                            if match:
                                club_id = match.group(1)
                    
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
                        
                        # Mevki Sayıları ve Finansalları (Varsayılan 0 olarak başlatılır)
                        'Kaleci_Sayisi': 0,
                        'Kaleci_Toplam_Deger_Euro': 0.0,
                        'Kaleci_Ortalama_Deger_Euro': 0.0,
                        
                        'Defans_Sayisi': 0,
                        'Defans_Toplam_Deger_Euro': 0.0,
                        'Defans_Ortalama_Deger_Euro': 0.0,
                        
                        'Ortasaha_Sayisi': 0,
                        'Ortasaha_Toplam_Deger_Euro': 0.0,
                        'Ortasaha_Ortalama_Deger_Euro': 0.0,
                        
                        'Forvet_Sayisi': 0,
                        'Forvet_Toplam_Deger_Euro': 0.0,
                        'Forvet_Ortalama_Deger_Euro': 0.0,
                        
                        'Ortalama_Piyasa_Degeri_Euro': ortalama_deger,
                        'Toplam_Piyasa_Degeri_Euro': toplam_deger,
                        'Club_ID': club_id
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
    
    print("===================================================================")
    print("Tarayıcı başlatılıyor...")
    print("Mevki bazlı sayısal ve finansal (Toplam/Ortalama Değer) verilerin")
    print("tamamı çekilecektir. Lütfen arkanıza yaslanın ve bekleyin.")
    print("===================================================================\n")
    
    options = uc.ChromeOptions()
    options.page_load_strategy = 'eager' 
    
    driver = uc.Chrome(options=options, version_main=146)
    driver.maximize_window()
    driver.set_page_load_timeout(30)
    
    try:
        for yil in range(baslangic_yili, bitis_yili + 1):
            print(f"\n[{yil}-{yil+1}] SEZONU BAŞLIYOR...")
            
            # --- 1. KADRO (GENEL) VERİSİNİ ÇEK ---
            url_kadro = f"https://www.transfermarkt.com.tr/super-lig/startseite/wettbewerb/TR1/plus/1?saison_id={yil}"
            
            if not safe_get(driver, url_kadro):
                print(f" [!!!] {yil} Kadro ana sayfası atlandı (Aşılamayan zaman aşımı).")
                continue
                
            time.sleep(random.uniform(2.0, 4.0)) 
            
            html_kadro = driver.page_source
            kadro_verisi = get_transfermarkt_squad_data(html_kadro, yil)
            
            # --- 1.5. KULÜP SAYFALARINA GİRİP MEVKİ SAYI VE DEĞERLERİNİ ÇEK ---
            print(f" -> Takımların detaylı oyuncu bazlı finansal analizleri taranıyor...")
            for item in kadro_verisi:
                club_id = item.get('Club_ID')
                if not club_id:
                    if 'Club_ID' in item: del item['Club_ID']
                    continue
                
                url_team = f"https://www.transfermarkt.com.tr/-/kader/verein/{club_id}/saison_id/{yil}"
                
                if not safe_get(driver, url_team):
                    print(f"    * {item['Takim']} sayfası zaman aşımına uğradı, 0 olarak kaydedilecek.")
                    del item['Club_ID']
                    continue
                    
                time.sleep(random.uniform(1.5, 3.0))
                
                soup_team = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Kasaları sıfırla
                gk_c = df_c = md_c = fw_c = 0
                gk_v = df_v = md_v = fw_v = 0.0
                
                inline_tables = soup_team.find_all('table', class_='inline-table')
                
                for tab in inline_tables:
                    trs = tab.find_all('tr')
                    if len(trs) >= 2:
                        pos_text = trs[-1].text.strip()
                        mapped = map_position(pos_text)
                        
                        # Oyuncunun piyasa değerini bul (Ana tablo satırının en son hücresi)
                        val = 0.0
                        main_tr = tab.find_parent('tr')
                        if main_tr:
                            tds = main_tr.find_all('td', recursive=False)
                            if tds:
                                val_text = tds[-1].text.strip()
                                val = parse_market_value(val_text)
                        
                        if mapped == 'Kaleci':
                            gk_c += 1
                            gk_v += val
                        elif mapped == 'Defans':
                            df_c += 1
                            df_v += val
                        elif mapped == 'Orta Saha':
                            md_c += 1
                            md_v += val
                        elif mapped == 'Forvet':
                            fw_c += 1
                            fw_v += val
                            
                # Sayıları ve Değerleri Sözlüğe Yaz
                item['Kaleci_Sayisi'] = gk_c
                item['Kaleci_Toplam_Deger_Euro'] = gk_v
                item['Kaleci_Ortalama_Deger_Euro'] = gk_v / gk_c if gk_c > 0 else 0.0
                
                item['Defans_Sayisi'] = df_c
                item['Defans_Toplam_Deger_Euro'] = df_v
                item['Defans_Ortalama_Deger_Euro'] = df_v / df_c if df_c > 0 else 0.0
                
                item['Ortasaha_Sayisi'] = md_c
                item['Ortasaha_Toplam_Deger_Euro'] = md_v
                item['Ortasaha_Ortalama_Deger_Euro'] = md_v / md_c if md_c > 0 else 0.0
                
                item['Forvet_Sayisi'] = fw_c
                item['Forvet_Toplam_Deger_Euro'] = fw_v
                item['Forvet_Ortalama_Deger_Euro'] = fw_v / fw_c if fw_c > 0 else 0.0
                
                print(f"    * {item['Takim']} tamamlandı (Toplam Oyuncu Değerleri Hesaplandı)")
                del item['Club_ID']

            # --- 2. PUAN DURUMU VERİSİNİ ÇEK ---
            url_puan = f"https://www.transfermarkt.com.tr/super-lig/tabelle/wettbewerb/TR1/saison_id/{yil}"
            
            if safe_get(driver, url_puan):
                time.sleep(random.uniform(2.0, 4.0))
                html_puan = driver.page_source
                puan_verisi = get_transfermarkt_standings(html_puan, yil)
            else:
                puan_verisi = []
                print(f" [!!!] {yil} Puan durumu atlandı (Aşılamayan zaman aşımı).")
            
            # --- DF OLUŞTUR VE LİSTEYE EKLE ---
            df_kadro = pd.DataFrame(kadro_verisi)
            df_puan = pd.DataFrame(puan_verisi)
            
            print(f" -> SEZON ÖZETİ: Kadro {len(df_kadro)} Satır | Puan Durumu {len(df_puan)} Satır Çekildi")
            
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
            print(f"[*] Kadro (Mevki/Finansal) Verileri Kaydedildi: {yol_kadro} ({len(df_kadro_final)} Satır)")
            
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