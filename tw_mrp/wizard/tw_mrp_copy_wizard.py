# -*- coding: utf-8 -*-

# 1: imports of python lib
import re

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, Command, _


# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwMrpCopyWizard(models.TransientModel):
    _name = "tw.mrp.copy.wizard"
    _description = "Wizard to copy extras to other companies"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    source_bom_id = fields.Many2one('mrp.bom', string='Source', required=True)
    target_company_ids = fields.Many2many('res.company', string='Target Companies')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_copy(self):
        self.ensure_one()

        base_name = self.source_bom_id.code or ''
        match = re.search(r'^(.*)\s(\d+)$', base_name)
        if match:
            base_name = match.group(1)

        domain = [('code', '=like', base_name + '%')] if base_name else [('code', '!=', False)]
        existing_boms = self.env['mrp.bom'].sudo().search(domain)
        used_codes = set(existing_boms.mapped('code'))

        next_seq = 1
        new_bom_ids = [self.source_bom_id.id]

        for company in self.target_company_ids:
            bom_code = False

            domain = [
                ('product_tmpl_id', '=', self.source_bom_id.product_tmpl_id.id),
                ('product_id', '=', self.source_bom_id.product_id.id),
                ('type', '=', self.source_bom_id.type),
                ('company_id', '=', company.id),
            ]
            existing_bom = self.env['mrp.bom'].sudo().search(domain, limit=1)

            if existing_bom and existing_bom.code and existing_bom.code.startswith(base_name):
                bom_code = existing_bom.code
            else:
                while True:
                    candidate = f"{base_name} {next_seq}".strip()
                    if candidate not in used_codes:
                        bom_code = candidate
                        used_codes.add(bom_code)
                        break
                    next_seq += 1

            bom_data = {
                'product_tmpl_id': self.source_bom_id.product_tmpl_id.id,
                'product_id': self.source_bom_id.product_id.id,
                'product_qty': self.source_bom_id.product_qty,
                'product_uom_id': self.source_bom_id.product_uom_id.id,
                'code': bom_code,
                'type': self.source_bom_id.type,
                'company_id': company.id,
            }

            # Ngumpulin data line dari sumber
            lines_data = []
            for line in self.source_bom_id.bom_line_ids:
                if line.product_id.company_id and line.product_id.company_id.id != company.id:
                    continue
                # Nyimpen line dalam dict
                lines_data.append({
                    'product_id': line.product_id.id,
                    'product_qty': line.product_qty,
                    'product_uom_id': line.product_uom_id.id,
                })
            # Kalo BOM target udah ada lakuin update aja (ini yang sebelumnya ngelakuin unlink)
            if existing_bom:
                bom = existing_bom
                # Update header BOM terlebih dahulu
                bom.write(bom_data)
                # Ngambil semua line yang ada di BOM Target
                existing_lines = list(bom.bom_line_ids)
                lines_commands = []

                for data in lines_data:
                    # Nyari line dengan product yang sama sudah ada atau belum di existing
                    match = next((l for l in existing_lines if l.product_id.id == data['product_id']), None)
                    if match:
                        # Kalo ketemu maka dihapus dari list sehingga sisanya nanti adalah yang harus dihapus dengan line commands
                        existing_lines.remove(match)
                        update_vals = {}
                        # Check line ada yang berubah atau engga kalo berubah lakukan update
                        if match.product_qty != data['product_qty']:
                            update_vals['product_qty'] = data['product_qty']
                        if match.product_uom_id.id != data['product_uom_id']:
                            update_vals['product_uom_id'] = data['product_uom_id']

                        # 1 = Update
                        if update_vals:
                            lines_commands.append((1, match.id, update_vals))
                    else:
                        # 0 = Create
                        lines_commands.append((0, 0, data))

                for line in existing_lines:
                    # 2 = Delete
                    lines_commands.append((2, line.id))

                if lines_commands:
                    bom.write({'bom_line_ids': lines_commands})
            else:
                bom_data['bom_line_ids'] = [(0, 0, data) for data in lines_data]
                bom = self.env['mrp.bom'].sudo().with_company(company.id).create(bom_data)

            new_bom_ids.append(bom.id)

        return {
            'name': _('Generated BoMs'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.bom',
            'view_mode': 'list,form',
            'domain': [('id', 'in', new_bom_ids)],
        }

    # 14: private methods