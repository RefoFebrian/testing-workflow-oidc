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

class TwExportMftFileSto(models.TransientModel):
    _name = "tw.export.mft.file.sto"
    _description = 'Export MFT File STO'

    # 7: defaults methods
    def _get_default_datetime(self):
        return datetime.now()
    
    def _get_default_start_date(self):
        return date.today().replace(day=1)

    def _get_default_end_date(self):
        return date.today() - relativedelta(days=1)

    def _get_default_nextcall_date(self):
        cron_obj = self.env.ref('tw_mft_file_sto.tw_ir_cron_auto_generate_mft_file_sto')
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
    def action_export_mft_file_sto_tree(self):
        domain = []
        name = 'Export MFT File STO'
        path = 'export-mft-file-sto'
        form_view_id = self.env.ref('tw_mft_file_sto.tw_export_mft_file_sto_wizard_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'path': path,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'tw.export.mft.file.sto',
            'domain': domain,
            'views': [(form_view_id, 'form')],
            'context': {
                'search_default_fieldname': 1,
                'readonly_by_pass': 1
            },
        }
    
    def action_export(self, is_scheduller=False, params=None):
        filename = 'H2Z' + self._get_default_datetime().strftime('%d%m') + '.STO'
        if is_scheduller:
            try:
                result, list_of_product_code = self._get_data(params=params)
            except Exception as err:
                error = f'Exception Generate MFT File STO: {err}'
                _logger.warning(error)
                self._create_error_log(error)
                return True

            try:
                file = base64.b64encode(result.encode('utf-8')).decode('utf-8')
                if not file:
                    error = "Failed to Generate MFT File STO, there's no data"
                    _logger.warning(error)
                    self._create_error_log(error)
                    return True

                self.env['tw.config.files'].with_context({'name': 'AHM-INTERFACE', 'type': 'mft'}).sudo().upload_file(filename, file)
                
            except Exception as err:
                error = f'Exception Generate MFT File STO: {err}'
                _logger.warning(error)
                self._create_error_log(error)

            return True
        
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        data = self._get_data_from_query(params=params)
        if data and self.is_skip_scheduler:
            schedule_action = self.env.ref('tw_mft_file_sto.tw_ir_cron_auto_generate_mft_file_sto')
            if schedule_action:
                schedule_action.suspend_security().write({'nextcall': schedule_action.nextcall + timedelta(days=1)})
            
        self.suspend_security().write({'name': filename, 'state': 'get'})
        return self.env['web.report'].sudo().generate_report('Report MFT File STO', data)

    def schedule_auto_generate_mft_file_sto(self, params=None):
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
            query_where += f" AND quant.in_date + INTERVAL '7 hours' BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'"
        else:
            query_where += f" AND quant.in_date + INTERVAL '7 hours' BETWEEN '{date.today()} 00:00:00' AND '{date.today()} 23:59:59'"

        query = f"""
            SELECT 'H2Z  ' --kode main dealer
                || '{self._get_default_datetime().strftime('%d%m%Y')}' --tanggal stock dilaporkan
                || left(template.default_code || '                         ', 25) --part number
                || left(trim(SUM(quant.quantity)::int::text, ' ') || '          ', 10) --qty stock
                || left(trim(to_char((product.standard_price ->> quant.company_id::text)::float,'9999999999'), ' ') || '          ', 10) --harga pokok
                || left(trim(template.list_price::int::text, ' ') || '          ', 10) --harga jual
                as data,
                template.default_code as product_code
            FROM stock_quant quant
            INNER JOIN res_company company ON company.id = quant.company_id
            INNER JOIN stock_warehouse warehouse ON warehouse.company_id = company.id
            INNER JOIN stock_location location ON quant.location_id = location.id AND location.id = warehouse.lot_stock_id
            LEFT JOIN product_product product ON quant.product_id = product.id
            INNER JOIN product_template template ON product.product_tmpl_id = template.id
            INNER JOIN product_category category ON template.categ_id = category.id
            WHERE 1=1
            AND template.division = 'Sparepart'
            AND company.code = 'MML'
            AND category.name NOT ILIKE 'NONHGP%'
            AND quant.consolidated_date is not null
            AND product.standard_price is not null
            {query_where}
            GROUP BY template.default_code, product.standard_price, template.list_price, quant.company_id
        """
        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()

        return ress

    def _get_data(self, params=None):
        result = ''
        list_of_product_code = []
        data = self._get_data_from_query(params=params)
        for res in data:
            if res.get('data') and res.get('data') != 'None':
                result += str(res.get('data'))
                result += '\r\n'
            if res.get('product_code') not in list_of_product_code:
                list_of_product_code.append(res.get('product_code'))

        return result, list_of_product_code
    
    def _create_error_log(self, error):
        name = description = 'Auto Generate MFT File STO'
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        response = {'error': error}
        api_log_model = self.env['tw.api.log'].sudo()
        api_log_model.create_api_log(name, url, description, '', response, {}, {})

    
