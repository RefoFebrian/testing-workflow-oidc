# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, timedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TWLossDemand(models.Model):
    _name = "tw.loss.demand"
    _description = "Loss Demand"

    # 7: defaults methods
  
    def _get_default_date(self):
        return fields.Date.today()

    def _get_default_branch(self):
        company_ids = False
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1 :
            return company_ids[0].id
        return False

    # 8: fields
    date = fields.Date('Tanggal',default=_get_default_date)
    mobile = fields.Char('Mobile')
    qty = fields.Integer('Qty', default=1)
    is_loss_demand = fields.Boolean('Loss Demand', default=False)
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())

    # 9: relation fields
    company_id = fields.Many2one('res.company', string ='Branch', default=_get_default_branch, domain=[('parent_id','!=',False)])  
    product_id = fields.Many2one('product.product', string ='Product', domain=[('is_asset','=',False),('division','=','Sparepart')])
    partner_id = fields.Many2one('res.partner',string='Customer')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id and self.partner_id.mobile:
            self.mobile = self.partner_id.mobile

    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list): 
        for values in vals_list:       
            value = []
            branch = values.get('company_id')
            product = values.get('product_id')
            qty = values.get('qty') or 0
            if qty <= 0:
                raise ValidationError(_('Jumlah Qty Minimal 1 !'))

            if branch and product :
                query = """ 
                    select l.company_id
                        , p.default_code
                        , t.name as product_name
                        , q.product_id
                        , sum(case when q.consolidated_date IS NULL THEN q.quantity ELSE 0 END) as qty_titipan
                        , sum(case when q.consolidated_date IS NOT NULL THEN q.quantity ELSE 0 END) as qty_stock
                        , case WHEN l.usage='internal' then COALESCE(
                            (select sum(product_uom_qty) from stock_move sm left join stock_picking sp on sm.picking_id=sp.id 
                                left join stock_picking_type spt on sp.picking_type_id=spt.id
                                left join stock_location stl on sm.location_dest_id=stl.id 
                                where spt.code in ('outgoing','interbranch_out') 
                                    and sp.company_id=l.company_id 
                                    and sp.state not in ('draft','cancel','done') 
                                    and sp.division='Sparepart' 
                                    and sm.product_id=q.product_id
                            ),0
                        ) 
                        else 0 end as qty_reserved_end
                        from stock_quant q
                        INNER JOIN stock_location l ON q.location_id = l.id AND l.usage = 'internal'
                        LEFT JOIN product_product p ON q.product_id = p.id
                        LEFT JOIN product_template t ON p.product_tmpl_id = t.id
                        LEFT JOIN product_category c ON t.categ_id = c.id 
                        LEFT JOIN product_category c2 ON c.parent_id = c2.id 
                        WHERE (c.name = 'Sparepart' or c2.name = 'Sparepart')  and q.product_id = %s and l.company_id = %s
                        group by l.company_id, l.warehouse_id, l.complete_name, l.usage, p.default_code, t.name, q.product_id
                        """%(product,branch)
                self._cr.execute (query)

                ress = self._cr.fetchall()
            
                qty_intransit = 0
                qty_reserved = 0
                qty_stok = 0

                for x in ress :
                    qty_intransit += x[4]
                    qty_reserved += x[6]
                    qty_stok += x[5]

                total_available = qty_stok - qty_reserved
                stock_intransit = qty_intransit
                stock_available = total_available
                stock_reserved = qty_reserved
                total_stock = qty_stok + qty_intransit

                if total_stock > 0 :
                    raise ValidationError(_('Perhatian ! Stock masih Tersedia !')) 

        create= super(TWLossDemand,self).create(vals_list)
        return create

    # 13: action methods
    def action_save_loss_demand(self):
        self.write({
            'company_id': self.company_id.id,
            'product_id': self.product_id.id,
            'date': self.date,
            'partner_id': self.partner_id.id,
            'mobile': self.mobile,
            'division': self.division,
            'qty': self.qty,
            'is_loss_demand': False
        })

    # 14: private methods
