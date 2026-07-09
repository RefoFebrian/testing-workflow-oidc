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

class TwExportMftFileSal(models.TransientModel):
    _name = "tw.export.mft.file.sal"
    _description = 'Export MFT File SAL'

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
        cron_obj = self.env.ref('tw_mft_file_sal.tw_ir_cron_auto_generate_mft_file_sal')
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
    def action_export_mft_file_sal_tree(self):
        domain = []
        name = 'Export MFT File SAL'
        path = 'export-mft-file-sal'
        form_view_id = self.env.ref('tw_mft_file_sal.tw_export_mft_file_sal_wizard_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'path': path,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'tw.export.mft.file.sal',
            'domain': domain,
            'views': [(form_view_id, 'form')],
            'context': {
                'search_default_fieldname': 1,
                'readonly_by_pass': 1
            },
        }
    
    def action_export(self, is_scheduller=False, params=None):
        filename = 'H2Z' + self._get_default_datetime().strftime('%d%m') + '.SAL'
        if is_scheduller:
            try:
                result, list_of_transaction_name = self._get_data(params=params)
            except Exception as err:
                error = f'Exception Generate MFT File SAL: {err}'
                _logger.warning(error)
                self._create_error_log(error)
                return True

            try:
                file = base64.b64encode(result.encode('utf-8')).decode('utf-8')
                if not file:
                    error = "Failed to Generate MFT File SAL, there's no data"
                    _logger.warning(error)
                    self._create_error_log(error)
                    return True

                self.env['tw.config.files'].with_context({'name': 'AHM-INTERFACE', 'type': 'mft'}).sudo().upload_file(filename, file)
                self._process_transaction_mft_sal(list_of_transaction_name)
                
            except Exception as err:
                error = f'Exception Generate MFT File SAL: {err}'
                _logger.warning(error)
                self._create_error_log(error)

            return True

        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        
        data = self._get_data_from_query(params=params)
        if data and self.is_skip_scheduler:
            schedule_action = self.env.ref('tw_mft_file_sal.tw_ir_cron_auto_generate_mft_file_sal')
            if schedule_action:
                schedule_action.suspend_security().write({'nextcall': schedule_action.nextcall + timedelta(days=1)})
            
        self.suspend_security().write({'name': filename, 'state': 'get'})
        return self.env['web.report'].sudo().generate_report('Report MFT File SAL', data)

    def schedule_auto_generate_mft_file_sal(self, params=None):
        return self.action_export(is_scheduller=True, params=params)
        
    # 14: private methods
    def _get_data_from_query(self, type='all', params=None):
        options = self.options or type
        query_where_so = ' AND so.state_sal_mft IS NOT TRUE'
        query_where_mo = ' AND mo.state_sal_mft IS NOT TRUE'
        
        start_date = self.start_date
        end_date = self.end_date
        if params and params.get('start_date'):
            start_date = params.get('start_date')
        if params and params.get('end_date'):
            end_date = params.get('end_date')
        if start_date and end_date:
            query_where_so += f" AND inv.invoice_date BETWEEN '{start_date}' AND '{end_date}'"
            query_where_mo += f" AND mo.confirm_date + INTERVAL '7 hours' BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'"
        
        company_id = False
        if params and params.get('company_id'):
            company_id = params.get('company_id')
        if not company_id and self.company_id:
            company_id = self.company_id.id
        if company_id:
            query_where_so += f' AND branch.id = {company_id}'
            query_where_mo += f' AND branch.id = {company_id}'

        list_requester_partner_code_mo = self.env['ir.config_parameter'].sudo().get_param('tw_mft_file_sal.list_requester_partner_code_mo') or []
        
        query_mo = f"""
            SELECT
                LEFT('H2Z' || '     ', 5)  --- kode main dealer
                || left(mo.name || '                              ', 30)  ---NO FAKTUR
                || left(TO_CHAR((mo.confirm_date + INTERVAL '7 hours'), 'DDMMYYYY HH24MISS') || '                    ',20) ---TANGGAL FAKTUR
                || left(COALESCE(company.atpm_code, 'NONCH') || '     ', 5)  ---KODE DEALER
                || left(sp.picking_name || '               ', 15)  ---NO PICKING SHEET
                || left(mo.name || '                              ', 30)  ---NOMOR PO DEAELR
                || left(pt.name ->> 'en_US' || '                         ', 25)  ---PRODUCT
                || right('          ' || mol.qty || '', 10)  ---QTY
                || right('               ' || mol.qty * mol.price || '', 15)  --- HET 
                || right('               ' || ROUND(cast((((mol.price )-(mol.price* ((0)/100)))*mol.qty)/(COALESCE(at.amount, 0 ) + 1) as numeric),2) || '', 15)  --- HET - Disc. 
                || right('               '|| ROUND(cast(mol.initial_cogs  * mol.qty as numeric), 2) || '', 15)  --- HPP
                as data
            , mo.name as transaction_name
            FROM tw_mutation_order mo
            INNER JOIN tw_mutation_order_line mol ON mol.mutation_order_id = mo.id
            INNER JOIN tw_stock_distribution sd ON sd.id = mo.stock_distribution_id
            INNER JOIN LATERAL(
                SELECT
                    mutation_order_id,
                    MIN(spick.name) AS picking_name
                FROM stock_picking spick
                INNER JOIN stock_picking_type spt ON spick.picking_type_id = spt.id AND spt.code = 'outgoing'
                WHERE spick.mutation_order_id = mo.id
                GROUP BY mutation_order_id
            ) sp ON mo.id = sp.mutation_order_id
            INNER JOIN product_product as p ON p.id = mol.product_id
            INNER JOIN product_template pt ON p.product_tmpl_id = pt.id
            INNER JOIN product_category pc ON pt.categ_id = pc.id 
            INNER JOIN res_company branch ON branch.id = mo.company_id
            LEFT JOIN tw_selection branch_type ON branch_type.id = branch.branch_type_id 
            INNER JOIN res_partner rp ON rp.id = sd.requester_id
            INNER JOIN res_company company ON company.partner_id = rp.id
            LEFT JOIN product_taxes_rel ptr ON ptr.prod_id = pt.id
            LEFT JOIN account_tax at ON at.id = ptr.tax_id
            WHERE 1=1
            AND mo.division = 'Sparepart'
            AND mo.state IN ('confirm','done')
            AND mol.qty > 0
            AND pc.name NOT ILIKE 'NONHGP%%'
            AND branch_type.value = 'MD'
            {query_where_mo}
        """

        query_so = f"""
            SELECT 
                LEFT('H2Z' || '     ', 5)  --- KODE MD
                || left(inv.name || '                              ', 30)  ---NO FAKTUR
                || left(TO_CHAR((inv.date + INTERVAL '7 hours'), 'DDMMYYYY HH24MISS') || '                    ',20) ---TANGGAL FAKTUR
                || left(COALESCE(company.atpm_code, 'NONCH') || '     ', 5)  ---KODE DEALER
                || left(spick.picking_name || '               ', 15)  ---NO PICKING SHEET
                || left(so.name || '                              ', 30)  ---NOMOR PO DEAELR
                || left(pt.name ->> 'en_US' || '                         ', 25)  ---PRODUCT
                || right('          ' || sol.product_uom_qty  || '', 10)  ---QTY
                || right('               ' || sol.product_uom_qty  * sol.price_unit || '', 15)  --- HET 
                || right('               ' || ROUND(sol.price_subtotal * (COALESCE(at.amount, 0) + 1), 2) || '', 15)  --- HET - Disc. 
                || right('               '|| ROUND(cast(sol.cogs * sol.product_uom_qty as numeric), 2) || '', 15)  --- HPP
                as data
            , so.name as transaction_name
            FROM tw_sale_order so
            INNER JOIN tw_sale_order_line sol ON sol.order_id = so.id
            LEFT JOIN account_tax_tw_sale_order_line_rel attsolr on attsolr.tw_sale_order_line_id = sol.id
            LEFT JOIN account_tax at on at.id = attsolr.account_tax_id
            INNER JOIN account_move inv ON inv.ref = so.name
            INNER JOIN tw_stock_distribution sd on sd.id = so.stock_distribution_id
            INNER JOIN res_company branch ON sd.company_id = branch.id
            LEFT JOIN tw_selection branch_type ON branch_type.id = branch.branch_type_id 
            INNER JOIN product_product as p ON sol.product_id = p.id
            INNER JOIN product_template pt ON p.product_tmpl_id = pt.id
            INNER JOIN product_category pc ON pt.categ_id = pc.id 
            LEFT JOIN res_partner rp ON rp.id = sd.requester_id
            LEFT JOIN res_company company ON company.partner_id = rp.id
            LEFT JOIN LATERAL (
                SELECT 
                    sale_order_id,
                    MIN(spick.name) AS picking_name
                FROM stock_picking spick
                LEFT JOIN stock_picking_type spt ON spick.picking_type_id = spt.id AND spt.code IN ('incoming', 'outgoing')
                WHERE spick.sale_order_id = so.id
                GROUP BY sale_order_id
            ) spick ON so.id = spick.sale_order_id
            WHERE 1=1
            AND inv.state IN ('open','paid')
            AND so.division = 'Sparepart'
            AND branch_type.value = 'MD'
            AND sol.product_uom_qty > 0
            AND pc.name NOT ILIKE 'NONHGP%%'
            {query_where_so}
            ORDER BY inv.invoice_date ASC, inv.name, pt.name ->> 'en_US'
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
        name = description = 'Auto Generate MFT File SAL'
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        response = {'error': error}
        api_log_model = self.env['tw.api.log'].sudo()
        api_log_model.create_api_log(name, url, description, '', response, {}, {})

    def _process_transaction_mft_sal(self, list_of_transaction_name):
        for transaction_name in list_of_transaction_name:
            if transaction_name[0:2] == 'SO':
                query = f"""
                    UPDATE tw_sale_order
                    SET state_sal_mft = TRUE
                    WHERE name = '{transaction_name}'
                """
            elif transaction_name[0:2] == 'MO':
                query = f"""
                    UPDATE tw_mutation_order
                    SET state_sal_mft = TRUE
                    WHERE name = '{transaction_name}'
                """
            self.env.cr.execute(query)

    
