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

class TwExportMftFilePOD(models.TransientModel):
    _name = "tw.export.mft.file.pod"
    _description = 'Export MFT File POD'

    # 7: defaults methods
    def _get_default_branch(self):
        return self.env.user.company_ids.filtered(lambda b: b.parent_id == False) if self.env.user.company_ids else False
    
    def _get_default_datetime(self):
        return datetime.now()
    
    def _get_default_start_date(self):
        return date.today().replace(day=1)

    def _get_default_end_date(self):
        return date.today() - relativedelta(days=1)

    def _get_default_nextcall_date(self):
        cron_obj = self.env.ref('tw_mft_file_pod.tw_ir_cron_auto_generate_mft_file_pod')
        if cron_obj:
            return cron_obj.nextcall

    # 8: fields
    name = fields.Char(string='Filename', readonly=True)
    state = fields.Selection((
        ('choose', 'choose'),
        ('get', 'get')
    ), default=lambda *a: 'choose')
    options = fields.Selection([
        ('all', 'All'),
        ('dll', 'DLL'),
        ('mmw', 'MMW')
    ], string='Options', default='all')
    start_date = fields.Date(string='Start Date', default=_get_default_start_date)
    end_date = fields.Date(string='End Date', default=_get_default_datetime)
    nextcall_date = fields.Datetime(string='Nextcall Date', default=_get_default_nextcall_date)
    is_skip_scheduler = fields.Boolean(string='Skip Scheduler H+1', default=False, help="Menambahkan 1 hari untuk next execute schedule action untuk menghindari replace data")

    # 9: relation fields
    company_id = fields.Many2one(comodel_name='res.company', string='Branch', domain="[('parent_id','=',False)]", default=_get_default_branch)

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods
    def action_export_mft_file_pod_tree(self):
        domain = []
        name = 'Export MFT File POD'
        path = 'export-mft-file-pod'
        form_view_id = self.env.ref('tw_mft_file_pod.tw_export_mft_file_pod_wizard_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'path': path,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'tw.export.mft.file.pod',
            'domain': domain,
            'views': [(form_view_id, 'form')],
            'context': {
                'search_default_fieldname': 1,
                'readonly_by_pass': 1
            },
        }
    
    def action_export(self, is_scheduller=False, params=None):
        filename = 'H2Z' + self._get_default_datetime().strftime('%d%m') + '.POD'
        if is_scheduller:
            try:
                result, list_of_transaction_name = self._get_data(params=params)
            except Exception as err:
                error = f'Exception Generate MFT File POD: {err}'
                _logger.warning(error)
                self._create_error_log(error)
                return True

            try:
                file = base64.b64encode(result.encode('utf-8')).decode('utf-8')
                if not file:
                    error = "Failed to Generate MFT File POD, there's no data"
                    _logger.warning(error)
                    self._create_error_log(error)
                    return True

                self.env['tw.config.files'].with_context({'name': 'AHM-INTERFACE', 'type': 'mft'}).sudo().upload_file(filename, file)
                self._process_transaction_mft_pod(list_of_transaction_name)
                
            except Exception as err:
                error = f'Exception Generate MFT File POD: {err}'
                _logger.warning(error)
                self._create_error_log(error)

            return True

        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        data = self._get_data_from_query(params=params)
        if data and self.is_skip_scheduler:
            schedule_action = self.env.ref('tw_mft_file_pod.tw_ir_cron_auto_generate_mft_file_pod')
            if schedule_action:
                schedule_action.suspend_security().write({'nextcall': schedule_action.nextcall + timedelta(days=1)})
            
        self.suspend_security().write({'name': filename, 'state': 'get'})
        return self.env['web.report'].sudo().generate_report('Report MFT File POD', data)

    def schedule_auto_generate_mft_file_pod(self, params=None):
        return self.action_export(is_scheduller=True, params=params)
        
    # 14: private methods
    def _get_data_from_query(self, type='all', params=None):
        options = self.options or type
        query_where_so = ' AND so.state_pod_mft IS NOT TRUE'
        query_where_mo = ' AND mo.state_pod_mft IS NOT TRUE'
        query_where_bundling = ' AND mp.state_pod_mft IS NOT TRUE'
        
        start_date = self.start_date
        end_date = self.end_date
        if params and params.get('start_date'):
            start_date = params.get('start_date')
        if params and params.get('end_date'):
            end_date = params.get('end_date')
        if start_date and end_date:
            query_where_so += f" AND inv.date_invoice BETWEEN '{start_date}' AND '{end_date}'"
            query_where_mo += f" AND mo.confirm_date + INTERVAL '7 hours' BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'"
            query_where_bundling += f" AND mp.confirm_date + INTERVAL '7 hours' BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'"
        
        company_id = False
        if params and params.get('company_id'):
            company_id = params.get('company_id')
        if not company_id and self.company_id:
            company_id = self.company_id.id
        if company_id:
            query_where_so += f' AND b.id = {company_id}'
            query_where_mo += f' AND b.id = {company_id}'
            query_where_bundling += f' AND b.id = {company_id}'

        list_requester_partner_code_mo = self.env['ir.config_parameter'].sudo().get_param('tw_mft_file_pod.list_requester_partner_code_mo') or []
        
        query_mo = f"""
            SELECT
                LEFT(COALESCE(parent.code, 'H2Z') || '     ', 5) --- KODE MD
                || LEFT(COALESCE(brp.atpm_code, 'NONCH')  || '     ', 5) --- KODE DEALER
                || LEFT(mo.name || '                              ', 30) --- NOMOR PO DEAELR
                || LEFT(TO_CHAR((mo.confirm_date + INTERVAL '7 hours'), 'DDMMYYYY HH24MISS') || '                    ',20) --- TANGGAL FAKTUR
                || LEFT(pt.name ->> 'en_US'      || '                         ', 25) --- PRODUCT
                || RIGHT('          '|| FLOOR(mol.qty * 1.018) || '', 10)  --- QTY
                || CASE UPPER(pot.name) WHEN 'HOTLINE' THEN 'H' ELSE 'R' END
                AS data
                , mo.name AS transaction_name
            FROM tw_mutation_order mo
            INNER JOIN tw_mutation_order_line mol ON mol.mutation_order_id = mo.id
            INNER JOIN tw_stock_distribution sd ON mo.stock_distribution_id = sd.id
            INNER JOIN product_product p ON mol.product_id = p.id
            INNER JOIN product_template pt ON p.product_tmpl_id = pt.id
            INNER JOIN product_category pc ON pt.categ_id = pc.id
            INNER JOIN res_company b ON mo.company_id = b.id
            LEFT JOIN res_company parent ON b.parent_id = parent.id
            INNER JOIN tw_selection bt ON b.branch_type_id = bt.id
            INNER JOIN res_partner rp ON sd.requester_id = rp.id
            LEFT JOIN res_company brp ON brp.partner_id = rp.id
            LEFT JOIN tw_purchase_order_type pot ON sd.purchase_order_type_id = pot.id
            WHERE 1=1
            AND mo.division = 'Sparepart'
            AND mo.state IN ('confirm', 'done')
            AND mol.qty > 0
            AND pc.name NOT ILIKE 'NONHGP%%'
            AND bt.value = 'MD'
            {query_where_mo}
            ORDER BY mo.confirm_date ASC, mo.name, pt.name ->> 'en_US'
        """

        query_so = f"""
            SELECT
                LEFT(COALESCE(parent.code, 'H2Z') || '     ', 5) --- KODE MD
                || LEFT(COALESCE(brp.atpm_code, 'NONCH')  || '     ', 5) --- KODE DEALER
                || LEFT(so.name || '                              ', 30) --- NOMOR PO DEALER
                || LEFT(TO_CHAR((inv.date_invoice + INTERVAL '7 hours'), 'DDMMYYYY HH24MISS') || '                    ',20) --- TANGGAL FAKTUR
                || LEFT(pt.name ->> 'en_US'      || '                         ', 25) --- PRODUCT
                || RIGHT('          ' || FLOOR(sol.product_uom_qty * 1.018) || '', 10) --- QTY
                || CASE UPPER(pot.name) WHEN 'HOTLINE' THEN 'H' ELSE 'R' END
                AS data
                , so.name AS transaction_name
            FROM tw_sale_order so
            INNER JOIN tw_sale_order_line sol ON sol.order_id = so.id
            INNER JOIN tw_stock_distribution sd ON so.stock_distribution_id = sd.id
            INNER JOIN res_company b ON sd.company_id = b.id
            LEFT JOIN res_company parent ON b.parent_id = parent.id
            INNER JOIN tw_selection bt ON b.branch_type_id = bt.id
            INNER JOIN product_product p ON sol.product_id = p.id
            INNER JOIN product_template pt ON p.product_tmpl_id = pt.id
            INNER JOIN product_category pc ON pt.categ_id = pc.id
            LEFT JOIN res_partner rp ON sd.requester_id = rp.id
            LEFT JOIN res_company brp ON brp.partner_id = rp.id
            LEFT JOIN tw_purchase_order_type pot ON sd.purchase_order_type_id = pot.id
            LEFT JOIN LATERAL (
                SELECT
                    am.invoice_date date_invoice
                FROM account_move am
                WHERE 1=1
                AND am.division = 'Sparepart'
                AND am.ref = so.name
                AND am.invoice_origin = so.name
                AND am.move_type = 'out_invoice'
                AND am.company_id = b.id
                LIMIT 1
            ) inv ON TRUE
            WHERE 1=1
            AND so.state IN ('approved', 'sale', 'done')
            AND so.division = 'Sparepart'
            AND bt.value = 'MD'
            AND sol.product_uom_qty > 0
            AND pc.name NOT ILIKE 'NONHGP%%'
            {query_where_so}
            ORDER BY inv.date_invoice ASC, so.name, pt.name ->> 'en_US'
        """

        query_bundling = f"""
            SELECT
                LEFT(COALESCE(parent.code, 'H2Z') || '     ', 5) --- KODE MD
                || LEFT(COALESCE(tbs.atpm_code_bundling, 'NONCH')  || '     ', 5) --- KODE DEALER
                || LEFT(mp.name || '                              ', 30) --- NOMOR PO DEAELR
                || LEFT(TO_CHAR((mp.confirm_date + INTERVAL '7 hours'), 'DDMMYYYY HH24MISS') || '                    ',20) --- TANGGAL FAKTUR
                || LEFT(pt.name ->> 'en_US'      || '                         ', 25) --- PRODUCT
                || RIGHT('          '|| FLOOR(sm.product_uom_qty * 1.018) || '', 10)  --- QTY
                || CASE UPPER(mp.order_type) WHEN 'HOTLINE' THEN 'H' ELSE 'R' END
                AS data
                , mp.name AS transaction_name
            FROM mrp_production mp
            LEFT JOIN res_company b ON mp.company_id = b.id
            LEFT JOIN res_company parent ON b.parent_id = parent.id
            LEFT JOIN tw_branch_setting tbs ON tbs.company_id = b.id
            INNER JOIN tw_selection bt ON b.branch_type_id = bt.id
            INNER JOIN stock_move sm ON sm.raw_material_production_id = mp.id
            INNER JOIN product_product p ON sm.product_id = p.id
            INNER JOIN product_template pt ON p.product_tmpl_id = pt.id
            INNER JOIN product_category pc ON pt.categ_id = pc.id
            WHERE 1=1
            AND pt.division = 'Sparepart'
            AND mp.state = 'done'
            AND mp.order_type = 'bundling'
            AND bt.value = 'MD'
            AND sm.product_uom_qty > 0
            AND pc.name NOT ILIKE 'NONHGP%%'
            {query_where_bundling}
            ORDER BY mp.confirm_date ASC, mp.name, pt.name ->> 'en_US'
        """

        if options == 'all':
            query_where_mo += " AND rp.code NOT IN ('DLL', 'MMW')"
            if list_requester_partner_code_mo:
                query_where_so += f" AND rp.code NOT IN {str(tuple(list_requester_partner_code_mo)).replace(',)', ')')}"

            query = f"""
                (
                    {query_so}
                )
                UNION ALL
                (
                    {query_mo}
                )
                UNION ALL
                (
                    {query_bundling}
                )
            """
        else:
            if options == 'dll':
                query_where_mo += " AND rp.code = 'DLL'"
            elif options == 'mmw':
                query_where_mo += " AND rp.code = 'MMW'"
            
            query = query_mo

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
        name = description = 'Auto Generate MFT File POD'
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        response = {'error': error}
        api_log_model = self.env['tw.api.log'].sudo()
        api_log_model.create_api_log(name, url, description, '', response, {}, {})

    def _process_transaction_mft_pod(self, list_of_transaction_name):
        for transaction_name in list_of_transaction_name:
            if transaction_name[0:2] == 'SO':
                query = f"""
                    UPDATE tw_sale_order
                    SET state_pod_mft = TRUE
                    WHERE name = '{transaction_name}'
                """
            elif transaction_name[0:2] == 'MO':
                query = f"""
                    UPDATE tw_mutation_order
                    SET state_pod_mft = TRUE
                    WHERE name = '{transaction_name}'
                """
            self.env.cr.execute(query)
