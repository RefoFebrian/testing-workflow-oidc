# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class MappingMasterJasa(models.Model):
    _name = "tw.dgi.mapping.master.jasa"
    _description = "Mapping Master Jasa"
    _rec_name = "display_name"
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    
    main_dealer_id = fields.Many2one('res.partner',string='Main Dealer',required=True)
    company_id = fields.Many2one('res.company',string='Branch')
    active = fields.Boolean(string='Active',default=True)
    line_ids = fields.One2many('tw.dgi.mapping.master.jasa.line','mapping_id',string='Lines')

    @api.depends('main_dealer_id', 'company_id')
    def _compute_display_name(self):
        for rec in self:
            main = rec.main_dealer_id.name or ''
            branch = rec.company_id.name or ''
            rec.display_name = f"{main} - {branch}" if main or branch else "Mapping Jasa"

    @api.model_create_multi
    def create(self,vals_list):
        for rec in vals_list:
            main_dealer_id = rec.get('main_dealer_id')
            branch_id = rec.get('company_id')
            existing = self._search_exist_record(main_dealer_id,branch_id)

            if existing and branch_id:
                raise UserError(
                    f"Data dengan Main Dealer '{existing.main_dealer_id.name}' dengan Branch '{existing.company_id.name}' sudah ada."
                )
            elif existing:
                raise UserError(
                    f"Data dengan Main Dealer '{existing.main_dealer_id.name}' sudah ada."
                )

        return super(MappingMasterJasa, self).create(vals_list)
    
    def write(self,vals):
        for rec in self:
            main_dealer_id = vals.get('main_dealer_id') or rec.main_dealer_id
            branch_id = vals.get('company_id') or rec.company_id
            existing = self._search_exist_record(main_dealer_id,branch_id,rec.id)

            if existing and branch_id:
                raise UserError(
                    f"Data dengan Main Dealer '{existing.main_dealer_id.name}' dengan Branch '{existing.company_id.name}' sudah ada."
                )
            elif existing:
                raise UserError(
                    f"Data dengan Main Dealer '{existing.main_dealer_id.name}' sudah ada."
                )
        return super(MappingMasterJasa, self).write(vals)

    def unlink(self):
        raise UserError('Data tidak bisa dihapus, silahkan nonaktifkan saja.')

    def action_upload_mapping_jasa_wizard(self):
        return {
            'name':'Upload Mapping Jasa Line',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.upload.mapping.jasa.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context':{
                'default_mapping_id':self.id,
            }
        }

    def _search_exist_record(self,main_dealer_id,branch_id,exclude_id=False):
        md_id = main_dealer_id.id if hasattr(main_dealer_id,'id') else main_dealer_id
        branch_id_val = branch_id.id if hasattr(branch_id,'id') else branch_id

        domain = [('main_dealer_id', '=', md_id)]
        if branch_id_val:
            domain.append(('company_id', '=', branch_id_val))
        else:
            domain.append(('company_id', '=', False))
        if exclude_id:
            domain.append(('id', '!=', exclude_id))
        return self.env['tw.dgi.mapping.master.jasa'].suspend_security().search(domain, limit=1)

class MappingMasterJasaLine(models.Model):
    _name = "tw.dgi.mapping.master.jasa.line"
    _description = "Mapping Master Jasa Line"

    mapping_id = fields.Many2one('tw.dgi.mapping.master.jasa',string='Mapping',ondelete='cascade')
    product_id = fields.Many2one('product.product',string='Product Jasa',required=True)
    product_md = fields.Char(string='Product MD',required=True)
    active = fields.Boolean(string='Active',default=True)

    @api.model_create_multi
    def create(self, vals_list):
        seen = set()
        for rec in vals_list:
            mapping_id = rec.get('mapping_id')
            product_id = rec.get('product_id')
            product_md = rec.get('product_md')

            key = (mapping_id,product_id,product_md)
            if key in seen:
                raise UserError(
                    f"Terdapat duplikat Line dengan Product ID {key[1]} dan Product MD '{key[2]}' di record yang sama."
                )
            seen.add(key)

            existing_line = self.env['tw.dgi.mapping.master.jasa.line'].suspend_security().search([
                ('mapping_id', '=', mapping_id),
                ('product_id', '=', product_id),
                ('product_md', '=', product_md),
            ], limit=1)

            if existing_line:
                raise UserError(
                    f"Lines dengan product '{existing_line.product_id.display_name}' dengan product MD '{existing_line.product_md}' sudah ada."
                )
        return super(MappingMasterJasaLine, self).create(vals_list)

