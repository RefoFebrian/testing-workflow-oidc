# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, api

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwPurchaseOrderAccountMove(models.Model):
    _inherit = "account.move"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def _get_sequence_name(self):
        """
        Generate sequence name untuk vendor bill dari PO berdasarkan division.
        - Division Unit → prefix 'PU'
        - Division Sparepart → prefix 'PS'
        """
        self.ensure_one()
        
        # Hanya untuk vendor bill
        if self.move_type != 'in_invoice':
            if hasattr(super(), '_get_sequence_name'):
                return super()._get_sequence_name()
            return False
        
        # Cek apakah berasal dari PO dan division Unit/Sparepart
        is_from_po = self.ref and self.ref.startswith('PO/')
        
        if is_from_po and self.division and self.company_id:
            prefix = False
            if self.division == 'Unit':
                prefix = 'PU'
            elif self.division == 'Sparepart':
                prefix = 'PS'
            
            if prefix:
                return self.env['ir.sequence'].with_company(
                    self.company_id
                ).get_sequence_code(prefix, self.company_id.code)
        
        # Fallback ke method parent jika ada
        if hasattr(super(), '_get_sequence_name'):
            return super()._get_sequence_name()
        return False
