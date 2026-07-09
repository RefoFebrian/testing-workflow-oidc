#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib
import logging
# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


_logger = logging.getLogger(__name__)

class TedsUnitParts(models.Model):
    _inherit = "tw.unit.parts"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    def action_import(self, file_obj):
        res = True
        b2b_file_content = self.env['tw.b2b.file.content']
        ptm_content = b2b_file_content.suspend_security().search([('b2b_file_id', '=', file_obj.id),
                                                                   ('state', '=', 'draft')], limit=500)
        try:
            for ptm in ptm_content:
                ptm._process_ptm()
                
        except Exception:
            self._cr.rollback()
            res = False

        finally :
            self._cr.commit()
            ptm_content.write({ 'state': 'done' })

        return res
    
    def check_file_ptm(self):
        b2b_file = self.env['tw.b2b.file'].suspend_security().search([
            ('ext','=','PTM'), ('state','=','draft')], limit=1)
        if b2b_file:
            content = b2b_file.content_file_ids.filtered(lambda x: x.state == 'draft')
            if not content:
                b2b_file.suspend_security().write({ 'state': 'done' })
            else:
                self.action_import(b2b_file)
                
    def check_file_pvtm(self):
        tw_b2b_file = self.env['tw.b2b.file']
        tw_b2b_file_content = self.env['tw.b2b.file.content']
        tw_unit_parts_line = self.env['tw.unit.parts.line']

        b2b_file = tw_b2b_file.suspend_security().search([
            ('ext', '=', 'PVTM'),
            ('state', '=', 'draft')],
            limit=1, order='write_date desc')
        if b2b_file:
            content = tw_b2b_file_content.suspend_security().search([
                ('b2b_file_id','=',b2b_file.id),
                ('state','=','draft')])
            if not content:
                b2b_file.suspend_security().write({ 'state': 'done' })
            else:
                tw_unit_parts_line.action_import(b2b_file)


class TWUnitPartsLine(models.Model):
    _inherit = "tw.unit.parts.line"
    
    # 8: fields
    
    # 9: relation fields

    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods

    # 12: override methods
    
    @api.model
    def action_import(self,file_obj):
        tw_b2b_file_content = self.env['tw.b2b.file.content']
        pvtm_file = tw_b2b_file_content.suspend_security().search([
            ('b2b_file_id', '=', file_obj.id),
            ('state', '=', 'draft')], limit=500)
        res = True
        try:
            for pvtm in pvtm_file:
                pvtm._process_pvtm()
        
        except Exception:
            self._cr.rollback()
            res = False
        
        finally:
            self._cr.commit()
            pvtm_file.write({'state':'done'})
        
        return res
            