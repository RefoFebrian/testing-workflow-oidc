# The currencies supported by BCA, in ISO 4217 format.
SUPPORTED_CURRENCIES = [
    'IDR',
    'PHP',
]

# To correctly allow lowest decimal place rounding
CURRENCY_DECIMALS = {
    'IDR': 0,
    'PHP': 0,
}

# The codes of the payment methods to activate when BCA is activated.
DEFAULT_PAYMENT_METHOD_CODES = {
    # Primary payment methods.
    'card',
    'dana',
    'ovo',
    'qris',

    # Brand payment methods.
    'visa',
    'mastercard',
}

# Mapping of payment code to channel code according to BCA API
PAYMENT_METHODS_MAPPING = {
    'transfer': ['BNI', 'MANDIRI', 'PERMATA', 'BRI', 'BCA'],
    'virtual_account': ['BNI', 'MANDIRI', 'PERMATA', 'BRI', 'BCA'],
    'bank_bca': ['BCA'],
    'bank_permata': ['PERMATA'],
    'bpi': ['DD_BPI'],
    'card': ['CREDIT_CARD'],
    'maya': ['PAYMAYA'],
}

# Mapping of transaction states to BCA payment statuses.
PAYMENT_STATUS_MAPPING = {
    'draft': (),
    'pending': ('PENDING'),
    'done': ('SUCCEEDED', 'PAID', 'CAPTURED', 'SETTLED'),
    'cancel': ('CANCELLED', 'EXPIRED'),
    'error': ('FAILED',)
}