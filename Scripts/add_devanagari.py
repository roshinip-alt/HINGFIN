import csv

dictionary_file = "../Dataset/ticker_dictionary.tsv"

# Devanagari forms for the NIFTY50 companies.
# These are candidate forms and should be hand-checked before final release.
devanagari_forms = {
    "ADANIENT": "अडानी एंटरप्राइजेज लिमिटेड",
    "ADANIPORTS": "अडानी पोर्ट्स एंड स्पेशल इकोनॉमिक ज़ोन लिमिटेड",
    "APOLLOHOSP": "अपोलो हॉस्पिटल्स एंटरप्राइज लिमिटेड",
    "ASIANPAINT": "एशियन पेंट्स लिमिटेड",
    "AXISBANK": "एक्सिस बैंक लिमिटेड",
    "BAJAJ-AUTO": "बजाज ऑटो लिमिटेड",
    "BAJFINANCE": "बजाज फाइनेंस लिमिटेड",
    "BAJAJFINSV": "बजाज फिनसर्व लिमिटेड",
    "BEL": "भारत इलेक्ट्रॉनिक्स लिमिटेड",
    "BHARTIARTL": "भारती एयरटेल लिमिटेड",
    "CIPLA": "सिप्ला लिमिटेड",
    "COALINDIA": "कोल इंडिया लिमिटेड",
    "DRREDDY": "डॉ. रेड्डीज़ लेबोरेट्रीज़ लिमिटेड",
    "EICHERMOT": "आयशर मोटर्स लिमिटेड",
    "ETERNAL": "इटरनल लिमिटेड",
    "GRASIM": "ग्रासिम इंडस्ट्रीज़ लिमिटेड",
    "HCLTECH": "एचसीएल टेक्नोलॉजीज़ लिमिटेड",
    "HDFCBANK": "एचडीएफसी बैंक लिमिटेड",
    "HDFCLIFE": "एचडीएफसी लाइफ इंश्योरेंस कंपनी लिमिटेड",
    "HINDALCO": "हिंडाल्को इंडस्ट्रीज़ लिमिटेड",
    "HINDUNILVR": "हिंदुस्तान यूनिलीवर लिमिटेड",
    "ICICIBANK": "आईसीआईसीआई बैंक लिमिटेड",
    "ITC": "आईटीसी लिमिटेड",
    "INFY": "इन्फोसिस लिमिटेड",
    "INDIGO": "इंटरग्लोब एविएशन लिमिटेड",
    "JSWSTEEL": "जेएसडब्ल्यू स्टील लिमिटेड",
    "JIOFIN": "जियो फाइनेंशियल सर्विसेज़ लिमिटेड",
    "KOTAKBANK": "कोटक महिंद्रा बैंक लिमिटेड",
    "LT": "लार्सन एंड टुब्रो लिमिटेड",
    "M&M": "महिंद्रा एंड महिंद्रा लिमिटेड",
    "MARUTI": "मारुति सुज़ुकी इंडिया लिमिटेड",
    "MAXHEALTH": "मैक्स हेल्थकेयर इंस्टीट्यूट लिमिटेड",
    "NTPC": "एनटीपीसी लिमिटेड",
    "NESTLEIND": "नेस्ले इंडिया लिमिटेड",
    "ONGC": "ऑयल एंड नेचुरल गैस कॉरपोरेशन लिमिटेड",
    "POWERGRID": "पावर ग्रिड कॉरपोरेशन ऑफ इंडिया लिमिटेड",
    "RELIANCE": "रिलायंस इंडस्ट्रीज़ लिमिटेड",
    "SBILIFE": "एसबीआई लाइफ इंश्योरेंस कंपनी लिमिटेड",
    "SHRIRAMFIN": "श्रीराम फाइनेंस लिमिटेड",
    "SBIN": "स्टेट बैंक ऑफ इंडिया",
    "SUNPHARMA": "सन फार्मास्युटिकल इंडस्ट्रीज़ लिमिटेड",
    "TCS": "टाटा कंसल्टेंसी सर्विसेज़ लिमिटेड",
    "TATACONSUM": "टाटा कंज्यूमर प्रोडक्ट्स लिमिटेड",
    "TMPV": "टाटा मोटर्स पैसेंजर व्हीकल्स लिमिटेड",
    "TATASTEEL": "टाटा स्टील लिमिटेड",
    "TECHM": "टेक महिंद्रा लिमिटेड",
    "TITAN": "टाइटन कंपनी लिमिटेड",
    "TRENT": "ट्रेंट लिमिटेड",
    "ULTRACEMCO": "अल्ट्राटेक सीमेंट लिमिटेड",
    "WIPRO": "विप्रो लिमिटेड",
}

# Read existing dictionary
with open(dictionary_file, "r", encoding="utf-8", newline="") as f:
    rows = list(csv.reader(f, delimiter="\t"))

# Existing symbol + Devanagari combinations
existing = {
    (row[0], row[1])
    for row in rows[1:]
    if len(row) >= 2
}

added = 0

# Add only missing Devanagari rows
with open(dictionary_file, "a", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, delimiter="\t", lineterminator="\n")

    for symbol, devanagari in devanagari_forms.items():
        if (symbol, devanagari) not in existing:
            writer.writerow([
                symbol,
                devanagari,
                "devanagari",
                "False"
            ])
            added += 1

print(f"Added {added} Devanagari rows.")
print(f"Total Devanagari candidates: {len(devanagari_forms)}")