# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwApiConfigurationInherit(models.Model):
    _inherit = "tw.api.configuration"

    # 7: defaults methods

    # 8: fields
    region = fields.Char('Region')
    bucket = fields.Char('Bucket')
    source_prefix = fields.Char('Source Prefix')
    destination_prefix = fields.Char('Destination Prefix')

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def _get_config_aws(self):
        config_obj = self.get_api_config('aws')
        if not config_obj:
            return False
        
        result = {
            'aws_access_key': config_obj.api_key,
            'aws_secret_key': config_obj.api_secret,
            'region': config_obj.region,
            'bucket': config_obj.bucket,
            'source_prefix': config_obj.source_prefix,
            'destination_prefix': config_obj.destination_prefix
        }
        return result