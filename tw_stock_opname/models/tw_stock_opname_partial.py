from odoo import models, fields
from odoo.exceptions import UserError as Warning
from datetime import datetime

class StockOpnamePartialWizard(models.TransientModel):
    _name = "tw.stock.opname.partial"
    _description = "Wizard Stock Opname Partial"

    def _get_default_main_dealer_code(self):
        return self.env['res.company'].get_default_main_dealer_code()

    def _get_default_datetime(self):
        return datetime.now()
    
    intransit_list = fields.Text('Intransit')
    
    proses = fields.Selection([
        ('generate', 'Generate'),
        ('recount', 'Recount') 
    ], string='Status', readonly=True, default='generate')
    type_so = fields.Selection([
        ('cycle_count', 'Cycle Count'),
        ('stock_opname', 'Stock Opname') 
    ], string='Tipe', default='stock_opname')
    
    opname_id = fields.Many2one('tw.stock.opname', ondelete="cascade")
    company_id = fields.Many2one('res.company', related='opname_id.company_id', string="Branch")
    partial_line_ids = fields.One2many('tw.stock.opname.partial.line', 'partial_id', domain=[('line_type', '=', 'unit')])
    partial_accessories_line_ids = fields.One2many('tw.stock.opname.partial.line', 'partial_id',domain=[('line_type', '=', 'accessory')])

    def action_generate(self):
        if self.opname_id.division == 'Unit':
            unit_data = self._get_unit_stock()
            accessories_data = self._get_accessories_stock()

            line_opname=[]
            for item in unit_data :
                lot_obj = self.env['stock.lot'].suspend_security().browse(item['lot_id'])
                line_opname.append([0, 0,  {
                    'product_id' : item.get('product_id'),
                    'location_id': lot_obj.location_id.id if not item.get('location_id') else item['location_id'],
                    'qty_system' : item.get('qty_system'),
                    'lot_id' :lot_obj.id,
                    'chassis_no': lot_obj.chassis_number,
                }])

            accessories_lines = []
            for item in accessories_data:
                accessories_lines.append([0, 0, {
                    'product_id': item.get('product_id'),
                    'qty_system': item.get('qty_system'),
                    'state': 'open',
                    'is_count': False,
                    'qty_good': 0.0,
                    'qty_not_good': 0.0,
                    'location_id': item.get('location_id'),
                }])

            # Create line Lokasi berdasarkan Detail SO
            self.opname_id.sudo().write({
                'detail_opname_ids' : line_opname,
                'detail_accessories_ids': accessories_lines
            })
            lokasi_vals = self.env['tw.stock.opname.location'].sudo().create_lokasi(self.opname_id.id)
            accessories_lokasi_vals = self.env['tw.stock.opname.accessories.location'].sudo().create_accessories_lokasi(self.opname_id.id)
            code = self.opname_id.generate_random_code()

            self.opname_id.sudo().write({
                'so_location_ids' : lokasi_vals,
                'so_accessories_location_ids': accessories_lokasi_vals,
                'code' : code,
                'state':'open',
                'open_uid': self._uid,
                'open_date': self._get_default_datetime(),
            })

        elif self.opname_id.division == 'Sparepart':
            if self.proses == 'recount':
                list_location = []
                for item in self.partial_line_ids:
                    list_location.append(item.location_id.id)
                detail_so = []
                for detail in self.opname_id.detail_opname_ids:
                    if detail.location_id.id in list_location:
                        if detail.state == 'anomali':
                            continue
                        detail_so.append([1, int(detail.id), {
                            'state' : 'open',
                            'qty_count' : 0,
                            'selisih' : 0,
                            'count_date' : None,
                            'is_recount' : True,
                            'employee_id' : None
                        }])
                self.opname_id.write({
                    'detail_opname_ids' : detail_so,
                    'state': 'recount',
                    'confirm_uid': self._uid,
                    'confirm_date': self._get_default_datetime()
                })
            else:
                data = self._get_sparepart_stock()
                if not data:
                    raise Warning("Detail Stock Opname tidak tergenerate.Stock pada branch ini kosong.")
                line_opname = []
                for line in data:
                    line_opname.append([0, 0, {
                        'product_id': line['product_id'],
                        'location_id': line['location_id'],
                        'qty_system': line['qty_system']
                    }])


                self.opname_id.write({
                    'detail_opname_ids' : line_opname,
                    'state': 'open',
                    'type_so' : self.type_so,
                    'open_uid': self._uid,
                    'open_date': self._get_default_datetime(),
                })

    def action_confirm_generate(self):
        return self.action_generate()

    def action_delete_partial(self):
        self.partial_line_ids.unlink()
        self.partial_accessories_line_ids.unlink()
        form_id = self.env.ref('tw_stock_opname.view_tw_stock_opname_partial_wizard').id
        return {
            'type': 'ir.actions.act_window',
            'name': ('Stock Opname Partial'),
            'res_model': 'tw.stock.opname.partial',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(form_id, 'form')],
            'target':'new',
            'res_id' : self.id,
            'context' : {
                'default_division': self.opname_id.division
            }
        }

    def _get_unit_stock(self):
        if not self.partial_line_ids:
            return []
        
        partial_line_ids = str(tuple(self.partial_line_ids.location_id.ids)).replace(',)', ')')
        query_where = f"WHERE sl.company_id = {self.opname_id.company_id.id}"
        query_where += f" AND sl.id IN {partial_line_ids}"
        if self.opname_id.division:
            query_where += f" AND pp.division = '{self.opname_id.division}'"

        query = f"""
            SELECT 
                sq.product_id,
                SUM(sq.quantity) AS qty_system,
                sq.lot_id,
                sl.id AS location_id
            FROM stock_quant sq
            LEFT JOIN stock_location sl ON sq.location_id = sl.id
            LEFT JOIN product_product pp ON sq.product_id = pp.id
            {query_where}
            GROUP BY 
                sq.product_id, 
                sq.lot_id, 
                sl.id;
        """

        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()

    def _get_accessories_stock(self):
        if not self.partial_accessories_line_ids:
            return []

        partial_accessories_line_ids = str(tuple(self.partial_accessories_line_ids.location_id.ids)).replace(',)', ')')
        query_where = f"WHERE sl.company_id = {self.opname_id.company_id.id}"
        query_where += f" AND sl.id IN {partial_accessories_line_ids}"

        if self.opname_id.division:
            query_where += f" AND (pp.division IS NULL OR pp.division != '{self.opname_id.division}')"

        query_where += " AND pc.complete_name ILIKE '%Extras%'"

        query = f"""
            SELECT 
                sq.product_id,
                SUM(sq.quantity) AS qty_system,
                sl.id AS location_id
            FROM stock_quant sq
            LEFT JOIN stock_location sl ON sq.location_id = sl.id
            LEFT JOIN product_product pp ON sq.product_id = pp.id
            LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
            LEFT JOIN product_category pc ON pt.categ_id = pc.id
            {query_where}
            GROUP BY 
                sq.product_id,
                sl.id;
        """

        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()

    def _get_sparepart_stock(self):
        if not self.partial_line_ids:
            return []
        
        partial_line_ids = str(tuple(self.partial_line_ids.location_id.ids)).replace(',)', ')')
        query_where = f"WHERE sl.company_id = {self.opname_id.company_id.id}"

        if self.partial_line_ids:
            query_where += f" AND sl.id IN {partial_line_ids}"
        if self.opname_id.division:
            query_where += f" AND pp.division = '{self.opname_id.division}'"

        query = f"""
            SELECT 
                sq.product_id,
                sl.id as location_id,
                SUM(sq.quantity) AS qty_system
            FROM stock_quant sq
            LEFT JOIN stock_location sl ON sq.location_id = sl.id
            LEFT JOIN product_product pp ON sq.product_id = pp.id
            {query_where}
            GROUP BY 
                sq.product_id, 
                sl.id;
        """

        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()
