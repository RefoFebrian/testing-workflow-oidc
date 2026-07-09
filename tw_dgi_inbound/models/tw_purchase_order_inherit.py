# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _

# 4: imports from odoo modules
from odoo.exceptions import UserError

# 5: local imports

# 6: Import of unknown third party lib


class TwPurchaseOrderDGI(models.Model):
    _name = "purchase.order"
    _inherit = ["purchase.order", "tw.dgi.info.mixin"]

    # 8: fields
    md_reference_po = fields.Char(
        string='MD Reference PO',
        index=True,
        help="No Purchase Order dari Main Dealer (DGI)",
        copy=False,
    )
    md_reference_sl = fields.Char(
        string='MD Reference SL',
        index=True,
        help="No Shipping List dari Main Dealer (DGI)",
        copy=False,
    )
    is_dgi = fields.Boolean(
        string='Is DGI',
        default=False,
        help="Flag apakah PO ini berasal dari DGI",
        copy=False,
    )
    dgi_get_date = fields.Datetime(
        string='DGI Get Date',
        help="Tanggal data diambil dari DGI",
        copy=False,
    )
    dgi_get_uid = fields.Many2one(
        comodel_name='res.users',
        string='DGI Get By',
        help="User yang mengambil data dari DGI",
        copy=False,
    )

    # 13: action methods
    def action_open_dgi_uinb_wizard(self):
        """Open DGI Unit Inbound wizard from Purchase Order list or form."""
        company_id = self.company_id.id if self and len(self) == 1 else self.env.company.id
        po_id = self.md_reference_po if self and len(self) == 1 else False
        return {
            'name': _('DGI Unit Inbound'),
            'type': 'ir.actions.act_window',
            'res_model': 'tw.dgi.uinb.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_company_id': company_id,
                'default_po_id': po_id or False,
            },
        }

    def action_open_dgi_pinb_wizard(self):
        """Open DGI Part Inbound wizard from Purchase Order list or form."""
        company_id = self.company_id.id if self and len(self) == 1 else self.env.company.id
        po_id = self.md_reference_po if self and len(self) == 1 else False
        return {
            'name': _('DGI Part Inbound'),
            'type': 'ir.actions.act_window',
            'res_model': 'tw.dgi.pinb.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_company_id': company_id,
                'default_po_id': po_id or False,
            },
        }

    def action_show_dgi_info(self):
        """Override to pass PO specific context to DGI Info Wizard"""
        res = super().action_show_dgi_info()
        res['context'].update({
            'default_md_reference_po': self.md_reference_po,
            'default_md_reference_sl': self.md_reference_sl,
        })
        return res
