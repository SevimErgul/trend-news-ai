# news_fetch.py
import os
import json
import feedparser
import firebase_admin
from firebase_admin import credentials, firestore
from transformers import pipeline

# -----------------------------
# 1. Firebase bağlantısı
# -----------------------------
firebase_key_json = os.environ.get("FIREBASE_KEY_JSON")
if not firebase_key_json:
    raise Exception("FIREBASE_KEY_JSON ortam değişkeni tanımlı değil!")

cred_dict = json.loads(firebase_key_json)
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()

# -----------------------------
# 2. RSS kaynakları
# -----------------------------
FEEDS = [
    "https://www.hurriyet.com.tr/rss/anasayfa",
    "http://feeds.bbci.co.uk/turkce/rss.xml"
]

# -----------------------------
# 3. AI özetleyici (hafif model)
# -----------------------------
print("AI özetleyici modeli yükleniyor...")
ozetleyici = pipeline("summarization", model="t5-small", tokenizer="t5-small")

def ozet_hazirla(metin):
    """Kısa haber metinlerini özetle"""
    if not metin:
        return ""
    try:
        ozet = ozetleyici(metin[:500], max_length=60, min_length=15, do_sample=False)
        return ozet[0]['summary_text']
    except Exception as e:
        print("Özetleme hatası:", e)
        return metin[:150]

# -----------------------------
# 4. Haberleri çekme ve kaydetme
# -----------------------------
def fetch_and_save(limit_per_feed=3):
    toplam = 0
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            source = feed.feed.get("title", url)
            entries = feed.entries[:limit_per_feed]

            for e in entries:
                baslik = e.get("title", "")
                link = e.get("link", "")
                tarih = e.get("published", "")
                metin = e.get("summary", "")

                if not baslik or not link:
                    continue

                # AI ile özetle
                ozet = ozet_hazirla(metin)

                # Firestore'a kaydet
                haber_doc = {
                    "baslik": baslik,
                    "ozet": ozet,
                    "link": link,
                    "kaynak": source,
                    "tarih": tarih
                }
                db.collection("haberler").add(haber_doc)
                toplam += 1
                print(f"Kaydedildi: {baslik[:60]}...")
        except Exception as ex:
            print(f"{url} kaynağında hata: {ex}")

    print(f"Toplam {toplam} haber kaydedildi.")

# -----------------------------
# 5. Ana çalışma
# -----------------------------
if __name__ == "__main__":
    fetch_and_save(limit_per_feed=3)
