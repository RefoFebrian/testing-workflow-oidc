from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

import logging
_logger = logging.getLogger(__name__)

class RPABranchSetting(models.Model):
    _inherit = "tw.branch.setting"
   
    rpa_additional_location_id = fields.Many2one('stock.location', string="Location RPA Additional")
    rpa_topup_location_id = fields.Many2one('stock.location', string="Location RPA Topup/Simpart")
    rpa_hotline_location_id = fields.Many2one('stock.location', string="Location RPA Hotline")
    rpa_backup_hotline_location_id = fields.Many2one('stock.location', string="Location RPA Backup Hotline")

    def _check_rpa_branch_locations(self, branch_code):
        branch_config = self.search([('company_id.code', '=', branch_code)], limit=1)
        _logger.info(f"Branch Config Name {branch_config.name}")
        if not branch_config:
            raise Warning(f"Branch Config {branch_code} does not exists")
        
        if not branch_config.rpa_additional_location_id:
            raise Warning("Location RPA Additional is not defined in the Branch Configuration!")
        elif not branch_config.rpa_topup_location_id:
            raise Warning("Location RPA Topup/Simpart is not defined in the Branch Configuration!")
        elif not branch_config.rpa_hotline_location_id:
            raise Warning("Location RPA Hotline is not defined in the Branch Configuration!")
        elif not branch_config.rpa_backup_hotline_location_id:
            raise Warning("Location RPA Backup Hotline is not defined in the Branch Configuration!")
        
        return branch_config