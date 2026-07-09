# -*- coding: utf-8 -*-

# 1: imports of python lib
import pytz
from datetime import datetime
from ast import literal_eval
from lxml import etree

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import frozendict
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwFakturPajakMixin(models.AbstractModel):
    _name = "tw.faktur.pajak.mixin"
    _description = "Faktur Pajak Mixin"
    

    # 8: Fields
    is_combined_tax = fields.Boolean('Pajak Gabungan?')

    # 9: Relation Fields
    faktur_pajak_out_id = fields.Many2one('tw.faktur.pajak.out', string="Faktur Pajak Out")
    number_faktur_pajak = fields.Char(
        string='Number Faktur Pajak',
        compute='_compute_number_faktur_pajak',
        inverse='_inverse_number_faktur_pajak',
        store=True,
    )
    date_faktur_pajak = fields.Date(
        string='Tanggal Faktur Pajak',
        compute='_compute_date_faktur_pajak',
        inverse='_inverse_date_faktur_pajak',
        store=True,
    )
    
    # 10: private method
    
    @api.depends('faktur_pajak_out_id', 'faktur_pajak_out_id.name')
    def _compute_number_faktur_pajak(self):
        """
        Compute number_faktur_pajak from faktur_pajak_out_id.name if exists.
        Keep existing value if no relation is set.
        """
        for record in self:
            if record.faktur_pajak_out_id:
                record.number_faktur_pajak = record.faktur_pajak_out_id.name
            # If no faktur_pajak_out_id, keep the existing/manual value
            elif not record.number_faktur_pajak:
                record.number_faktur_pajak = False

    def _inverse_number_faktur_pajak(self):
        """
        Allow manual input of number_faktur_pajak when faktur_pajak_out_id is not set.
        """
        pass  # Just allow the value to be stored

    @api.depends('faktur_pajak_out_id', 'faktur_pajak_out_id.date')
    def _compute_date_faktur_pajak(self):
        """
        Compute date_faktur_pajak from faktur_pajak_out_id.date if exists.
        Keep existing value if no relation is set.
        """
        for record in self:
            if record.faktur_pajak_out_id:
                record.date_faktur_pajak = record.faktur_pajak_out_id.date
            # If no faktur_pajak_out_id, keep the existing/manual value
            elif not record.date_faktur_pajak:
                record.date_faktur_pajak = False

    def _inverse_date_faktur_pajak(self):
        """
        Allow manual input of date_faktur_pajak when faktur_pajak_out_id is not set.
        """
        pass  # Just allow the value to be stored

    def scheduller_faktur_pajak(self,context=None):
        """
        Override this in sub modules with use faktur pajak mixin
        """
        pass

    def get_number_faktur_pajak(self):
        faktur_pajak_out = self.env['tw.faktur.pajak.out']
        return faktur_pajak_out.get_number_of_faktur_pajak(self._name, self.id)
       
    
        
