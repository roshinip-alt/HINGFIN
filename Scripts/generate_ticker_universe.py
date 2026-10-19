import pandas as pd

input_file = "../Dataset/NIFTY50.tsv"
output_file = "../Dataset/ticker_dictionary.tsv"
df = pd.read_csv(input_file, sep="\t")
short_aliases = {
    "ADANIENT": [
        "Adani Enterprises"
    ],

    "ADANIPORTS": [
        "Adani Ports"
    ],

    "APOLLOHOSP": [
        "Apollo Hospitals"
    ],

    "ASIANPAINT": [
        "Asian Paints"
    ],

    "AXISBANK": [
        "Axis Bank"
    ],

    "BAJAJ-AUTO": [
        "Bajaj Auto"
    ],

    "BAJFINANCE": [
        "Bajaj Finance"
    ],

    "BAJAJFINSV": [
        "Bajaj Finserv"
    ],

    "BEL": [
        "Bharat Electronics"
    ],

    "BHARTIARTL": [
        "Bharti Airtel",
        "Airtel"
    ],

    "CIPLA": [
        "Cipla"
    ],

    "COALINDIA": [
        "Coal India"
    ],

    "DRREDDY": [
        "Dr Reddy's",
        "Dr. Reddy's"
    ],

    "EICHERMOT": [
        "Eicher Motors"
    ],

    "ETERNAL": [
        "Eternal",
        "Zomato"
    ],

    "GRASIM": [
        "Grasim"
    ],

    "HCLTECH": [
        "HCL Tech",
        "HCL Technologies"
    ],

    "HDFCBANK": [
        "HDFC Bank"
    ],

    "HDFCLIFE": [
        "HDFC Life"
    ],

    "HINDALCO": [
        "Hindalco"
    ],

    "HINDUNILVR": [
        "Hindustan Unilever",
        "HUL"
    ],

    "ICICIBANK": [
        "ICICI Bank"
    ],

    "ITC": [
        "ITC"
    ],

    "INFY": [
        "Infosys"
    ],

    "INDIGO": [
        "IndiGo"
    ],

    "JSWSTEEL": [
        "JSW Steel"
    ],

    "JIOFIN": [
        "Jio Financial",
        "Jio Finance"
    ],

    "KOTAKBANK": [
        "Kotak Bank",
        "Kotak Mahindra Bank"
    ],

    "LT": [
        "L&T",
        "Larsen & Toubro"
    ],

    "M&M": [
        "Mahindra & Mahindra",
        "M&M",
        "Mahindra"
    ],

    "MARUTI": [
        "Maruti Suzuki",
        "Maruti"
    ],

    "MAXHEALTH": [
        "Max Healthcare",
        "Max Health"
    ],

    "NTPC": [
        "NTPC"
    ],

    "NESTLEIND": [
        "Nestle India"
    ],

    "ONGC": [
        "ONGC",
        "Oil and Natural Gas Corporation"
    ],

    "POWERGRID": [
        "Power Grid",
        "Power Grid Corporation"
    ],

    "RELIANCE": [
        "Reliance",
        "Reliance Industries",
        "RIL"
    ],

    "SBILIFE": [
        "SBI Life"
    ],

    "SHRIRAMFIN": [
        "Shriram Finance"
    ],

    "SBIN": [
        "SBI",
        "State Bank of India"
    ],

    "SUNPHARMA": [
        "Sun Pharma",
        "Sun Pharmaceutical"
    ],

    "TCS": [
        "TCS",
        "Tata Consultancy Services"
    ],

    "TATACONSUM": [
        "Tata Consumer"
    ],

    "TMPV": [
        "Tata Motors",
        "Tata Motors Passenger Vehicles"
    ],

    "TATASTEEL": [
        "Tata Steel"
    ],

    "TECHM": [
        "Tech Mahindra"
    ],

    "TITAN": [
        "Titan",
        "Titan Company"
    ],

    "TRENT": [
        "Trent"
    ],

    "ULTRACEMCO": [
        "UltraTech Cement",
        "UltraTech"
    ],

    "WIPRO": [
        "Wipro"
    ]
}

rows = []
for _, company in df.iterrows():

    symbol = str(company["Symbol"]).strip()
    legal_name = str(company["Company Name"]).strip()
    rows.append({
        "symbol": symbol,
        "surface_form": legal_name,
        "surface_form_type": "legal",
        "is_ambiguous": False
    })
    rows.append({
        "symbol": symbol,
        "surface_form": symbol,
        "surface_form_type": "short",
        "is_ambiguous": False
    })
    aliases = short_aliases.get(symbol, [])

    for alias in aliases:
        rows.append({
            "symbol": symbol,
            "surface_form": alias,
            "surface_form_type": "short",
            "is_ambiguous": False
        })

        rows.append({
            "symbol": symbol,
            "surface_form": "$" + alias,
            "surface_form_type": "cashtag",
            "is_ambiguous": False
        })

        rows.append({
            "symbol": symbol,
            "surface_form": "#" + alias,
            "surface_form_type": "hashtag",
            "is_ambiguous": False
        })

        rows.append({
            "symbol": symbol,
            "surface_form": "$" + symbol,
            "surface_form_type": "cashtag",
            "is_ambiguous": False
        })

        rows.append({
            "symbol": symbol,
            "surface_form": "#" + symbol,
            "surface_form_type": "hashtag",
            "is_ambiguous": False
        })

ticker_dictionary = pd.DataFrame(rows)

ticker_dictionary = ticker_dictionary.drop_duplicates(
    subset=[
        "symbol",
        "surface_form",
        "surface_form_type"
    ]
)

ticker_dictionary.to_csv(
    output_file,
    sep="\t",
    index=False
)

print("Ticker dictionary created successfully!")
print(f"Total rows: {len(ticker_dictionary)}")

print("\nRows by type:")
print(ticker_dictionary["surface_form_type"].value_counts())

print("\nFirst 30 rows:")
print(ticker_dictionary.head(30).to_string(index=False))