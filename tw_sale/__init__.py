def _tw_sale_post_init(env):
    env['res.config.settings'].create({
        'default_invoice_policy': 'delivery',  # Activate pricelist
    }).execute()

from . import models
from . import report