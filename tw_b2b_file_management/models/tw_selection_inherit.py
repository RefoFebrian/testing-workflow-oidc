from odoo import models


class MftFileExtensionSelection(models.Model):
    _inherit = "tw.selection"
    
    def get_mft_file_extension_options(self, name=None):
        domain = [('type','=','MftFileExtension')]
        if name:
            domain.append(('name', '=', name))
        
        return [(select.value, select.name) for select in self.search(domain)]