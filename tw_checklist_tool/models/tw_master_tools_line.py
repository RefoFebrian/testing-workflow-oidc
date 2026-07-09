# 1: imports of python lib
import datetime

from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api


# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwMasterToolsLine(models.Model):
    _name = "tw.master.tools.line"
    _description = "Master Tools Line"

    # 7: defaults methods

    # 8: fields
    qty_tool = fields.Integer('Qty')
    files_upload = fields.Binary('Upload Photo')
    filename_upload = fields.Char('Photo Filename')
    files = fields.Binary('Download Photo', compute='_compute_files')
    filename = fields.Char('Photo')

    # 9: relation fields
    master_tools_id = fields.Many2one('tw.master.tools', string="Master Tools")
    product_id = fields.Many2one('product.product', string="Product Name", domain="[('product_tmpl_id.categ_id.parent_id.name', '=', 'Sparepart')]")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    def _compute_files(self):
        for x in self:
            if x.filename:
                x.files = self.env['tw.config.files'].suspend_security().get_file(x.filename)
            else:
                x.files = False

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            qty_tool = vals.get('qty_tool')
            if qty_tool is not None:
                if not isinstance(qty_tool, (int, float)) or qty_tool < 0:
                    raise Warning("Qty Tool harus berupa angka positif.")

            files = vals.get('files_upload')
            if files:
                filename_upload_tokens = str(vals.get('filename_upload')).split('.')
                foto_axt = filename_upload_tokens[len(filename_upload_tokens) - 1].lower()
                if foto_axt not in (('jpg', 'jpeg', 'png')):
                    raise Warning('Perhatian!\nFoto Harus Dalam Format JPG, JPEG atau PNG!')

                now = (datetime.datetime.today() + relativedelta(hours=7)).strftime('-%Y-%m-%d_%H_%M_%S_%f')
                filename = str('master_tool') + now + '.' + foto_axt
                self.env['tw.config.files'].suspend_security().upload_file(filename, files)
                # vals['files_upload'] = False
                vals['filename_upload'] = filename
                vals['files'] = False
                vals['filename'] = filename
        return super(TwMasterToolsLine, self).create(vals_list)

    def write(self, vals):
        qty_tool = vals.get('qty_tool')
        if qty_tool is not None:
            if not isinstance(qty_tool, (int, float)) or qty_tool < 0:
                raise Warning("Qty Tool harus berupa angka positif.")

        files_upload = vals.get('files_upload')
        if files_upload:
            filename_upload = vals.get('filename_upload')
            if not filename_upload:
                filename_upload = self.filename_upload or 'image.jpg'
                
            filename_upload_tokens = str(filename_upload).split('.')
            foto_ext = filename_upload_tokens[len(filename_upload_tokens) - 1].lower()
            if foto_ext not in ('jpg', 'jpeg', 'png'):
                raise Warning('Perhatian!\nFoto Harus Dalam Format JPG, JPEG atau PNG!')

            now = (datetime.datetime.today() + relativedelta(hours=7)).strftime('-%Y-%m-%d_%H_%M_%S_%f')
            filename = str('master_tool') + now + '.' + foto_ext
            self.env['tw.config.files'].suspend_security().upload_file(filename, files_upload)

            # vals['files_upload'] = False
            vals['filename_upload'] = filename
            vals['files'] = False
            vals['filename'] = filename

        return super(TwMasterToolsLine, self).write(vals)

    # 13: action methods

    # 14: private methods
    def export_file(self):
        self.ensure_one()

        if not self.filename:
            return False

        return {
            'type': 'ir.actions.act_url',
            'url': (
                       '/web/content?'
                       'model=tw.master.tools.line'
                       '&id=%d'
                       '&field=files'
                       '&filename=%s'
                       '&download=true'
                   ) % (self.id, self.filename),
            'target': 'self',
        }
