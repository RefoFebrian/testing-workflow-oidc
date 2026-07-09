import phonenumbers

def sanitize(phone_number):
    if not phone_number.startswith('+'):
        phone_number = f'+{phone_number}'
    try:
        phone_nbr = phonenumbers.parse(phone_number)
        is_valid = phonenumbers.is_valid_number(phone_nbr)
        print(f"Parsed: {phone_number}, Valid: {is_valid}")
        if is_valid:
            number_only = phonenumbers.format_number(phone_nbr, phonenumbers.PhoneNumberFormat.NATIONAL).replace(' ', '').replace('-', '')
            print(f"Sanitized: {number_only}")
    except Exception as e:
        print(f"Error: {e}")

sanitize("87738917694")
sanitize("6287738917694")
sanitize("087738917694")
