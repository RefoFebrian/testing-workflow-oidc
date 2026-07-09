# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime
import math

# 2: import of known third party lib
import xlrd
import base64

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class InheritTwP2pPurchaseOrder(models.Model):
    _inherit = "tw.p2p.purchase.order"

    # 7: defaults methods
    def _get_default_main_dealer_atpm_code(self):
        return self.env['res.company'].get_default_main_dealer_atpm_code()
    
    # 8: fields
    
    # Audit Trail
    
    # 9: relation fields
    export_upo_ids = fields.One2many('tw.p2p.export.upo','purchase_order_id',string='Export UPO')
    b2b_error_log_ids = fields.One2many('tw.b2b.error.log', 'p2p_id', string="MFT Error Log")

    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    
    # 12: override methods
    def action_verification(self):
        verification = super(InheritTwP2pPurchaseOrder,self).action_verification()
        
        self.action_export_upo()
        file_upo = self._check_upo_file()
        if file_upo:
            file_upo.action_revision()

        self.b2b_error_log_ids.filtered(lambda x: x.state == 'open').write({'state': 'done'})
        
        return verification
    
    def action_revisi(self):
        revision = super(InheritTwP2pPurchaseOrder,self).action_revisi()
        for p2p in self:
            file_upo = p2p._check_upo_file()
            if file_upo:
                file_upo.action_revision()
        return revision

    def confirm_order(self):
        confirm = super(InheritTwP2pPurchaseOrder,self).confirm_order()
        file_upo = self.env['tw.p2p.export.upo'].search([('purchase_order_id', '=', self.id)], limit=1)
        if file_upo:
            file_upo.action_done()
        
        return confirm
    
    # 13: action methods
    

    # 14: private methods
    def _check_upo_file(self):
        file_upos = self.env['tw.p2p.export.upo'].search([('purchase_order_id', '=', self.id)], order='id asc')
        file_upo_except_last = file_upos[:-1]
        if file_upo_except_last: 
            return file_upo_except_last
        else:
            return False

    def action_export_upo(self):
        result = ''
        kodeMD = self._get_default_main_dealer_atpm_code()
        bulan = self._get_default_date().strftime('%m')
        tahun = self._get_default_date().strftime('%Y') 
        po_md = self.name
        po_sparepart = self._get_default_date().strftime('%d%m%Y')  
        if self.purchase_order_type_id.name=='Fix':
            tipe_po = 'F'
        else:
            tipe_po = 'A'
        periode = self.env['tw.p2p.periode'].search([('name','=',self.periode_id)])
        eff_start_date = str(periode.start_date.strftime('%d%m%Y'))
        eff_end_date = str(periode.end_date.strftime('%d%m%Y'))
        dealer_company_id = self.dealer_id.company_id
        # TODO: Sambungkan ke pricelist
        # pricelist_id = dealer_company_id.pricelist_beli_unit_id
        uom_id = False
        # if not pricelist_id :
        #     raise Warning(("Perhatian! \npricelist beli belum ada, silahkan ditambahkan di Branch."))
        if self.division == 'Unit':
            if self.type_name == 'Fix' :      
                for x in self.purchase_line_ids :
                    product_uom_po_id = x.product_id.uom_po_id.id
                    if not uom_id:
                        uom_id = product_uom_po_id      
                    # date_order_str = datetime.strptime(self.date, DEFAULT_SERVER_DATETIME_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT)
                    # price = pricelist_id.price_get(x.product_id.id, x.fix_qty or 1.0, self.supplier_id or False, context={'uom': uom_id, 'date': date_order_str})[pricelist_id.id]
                    
                    # if not price :
                    #     raise Warning(("Perhatian! \nProduct %s tidak ada dalam pricelist %s")%(x.product_id.name,pricelist_id.name))  
                    product_template = x.product_id.product_tmpl_id.name
                    color = ', '.join(x.product_id.product_template_attribute_value_ids.mapped('name')) if x.product_id.product_template_attribute_value_ids else ''
                    
                    qty_fix = str(x.fix_qty)
                    tent1_qty = str(x.tent1_qty)
                    tent2_qty = str(x.tent2_qty)
                    result += kodeMD +';'+ bulan +';'+ tahun +';'+ product_template +';'+ color +';'+ qty_fix +';'+tent1_qty+';'+tent2_qty+';'+po_md+';'+tipe_po+';'+eff_start_date+';'+eff_end_date+';'
                    result += '\n\r'  
            if self.type_name == 'Additional' :      
                for x in self.additional_line_ids :
                    product_uom_po_id = x.product_id.uom_po_id.id
                    if not uom_id:
                        uom_id = product_uom_po_id           
                    # date_order_str = datetime.strptime(self.date, DEFAULT_SERVER_DATETIME_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT)
                    # price = pricelist_id.price_get(x.product_id.id, x.fix_qty or 1.0, self.supplier_id or False, context={'uom': uom_id, 'date': date_order_str})[pricelist_id.id]
                    # price = x.price
                    # if not price :
                    #     raise Warning(("Perhatian ! \nProduct %s tidak ada dalam pricelist %s")%(x.product_id.name,pricelist_id.name))  
                    product_template = str(x.product_id.product_tmpl_id.name).encode('ascii','ignore').decode('ascii')
                    color = ', '.join(x.product_id.product_template_attribute_value_ids.mapped('name')) if x.product_id.product_template_attribute_value_ids else ''
                    
                    qty_fix = str(x.fix_qty).encode('ascii','ignore').decode('ascii')
                    tent1_qty = str(0).encode('ascii','ignore').decode('ascii')
                    tent2_qty = str(0).encode('ascii','ignore').decode('ascii')
                    result += kodeMD +';'+ bulan +';'+ tahun +';'+ product_template +';'+ color +';'+ qty_fix +';'+tent1_qty+';'+tent2_qty+';'+po_md+';'+tipe_po+';'+eff_start_date+';'+eff_end_date+';'
                    result += '\n\r'
        elif self.division == 'Sparepart':
            # Dictionary untuk menyimpan data berdasarkan kategori
            spareparts_dict = {}

            for x in self.purchase_line_ids:
                result = ''
                product_uom_po_id = x.product_id.uom_po_id.id
                if not uom_id:
                    uom_id = product_uom_po_id  

                # Ambil kategori produk
                categ = x.product_id.categ_id.name
                product_template = str(x.product_id.product_tmpl_id.name).encode('ascii', 'ignore').decode('ascii')
                qty_fix = str(x.fix_qty).encode('ascii', 'ignore').decode('ascii')

                # Membuat string result untuk item ini
                result = (
                    kodeMD + ';' + bulan + ';' + tahun + ';' +
                    product_template + ';' + qty_fix + ';' +
                    po_md + ';' + tipe_po + ';' + categ + ';' + eff_start_date + ';' + eff_end_date + ';'
                )
                result += '\n\r'

                # Tambahkan ke kategori yang sesuai dalam dictionary
                if categ not in spareparts_dict:
                    spareparts_dict[categ] = ''
                spareparts_dict[categ] += result

            # Ubah dictionary menjadi list sesuai format yang diminta
            spareparts = [{'title': title, 'content': content} for title, content in spareparts_dict.items()]
        
        config_obj = self.env['tw.config.files'].sudo().search([('name','=','MFT-OUT')], limit=1)
        if config_obj:
            path = config_obj.local_path
            nama = kodeMD + '-' + po_md.replace("/","") + '.UPO'
            if self.revisi_ke > 0:
                nama = 'AHM-'+kodeMD + '-' + po_md.replace("/","") + '_' + str(self.revisi_ke) + '_.UPO'
            if self.division == 'Sparepart':
                # Format: AHM-{MD_CODE}-{DDMMYYYY}{FIX_CATEGORY or ADD}.PPO
                if self.type_name == 'Fix':
                    fix_category_name = self.category_fix_order_id.name if self.category_fix_order_id else ''
                else:
                    # Additional type uses 'ADD'
                    fix_category_name = 'ADD'
                nama = 'AHM-' + kodeMD + '-' + po_sparepart + fix_category_name + '.PPO'
                if self.revisi_ke > 0:
                    nama = 'AHM-' + kodeMD + '-' + po_sparepart + fix_category_name + '_' + str(self.revisi_ke) + '_.PPO'
                
                # Combine all content from spareparts into single result
                result = ''
                for order in spareparts:
                    result += order['content']
                
                url_file = path + '/' + nama
                file = open(url_file, 'w+')
                self.env['tw.p2p.export.upo'].create({
                    'purchase_order_id': self.id,
                    'filename': nama,
                    'content': result,
                })
                file.write(result)
                file.close()
                return
            
            url_file = path + '/' + nama
            file = open(url_file,'w+')
            self.env['tw.p2p.export.upo'].create({
                'purchase_order_id': self.id,
                'filename': nama,
                'content': result,
            })
            file.write(result)
            file.close()
        else:
            raise Warning("Belum ada konfigurasi folder penyimpanan file UPO (MFT-OUT)!")