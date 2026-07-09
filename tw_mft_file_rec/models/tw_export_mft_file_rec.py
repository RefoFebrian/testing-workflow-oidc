# 1: imports of python lib
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import base64

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib

class TwExportMftFileRec(models.TransientModel):
    _name = "tw.export.mft.file.rec"
    _description = 'Export MFT File REC'

    # 7: defaults methods
    def _get_default_datetime(self):
        return datetime.now()
    
    def _get_default_start_date(self):
        return date.today().replace(day=1)

    def _get_default_end_date(self):
        return date.today() - relativedelta(days=1)

    def _get_default_nextcall_date(self):
        cron_obj = self.env.ref('tw_mft_file_rec.tw_ir_cron_auto_generate_mft_file_rec')
        if cron_obj:
            return cron_obj.nextcall

    # 8: fields
    name = fields.Char(string='Filename', readonly=True)
    state = fields.Selection((
        ('choose', 'choose'),
        ('get', 'get')
    ), default=lambda *a: 'choose')
    start_date = fields.Date(string='Start Date', default=_get_default_start_date)
    end_date = fields.Date(string='End Date', default=_get_default_datetime)
    nextcall_date = fields.Datetime(string='Nextcall Date', default=_get_default_nextcall_date)
    is_skip_scheduler = fields.Boolean(string='Skip Scheduler H+1', default=False, help="Menambahkan 1 hari untuk next execute schedule action untuk menghindari replace data")

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods
    def action_export_mft_file_rec_tree(self):
        domain = []
        name = 'Export MFT File REC'
        path = 'export-mft-file-rec'
        form_view_id = self.env.ref('tw_mft_file_rec.tw_export_mft_file_rec_wizard_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'path': path,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'tw.export.mft.file.rec',
            'domain': domain,
            'views': [(form_view_id, 'form')],
            'context': {
                'search_default_fieldname': 1,
                'readonly_by_pass': 1
            },
        }
    
    def action_export(self, is_scheduller=False, params=None):
        filename = 'H2Z' + self._get_default_datetime().strftime('%d%m%Y') + '.REC'
        if is_scheduller:
            try:
                result, list_of_transaction_name = self._get_data(params=params)
            except Exception as err:
                error = f'Exception Generate MFT File REC: {err}'
                _logger.warning(error)
                self._create_error_log(error)
                return True

            try:
                file = base64.b64encode(result.encode('utf-8')).decode('utf-8')
                if not file:
                    error = "Failed to Generate MFT File REC, there's no data"
                    _logger.warning(error)
                    self._create_error_log(error)
                    return True

                self.env['tw.config.files'].with_context({'name': 'AHM-INTERFACE', 'type': 'mft'}).sudo().upload_file(filename, file)
                
            except Exception as err:
                error = f'Exception Generate MFT File REC: {err}'
                _logger.warning(error)
                self._create_error_log(error)

            return True

        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        data = self._get_data_from_query(params=params)
        if data and self.is_skip_scheduler:
            schedule_action = self.env.ref('tw_mft_file_rec.tw_ir_cron_auto_generate_mft_file_rec')
            if schedule_action:
                schedule_action.suspend_security().write({'nextcall': schedule_action.nextcall + timedelta(days=1)})
            
        self.suspend_security().write({'name': filename, 'state': 'get'})
        return self.env['web.report'].sudo().generate_report('Report MFT File REC', data)

    def schedule_auto_generate_mft_file_rec(self, params=None):
        return self.action_export(is_scheduller=True, params=params)
        
    # 14: private methods
    def _get_data_from_query(self, params=None):
        query_where = ''
        
        start_date = self.start_date
        end_date = self.end_date
        if params and params.get('start_date'):
            start_date = params.get('start_date')
        if params and params.get('end_date'):
            end_date = params.get('end_date')
        if start_date and end_date:
            query_where += f" AND picking.date_done + INTERVAL '7 hours' BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'"
        else:
            query_where += f" AND picking.date_done + INTERVAL '7 hours' BETWEEN '{date.today()} 00:00:00' AND '{date.today()} 23:59:59'"

        list_category_product = self.env['ir.config_parameter'].sudo().get_param('tw_mft_file_rec.list_category_product')
        if list_category_product:
            query_where += f' AND category.name NOT IN {list_category_product}'

        query = f"""
            SELECT
                RPAD('H2Z', 5, ' ') ||
                RPAD(COALESCE(batch.name, ''), 30, ' ') ||
                RPAD(TO_CHAR((picking.date_done + INTERVAL '7 hours'), 'DDMMYYYY') || ' 120000', 20, ' ') ||
                RPAD(COALESCE(picking.mft_reference, '') || 'AHM', 30, ' ') ||
                RPAD(COALESCE(po.origin, ''), 30, ' ') ||
                RPAD(COALESCE(p_template.default_code, ''), 25, ' ') ||
                LPAD(COALESCE(move.quantity::int::text, '0'), 10, ' ') as data,
                picking.name as transaction_name
            FROM stock_picking picking
            JOIN stock_picking_type picking_type ON picking_type.id = picking.picking_type_id
            JOIN stock_move move ON move.picking_id = picking.id
            JOIN product_product product ON product.id = move.product_id
            JOIN product_template p_template ON p_template.id = product.product_tmpl_id
            JOIN product_category category ON category.id = p_template.categ_id
            JOIN purchase_order po ON po.id = picking.purchase_order_id
            LEFT JOIN stock_picking_batch batch ON batch.id = picking.batch_id
            LEFT JOIN res_partner partner ON partner.id = picking.partner_id
            LEFT JOIN res_company company ON company.id = picking.company_id
            WHERE 1=1
            AND picking.division = 'Sparepart'
            AND partner.code = 'AHM'
            AND company.code = 'MML'
            AND picking.state = 'done'
            AND picking_type.code = 'incoming'
            {query_where}
        """
        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()

        return ress

    def _get_data(self, params=None):
        result = ''
        list_of_transaction_name = []
        data = self._get_data_from_query(params=params)
        for res in data:
            if res.get('data') and res.get('data') != 'None':
                result += str(res.get('data'))
                result += '\r\n'
            if res.get('transaction_name') not in list_of_transaction_name:
                list_of_transaction_name.append(res.get('transaction_name'))

        return result, list_of_transaction_name
    
    def _create_error_log(self, error):
        name = description = 'Auto Generate MFT File REC'
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        response = {'error': error}
        api_log_model = self.env['tw.api.log'].sudo()
        api_log_model.create_api_log(name, url, description, '', response, {}, {})

    
