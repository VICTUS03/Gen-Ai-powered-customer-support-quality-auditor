import re

def is_luhn_valid(number):
    """Checks if a string of digits passes the Luhn Algorithm."""
    digits = [int(d) for d in re.sub(r'\D', '', number)]
    if len(digits) < 13: return False
    
    # Reverse the digits and apply Luhn logic
    checksum = 0
    reverse_digits = digits[::-1]
    for i, digit in enumerate(reverse_digits):
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0

def mask_pii(text):
    """Redacts PII with smart validation to avoid false positives."""
    
    # 1. Advanced Credit Card Redaction
    # First, find potential 13-16 digit candidates
    card_candidates = re.findall(r'\b(?:\d[ -]*?){13,19}\b', text)
    for candidate in card_candidates:
        if is_luhn_valid(candidate):
            text = text.replace(candidate, '[VALID_CARD_REDACTED]')

    # 2. Email Addresses (Standard)
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    
    # 3. Phone Numbers (Improved to avoid small IDs)
    # Looks for specific phone patterns: (123) 456-7890 or 123-456-7890
    text = re.sub(r'\b(?:\+?\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}\b', '[PHONE]', text)
    
    # 4. SSN
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
    
    return text