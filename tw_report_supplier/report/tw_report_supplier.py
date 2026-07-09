# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwReportSupplier(models.TransientModel):
    _name = "tw.report.supplier"
    _description = "TW Report Supplier"

    # 7: defaults methods

    # 8: fields
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    option = fields.Selection([('ahass', 'Laporan AHASS'), ('biro_jasa', 'Laporan Birojasa'), ('dealer', 'Laporan Dealer'), ('finance_company', 'Laporan Finance Company'), ('forwarder', 'Laporan Forwarder'), ('principle', 'Laporan Principle'), ('showroom', 'Laporan Showroom'), ('supplier', 'Laporan Supplier'),], string='Type Supplier', required=True)

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_print_report(self):
        self.ensure_one()

        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        start_date = self.start_date
        end_date = self.end_date
        option = self.option

        if start_date and end_date and start_date > end_date:
            raise UserError(_("End Date harus lebih besar dari Start Date."))

        CATEGORY_MAP = {'ahass': ['AHASS'], 'biro_jasa': ['Birojasa'], 'dealer': ['Dealer'], 'finance_company': ['Finance Company'], 'forwarder': ['Forwarder'], 'principle': ['Principle'], 'showroom': ['Showroom'], 'supplier': ['Supplier', 'General Supplier'],}
        category_names = CATEGORY_MAP.get(option, [])

        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date

        for i, name in enumerate(category_names):
            params[f'cat_{i}'] = f'%{name}%'

        query = """
            SELECT 
                s.name AS "Nama",
                s.code AS "Kode Supplier",
                s.identification_number AS "No KTP",
                s.no_npwp AS "NPWP",
                s.street AS "Alamat",
                c.name AS "Prov",
                co.name AS "Kota",
                d.name AS "Kecamatan",
                sd.name AS "Kelurahan",
                s.alamat_pkp AS "Alamat PKP",
                s.tgl_pengukuhan AS "Tanggal PKP"
            FROM res_partner s
            LEFT JOIN res_city c ON c.id = s.city_id
            LEFT JOIN res_country_state co ON co.id = s.state_id
            LEFT JOIN res_district d ON d.id = s.district_id
            LEFT JOIN res_sub_district sd ON sd.id = s.sub_district_id
            WHERE 1=1
        """

        # Date filter
        if start_date:
            query += "\nAND s.tgl_pengukuhan >= %(start_date)s"
        if end_date:
            query += "\nAND s.tgl_pengukuhan <= %(end_date)s"

        # Category filter
        if category_names:
            category_conditions = ' OR '.join([f"cat.name::text ILIKE %(cat_{i})s" for i in range(len(category_names))])
            query += f"""
                AND EXISTS (
                    SELECT 1
                    FROM res_partner_res_partner_category_rel rel
                    JOIN res_partner_category cat ON cat.id = rel.category_id
                    WHERE rel.partner_id = s.id
                    AND ({category_conditions})
                )
            """

        query += "\nORDER BY s.name, s.id"

        self.env.cr.execute(query, params)

        res_data = self.env.cr.dictfetchall()
        report_name = dict(self._fields['option'].selection).get(option)
        return self.env['web.report'].generate_report(report_name, res_data, start_date=start_date, end_date=end_date, capitalize=False, show_total_footer=False,)

    # 14: private methods
