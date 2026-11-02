# nifty_aliases.py

COMPANIES = {
    "ADANIENT": {
        "name": "Adani Enterprises Ltd.",
        "aliases": ["adani enterprises", "adanient", "adani share", "adani stock"]
    },
    "ADANIPORTS": {
        "name": "Adani Ports & SEZ Ltd.",
        "aliases": ["adani ports", "adanports", "adaniports", "adani port"]
    },
    "APOLLOHOSP": {
        "name": "Apollo Hospitals Enterprise Ltd.",
        "aliases": ["apollo hospitals", "apollo hospital", "apollohosp"]
    },
    "ASIANPAINT": {
        "name": "Asian Paints Ltd.",
        "aliases": ["asian paints", "asianpaint", "asianpaint"]
    },
    "AXISBANK": {
        "name": "Axis Bank Ltd.",
        "aliases": ["axis bank", "axisbank"]
    },
    "BAJAJ-AUTO": {
        "name": "Bajaj Auto Ltd.",
        "aliases": ["bajaj auto", "bajajauto"]
    },
    "BAJFINANCE": {
        "name": "Bajaj Finance Ltd.",
        "aliases": ["bajaj finance", "bajajfinance"]
    },
    "BAJAJFINSV": {
        "name": "Bajaj Finserv Ltd.",
        "aliases": ["bajaj finserv", "bajajfinsv"]
    },
    "BEL": {
        "name": "Bharat Electronics Ltd.",
        "aliases": ["bharat electronics", "bel share", "bel stock"]
    },
    "BHARTIARTL": {
        "name": "Bharti Airtel Ltd.",
        "aliases": ["bharti airtel", "airtel share", "airtel stock", "bhartiartl"]
    },
    "CIPLA": {
        "name": "Cipla Ltd.",
        "aliases": ["cipla", "cipla share", "cipla stock"]
    },
    "COALINDIA": {
        "name": "Coal India Ltd.",
        "aliases": ["coal india", "coalindia", "coal india share"]
    },
    "DRREDDY": {
        "name": "Dr. Reddy's Laboratories Ltd.",
        "aliases": ["dr reddy", "dr reddys", "drreddy"]
    },
    "EICHERMOT": {
        "name": "Eicher Motors Ltd.",
        "aliases": ["eicher motors", "eicher", "eichermot"]
    },
    "ETERNAL": {
        "name": "Eternal Ltd.",
        "aliases": ["eternal", "eternal share", "eternal stock", "zomato"]
    },
    "GRASIM": {
        "name": "Grasim Industries Ltd.",
        "aliases": ["grasim", "grasim industries"]
    },
    "HCLTECH": {
        "name": "HCL Technologies Ltd.",
        "aliases": ["hcl tech", "hcl technologies", "hcltech"]
    },
    "HDFCBANK": {
        "name": "HDFC Bank Ltd.",
        "aliases": ["hdfc bank", "hdfcbank"]
    },
    "HDFCLIFE": {
        "name": "HDFC Life Insurance Company Ltd.",
        "aliases": ["hdfc life", "hdfclife"]
    },
    "HINDALCO": {
        "name": "Hindalco Industries Ltd.",
        "aliases": ["hindalco", "hindalco industries"]
    },
    "HINDUNILVR": {
        "name": "Hindustan Unilever Ltd.",
        "aliases": ["hindustan unilever", "hul", "hindunilvr"]
    },
    "ICICIBANK": {
        "name": "ICICI Bank Ltd.",
        "aliases": ["icici bank", "icicibank"]
    },
    "ITC": {
        "name": "ITC Ltd.",
        "aliases": ["itc share", "itc stock", "itc limited"]
    },
    "INFY": {
        "name": "Infosys Ltd.",
        "aliases": ["infosys", "infy", "infosys share"]
    },
    "INDIGO": {
        "name": "InterGlobe Aviation Ltd.",
        "aliases": ["indigo", "interglobe aviation", "indigo share"]
    },
    "JSWSTEEL": {
        "name": "JSW Steel Ltd.",
        "aliases": ["jsw steel", "jswsteel"]
    },
    "JIOFIN": {
        "name": "Jio Financial Services Ltd.",
        "aliases": ["jio financial", "jiofin", "jio finance"]
    },
    "KOTAKBANK": {
        "name": "Kotak Mahindra Bank Ltd.",
        "aliases": ["kotak bank", "kotak mahindra", "kotakbank"]
    },
    "LT": {
        "name": "Larsen & Toubro Ltd.",
        "aliases": ["larsen toubro", "l&t", "l&t share", "larsen"]
    },
    "M&M": {
        "name": "Mahindra & Mahindra Ltd.",
        "aliases": ["mahindra", "mahindra and mahindra", "m&m", "m&m share"]
    },
    "MARUTI": {
        "name": "Maruti Suzuki India Ltd.",
        "aliases": ["maruti", "maruti suzuki", "maruti share"]
    },
    "MAXHEALTH": {
        "name": "Max Healthcare Institute Ltd.",
        "aliases": ["max healthcare", "maxhealth", "max hospital"]
    },
    "NTPC": {
        "name": "NTPC Ltd.",
        "aliases": ["ntpc", "ntpc share", "ntpc stock"]
    },
    "NESTLEIND": {
        "name": "Nestle India Ltd.",
        "aliases": ["nestle india", "nestle share", "nestleind"]
    },
    "ONGC": {
        "name": "Oil & Natural Gas Corporation Ltd.",
        "aliases": ["ongc", "ongc share", "ongc stock"]
    },
    "POWERGRID": {
        "name": "Power Grid Corporation of India Ltd.",
        "aliases": ["power grid", "powergrid", "power grid share"]
    },
    "RELIANCE": {
        "name": "Reliance Industries Ltd.",
        "aliases": ["reliance", "reliance industries", "reliance share", "reliance stock"]
    },
    "SBILIFE": {
        "name": "SBI Life Insurance Company Ltd.",
        "aliases": ["sbi life", "sbilife", "sbi life share"]
    },
    "SHRIRAMFIN": {
        "name": "Shriram Finance Ltd.",
        "aliases": ["shriram finance", "shriramfin"]
    },
    "SBIN": {
        "name": "State Bank of India Ltd.",
        "aliases": ["sbi", "state bank of india", "sbin", "sbi share"]
    },
    "SUNPHARMA": {
        "name": "Sun Pharmaceutical Industries Ltd.",
        "aliases": ["sun pharma", "sunpharma", "sun pharmaceutical"]
    },
    "TCS": {
        "name": "Tata Consultancy Services Ltd.",
        "aliases": ["tcs", "tcs share", "tcs stock"]
    },
    "TATACONSUM": {
        "name": "Tata Consumer Products Ltd.",
        "aliases": ["tata consumer", "tataconsum"]
    },
    "TMPV": {
        "name": "Tata Motors Passenger Vehicles Ltd.",
        "aliases": ["tata motors passenger", "tmpv", "tata motors"]
    },
    "TATASTEEL": {
        "name": "Tata Steel Ltd.",
        "aliases": ["tata steel", "tatasteel"]
    },
    "TECHM": {
        "name": "Tech Mahindra Ltd.",
        "aliases": ["tech mahindra", "techm"]
    },
    "TITAN": {
        "name": "Titan Company Ltd.",
        "aliases": ["titan", "titan company", "titan share"]
    },
    "TRENT": {
        "name": "Trent Ltd.",
        "aliases": ["trent", "trent share", "trent stock"]
    },
    "ULTRACEMCO": {
        "name": "UltraTech Cement Ltd.",
        "aliases": ["ultratech", "ultratech cement", "ultracemco"]
    },
    "WIPRO": {
        "name": "Wipro Ltd.",
        "aliases": ["wipro", "wipro share", "wipro stock"]
    }
}