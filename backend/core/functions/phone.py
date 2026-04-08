import re


def formatPhoneNr(number: str, country_code: str = '+46') -> str:
    """Normalize a phone number into international format."""
    number = re.sub(r'[^0-9+]', '', number)
    if number.startswith('00'):
        number = '+' + number[2:]
    if not number.startswith('+'):
        number = country_code + (number[1:] if number.startswith('0') else number)
    return number
