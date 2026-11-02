import re


# =========================================================
# STOCK / INVESTMENT TERMS
# =========================================================

STOCK_TERMS = [
    "share",
    "shares",
    "stock",
    "price",
    "target",
    "target price",
    "buy",
    "buying",
    "bought",
    "sell",
    "selling",
    "sold",
    "hold",
    "holding",
    "accumulate",
    "accumulation",
    "invest",
    "investment",
    "investing",
    "profit",
    "loss",
    "return",
    "returns",
    "gain",
    "gains",
    "downside",
    "upside",
    "valuation",
    "overvalued",
    "undervalued",
    "expensive",
    "cheap",
    "breakout",
    "breakdown",
    "support",
    "resistance",
    "bullish",
    "bearish",
    "rally",
    "crash",
    "rise",
    "rising",
    "fall",
    "falling",
    "dropped",
    "drop",
    "down",
    "increase",
    "increased",
    "decrease",
    "decreased",

    # Hinglish
    "upar",
    "neeche",
    "gira",
    "gir gaya",
    "gir raha",
    "girega",
    "badha",
    "badh gaya",
    "badh raha",
    "badhega",
    "badega",
    "upar jayega",
    "upar jaayega",
    "neeche jayega",
    "neeche jaayega",
    "khareed",
    "kharid",
    "bech",
    "bechna",
    "rok",
    "rakho",
    "lena",
    "le sakte",
    "lena chahiye",
    "buy karna",
    "sell karna",
    "buy kare",
    "sell kare",
    "buy karo",
    "sell karo",
    "hold karo",
    "hold karna",
    "hold rakho",
    "accumulate kar",
    "support hai",
    "resistance hai",
    "multibagger",
]


# =========================================================
# GENERIC / IRRELEVANT COMMENTS
# =========================================================

GENERIC_EXCLUDE = [
    "guru ji",
    "guruji",
    "best teacher",
    "best sir",
    "great teacher",
    "thanks sir",
    "thank you sir",
    "thankyou sir",
    "nice video",
    "great video",
    "good video",
    "awesome video",
    "excellent video",
    "love your videos",
    "love your analysis",
    "please make video",
    "please cover",
    "cover this",
    "cover that",
    "new update share kro",
    "update share kro",
]


# =========================================================
# POSITIVE STOCK SENTIMENT
# =========================================================

POSITIVE_TERMS = [
    "buy",
    "buying",
    "bought",
    "accumulate",
    "accumulation",
    "bullish",
    "strong",
    "strong stock",
    "good stock",
    "good price",
    "good time",
    "undervalued",
    "cheap",
    "upside",
    "profit",
    "gains",
    "gain",
    "rally",
    "breakout",
    "break out",
    "multibagger",

    # Hinglish
    "upar jayega",
    "upar jaayega",
    "badh jayega",
    "badh raha",
    "badhega",
    "badega",
    "strong lag",
    "acha lag",
    "achha lag",
    "sahi price",
    "sahi time",
    "le sakte",
    "lena chahiye",
    "buy karna chahiye",
    "buy karo",
    "accumulate kar sakte",
    "kharid lo",
    "kharidna chahiye",
]


# =========================================================
# NEGATIVE STOCK SENTIMENT
# =========================================================

NEGATIVE_TERMS = [
    "sell",
    "selling",
    "sold",
    "bearish",
    "weak",
    "weak stock",
    "bad stock",
    "overvalued",
    "expensive",
    "downside",
    "loss",
    "losses",
    "crash",
    "breakdown",
    "fall",
    "falling",
    "dropped",
    "drop",
    "down",
    "gir gaya",
    "gir raha",
    "girega",
    "neeche jayega",
    "neeche jaayega",
    "bura lag",
    "weak lag",
    "risky",
    "risk hai",
    "risk",
    "avoid",
    "mat lo",
    "mat lena",
    "sell karna chahiye",
    "sell karo",
]


# =========================================================
# NORMALIZE
# =========================================================

def normalize(text):
    return re.sub(r"\s+", " ", text.lower().strip())


# =========================================================
# COMPANY CHECK
# =========================================================

def mentions_company(comment, aliases):

    text = normalize(comment)

    for alias in aliases:

        alias = alias.lower().strip()

        if alias in text:
            return True

    return False


# =========================================================
# GENERIC COMMENT CHECK
# =========================================================

def is_generic_comment(comment):

    text = normalize(comment)

    for phrase in GENERIC_EXCLUDE:

        if phrase in text:
            return True

    return False


# =========================================================
# QUESTION CHECK
# =========================================================

def is_question_only(comment):

    text = normalize(comment)

    # -----------------------------------------------------
    # Clear question mark = normally a question.
    # -----------------------------------------------------

    if "?" in text:
        return True

    # -----------------------------------------------------
    # Common question constructions without ?
    # -----------------------------------------------------

    question_patterns = [
        r"\bwhat\b",
        r"\bwhy\b",
        r"\bhow\b",
        r"\bwhen\b",
        r"\bwhich\b",
        r"\bshould i\b",
        r"\bcan i\b",
        r"\bwill it\b",

        r"\bkya\b",
        r"\bkyu\b",
        r"\bkyon\b",
        r"\bkaise\b",
        r"\bkab\b",
        r"\bkaha\b",
        r"\bkitna\b",
        r"\bkitne\b",

        r"\bkya hoga\b",
        r"\bka kya hoga\b",
        r"\bbuy karu\b",
        r"\bsell karu\b",
        r"\bhold karu\b",
    ]

    for pattern in question_patterns:

        if re.search(pattern, text):
            return True

    return False


# =========================================================
# STOCK CONTEXT
# =========================================================

def has_stock_context(comment):

    text = normalize(comment)

    return any(
        term in text
        for term in STOCK_TERMS
    )


# =========================================================
# SENTIMENT
# =========================================================

def classify_sentiment(comment):

    text = normalize(comment)

    positive_score = 0
    negative_score = 0

    for term in POSITIVE_TERMS:

        if term in text:
            positive_score += 1

    for term in NEGATIVE_TERMS:

        if term in text:
            negative_score += 1

    if positive_score > negative_score and positive_score > 0:
        return "Positive"

    if negative_score > positive_score and negative_score > 0:
        return "Negative"

    if positive_score == negative_score == 0:
        return "Neutral"

    return "Neutral"


# =========================================================
# FINAL EVALUATION
# =========================================================

def evaluate_comment(comment, aliases):

    text = normalize(comment)

    # Empty
    if not text:
        return False, None, "empty"

    # Generic YouTuber/video comment
    if is_generic_comment(text):
        return False, None, "generic comment"

    # Must mention target company
    if not mentions_company(text, aliases):
        return False, None, "target company not mentioned"

    # Must contain stock/investment context
    if not has_stock_context(text):
        return False, None, "not stock related"

    # Questions are excluded
    if is_question_only(text):
        return False, None, "question only"

    # Actual sentiment
    sentiment = classify_sentiment(text)

    return True, sentiment, "valid stock sentiment"