from odoo import models, fields, api
from odoo.exceptions import UserError as Warning
from datetime import date

import base64
import xlrd

class MasterDiscount(models.TransientModel):
    _name = "tw.sale.discount.items.upload"
    _description = "Upload Master Discount"

    def _get_default_date(self):
        return date.today()

    def _domain_product_category(self):
        categ_ids = self.env['product.category'].get_child_ids('Sparepart')
        return [('id','in',categ_ids)]

    categ_ids = fields.Many2many('product.category', 'tw_master_discount_upload_categ_rel', 'upload_discount_id','categ_id', 'Sub Category',domain=_domain_product_category)
    file = fields.Binary(string='File')
    filename = fields.Char(string="Filename")
    upload_date = fields.Date(string='Tanggal Upload', default=_get_default_date)
    
    def action_upload(self):
        data = base64.decodebytes(self.file)
        excel = xlrd.open_workbook(file_contents = data)  
        data = excel.sheet_by_index(0)

        for categ in self.categ_ids:
            line_ids = []
            for rx in range(1,data.nrows):
                product = [data.cell(rx, ry).value for ry in range(data.ncols)][0]
                additional = [data.cell(rx, ry).value for ry in range(data.ncols)][1]
                topup = [data.cell(rx, ry).value for ry in range(data.ncols)][2]
                simpart = [data.cell(rx, ry).value for ry in range(data.ncols)][3]
                hotline = [data.cell(rx, ry).value for ry in range(data.ncols)][4]
                fix = [data.cell(rx, ry).value for ry in range(data.ncols)][5]
                vals = {'categ_id':categ.id}

                product_id = False
                if product != '':
                    product_obj = self.env['product.product'].suspend_security().search([('name_template','=',product)])
                    if product_obj.categ_id.id != categ.id:
                        raise Warning('Silahkan hapus category yang tidak tertera pada file xls anda!\nCategory Data Upload : %s, Category yang dipilih : %s' % (product_obj.categ_id.name,categ.name))
                    product_id = product_obj.id
                if additional != '':
                    vals.update({'additional':float(additional)})
                if topup != '':
                    vals.update({'topup':float(topup)})
                if simpart != '':
                    vals.update({'simpart':float(simpart)})
                if hotline != '':
                    vals.update({'hotline':float(hotline)})
                if fix != '':
                    vals.update({'fix':float(fix)})
                
                if product_id:
                    vals.update({'product_id':product_id})
                master_disc_obj = self.env['tw.sale.discount.items'].suspend_security().search([('categ_id','=',categ.id),('product_id','=',product_id)])
                if not master_disc_obj:
                    create = master_disc_obj.suspend_security().create(vals)
                else:
                    master_disc_obj.suspend_security().write(vals)

        list_id = self.env.ref('tw_sale_order_discount.view_tw_sale_discount_items_list').id
        return {
            'name': ('Master Discount'),
            'res_model': 'tw.sale.discount.items',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'views': [(list_id, 'list'),(False, 'form')],
            'view_type': 'form',
            'view_mode': 'list,form',
            'target': 'current',
        }