#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import AccessError, UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class productProduct(models.Model):
    _inherit = "product.product"
    _order = "id desc"
    _rec_names_search = ['name', 'default_code']

    # 7: defaults methods

    # 8: fields
    group_part =  fields.Selection([
       ('HGP','HGP'),
       ('OIL','OIL'),
       ('HGA','HGA'),],string='Group Part') 
    part_component = fields.Selection([
       ('E','Engine'),
       ('F','Frame'),
       ('L','Electrical'),],string='Component') 
    part_important = fields.Selection([
        ('Important Part','Important Part'),
        ('Additional Part','Additional Part'),
        ('Safety Part','Safety Part'),
        ('Other Part','Other Part'),], string='Important') 
    rank = fields.Selection([
        ('A','A'),
        ('B','B'),
        ('C','C'),
        ('D','D'),
        ('E','E'),
        ('F','F'),],string='Rank')
    life_time = fields.Selection([
        ('L','Long'),
        ('S','Sort'),
        ('O','Other'),],string='Long/Short Life Time')
    part_import = fields.Selection([
        ('M','Local'),
        ('Y','Import'),],default='M',string='Import/Local')
    is_fast_moving = fields.Boolean(string='Fast Moving')
    service_frt = fields.Float('Flate Rate Time')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(),compute='_compute_division_from_categ_id',store=True)

    # 9: relation fields
    
    #? Remove domain=[('attribute_line_id.value_count', '>', 1)] supaya produk dengan 1 attribute juga bisa muncul
    product_template_variant_value_ids = fields.Many2many('product.template.attribute.value', relation='product_variant_combination', domain=[], string="Variant Values", ondelete='restrict')
    
    
    # 10: constraints & sql constraints

    # 10: compute/depends & on change methods
    @api.depends('categ_id')
    def _compute_division_from_categ_id(self):
        for prod in self:
            if prod.categ_id:
                prod.division = self.product_tmpl_id.get_division_from_categ_id(prod.categ_id)
            else:
                prod.division = False

    # 12: override methods   
    @api.depends('name', 'default_code', 'product_tmpl_id')
    @api.depends_context('display_default_code', 'seller_id', 'company_id', 'partner_id', 'lang')
    def _compute_display_name(self):
        from odoo.tools import unique

        def get_display_name(name, code):
            if self._context.get('display_default_code', True) and code:
                return f'[{code}] {name}'
            return name

        partner_id = self._context.get('partner_id')
        if partner_id:
            partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
        else:
            partner_ids = []
        company_id = self.env.context.get('company_id')

        # all user don't have access to seller and partner
        # check access and use superuser
        self.check_access("read")

        product_template_ids = self.sudo().product_tmpl_id.ids

        if partner_ids:
            # prefetch the fields used by the `display_name`
            supplier_info = self.env['product.supplierinfo'].sudo().search_fetch(
                [('product_tmpl_id', 'in', product_template_ids), ('partner_id', 'in', partner_ids)],
                ['product_tmpl_id', 'product_id', 'company_id', 'product_name', 'product_code'],
            )
            supplier_info_by_template = {}
            for r in supplier_info:
                supplier_info_by_template.setdefault(r.product_tmpl_id, []).append(r)

        for product in self.sudo():
            variant = product.product_template_attribute_value_ids._get_combination_code()

            name = variant and "%s (%s)" % (product.name, variant) or product.name
            sellers = self.env['product.supplierinfo'].sudo().browse(self.env.context.get('seller_id')) or []
            if not sellers and partner_ids:
                product_supplier_info = supplier_info_by_template.get(product.product_tmpl_id, [])
                sellers = [x for x in product_supplier_info if x.product_id and x.product_id == product]
                if not sellers:
                    sellers = [x for x in product_supplier_info if not x.product_id]
                # Filter out sellers based on the company. This is done afterwards for a better
                # code readability. At this point, only a few sellers should remain, so it should
                # not be a performance issue.
                if company_id:
                    sellers = [x for x in sellers if x.company_id.id in [company_id, False]]
            if sellers:
                temp = []
                for s in sellers:
                    seller_variant = s.product_name and (
                        variant and "%s (%s)" % (s.product_name, variant) or s.product_name
                        ) or False
                    temp.append(get_display_name(seller_variant or name, s.product_code or product.default_code))

                product.display_name = ", ".join(unique(temp))
            else:
                product.display_name = get_display_name(name, product.default_code)

    @api.model_create_multi
    def create(self,vals_list):
        products = super(productProduct, self.with_context(create_product_product=True)).create(vals_list)
        return products
    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            import re
            parts = name.split('|', 1)

            if len(parts) == 2:
                code_part = parts[0].strip()
                color_part = parts[1].strip()

                args = [
                    ('default_code', '=ilike', code_part),
                    (
                        'product_template_variant_value_ids.product_attribute_value_id.code',
                        '=ilike',
                        color_part
                    )
                ] + args
            else:
                args = ['|',
                    ('name', operator, name),
                    ('default_code', operator, name)
                ] + args

        records = self.search(args, limit=limit)
        return [(rec.id, rec.display_name) for rec in records.sudo()]

    def get_formview_action(self, access_uid=None):
        """ Override this method in order to redirect many2one towards the right model depending on access_uid """
        user = self.env.user
        if access_uid:
            user = self.env['res.users'].browse(access_uid).sudo()
        if not user.has_group('tw_product.group_tw_product_product_form_read'):
            raise AccessError(_("You do not have access to this document."))
            
        res = super().get_formview_action(access_uid=access_uid)
        return res

    # 13: action method

    # 14: private method
    def _get_product_ids_by_division(self, division):
        get_product_query = """
            SELECT pp.id
                FROM product_product pp
                    JOIN product_template pt ON pp.product_tmpl_id = pt.id
                    JOIN product_category pc ON pt.categ_id = pc.id
                    JOIN product_category pc_p ON pc.parent_id = pc_p.id
                        WHERE pc_p.name = '%s'
        """ % (division)
        self._cr.execute(get_product_query)
        product_ress = self._cr.fetchall()
        return product_ress or False
 
    def _get_account(self, product_obj):
        account = False
        if product_obj:
            account = product_obj.property_account_income.id

        if not account:
            account = product_obj.categ_id.property_account_income_categ.id
            if not account:
                account = product_obj.categ_id.parent_id.property_account_income_categ.id
        return account
    
    def _get_stock_account(self):
        self.ensure_one()
        if self.categ_id.property_stock_account_input_categ_id:
            return self.categ_id.property_stock_account_input_categ_id.id
        elif self.categ_id.parent_id.property_stock_account_input_categ_id:
            return self.categ_id.parent_id.property_stock_account_input_categ_id.id
        elif self.property_account_income_id:
            return self.property_account_income_id.id
        
        raise Warning(_(f"Product {self.name} does not have account income"))
    
    def get_available_serial(self, location_id):
        for product in self:
            quants = self.env['stock.quant'].search([(
                'product_id', '=', product.id),
                ('location_id', '=', location_id),
                ('lot_id.state', '=', 'stock')
            ])
            serial_ids = {quant.lot_id.id for quant in quants if quant.lot_id}
            return list(serial_ids)
     
    def _get_product_desciption(self):
        self.ensure_one()
        name = self.display_name
        if self.description_sale:
            name += '\n' + self.description_sale
        
        return name
    
    def _get_unit_product_id(self,unit_code,color_code):
        query = f"""
            SELECT
                product.id,
                product.default_code,
                attr_value.code
                FROM product_product product
                LEFT JOIN product_variant_combination variant ON product.id = variant.product_product_id
                LEFT JOIN product_template_attribute_value attr ON variant.product_template_attribute_value_id = attr.id
                LEFT JOIN product_attribute_value attr_value ON attr.product_attribute_value_id = attr_value.id
            WHERE product.default_code = '{unit_code}' and attr_value.code = '{color_code}' 
        """
        self._cr.execute(query)
        data = self._cr.fetchone()
        if data:
            return data[0]
        
        return False
   
    def _get_sparepart_product_id(self,unit_code):
        query = f"""
            SELECT
                product.id,
                product.default_code
                FROM product_product product
            WHERE product.default_code = '{unit_code}' 
        """
        self._cr.execute(query)
        data = self._cr.fetchone()
        if data:
            return data[0]
        
        return False
