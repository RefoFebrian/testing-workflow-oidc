#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib
import itertools
import psycopg2
import logging
from functools import reduce
from lxml import etree

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, tools, _
from odoo.fields import Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, AccessError, ValidationError

# 5: local imports

# 6: Import of unknown third party lib


class productTemplate(models.Model):
    _inherit = "product.template"
    _order = "id desc"
    _rec_names_search = ['name', 'default_code']
    _logger = logging.getLogger(__name__)

    # 7: defaults methods

    # 8: fields

    reference_code_bundling = fields.Char('Bundling dari', compute='_compute_reference_code_bundling', store=True)
    factur_code = fields.Char('Kode Faktur')
    default_code = fields.Char('Internal Reference') # ? Inherit this default field for deleting its compute function
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(), compute='_compute_division_from_categ_id',store=True)
    engine_code = fields.Char('Kode Mesin', help='Previously known as kd_mesin.')

    # 9: relation fields
    product_origin_id = fields.Many2one('product.template', string='Product Origin', help='Produk awal sebelum dijadikan produk bundling')
    part_unit_id = fields.Many2one('tw.unit.parts', string="Unit Parts")
    company_id = fields.Many2one('res.company', 'Branch', index=True)

    # 10: constraints & sql constraints

    # 10: compute/depends & on change methods
    @api.depends('categ_id')
    def _compute_division_from_categ_id(self):
        for prod in self:
            if prod.categ_id:
                prod.division = self.get_division_from_categ_id(prod.categ_id)
            else:
                prod.division = False

    @api.depends('product_variant_ids', 'product_variant_ids.default_code')
    def _compute_default_code(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.default_code = template.product_variant_ids.default_code
        for template in (self - unique_variants):
            for code in self.product_variant_ids :
                template.default_code = code.default_code
    
    @api.depends('product_origin_id')
    def _compute_reference_code_bundling(self):
        for prod in self:
            if prod.product_origin_id:
                prod.reference_code_bundling = prod.product_origin_id.default_code
            else:
                prod.reference_code_bundling = False

    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        action_name = self.env.context.get('action_name')
        if action_name:
            for vals in vals_list:
                valid_category = self.get_category_name(vals, action_name)
                if not valid_category:
                    raise ValidationError(_("Form ini adalah menu untuk Create Product %s\nPeriksa kembali field Category atau navigasi ke menu sesuai kategori yang ingin dibuat.") % (action_name))
        product_template = super(productTemplate, self).create(vals_list)
        return product_template

    def write(self, vals):
        # Pengecekan Form edit
        if not vals.get('categ_id') and self.categ_id:
            vals['categ_id'] = self.categ_id.id
        action_name = self.env.context.get('action_name')
        if action_name:
            valid_category = self.get_category_name(vals, action_name)
            if not valid_category:
                raise ValidationError(_("Form ini adalah menu untuk Update Product %s\nPeriksa kembali field Category atau navigasi ke menu sesuai kategori yang ingin diupdate.") % (action_name))

        # Pengecekan duplikat attribute values. Penting untuk migrasi supaya attribute line di template tidak duplikat.
        vals = self._prepare_write_vals(vals)

        product_template = super(productTemplate, self).write(vals)
        if 'active' in vals and not vals.get('active'):
            self.with_context(active_test=False).mapped('product_variant_ids').write({'active': vals.get('active')})
        return product_template

    def get_formview_action(self, access_uid=None):
        """ Override this method in order to redirect many2one towards the right model depending on access_uid """
        user = self.env.user
        if access_uid:
            user = self.env['res.users'].browse(access_uid).sudo()
        if not user.has_group('tw_product.group_tw_product_template_form_read'):
            raise AccessError(_("You do not have access to this document."))
            
        res = super().get_formview_action(access_uid=access_uid)
        return res

    # 13: action methods

    # 14: private methods
    def _prepare_variant_values(self, combination):
        self.ensure_one()
        vals = super()._prepare_variant_values(combination)
        vals.update({
            'default_code': self.default_code,
            'division': self.division,
        })
        return vals
        
    def _auto_init(self):
        res = super(productTemplate, self)._auto_init()
        self._cr.execute("SELECT indexname FROM pg_indexes WHERE indexname = 'product_template_name_division_index'")
        if not self._cr.fetchone():
            self._cr.execute('CREATE INDEX product_template_name_division_index ON product_template(name,division)')
        return res
    
    def get_division_from_categ_id(self, categ_id):
        list_of_division = self.env['tw.selection'].get_division_options()
        list_of_categ = [p.strip() for p in categ_id.complete_name.split('/')]
        for div in list_of_division:

            if div[1].strip() in list_of_categ:
                return div[0]

    def get_product_variant(self, default_code, attribute_code):
    # Get product template
        product_template = self.env['product.template'].search([('default_code', '=', default_code)], limit=1)
        if not product_template:
            raise Warning(_(f"Product template {default_code} not found"))

        # Get attribute value
        attribute_value = self.env['product.attribute.value'].search([('code', '=', attribute_code)], limit=1)
        if not attribute_value:
            raise Warning(_(f"Attribute value {attribute_code} not found"))

        # Get or create product template attribute value
        ptav = self.env['product.template.attribute.value'].search([
            ('product_tmpl_id', '=', product_template.id),
            ('product_attribute_value_id', '=', attribute_value.id)
        ], limit=1)

        variant = product_template._get_variant_for_combination(ptav)
        if not variant:
            raise Warning(_(f"Variant for product template {default_code} and attribute {attribute_code} not found"))
        
        return variant
    
    def get_category_name(self, vals, action_name):
        product_categ_id = vals.get('categ_id')
        if product_categ_id:
            categ_id = self.env['product.category'].browse(product_categ_id)
            categ_list = categ_id.complete_name.split('/')
            categ_list = [p.strip() for p in categ_list]
            return action_name in categ_list
        return False

    # ------ Method pengecekan attribute lines agar tidak duplikat -----
    def _prepare_write_vals(self, vals):
        prepared_vals = dict(vals)
        
        if 'attribute_line_ids' in prepared_vals:
            self.ensure_one() # Hanya boleh edit warna per produk! jika langsung banyak product bisa menyebabkan duplikasi.
            prepared_vals['attribute_line_ids'] = self._prepare_attribute_line_commands(prepared_vals['attribute_line_ids'])
            if not prepared_vals['attribute_line_ids']:
                prepared_vals.pop('attribute_line_ids')

        return prepared_vals

    def _prepare_attribute_line_commands(self, att_commands):
        remaining_commands = []
        for command in att_commands:
            operation, values = self._get_attribute_line_values(command)
            if operation != Command.CREATE or not values:
                remaining_commands.append(command)
                continue

            attribute_id = values.get('attribute_id')
            if not attribute_id:
                remaining_commands.append(command)
                continue

            existing_line = self.attribute_line_ids.filtered(lambda line: line.attribute_id.id == attribute_id)[:1]
            if not existing_line:
                remaining_commands.append(command)
                continue

            self._append_missing_attribute_values(existing_line, values)

        return remaining_commands

    def _get_attribute_line_values(self, command):
        if isinstance(command, Command):
            operation = command[0]
            values = command[2]
        elif isinstance(command, (list, tuple)) and len(command) >= 3:
            operation = command[0]
            values = command[2]
        else:
            return None, None

        if not isinstance(values, dict):
            return operation, None
        return operation, values

    def _append_missing_attribute_values(self, attribute_line, values):
        incoming_ids = []
        for item in values.get('value_ids', []):
            if isinstance(item, Command):
                if item[0] == Command.SET:
                    incoming_ids.extend(item[2] or [])
                elif item[0] == Command.LINK:
                    incoming_ids.append(item[1])
            elif isinstance(item, (list, tuple)) and len(item) >= 3:
                if item[0] == Command.SET:
                    incoming_ids.extend(item[2] or [])
                elif item[0] == Command.LINK:
                    incoming_ids.append(item[1])

        new_ids = [value_id for value_id in incoming_ids if value_id not in attribute_line.value_ids.ids]
        if new_ids:
            attribute_line.write({'value_ids': [Command.set(attribute_line.value_ids.ids + new_ids)]})
    
    # ------ End of Method pengecekan attribute lines agar tidak duplikat -----

