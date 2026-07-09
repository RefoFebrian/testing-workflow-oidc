# -*- coding: utf-8 -*-

# 1: imports of python lib
import difflib
import json
import os
import logging
import re

# 2: import of known third party lib
from datetime import date, timedelta, datetime

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


_logger = logging.getLogger(__name__)

# TODO: penulisan model masih menggunakan gaya lama (model di taruh di variable lalu di panggil saat akan search atau create)
# TODO: seharusnya tidak perlu di tampung di variable
class TwB2BFileContent(models.Model):
    _name = "tw.b2b.file.content"
    _description = "B2B File Content"
    _order = "id desc"
    
    # 7: defaults methods
    def _get_default_main_dealer_code(self):
        return self.env['res.company'].get_default_main_dealer_code()
    
    # 8: fields
    name = fields.Char(string="Content", help="File B2B Content for each rows of B2B File.")
    state = fields.Selection([('open', 'Open'), ('error', 'Error'), ('pending', 'Pending'), ('done', 'Done')],
                              default='open', string="Status",
                              help=" * Open: The content has not been processed yet.\n"
                                   " * Error: An error occurred while processing the content.\n"
                                   " * Pending: The content is waiting for certain conditions to be met before finalizing.\n"
                                   " * Done: The content has been processed and successfully recorded in the database.\n")
    log = fields.Text(help="Record anomaly occured when processing the contents")
    
    # 9: relation fields
    file_id = fields.Many2one('tw.b2b.file', string="B2B File", help="Related File", ondelete='cascade')
    content_line_ids = fields.One2many('tw.b2b.file.content.line', 'file_content_id', help="Related Content Detail")
    
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        contents = super().create(vals_list)
        # for content in contents:
        #     sep = content.file_id.separator
        #     row = content.name.split(sep)
        #     content.content_line_ids
            
        return contents

    # 13: action methods
    def convert_to_vals(self):
        vals = {}
        for line in self.content_line_ids:
            vals.update({ line.name: line.value })
        return vals

    def action_process_content(self):
        for content in self:
            content.process_file(content.file_id.config_id.name)
    
    def action_re_open_content(self):
        self.write({ 'state': 'open', 'log': False })
    
    def _get_unit_product_id(self,unit_code,color_code):
        product_id = self.env['product.product']._get_unit_product_id(unit_code,color_code)
        return product_id
        
    def _get_purchase_journal_id(self, company_id, division):
        branch_config_obj = self.env['tw.account.setting']._get_purchase_journal_id(company_id, division)
        return branch_config_obj
    
    def _get_purchase_line_id(self, order_id, product_id):
        obj_purchase_order_line = self.env['purchase.order.line']._get_purchase_line_id(order_id, product_id)
        return obj_purchase_order_line
    
    def _check_state_content_line(self):
        content_line_obj = [line.state for line in self.file_id.content_file_ids]
        if all(line == 'done' for line in content_line_obj):
            return True
        
        return False
    
    def _get_invoice_id(self,origin):
        content_obj = self.suspend_security().search([('file_id','=',self.file_id.id)])
        datas = [vals.value for line in content_obj for vals in line.content_line_ids if vals.name == origin]
        move_obj = self.env['account.move'].suspend_security().search([('invoice_origin','in',datas)])
        return move_obj
    
    def _get_query_file_content(self, query_select, query_join, query_where, group_by):
        query = f"""
            SELECT {query_select}
            FROM tw_b2b_file tbf
            JOIN tw_b2b_file_content tbfc ON tbfc.file_id = tbf.id
            {query_join}
            {query_where}
            {group_by}
        """
        return query
    
    def _get_total_qty(self, ext, key, key2, file_id=None, origin=''):
        query_select = ""
        query_join = ""
        group_by = ""
        sub_where = ""
        query_where = f"WHERE 1=1 AND tbf.ext = '{ext}'"
        if file_id:
            query_where += f" AND tbf.id = {file_id}"
        if ext == 'INV':
            query_select += "SUM(qty.value::INT) as total_qty"
            query_join += f"""
                JOIN tw_b2b_file_content_line qty ON qty.file_content_id = tbfc.id AND qty.name = 'qty'
                JOIN (
                    SELECT file_content_id
                    FROM tw_b2b_file_content_line
                    WHERE (name = 'ship_list_number' AND value = '{origin}')
                    OR (name = 'type_code' AND value = '{key}')
                    OR (name = 'color_code' AND value = '{key2}')
                    GROUP BY file_content_id
                    HAVING COUNT(DISTINCT name) = 3
                ) AS filtered_ids ON filtered_ids.file_content_id = tbfc.id
            """
        else:
            query_join = " JOIN tw_b2b_file_content_line tbfcl ON tbfcl.file_content_id = tbfc.id "
            if ext == 'SL':
                query_select += "COUNT(DISTINCT tbfcl.id) as total_qty"
                query_where += f" AND tbfcl.value = '{origin}'"
                group_by += "GROUP BY tbfcl.value"
            elif ext in ('PS', 'FDO'):
                if ext == 'FDO' and not file_id:
                    query_where += " AND tbf.state = 'done'"
                query_select += "SUM(tbfcl.value::INT) as total_qty"
                sub_where += f" AND sl.value::TEXT = '{origin}'"

            if ext != 'SL':
                query_where += f"""
                    AND tbfcl.name = '{key}'
                    AND EXISTS (
                        SELECT 1
                        FROM tw_b2b_file_content_line sl
                        WHERE sl.file_content_id = tbfc.id
                        AND sl.name = '{key2}'
                        {sub_where}
                    )
                """
        query = self._get_query_file_content(query_select,query_join,query_where,group_by)
        self._cr.execute(query)
        result = self._cr.fetchone()
        return result[0] if result else 0
    
    def _get_content(self,ext,key1,key2,value1,value2,origin):
        query_select = "DISTINCT tbfc.id"
        query_join = f"""
            JOIN tw_b2b_file_content_line tbfcl ON tbfcl.file_content_id = tbfc.id
            JOIN tw_b2b_file_content_line cl_type ON cl_type.file_content_id = tbfc.id AND cl_type.name = '{key1}' AND cl_type.value = '{value1}'
            JOIN tw_b2b_file_content_line cl_color ON cl_color.file_content_id = tbfc.id AND cl_color.name = '{key2}' AND cl_color.value = '{value2}'
        """
        query_where = f"WHERE tbf.ext = '{ext}' AND tbfcl.value = '{origin}' AND tbf.state != 'duplicate'"
        group_by = ""
        query = self._get_query_file_content(query_select,query_join,query_where,group_by)
        self._cr.execute(query)
        result = self._cr.fetchall()
        data = [rec[0] for rec in result]
        return data if data else False

    def process_file(self, ext):
        self.ensure_one()
        if self.state == 'open':
            method_name = f'_process_{ext.lower()}'
            process_method = getattr(self, method_name, None)
            if process_method:
                process_method()
            else:
                raise Warning(_(f"No attribute named _process_{ext.lower()}!"))

    # 14: private methods
    def _process_pmp(self, return_vals=False):
        template = self.env['product.template']
        category = self.env['product.category']
        vals = self.convert_to_vals()
        for record in self:
            product_category = category.search([('name', '=', vals.get('sparepart_category'))], limit=1)
            if not product_category:
                product_category = category.search([('name', '=', 'Sparepart')], limit=1)
                # raise Warning(_(f"Warning!\nProduct Category {vals.get('sparepart_category')} does not exists!"))
            
            default_code = vals.get('sparepart_code')
            name = vals.get('sparepart_description')
            description = vals.get('sparepart_description_2')

            prod_temp = template.search([('default_code', '=', default_code)], limit=1)
            if prod_temp:
                record.state = 'pending'
            else:
                vals = {
                    'name': name,
                    'default_code': default_code,
                    'description': description,
                    'categ_id': product_category.id,
                    'division' : 'Sparepart',
                    'sale_ok': True,
                    'purchase_ok': True,
                    'is_storable' : True,
                    'type': 'consu',
                    'list_price': vals.get('het'),
                }
                if not return_vals:
                    template.create(vals)
                    record.state = 'done'
                else:
                    record.state = 'done'
                    return vals

    def schedulle_pmp_price_update(self, date_check=True, end_date=3, limit=200):
        if date_check and date.today().day > end_date:
            return

        template = self.env['product.template']
        b2b_pmp = self.search([('state', '=', 'pending'), ('file_id.config_id.name', '=', 'PMP')],limit=limit)
        if b2b_pmp:
            for record in b2b_pmp:
                vals = record.convert_to_vals()
                default_code = vals.get('sparepart_code')
                name = vals.get('sparepart_description')
                description = vals.get('sparepart_description_2')
                product_template = template.search([('default_code', '=', default_code)])
                if product_template:
                    product_template.write({
                        'sale_ok': True,
                        'purchase_ok': True,
                        'is_storable' : True,
                        'type': 'consu',
                        'list_price': vals.get('het'),
                        'description': description,
                        'name': name,
                    })
                    record.state = 'done'
            b2b_pmp.write({ 'state': 'done' })

    def _process_ptm(self):
        template = self.env['product.template']
        unit_parts = self.env['tw.unit.parts']
        vals = self.convert_to_vals()
        
        obj_unit = template.search([('name', '=', vals.get('product_template'))])
        if not obj_unit:
            raise Warning(_(f"Product {vals.get('product_template')} does not found!"))
        
        obj_unit_parts = unit_parts.search([('name', '=', vals.get('unit_parts'))])
        if not obj_unit_parts:
            raise Warning(_(f"Unit Parts {vals.get('unit_parts')} does not found!"))
        
        obj_unit.write({ 'part_unit_id': obj_unit_parts.id })
        self.state = 'done'
    
    def _process_pvtm(self):
        template = self.env['product.template']
        unit_parts = self.env['tw.unit.parts']
        unit_parts_line = self.env['tw.unit.parts.line']
        vals = self.convert_to_vals()
        
        sparepart = template.search([('name', '=', vals.get('product_template'))], limit=1)
        if not sparepart:
            raise Warning(_(f"Sparepart {vals['product.template']} is not found in the system!"))
        
        obj_unit_parts = unit_parts.search([('name', '=', vals.get('unit_parts'))])
        if not obj_unit_parts:
            try:
                obj_unit_parts = unit_parts.create({ 'name': vals.get('unit_parts') })
            except Exception as e:
                self.state = 'error'
                raise Warning(_(f"Warning!\n{e}"))
        
        obj_unit_parts_line = obj_unit_parts.filtered(lambda x: x.part_code_id == sparepart.id)
        if not obj_unit_parts_line:
            try:
                obj_unit_parts_line = unit_parts_line.create({
                    'part_code_id': sparepart.id,
                    'part_unit_id': obj_unit_parts.id
                })
            except Exception as e:
                self.state = 'error'
                _logger.error(_(f"Warning!\n{e}"))
                return False

        self.state = 'done'
        return True
    
    def _process_sl(self, po_line_id=False):
        stock_lot = self.env['stock.lot'].suspend_security()
        stock_picking = self.env['stock.picking'].suspend_security()
        stock_picking_type = self.env['stock.picking.type'].suspend_security()
        stock_move = self.env['stock.move'].suspend_security()
        stock_move_line = self.env['stock.move.line'].suspend_security()
        res_company = self.env['res.company'].suspend_security()
        
        data = self.convert_to_vals()
        if not data:
            raise Warning(_('Data not found!\n Content line generation has been skipped.'))
        
        engine_number = str(data.get('engine_number')).replace(" ", "")
        lot_obj = stock_lot.search([('name', '=', engine_number)], limit=1)
        if lot_obj:
            raise Warning(_(f"Lot/SL {lot_obj.name} already exist!\n Content line generation has been skipped."))
        
        branch_obj = res_company.search([('code', '=', self._get_default_main_dealer_code())], limit=1)
        if not branch_obj:
            raise Warning(_(f'Branch {self._get_default_main_dealer_code()} not found!\n Content line generation has been skipped.'))
        
        product_id = self._get_unit_product_id(data.get('type_code'), data.get('color_code'))
        if not product_id:
            raise Warning(_(f"Product {data.get('type_code')} with color {data.get('color_code')} not found!\n Content line generation has been skipped."))
            
        picking_type_obj = stock_picking_type.get_picking_type('incoming', branch_obj.id, 'Unit')
        try:
            lot_vals = {
                'company_id': branch_obj.id,
                'name': engine_number if engine_number else False,
                'chassis_number': str(data.get('frame_number')) if data.get('frame_number') else False, 
                'sipb_number': str(data.get('sipb_number')) if data.get('sipb_number') else False,
                'ship_list_number': str(data.get('ship_list_number')) if data.get('ship_list_number') else False,
                'ship_list_date': data.get('ship_list_date')[4:] + "-" + data.get('ship_list_date')[2:4] + "-" + data.get('ship_list_date')[0:2],
                'division': 'Unit',
                'product_id': product_id,
                'supplier_id': branch_obj.default_supplier_id.id,
                'location_id': picking_type_obj.default_location_src_id.id,
                'purchase_order_id': po_line_id.order_id.id,
                'state': 'intransit',
            }
            lot_obj = stock_lot.create(lot_vals)
        except Exception as e:
            _logger.exception(f"Failed to create Lot/Serial Number in generate SL {data.get('ship_list_number')}")
            raise Warning(_(f"Warning!\n{e}"))
        
        try:
            # Try searching for existing picking based on SL number & PO number
            picking_obj = stock_picking.search([
                ('origin','=', po_line_id.order_id.name),
                ('mft_reference', '=', data.get('ship_list_number')),
                ('state', 'in', ('draft', 'assigned'))
            ], limit=1)
            if not picking_obj:
                # If not found, create new picking
                picking_vals = {
                    'company_id': branch_obj.id,
                    'origin': po_line_id.order_id.name,
                    'mft_reference': data.get('ship_list_number'),
                    'picking_type_id': picking_type_obj.id,
                    'division': 'Unit',
                    'partner_id': branch_obj.default_supplier_id.id,
                    'date': datetime.now(),
                    'min_date': datetime.now(),
                    'location_id': picking_type_obj.default_location_src_id.id,
                    'location_dest_id': picking_type_obj.default_location_dest_id.id,
                }
                picking_obj = stock_picking.create(picking_vals)
        except Exception as e:
            _logger.exception(f"Failed to create Picking in generate SL {data.get('ship_list_number')}")
            raise Warning(_(f"Warning!\n{e}"))
        
        try:
            move = False
            if po_line_id:
                move = self.env['stock.move'].search([
                    ('purchase_line_id', '=', po_line_id.id),
                    ('picking_id', '=', picking_obj.id),
                    ('state', 'in', ('draft', 'assigned'))
                ], limit=1)
                if move:
                    move.write({
                        'product_uom_qty': move.product_uom_qty + 1,
                    })
            if not move:
                product_move = {
                    'company_id': branch_obj.id,
                    'picking_id': picking_obj.id,
                    'picking_type_id': picking_type_obj.id,
                    'origin': data.get('ship_list_number'),
                    'name': lot_obj.product_id.default_code or '',
                    'product_uom': lot_obj.product_id.product_tmpl_id.uom_id.id,
                    'product_id': lot_obj.product_id.id,
                    'product_uom_qty': 1,
                    'date': datetime.now(),
                    'location_id': picking_type_obj.default_location_src_id.id,
                    'location_dest_id': picking_type_obj.default_location_dest_id.id,
                    'purchase_line_id': po_line_id.id,
                }
                move = self.env['stock.move'].sudo().create(product_move)
        except Exception as e:
            _logger.exception(f"Failed to create/confirm Move in generate SL {data.get('ship_list_number')}")
            raise Warning(_(f"Warning!\n{str(e)}"))
        
        self.suspend_security().write({'state': 'done'})
        return picking_obj
            
    def _process_fm(self):
        stock_lot = self.env['stock.lot'].suspend_security()
        
        data = self.convert_to_vals()
        if not data:
            raise Warning(_('Data not found!\n Content line generation has been skipped.'))
        
        engine_number = str(data.get('engine_number')).replace(" ", "")
        lot_obj = stock_lot.search([('name', '=', engine_number)], limit=1)
        if not lot_obj:
            raise Warning(_('Lot/SL not found!\n Content line generation has been skipped.'))
        
        try:
            lot_vals = {
                'factur_number': str(data.get('factur_number')) if data.get('factur_number') else False,
                'stnk_invoice_price': float(data.get('stnk_invoice_price')),
                'production_year': data.get('production_year'),
                'expedition_ship': data.get('expedition_ship'),
            }
            lot_obj.write(lot_vals)
        except Exception as e:
            _logger.exception(f"Failed to update Lot/Serial Number in generate FM {data.get('factur_number')}")
            raise Warning(_(f"Warning!\n{e}"))
        
        self.suspend_security().write({'state': 'done'})
    
    def _process_sipb(self):
        stock_lot = self.env['stock.lot'].suspend_security()
        stock_picking = self.env['stock.picking'].suspend_security()
        stock_move = self.env['stock.move'].suspend_security()
        purchase_order = self.env['purchase.order'].suspend_security()
        p2p_purchase_order = self.env['tw.p2p.purchase.order'].suspend_security()
        
        data = self.convert_to_vals()
        if not data:
            raise Warning(_('Data not found!\n Content line generation has been skipped.'))
            
        product_id = self._get_unit_product_id(data.get('type_code'), data.get('color_code'))
        if not product_id:
            raise Warning(_(f"Product {data.get('type_code')} with color {data.get('color_code')} not found!\n Content line generation has been skipped."))
        
        purchase_order_obj = purchase_order.search([('origin', '=', data.get('no_po_md'))], limit=1)
        if not purchase_order_obj:
            p2p_purchase_order_obj = p2p_purchase_order.search([('name', '=', data.get('no_po_md'))], limit=1)
            if p2p_purchase_order_obj:
                p2p_purchase_order_obj.confirm_order()
                purchase_order_obj = p2p_purchase_order_obj.purchase_order_id
                
            if not purchase_order_obj:
                raise Warning(_(f"P2P/Purchase Order {data.get('no_po_md')} not found!\n Content line generation has been skipped."))
        
        purchase_line_obj = self._get_purchase_line_id(purchase_order_obj.id, product_id)
        if not purchase_line_obj:
            raise Warning(_(f"Product {data.get('type_code')} with color {data.get('color_code')} not registered in Purchase Order {purchase_order_obj.name}!\n Content line generation has been skipped."))
        
        content_sl_ids = self._get_content('SL', 'type_code', 'color_code', data.get('type_code'), data.get('color_code'), data.get('sipb_number'))
        content_obj = self.suspend_security().browse(content_sl_ids)
        if not content_obj:
            raise Warning(_(f"Shipping List number for product {data.get('type_code')} with color {data.get('color_code')} not found!\n Content line generation has been skipped."))
            
        if len(content_sl_ids) != int(data.get('count')):
            raise Warning(_(
                f"Total quantity for Ship List is {len(content_sl_ids)}, "
                f"which does not match the total quantity for SIPB Number {data.get('sipb_number')} is {data.get('count')}.\n"
                "Content line generation has been skipped."
            ))
        
        try:
            # Generate SL by SIPB Number 
            picking_obj = self.env['stock.picking']
            for sl_content in content_obj:
                if sl_content.state in ('open', 'pending'):
                    # Use |= (Set Union) to merge without duplicates
                    picking_obj |= sl_content._process_sl(po_line_id=purchase_line_obj)
                    sl_content.file_id._update_states()
            for picking in picking_obj:
                picking.action_confirm()
        except Exception as e:
            self._cr.rollback()
            _logger.exception(f"Failed to generate SL in generate SIPB {data.get('sipb_number')}")
            raise Warning(_(f"Warning!\n{e}"))
            
        self.suspend_security().write({'state': 'done'})
    
    def _process_utc(self):
        categ_id = self.env['product.category'].sudo().search([('name','=','Unit')])
        if not categ_id:
            categ_id = self.env['product.category'].sudo().create({'name': 'Unit'})

        for record in self:
            vals = record.convert_to_vals()
            create_vals = {}
            if vals.get('kode'):
                product_tmpl_id = self.env['product.template'].sudo().search([
                    '|',
                    ('default_code','=',vals.get('kode')),
                    ('reference_code_bundling','=',vals.get('kode')),
                ], limit=1)
                # If product template already exist, skip template creation
                if not product_tmpl_id:
                    # Create product
                    if vals.get('cc'):
                        cc_final = vals.get('cc')
                        accepted_char = '1234567890.'
                        for char in cc_final:
                            if char not in accepted_char:
                                cc_final = cc_final.replace(char,'')
                        try:
                            if '.' in cc_final:
                                cc_final = float(re.search(r'\d+\.\d+', vals.get('cc')).group())
                        except ValueError:
                            error = "Format CC Motor salah! CC: %s\nKode: %s\nUTC ID: %s" % (vals.get('cc'),(vals.get('kode_warna') or vals.get('kode')),vals.get('id'))
                            _logger.error(error)
                    
                    create_vals = {
                        'default_code': vals.get('kode'),
                        'factur_code': vals.get('kode_marketing'),
                        'name' : vals.get('desksripsi_type'),
                        'categ_id' : categ_id.id,
                        'division' : 'Unit',
                        'sale_ok' : True,
                        'purchase_ok' : True,
                        'is_storable' : True,
                        'lot_valuated' : True,
                        'tracking' : 'serial',
                        'type' : 'consu',
                    }
            if vals.get('warna'):
                attr_id = self.env['product.attribute'].search([('name','=','Color')]).id
                if not attr_id:
                    attr_id = self.env['product.attribute'].sudo().create({'name': 'Color'}).id

                color_id = self.env['product.attribute.value'].search([
                    ('code','=',vals.get('warna')),
                    ('attribute_id','=',attr_id)
                ],limit=1)
                if not color_id:
                    color_id = self.env['product.attribute.value'].create({
                        'attribute_id': attr_id,
                        'code': vals.get('warna'),
                        'name': vals.get('keterangan_warna')
                    })
                color_val = {
                    'attribute_id': color_id.attribute_id.id,
                    'value_ids': [[4,color_id.id]],
                }
                    
            try:
                check_variant = self._get_unit_product_id(vals.get('kode'),vals.get('kode_warna'))
                if create_vals:
                    # Create Product template 
                    create_vals.update({'attribute_line_ids' : [[0,False,color_val]]})
                    self.env['product.template'].create(create_vals)
                elif product_tmpl_id and not check_variant:
                    # Update Product template / Create variant
                    product_tmpl_id.with_context(create_product_product=True).write({'attribute_line_ids' : [[1,product_tmpl_id.attribute_line_ids[0].id,color_val]]})

                record.state = 'done'
                self._cr.commit()
                _logger.info("Product %s created successfully" % vals.get('kode'))
            except Exception as e:
                self._cr.rollback()
                _logger.error("Failed to create product %s: %s" % (vals.get('kode'), e))
                record.write({'state':'error','log':e})

    def _process_psl(self):
        self.suspend_security().write({'state':'done'})

    def _process_upo(self):
        for line in self.content_line_ids:
            data_split = line.value.split(' ')
            product_code = data_split[3]
            product_color_code = data_split[4]
            p2p_number = data_split[8]
            product_id = self.env['product.product']._get_unit_product_id(product_code,product_color_code)
            if not product_id:
                raise Warning(_("Produk %s dengan warna %s tidak ditemukan!" % (product_code, product_color_code)))
            p2p_obj = self.env['tw.p2p.purchase.order'].search([('name','=',p2p_number)])
            if not p2p_obj:
                raise Warning(_("Nomor P2P Purchase Order %s tidak ditemukan!" % (p2p_number)))
            # create error log
            line.env['tw.b2b.error.log'].suspend_security().create({
                'p2p_id': p2p_obj.id,
                'name': self.name,
            })
        if p2p_obj.state == 'waiting_for_verification':
            p2p_obj.suspend_security().action_revisi()
        self.suspend_security().write({'state':'done'})

    def _obtain_invoice(self, data):
        ref = data.get('ref')
        division = data.get('division')
        invoice_date = data.get('invoice_date')
        invoice_date_due = data.get('invoice_date_due')
        move_type = data.get('move_type')
        journal_id = data.get('journal_id')
        invoice_origin = data.get('factur_number')
        branch = data.get('branch')
        name = data.get('name')
        partner_id = branch.default_supplier_id.id
        currency_id = branch.currency_id.id

        AccountMove = self.env['account.move'].suspend_security()

        invoice = AccountMove.search([
            ('invoice_origin', '=', invoice_origin),
            ('ref', '=', ref),
            ('company_id', '=', branch.id),
            ('division', '=', division),
            ('invoice_date', '=', invoice_date),
            ('move_type', '=', move_type),
            ('journal_id', '=', journal_id),
        ])
        if not invoice:
            invoice = AccountMove.create({
                'invoice_origin': invoice_origin,
                'name': name or '/',
                'ref': ref,
                'company_id': branch.id,
                'division': division,
                'partner_id': partner_id,
                'invoice_date': invoice_date,
                'invoice_date_due': invoice_date_due,
                'invoice_payment_term_id': False,
                'move_type': move_type,
                'journal_id': journal_id,
                'currency_id': currency_id,
            })
            invoice.action_open()

        return invoice
