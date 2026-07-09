STATE_MAPPING = {
    'success': 'unpaid',
    'initiated': 'draft',
    'paying': 'paid',
    'pending': 'unpaid',
    'refunded': 'declined',
    'canceled': 'declined',
    'failed': 'invalid',
    'not found': 'invalid',
    'Successfully': 'paid'
}

STATE_CODE_MAPPING = {
    '00': '1',
    '01': '2',
    '02': '1',
    '03': '2',
    '04': '0',
    '05': '0',
    '06': '0',
    '07': '0',
}

def flatten_dict(dictionary):
    flatten = {}
    for key, value in dictionary.items():
        if isinstance(value, list):
            for v in value:
                flatten.update(flatten_dict(v))
        elif isinstance(value, dict):
            flatten.update(value)
        else:
            flatten.update({ key: value })
    
    return flatten