#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError

# 5: local imports

# 6: Import of unknown third party lib

class twUnitParts(models.Model):
    _name = "tw.unit.parts"
    _description = "Unit Parts"

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string="Parts Unit Code")

    # 9: relation fields
    line_ids = fields.One2many('tw.unit.parts.line', 'part_unit_id', string="Parts Unit")
    
    # 10: constraints & sql constraints
    @api.constrains('name')
    def _check_exisiting_part(self):
        if self.search([('name', '=', self.name), ('id', 'not in', self.ids)]):
            raise ValidationError(_(f"Parts Unit with code {self.name} already exist!"))

    # 10: compute/depends & on change methods

    # 12: override methods


class TWUnitPartsLine(models.Model):
    _name = "tw.unit.parts.line"
    _description = "Unit Parts Detail"
    
    # 8: fields
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    desc_part = fields.Html(string='Part Description', compute='_compute_desc_part', store=True, translate=True)
    # 9: relation fields
    part_code_id = fields.Many2one('product.template', string='Part Code', domain=[('categ_id', 'child_of', 'Sparepart')])
    part_unit_id = fields.Many2one('tw.unit.parts', string='Unit', ondelete='cascade')

    # 10: constraints & sql constraints
    @api.constrains('part_code_id', 'part_unit_id')
    def _validate_part_code_unit(self):
        # Check duplicates within the same batch of lines being created/updated
        lines_to_check = self.filtered(lambda r: r.part_code_id and r.part_unit_id)
        seen = set()
        for record in lines_to_check:
            key = (record.part_code_id.id, record.part_unit_id.id)
            if key in seen:
                raise ValidationError(_(
                    f"Sparepart code {record.part_code_id.name} with unit {record.part_unit_id.name} "
                    "is duplicated in your input!"
                ))
            seen.add(key)
        
        # Check duplicates against existing records in database
        for record in lines_to_check:
            duplicate = self.search([
                ('id', 'not in', self.ids),
                ('part_code_id', '=', record.part_code_id.id),
                ('part_unit_id', '=', record.part_unit_id.id)
            ], limit=1)
            if duplicate:
                raise ValidationError(_(
                    f"Sparepart code {record.part_code_id.name} with unit {record.part_unit_id.name} "
                    "already exists in the database!"
                ))
    
    # 10: compute/depends & on change methods
    @api.depends('part_code_id')
    def _compute_name(self):
        for record in self:
            record.name = record.part_code_id.name if record.part_code_id else False
    
    @api.depends('part_code_id')
    def _compute_desc_part(self):
        for record in self:
            record.desc_part = record.part_code_id.description if record.part_code_id else False
            
    # 12: override methods
    @api.model
    def name_get(self, context=None):
        if context is None:
            context = {}
        res = []
        for record in self:
            rec = "[%s] %s" % (record.name, record.desc_part)
            res.append((record.id, rec))
        return res
    