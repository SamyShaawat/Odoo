# -*- coding: utf-8 -*-
##########################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
##########################################################################
import re

def my_compute_price(variant, pricelist):
    price_dict = pricelist.sudo()._price_get(variant, 1)
    price = list(price_dict.values())[0]
    return round(price, 2)


# List of common country codes (you can expand this list)
country_codes = [
    '+1', '+2','002', '+44', '+49', '+61', '+91', '+81', '+86', '+7', '+34', '+33',
    '+39', '+46', '+31', '+27', '+32', '+90', '+351', '+55', '+52', '+61', '+41'
    # Add more country codes as needed
]


def clean_phone_number(phone_number):
    if phone_number:
        # Remove spaces
        phone_number = phone_number.replace(" ", "")

        # Check if the phone number starts with any country code from the list
        for code in country_codes:
            if phone_number.startswith(code):
                # Remove the country code
                phone_number = phone_number[len(code):]
                break

        # Optionally, remove any non-digit characters (if the phone contains special characters)
        phone_number = re.sub(r'\D', '', phone_number)

        return phone_number
    else:
        return None