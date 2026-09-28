import re

PATTERNS = [
    ('IBAN', r'\bTR\s*(?:\d\s*){24}\b'),
    ('TC', r'\b[1-9]\d{10}\b'),
    ('EMAIL', r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}'),
    ('TELEFON', r'(?<!\w)(?:\+?90\s*)?0?5\d{2}[\s()-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}(?!\d)'),
    ('KART', r'\b(?:\d[ -]?){16}\b'),
    ('DOSYA', r'(?i)(?:dosya|esas|karar)\s*(?:no|numarası)?\s*[:.]?\s*\d{4}/\d+'),
    ('ADRES', r'(?im)(?:adres|ikametg[aâ]h)\s*:\s*[^\n]+'),
    ('KISI', r'(?im)(?:ad soyad|müvekkil|davacı|davalı|üçüncü kişi)\s*:\s*[^\n]+'),
]

def mask(text: str) -> str:
    for name, pattern in PATTERNS:
        text = re.sub(pattern, '['+name+']', text)
    return text

def public_query(text: str) -> str:
    """Dış kaynağa yalnızca kısa hukuki kavramlar gider; kimlik belirteçleri reddedilir."""
    cleaned = mask(text)
    if cleaned != text or len(text)>180 or '\n' in text or re.search(r'\[[A-Z]+\]', text):
        raise ValueError('Arama ifadesi kişisel veri veya olay anlatımı içeriyor.')
    return text.strip()
