# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError

# 5: local imports

# 6: Import of unknown third party lib


class TwSalesProgramLine(models.Model):
    _name = "tw.sales.program.line"
    _description = "Master Sales Program Line"

    # 7: defaults methods

    # 8: fields
    qty = fields.Integer('Qty',default=1)
    amount_dp = fields.Float('DP Minimal')
    discount_ahm = fields.Float('Diskon AHM')
    discount_md = fields.Float('Diskon MD')
    discount_dealer = fields.Float('Diskon Dealer')
    discount_finco = fields.Float('Diskon Finco')
    discount_others = fields.Float('Diskon Others')
    discount_total = fields.Float('Total Diskon', compute='_compute_amount_line')
    dp_type = fields.Selection([
        ('min', 'Min'),
        ('max', 'Max')
    ], string='Tipe DP')

    # 9: relation fields
    sales_program_id = fields.Many2one('tw.sales.program', string='Sales Program')
    sales_program_type_id = fields.Many2one('tw.selection', string='Tipe Sales Program', domain=[('type','=','MasterSalesProgram')])
    sales_program_type_name = fields.Char('Sales Program Type', related='sales_program_type_id.value')

    # 10: constraints & sql constraints
    @api.constrains('qty')
    def _check_qty(self):
        for data in self:
            if data.sales_program_type_name == 'Program Subsidi Barang':
                if data.qty < 1:
                    raise ValidationError(_('Qty harus > 0'))

    # 11: compute/depends & on change methods
    @api.depends('discount_ahm', 'discount_md', 'discount_dealer', 'discount_finco', 'discount_others')
    def _compute_amount_line(self):
        """
        This method is used to compute get discount total for each line data.
        """
        for line in self:
            price = (line.discount_ahm or 0.0) + (line.discount_md or 0.0) + (line.discount_dealer or 0.0) + (line.discount_finco or 0.0) + (line.discount_others or 0.0)
            line.discount_total = price

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        create = super(TwSalesProgramLine, self).create(vals_list)
        for key, vals in enumerate(vals_list):
            line_obj = create[key]
            if not line_obj.sales_program_type_id:
                line_obj.sales_program_type_id = line_obj.sales_program_id.sales_program_type_id.id

        return create
    
    # 13: action methods

    # 14: private methods