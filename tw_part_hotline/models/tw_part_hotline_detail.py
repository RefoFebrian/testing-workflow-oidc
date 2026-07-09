# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning, ValidationError

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib
class PartHotlineDetail(models.Model):
    _name = "tw.part.hotline.detail"
    _description = "TW Part Hotline Detail"

    # 7: defaults methods
    def _get_default_date(self):
        return fields.Date.context_today(self)

    @api.depends('product_id')
    def compute_product_code(self):
        for record in self:
            record.name = record.product_id.default_code

    @api.depends('product_id','qty','price')
    def compute_subtotal(self):
        for record in self:
            price_tax = 0
            price_subtotal = 0
            price = record.price * (1-(0.0) / 100.0)    
            taxes = record.tax_id.compute_all(
                price_unit=price,
                quantity=record.qty,
                product=record.product_id
                )
            if taxes.get('taxes',False):
                price_tax = taxes.get('taxes',0)[0].get('amount',0)
                price_subtotal = taxes.get('taxes',0)[0].get('base',0)
            record.price_tax = price_tax
            record.subtotal = price_subtotal

    # 8: fields
    name = fields.Char('Description',compute="compute_product_code",readonly=True)
    no_po = fields.Char('No Purchase Order')
    no_wo = fields.Char('No Work Order')
    no_ps = fields.Char('No Part Sales')
    po_date = fields.Date('Tgl Purchase Order')
    qty = fields.Float('Qty',default=1)
    qty_po = fields.Float('Qty PO')
    qty_available = fields.Float('Qty Available', compute='_compute_qty_available', store=True)
    qty_reserved = fields.Float('Qty Reserved', compute='_compute_qty_reserved', store=True)
    price = fields.Float('Price')
    price_tax = fields.Float('Price Tax',compute="compute_subtotal",store=True)
    subtotal = fields.Float('Subtotal',compute="compute_subtotal",store=True)
    is_available = fields.Boolean('Available') 
    state = fields.Selection([
        ('draft','Draft'),
        ('open','Open'),
        ('reserved','Reserved')],default='draft')
    status_po = fields.Selection([('draft','Draft'),('done','Done')],default='draft',string="State PO")

    # 9: relation fields
    hotline_id = fields.Many2one('tw.part.hotline','Part Hotline',ondelete='cascade')
    product_id = fields.Many2one('product.product','Product', domain=[('division','=','Sparepart')])
    tax_id = fields.Many2many('account.tax', 'part_hotline_tax', 'part_hotline_id', 'tax_id', 'Taxes') 

    # 10: constraints & sql constraints
    @api.constrains('hotline_id','product_id')
    def _check_hotline_product_unique(self):
        for rec in self:
            if rec.hotline_id and rec.product_id:
                if self.search([('hotline_id', '=', rec.hotline_id.id), ('product_id', '=', rec.product_id.id), ('id', '!=', rec.id)]):
                    raise ValidationError('Product tidak boleh duplicat !')

    # 11: compute/depends & on change methods
    @api.onchange('product_id')
    def onchange_product(self):
        categ_ids = self.env['product.category'].sudo().get_child_ids('Sparepart')
        dom = {'product_id':[('categ_id','in',categ_ids)]}
        if self.product_id:
            pricelist = self.hotline_id.company_id.branch_setting_id.pricelist_sale_sparepart_id
            if not pricelist:
                raise ValidationError('Pricelist Sparepart tidak ditemukan di Branch Setting %s !' % self.hotline_id.company_id.branch_setting_id.name)
            if self._origin:
                pricelist = self._origin.hotline_id.company_id.branch_setting_id.pricelist_sale_sparepart_id
            price_get = pricelist.with_company(self.hotline_id.company_id.id)._price_get(self.product_id,self.qty)
            price = price_get[pricelist.id]
            self.price = price
            self.tax_id = self.product_id.taxes_id

    @api.depends('hotline_id.work_order_id.state','hotline_id.part_sales_id.state')
    def _compute_qty_reserved(self):
        for rec in self:
            qty_reserved = 0
            if not rec.hotline_id or not rec.product_id:
                rec.qty_reserved = 0
                continue

            # Search WO lines linked to this hotline
            wo_lines = self.env['tw.work.order.line'].sudo().search([
                ('part_hotline_id', '=', rec.hotline_id.id),
                ('product_id', '=', rec.product_id.id),
                ('order_id.state', 'not in', ['draft', 'cancel', 'unused']),
            ])
            qty_reserved += sum(wo_lines.mapped('product_uom_qty'))

            # Search PS lines linked to this hotline
            ps_lines = self.env['tw.part.sales.line'].sudo().search([
                ('part_hotline_id', '=', rec.hotline_id.id),
                ('product_id', '=', rec.product_id.id),
                ('order_id.state', 'not in', ['draft', 'cancel', 'unused']),
            ])
            qty_reserved += sum(ps_lines.mapped('product_uom_qty'))
            rec.qty_reserved = qty_reserved

    @api.depends('qty_po', 'qty_reserved')
    def _compute_qty_available(self):
        for rec in self:
            rec.qty_available = rec.qty_po - rec.qty_reserved

    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        create = super(PartHotlineDetail,self).create(vals_list)
        for rec in create:
            if rec.state == 'draft':
                if rec.hotline_id.state != 'draft':
                    raise Warning ('Error')
        return create