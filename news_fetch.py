# news_fetch_auto.py
import feedparser
from transformers import pipeline
import firebase_admin
from firebase_admin import credentials, firestore

# --------------------------
# 1) Firebase ayarları
# --------------------------
cred = credentials.Certificate("firebase_key.json")  # Firebase key dosyan
firebase_admin.initialize_app(cred)
db = firestore.client()

# --------------------------
# 2) RSS kaynakları
# --------------------------
FEEDS = [
   "https://www.aa.com.tr/tr/rss/default?cat=guncel",
    "https://www.aa.com.tr/tr/rss/default?cat=ekonomi",
    "https://www.aa.com.tr/tr/rss/default?cat=spor",
    "http://www.hurriyet.com.tr/rss/anasayfa",
    "http://www.hurriyet.com.tr/rss/gundem",
    "https://www.milliyet.com.tr/rss/rssnew/sondakikarss.xml",
    "https://www.milliyet.com.tr/rss/rssnew/gundem.xml",
    "https://www.sabah.com.tr/rss/anasayfa.xml",
    "https://www.sabah.com.tr/rss/gundem.xml",
    "https://www.haberturk.com/rss/kategori/gundem.xml",
    "https://www.cumhuriyet.com.tr/rss/son_dakika.xml",
    "https://www.ensonhaber.com/rss/ensonhaber.xml",
    "https://rss.haberler.com/rss.asp?kategori=guncel",
    "https://www.yenisafak.com/rss/gundem.xml",
     "https://www.aksam.com.tr/rss/gundem.xml",
    "https://www.star.com.tr/rss/gundem.xml",
    "hhttps://www.birgun.net/rss/home",
    "https://www.gazeteduvar.com.tr/export/rss",
    "https://www.diken.com.tr/feed/",
    "https://www.tgrthaber.com.tr/feed/gundem",
    "https://www.ntv.com.tr/son-dakika.rss",
    "https://www.ntv.com.tr/turkiye.rss",
    "https://www.cnnturk.com/feed/rss/all/news",
    "https://www.cnnturk.com/feed/rss/turkiye/news",
    "http://www.trthaber.com/sondakika.rss",
    "http://www.trthaber.com/gundem.rss",
    "https://www.ahaber.com.tr/rss/anasayfa.xml",
    "https://www.ahaber.com.tr/rss/gundem.xml",
    "https://halktv.com.tr/service/rss.php",
    "http://feeds.bbci.co.uk/turkce/rss.xml",
    "https://rss.dw.com/rdf/rss-tur-all",
    "https://tr.sputniknews.com/export/rss2/archive/index.xml",
    "http://www.hurriyet.com.tr/rss/ekonomi",
    "https://www.milliyet.com.tr/rss/rssnew/ekonomi.xml",
    "https://www.sabah.com.tr/rss/ekonomi.xml",
    "https://www.ntv.com.tr/ekonomi.rss",
    "http://www.hurriyet.com.tr/rss/spor",
    "https://www.milliyet.com.tr/rss/rssnew/spor.xml",
    "https://www.sabah.com.tr/rss/spor.xml",
    "https://www.ntv.com.tr/teknoloji.rss",
    "https://www.dha.com.tr/rss/gundem.xml",
    "https://www.iha.com.tr/rss/gundem/",
    "https://www.iha.com.tr/rss/ekonomi/",
    "https://www.sozcu.com.tr/feed/",
    "https://www.sozcu.com.tr/kategori/gundem/feed/",
    "https://t24.com.tr/rss",
    "http://www.mynet.com/haber/rss/sondakika",
    "https://www.indyturk.com/rss",
    "https://odatv.com/rss.php",
    "https://www.turkiyegazetesi.com.tr/rss/rss.xml",
    "https://www.takvim.com.tr/rss/gundem.xml",
    "https://www.karar.com/rss/gundem.xml",
    "https://www.ekonomim.com/rss",
    "https://www.bloomberght.com/rss",
    "http://www.bigpara.com/rss/borsa/",
    "https://www.fanatik.com.tr/rss/rssnew/fanatikrss.xml",
    "https://www.fotomac.com.tr/rss/anasayfa.xml",
    "https://beinsports.com.tr/rss",
    "https://www.ntv.com.tr/spor.rss",
    "https://www.trthaber.com/spor.rss",
    "https://shiftdelete.net/feed",
    "https://webrazzi.com/feed/",
    "https://www.chip.com.tr/rss.xml",
    "https://teknoseyir.com/feed",
    "http://www.hurriyet.com.tr/rss/magazin",
    "https://www.milliyet.com.tr/rss/rssnew/magazinrss.xml",
    "https://www.sabah.com.tr/rss/magazin.xml",
    "https://www.ntv.com.tr/saglik.rss",
    "http://www.hurriyet.com.tr/rss/saglik",
    "https://www.cnnturk.com/feed/rss/saglik/news"
]

# --------------------------
# 3) AI Özetleyici (local)
# --------------------------
ozetleyici = pipeline("summarization", model="facebook/bart-large-cnn")

def ozet_hazirla(metin):
    try:
        ozet = ozetleyici(metin, max_length=60, min_length=25, do_sample=False)
        return ozet[0]['summary_text']
    except:
        return metin[:200]  # özetlenemezse ilk 200 karakteri al

# --------------------------
# 4) Haberleri çek ve özetle
# --------------------------
def fetch_and_save(limit_per_feed=5):
    toplam = 0
    for url in FEEDS:
        feed = feedparser.parse(url)
        source = feed.feed.get("title", url)
        entries = feed.entries[:limit_per_feed]
        for e in entries:
            baslik = e.get("title", "")
            link = e.get("link", "")
            tarih = e.get("published", "")
            metin = e.get("summary", "")  # RSS içeriği

            # AI ile özetle
            ozet = ozet_hazirla(metin)

            # Firebase'e kaydet
            haber_doc = {
                "baslik": baslik,
                "ozet": ozet,
                "link": link,
                "kaynak": source,
                "tarih": tarih
            }
            db.collection("haberler").add(haber_doc)
            toplam += 1
            print(f"Kaydedildi: {baslik[:50]}...")

    print(f"Toplam {toplam} haber kaydedildi.")

if __name__ == "__main__":
    fetch_and_save(limit_per_feed=2)  # her feedden 5 haber çek
