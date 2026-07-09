# 1: imports of python lib
import base64

# 2: import of known third party lib
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class ResUsersInherit(models.Model):
    _inherit = "res.users"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def verify_signature(self, signed_string, signature):
        api_config_obj = self.env['tw.api.configuration'].sudo().search([
            ('partner_id', '=', self.partner_id.id)
        ], limit=1)
        pubfile = api_config_obj.creds_public_file or self.credential_public_file
        if not pubfile:
            raise Warning(f'Client {self.login} does not has public file!')
        
        # pubfile might be a str, so ensure bytes
        if isinstance(pubfile, str):
            pubfile = pubfile.encode('utf-8')
        
        # decode base64 to bytes
        public_file = base64.b64decode(pubfile)
        pubkey = serialization.load_pem_public_key(public_file, backend=default_backend())
        try:
            # verify the signature send from client (signature and signed_string must also be bytes)
            sign = base64.b64decode(signature)

             # ensure signature is base64-encoded bytes
            if isinstance(signed_string, str):
                signed_string = signed_string.encode('utf-8')
                
            pubkey.verify(sign, signed_string, padding.PKCS1v15(), hashes.SHA256())
        except Exception as err:
            raise Warning(err)
        
        return True

    # 14: private methods