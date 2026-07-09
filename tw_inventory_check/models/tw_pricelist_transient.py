# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3: imports of odoo
from odoo.exceptions import UserError as Warning
from odoo import models, fields, api, _
from odoo.tools import html2plaintext

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TWPricelist(models.TransientModel):
    _name = "tw.pricelist.transient"
    _rec_name = "product_id"
    _description = "Check Stock Pricelist"

    # 7: defaults methods
    @api.model
    def _get_default_date(self): 
        return self.env['res.company'].get_default_date()

    def _get_default_branch(self):
        company_ids = False
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1 :
            return company_ids[0].id
        return False

    # 8: fields
    is_sparepart = fields.Boolean(string='Sparepart?', help="Helper variable for sparepart only, indicator to show stock_rfa_approved")
    is_unit = fields.Boolean(string='Unit?', help="Helper variable for unit only")
    harga_beli = fields.Float('Harga Beli')
    harga_jual = fields.Float('Harga Jual')
    harga_jual_bbn_hitam = fields.Float('Harga Jual BBN Hitam')
    harga_jual_bbn_merah = fields.Float('Harga Jual BBN Merah')
    harga_beli_previous = fields.Float('Harga Beli Previous')
    harga_jual_previous = fields.Float('Harga Jual Previous')
    harga_jual_bbn_hitam_previous = fields.Float('Harga Jual BBN Hitam Previous')
    harga_jual_bbn_merah_previous = fields.Float('Harga Jual BBN Merah Previous')
    total_stock = fields.Float('Total Stock')
    stock_intransit = fields.Float('Stock Intransit')
    stock_available = fields.Float('Stock Available')
    stock_reserved = fields.Float('Stock Reserved (All)')
    stock_rfa_approved = fields.Float('Stock RFA / Approved')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(), string='Division Name')

    # 9: relation fields
    company_id = fields.Many2one('res.company', string='Branch', default=_get_default_branch, domain=[('parent_id','!=',False)])
    division_id = fields.Many2one('tw.selection', string='Division', domain=[('type','=','Division')])
    available_division_ids = fields.Many2many('tw.selection', string='Available Division', compute='_compute_available_division_ids')
    product_id = fields.Many2one('product.product', 'Product')
    pricelist_purchase_unit_id = fields.Many2one('product.pricelist', string='Price List Beli Unit', domain=[('type','=','purchase')])
    pricelist_sale_unit_id = fields.Many2one('product.pricelist', string='Price List Jual Unit', domain=[('type','=','sale')])
    pricelist_purchase_sparepart_id = fields.Many2one('product.pricelist', string='Price List Beli Sparepart', domain=[('type','=','purchase')])
    pricelist_sale_sparepart_id = fields.Many2one('product.pricelist', string='Price List Jual Sparepart', domain=[('type','=','sale')])
    pricelist_bbn_hitam_id = fields.Many2one('product.pricelist', string='Price List Jual BBN Plat Hitam', domain=[('type','=','sale_bbn_hitam')])
    pricelist_bbn_merah_id = fields.Many2one('product.pricelist', string='Price List Jual BBN Plat Merah', domain=[('type','=','sale_bbn_merah')])
    pricelist_branch_other_ids = fields.One2many('tw.pricelist.branch.other.transient', 'pricelist_id', readonly=True, copy=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('default_division'):
            division_obj = self.env['tw.selection'].sudo().search([
                ('type','=','Division'),
                ('name','=',self.env.context.get('default_division'))
            ])
            if division_obj:
                res['division_id'] = division_obj.id
        return res

    
    @api.depends('is_sparepart', 'is_unit')
    def _compute_available_division_ids(self):
        for record in self:
            domain = [('type','=','Division')]
            if record.is_sparepart:
                domain.append(('value', 'in', ('Sparepart', 'Service','Umum')))
            if record.is_unit:
                domain.append(('value', 'in', ('Unit', 'Extras','Umum')))
            record.available_division_ids = self.env['tw.selection'].sudo().search(domain).ids
    
    @api.onchange('division_id')
    def _onchange_division_id(self):
        self.product_id = False
        if self.division_id:
            self.division = self.division_id.value
    
    @api.onchange('company_id', 'product_id')
    def onchange_pricelist(self):
        self.pricelist_sale_unit_id = False
        self.pricelist_purchase_unit_id = False
        self.pricelist_bbn_hitam_id = False
        self.pricelist_bbn_merah_id = False
        self.pricelist_purchase_sparepart_id = False
        self.pricelist_sale_sparepart_id = False
        self.harga_beli = False
        self.harga_jual = False
        self.harga_jual_bbn_hitam = False
        self.harga_jual_bbn_merah = False
        self.harga_beli_previous = False
        self.harga_jual_previous = False
        self.harga_jual_bbn_hitam_previous = False
        self.harga_jual_bbn_merah_previous = False
        self.total_stock = False
        self.stock_available = False
        self.stock_reserved = False
        self.stock_rfa_approved = False
        self.pricelist_branch_other_ids = False

        if self.product_id and self.company_id:
            branch_setting_obj = self.env['tw.branch.setting'].get_branch_setting(self.company_id)
            self.pricelist_purchase_unit_id = branch_setting_obj.pricelist_purchase_unit_id
            self.pricelist_sale_unit_id = branch_setting_obj.pricelist_sale_unit_id
            self.pricelist_purchase_sparepart_id = branch_setting_obj.pricelist_purchase_sparepart_id
            self.pricelist_sale_sparepart_id = branch_setting_obj.pricelist_sale_sparepart_id
            self.pricelist_bbn_hitam_id = branch_setting_obj.pricelist_sale_bbn_hitam_id
            self.pricelist_bbn_merah_id = branch_setting_obj.pricelist_sale_bbn_merah_id

            if self.division == 'Unit':
                # pricelist beli unit
                if self.pricelist_purchase_unit_id:
                    item_obj = self._check_item_availability(self.pricelist_purchase_unit_id, self.product_id)
                    if item_obj:
                        price_get_harga_beli = self.pricelist_purchase_unit_id.suspend_security()._price_get(self.product_id, 1)
                        price_harga_beli = price_get_harga_beli[self.pricelist_purchase_unit_id.id]
                        self.harga_beli = price_harga_beli
                        self.harga_beli_previous = price_harga_beli

                # pricelist jual unit
                if self.pricelist_sale_unit_id:
                    item_obj = self._check_item_availability(self.pricelist_sale_unit_id, self.product_id)
                    if item_obj:
                        price_get_harga_jual = self.pricelist_sale_unit_id.suspend_security()._price_get(self.product_id, 1)
                        price_harga_jual = price_get_harga_jual[self.pricelist_sale_unit_id.id]
                        self.harga_jual = price_harga_jual
                        self.harga_jual_previous = price_harga_jual

                # pricelist jual bbn hitam
                if self.pricelist_bbn_hitam_id:
                    item_obj = self._check_item_availability(self.pricelist_bbn_hitam_id, self.product_id)
                    if item_obj:
                        price_get_harga_jual_bbn_hitam = self.pricelist_bbn_hitam_id.suspend_security()._price_get(self.product_id, 1)
                        price_harga_jual_bbn_hitam = price_get_harga_jual_bbn_hitam[self.pricelist_bbn_hitam_id.id]
                        self.harga_jual_bbn_hitam = price_harga_jual_bbn_hitam
                        self.harga_jual_bbn_hitam_previous = price_harga_jual_bbn_hitam

                # pricelist jual bbn merah
                if self.pricelist_bbn_merah_id:
                    item_obj = self._check_item_availability(self.pricelist_bbn_merah_id, self.product_id)
                    if item_obj:
                        price_get_harga_jual_bbn_merah = self.pricelist_bbn_merah_id.suspend_security()._price_get(self.product_id, 1)
                        price_harga_jual_bbn_merah = price_get_harga_jual_bbn_merah[self.pricelist_bbn_merah_id.id]
                        self.harga_jual_bbn_merah = price_harga_jual_bbn_merah
                        self.harga_jual_bbn_merah_previous = price_harga_jual_bbn_merah

                query = """
                    SELECT
                        q.product_id, 
                        l.company_id, 
                        s.state,
                        sum(q.quantity) as qty,
                        sum(q.reserved_quantity) as qty_reserved
                    FROM stock_quant q
                    JOIN stock_location l on q.location_id = l.id
                    JOIN stock_lot s on q.lot_id = s.id
                    WHERE q.product_id = {product_id} 
                        AND l.company_id = {company_id} 
                        AND l.usage in ('internal','transit')
                    GROUP BY
                        q.product_id, l.company_id, s.state
                """.format(
                    product_id=self.product_id.id,
                    company_id=self.company_id.id
                )

                unit_intransit = 0
                unit_available = 0
                unit_reserved = 0

                self._cr.execute(query)
                ress = self._cr.dictfetchall()

                if ress:
                    for x in ress:
                        if x['state'] == 'intransit':
                            unit_intransit += x['qty']
                        elif x['state'] == 'stock':
                            unit_available += x['qty']
                        elif x['state'] == 'reserved':
                            unit_reserved += x['qty']

                unit_tot_qty = unit_intransit + unit_available + unit_reserved
                
                self.stock_intransit = unit_intransit
                self.stock_available = unit_available
                self.stock_reserved = unit_reserved
                self.total_stock = unit_tot_qty

            else:
                # pricelist beli sparepart
                if self.pricelist_purchase_sparepart_id:
                    item_obj = self._check_item_availability(self.pricelist_purchase_sparepart_id, self.product_id)
                    if item_obj:
                        price_get_harga_beli = self.pricelist_purchase_sparepart_id.suspend_security()._price_get(self.product_id, 1)
                        price_harga_beli = price_get_harga_beli[self.pricelist_purchase_sparepart_id.id]
                        self.harga_beli = price_harga_beli
                        self.harga_beli_previous = price_harga_beli
                
                # pricelist jual sparepart
                if self.pricelist_sale_sparepart_id:
                    item_obj = self._check_item_availability(self.pricelist_sale_sparepart_id, self.product_id)
                    if item_obj:
                        price_get_harga_jual = self.pricelist_sale_sparepart_id.suspend_security()._price_get(self.product_id, 1)
                        price_harga_jual = price_get_harga_jual[self.pricelist_sale_sparepart_id.id]
                        self.harga_jual = price_harga_jual
                        self.harga_jual_previous = price_harga_jual

                query_qty_rfa_approved = "0"

                branch_type_md = self.env['tw.selection'].get_selection('BranchType','MD')
                md_branch = self.env['res.company'].search([('branch_type_id','=',branch_type_md.id)],order='id',limit=1)
                branch_type_dl = self.env['tw.selection'].get_selection('BranchType','DL')
                dl_branch = self.env['res.company'].search([('branch_type_id','=',branch_type_dl.id)],order='id',limit=1)

                if self.company_id.branch_type_id == md_branch:
                    query_qty_rfa_approved = """
                        COALESCE((
                            SELECT SUM(sol.product_uom_qty)
                            FROM tw_sale_order_line sol
                            INNER JOIN tw_sale_order so ON sol.order_id = so.id
                            WHERE so.division = 'Sparepart'
                            AND so.state IN ('waiting_for_approval','approved')
                            AND so.company_id = l.company_id
                            AND sol.product_id = q.product_id
                            AND so.location_id = q.location_id
                        ),0) + COALESCE((
                            SELECT SUM(mol.qty)
                            FROM tw_mutation_order_line mol
                            INNER JOIN tw_mutation_order mo ON mol.mutation_order_id = mo.id
                            WHERE mo.division = 'Sparepart'
                            AND mo.state IN ('waiting_for_approval','approved')
                            AND mo.company_id = l.company_id
                            AND mol.product_id = q.product_id
                            AND mo.location_id = q.location_id
                        ),0)
                    """
                elif self.company_id.branch_type_id == dl_branch:
                    query_qty_rfa_approved = """
                        COALESCE((
                            SELECT SUM(wol.product_uom_qty)
                            FROM tw_work_order_line wol
                            INNER JOIN tw_work_order wo ON wol.order_id = wo.id
                            WHERE wo.state IN ('waiting_for_approval','approved')
                            AND wo.company_id = l.company_id
                            AND wol.product_id = q.product_id
                            AND wol.location_id = q.location_id
                        ),0)
                    """

                query_all_qty = """
                    SELECT 
                        l.company_id
                        , p.default_code
                        , t.name AS product_name
                        , q.product_id
                        , q.location_id
                        , COALESCE(intransit.qty_intransit,0) AS qty_intransit
                        , SUM(q.quantity) AS qty_stock
                        , SUM(q.reserved_quantity) AS qty_reserved
                        , {query_qty_rfa_approved} AS qty_rfa_approved
                    FROM stock_quant q
                    INNER JOIN stock_location l ON q.location_id = l.id AND l.usage = 'internal'
                    INNER JOIN res_company b ON l.company_id = b.id
                    LEFT JOIN product_product p ON q.product_id = p.id
                    LEFT JOIN product_template t ON p.product_tmpl_id = t.id
                    LEFT JOIN product_category c ON t.categ_id = c.id 
                    LEFT JOIN product_category c2 ON c.parent_id = c2.id 
                    LEFT JOIN (
                        SELECT 
                            sq.product_id,
                            sq.location_id,
                            SUM(sq.quantity) AS qty_intransit
                        FROM stock_quant sq
                        INNER JOIN stock_location l ON sq.location_id = l.id AND l.usage = 'transit'
                        WHERE sq.product_id = {product_id} and l.company_id = {company_id}
                        GROUP BY
                            sq.product_id,
                            sq.location_id
                    ) AS intransit ON intransit.product_id = q.product_id AND intransit.location_id = q.location_id
                    WHERE (c.name = 'Sparepart' OR c2.name = 'Sparepart') 
                    AND q.product_id = {product_id} and l.company_id = {company_id}
                    GROUP BY
                        l.company_id, 
                        l.warehouse_id,
                        l.complete_name,
                        l.usage,
                        intransit.qty_intransit,
                        p.default_code,
                        t.name,
                        q.product_id,
                        q.location_id
                """.format(
                    query_qty_rfa_approved=query_qty_rfa_approved,
                    product_id=self.product_id.id,
                    company_id=self.company_id.id
                )

                self._cr.execute(query_all_qty)
                ress = self._cr.dictfetchall()

                qty_intransit = 0
                qty_stok = 0
                qty_reserved = 0
                qty_rfa_approved = 0

                if ress:
                    for res in ress:
                        qty_intransit += res['qty_intransit']
                        qty_stok += res['qty_stock']
                        qty_reserved += res['qty_reserved']
                        qty_rfa_approved += res['qty_rfa_approved']

                total_available = qty_stok - (qty_reserved + qty_rfa_approved)

                self.stock_intransit = qty_intransit
                self.stock_available = total_available
                self.stock_reserved = qty_reserved
                self.stock_rfa_approved = qty_rfa_approved
                self.total_stock = qty_stok + qty_intransit

            other_branch_list = []

            if self.division == 'Unit':
                query = """
                    SELECT
                        l.company_id
                        , b.code
                        , b.name
                        , q.product_id
                        , sum(q.quantity)
                    FROM
                        stock_quant q
                    JOIN
                        stock_location l on q.location_id = l.id
                    JOIN
                        stock_lot s on q.lot_id = s.id
                    JOIN
                        res_company b on l.company_id = b.id
                    JOIN
                        tw_selection ts on b.branch_type_id = ts.id
                    WHERE
                        q.product_id = {product_id} and 
                        l.usage in ('internal','transit') and
                        s.state = 'stock' and
                        ts.value = 'DL' and
                        NOT EXISTS (SELECT 1 FROM tw_stock_quant_stock_move_rel rel WHERE rel.quant_id = q.id) and  
                        l.company_id != {company_id}
                    GROUP BY
                        l.company_id,b.code,b.name,q.product_id
                    ORDER BY
                        b.code
                """.format(
                    product_id=self.product_id.id,
                    company_id=self.company_id.id
                )
            else:
                # TODO change this so that qty RFA / Approved di MD / cabang included
                query = """
                    SELECT
                        l.company_id
                        , b.code
                        , b.name
                        , q.product_id
                        , sum(q.quantity)
                    FROM
                        stock_quant q
                    JOIN
                        stock_location l on q.location_id = l.id
                    JOIN
                        res_company b on l.company_id = b.id
                    WHERE
                        q.product_id = {product_id} and 
                        l.usage in ('internal','transit') and 
                        NOT EXISTS (SELECT 1 FROM tw_stock_quant_stock_move_rel rel WHERE rel.quant_id = q.id) and 
                        l.company_id != {company_id}
                    GROUP BY
                        l.company_id,b.code,b.name,q.product_id
                    ORDER BY
                        b.code
                """.format(
                    product_id=self.product_id.id,
                    company_id=self.company_id.id
                )
            
            self._cr.execute(query)
            ress = self._cr.fetchall()

            if ress:
                for res in ress:
                    other_branch_list.append([0, 0, {
                        'branch_code': res[1],
                        'branch_name': res[2],
                        'stock_available': res[4],
                    }])
            
            self.pricelist_branch_other_ids = other_branch_list

    # 12: override methods

    # 13: action methods
    def action_confirm(self):
        # Jika tidak sama bearti ada update harga
        if self.harga_beli_previous != self.harga_beli:
            price_unit_update = self._update_price(self.pricelist_purchase_unit_id,self.harga_beli)
            self.harga_beli_previous = price_unit_update
        if self.harga_jual_previous != self.harga_jual:
            price_unit_update = self._update_price(self.pricelist_sale_unit_id,self.harga_jual)
            self.harga_jual_previous = price_unit_update
        if self.harga_jual_bbn_hitam_previous != self.harga_jual_bbn_hitam:
            price_unit_update = self._update_price(self.pricelist_bbn_hitam_id,self.harga_jual_bbn_hitam)
            self.harga_jual_bbn_hitam_previous = price_unit_update
        if self.harga_jual_bbn_merah_previous != self.harga_jual_bbn_merah:
            price_unit_update = self._update_price(self.pricelist_bbn_merah_id,self.harga_jual_bbn_merah)
            self.harga_jual_bbn_merah_previous = price_unit_update

    def onchange_button(self):
        self.product_id = False
        self.company_id = False
        self.pricelist_sale_unit_id = False
        self.pricelist_purchase_unit_id = False
        self.pricelist_bbn_hitam_id = False
        self.pricelist_bbn_merah_id = False
        self.pricelist_purchase_sparepart_id = False
        self.pricelist_sale_sparepart_id = False
        self.harga_beli = False
        self.harga_jual = False
        self.harga_jual_bbn_hitam = False
        self.harga_jual_bbn_merah = False
        self.harga_beli_previous = False
        self.harga_jual_previous = False
        self.harga_jual_bbn_hitam_previous = False
        self.harga_jual_bbn_merah_previous = False
        self.total_stock = False
        self.stock_intransit = False
        self.stock_available = False
        self.stock_reserved = False
        self.stock_rfa_approved = False
        self.pricelist_branch_other_ids = False

    def action_create_loss_demand(self):
        this = self.sudo()
        form_view_id = self.env.ref('tw_inventory_check.tw_loss_demand_form_view').id
        product_id = this.product_id.id
        company_id = this.company_id.id
        this.onchange_button()
        return {
            'name': 'Create Loss Demand',
            'res_model': 'tw.loss.demand',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'views': [(form_view_id, 'form')],
            'view_mode': 'form',
            'target': 'new',
            'res_id': False,
            'context': {
                'default_readonly_by_pass': True,
                'default_company_id': company_id,
                'default_division': 'Sparepart',
                'default_product_id': product_id,
                'default_is_loss_demand': True
            }
        }

    # 14: private methods
    def _init_false(self):
        self.product_id = False
        self.company_id = False
        self.categ_id = False
        self.pricelist_sale_unit_id = False
        self.pricelist_purchase_unit_id = False
        self.pricelist_bbn_hitam_id = False
        self.pricelist_bbn_merah_id = False
        self.pricelist_purchase_sparepart_id = False
        self.pricelist_sale_sparepart_id = False
        self.harga_beli = False
        self.harga_jual = False
        self.harga_jual_bbn_hitam = False
        self.harga_jual_bbn_merah = False
        self.harga_beli_previous = False
        self.harga_jual_previous = False
        self.harga_jual_bbn_hitam_previous = False
        self.harga_jual_bbn_merah_previous = False
        self.total_stock = False
        self.stock_available = False
        self.stock_reserved = False
        self.stock_rfa_approved = False
        self.pricelist_branch_other_ids = False

    def _get_item_obj(self, pricelist_id, product_id):
        item_obj = self.env['product.pricelist.item'].suspend_security().search([
            ('pricelist_id', '=', pricelist_id.id),
            ('product_tmpl_id', '=', product_id.product_tmpl_id.id),
            ('state','=','active'),
            ('date_start','<=',datetime.now().strftime('%Y-%m-%d %H:%M:%S')), # 12-12-1099
            ('date_end','>=',datetime.now().strftime('%Y-%m-%d %H:%M:%S')), # 12-12-2099
        ])
        return item_obj

    def _check_item_availability(self, pricelist_id, product_id):
        """
        Check item availability because of constraint _get_applicable_rule
        is_only_use_pricelist = True
        """
        item_obj = self._get_item_obj(pricelist_id, product_id)
        if item_obj:
            return True

    def _update_price(self,pricelist_id,price_unit_update):
        pricelist_item_obj = self._get_item_obj(pricelist_id, self.product_id)
        data = {
            'state': 'new',
            'is_update': True,
            'pricelist_id': pricelist_id.id,
            'pricelist_version_id': pricelist_item_obj.pricelist_version_id.id,
            'applied_on': pricelist_item_obj.applied_on,
            'categ_id': pricelist_item_obj.categ_id.id,
            'product_tmpl_id': pricelist_item_obj.product_tmpl_id.id,
            'product_id': pricelist_item_obj.product_id.id,
            'service_category_id': pricelist_item_obj.service_category_id.id,
            'cost_based_on_id': pricelist_item_obj.cost_based_on_id.id,
            'fixed_price': price_unit_update,
            'compute_price': pricelist_item_obj.compute_price,
            'base': pricelist_item_obj.base,
            'base_pricelist_id': pricelist_item_obj.base_pricelist_id.id,
            'date_start': pricelist_item_obj.date_start,
            'date_end': pricelist_item_obj.date_end,
        }
        new_item_obj = self.env['product.pricelist.item'].create(data)
        new_item_obj.action_confirm_update_price()
        return price_unit_update
        
class TWPricelistBranchOther(models.TransientModel):
    _name = "tw.pricelist.branch.other.transient"
    _description = "Check Stock Pricelist Branch Other"

    # 7: defaults methods

    # 8: fields
    branch_code = fields.Char('Branch Code')
    branch_name = fields.Char('Branch Name')
    stock_available = fields.Float('Stock Available')

    # 9: relation fields
    pricelist_id = fields.Many2one('tw.pricelist.transient', 'Pricelist', required=True, ondelete='cascade')
