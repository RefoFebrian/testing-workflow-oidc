from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.exceptions import UserError as Warning

class VehicleDocumentReport(models.TransientModel):
    _name = "tw.vehicle.document.report"
    _description = "Vehicle Document Report"

    def _get_default_date(self): 
        return datetime.now()

    start_date = fields.Date('Start Date', default=_get_default_date)
    end_date = fields.Date('End Date', default=_get_default_date)

    options = fields.Selection([
        ('tracking_document','Tracking STNK BPKB'),
        ('lead_time','Lead Time STNK BPKB'),
        ('stock_registration','Stock STNK'),
        ('stock_ownership','Stock BPKB')
    ], string='Options', default='tracking_document')
    status_lead_time = fields.Selection([
        ('all','All'),
        ('complete','Complete'),
        ('outstanding','Outstanding')
    ],string="Status")

    def _get_default_companies(self):
        return self.env.user.company_ids.ids

    lot_ids = fields.Many2many('stock.lot', string='No Mesin')
    company_ids = fields.Many2many(
        comodel_name='res.company', 
        relation='tw_vehicle_document_report_company_rel',
        column1='vehicle_document_report_id', 
        column2='company_id', 
        string='Branch',
        default=_get_default_companies,
        domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)]
    )
    biro_jasa_ids = fields.Many2many(comodel_name='res.partner', relation='tw_vehicle_document_report_birojasa_rel',
                                  column1='vehicle_document_report_id', column2='biro_jasa_id', domain=[('category_id.name', '=', 'Birojasa')])
    finco_ids = fields.Many2many(comodel_name='res.partner', relation='tw_vehicle_document_report_finco_rel',
                                  column1='vehicle_document_report_id', column2='finco_id', domain=[('category_id.name', '=', 'Finance Company')])
    customer_ids = fields.Many2many(comodel_name='res.partner', relation='tw_vehicle_document_report_customer_rel',
                                  column1='vehicle_document_report_id', column2='customer_id')
    vehicle_registration_location_ids = fields.Many2many(
        'tw.vehicle.document.location', 
        relation='tw_vehicle_document_report_registration_location_rel',
        column1='vehicle_document_report_id', 
        column2='registration_location_id',
        string="Lokasi STNK", 
        domain=[('document_type', '=', 'vehicle_registration')]
    )
    vehicle_ownership_location_ids = fields.Many2many(
        'tw.vehicle.document.location',
        relation='tw_vehicle_document_report_ownership_location_rel',
        column1='vehicle_document_report_id',
        column2='ownership_location_id',
        string="Lokasi BPKB",
        domain=[('document_type', '=', 'vehicle_ownership')]
    )

    @api.onchange("options")
    def _onchange_options(self):
        self.lot_ids = False
        self.company_ids = False
        self.biro_jasa_ids = False
        self.finco_ids = False
        self.customer_ids = False
        self.vehicle_registration_location_ids = False
        self.vehicle_ownership_location_ids = False
        self.status_lead_time = False
        self.start_date = False
        self.end_date = False

    def _get_allowed_company_ids(self):
        """Get company IDs to filter. Use selected or fallback to user's companies."""
        if self.company_ids:
            return self.company_ids.ids
        return self.env.user.company_ids.ids

    def get_query_tracking_document(self):
        # Always filter by allowed companies
        allowed_companies = self._get_allowed_company_ids()
        company_filter = str(tuple(allowed_companies)).replace(',)', ')')
        where = f"WHERE b.id notnull and a.state = 'paid' AND a.company_id in {company_filter}"
        if self.biro_jasa_ids:
            where += " AND a.biro_jasa_id in {}".format(str(tuple(self.biro_jasa_ids.ids)).replace(',)', ')'))
        if self.finco_ids:
            where += " AND a.finco_id in {}".format(str(tuple(self.finco_ids.ids)).replace(',)', ')'))
        if self.customer_ids:
            where += " AND a.partner_id in {}".format(str(tuple(self.customer_ids.ids)).replace(',)', ')'))
        if self.vehicle_registration_location_ids:
            where += " AND a.vehicle_registration_location_id in {}".format(str(tuple(self.vehicle_registration_location_ids.ids)).replace(',)', ')'))
        if self.vehicle_ownership_location_ids:
            where += " AND a.vehicle_ownership_location_id in {}".format(str(tuple(self.vehicle_ownership_location_ids.ids)).replace(',)', ')'))
        if self.start_date:
            where += " AND k.date_order >= '{}'".format(self.start_date)
        if self.end_date:
            where += " AND k.date_order <= '{}'".format(self.end_date)
        if self.lot_ids:
            where += " AND a.id in {}".format(str(tuple(self.lot_ids.ids)).replace(',)', ')'))
            
        query = f"""
            select  
                b.name as nama_branch,  
                e.code as code_nama_customer,  
                e.name as nama_customer,
                e.street as alamat_customer,  
                a.name as engine_no,  
                a.chassis_number as chassis_no,
                c.name as lokasi_stnk, 
                d.name as lokasi_bpkb,  
                f.name as location_name,  
                g.name as supplier_name,  
                h.code as code_stnk_name,  
                h.name as stnk_name,  
                a.state as state,  
                i.name as finco_name,  
                j.name as birojasa_name,  
                k.name as sale_order,  
                a.invoice_date as tgl_sale_order,  
                z.name as purchase_order,  
                z."date" as tgl_purchase_order,  
                l.name as no_permohonan_faktur,  
                a.vehicle_document_request_date as tgl_faktur,  
                m.name as no_penerimaan_faktur,  
                a.vehicle_document_receive_date as tgl_terima,  
                a.doc_number as no_faktur,  
                a.print_date as tgl_cetak_faktur,  
                n.name as no_proses_stnk,  
                a.registration_process_date as tgl_proses_stnk,  
                o.name as no_proses_birojasa,  
                a.birojasa_billing_date as tgl_proses_birojasa,  
                '' as no_penyerahan_faktur,  
                '' as tgl_penyerahan_faktur, 
                q.name as no_penerimaan_stnk,   
                r.name as no_penerimaan_notice,  
                s.name as no_penerimaan_no_polisi,  
                t.name as no_penerimaan_bpkb,  
                a.notice_number as no_notice,  
                a.vehicle_ownership_number as no_bpkb,   
                a.plate_number as no_polisi,                         
                a.vehicle_registration_number as no_stnk,  
                a.notice_date as tgl_notice,  
                a.stnk_date as tgl_stnk,  
                a.vehicle_ownership_date as tgl_bpkb,  
                a.vehicle_ownership_order_number as no_urut_bpkb,  
                a.vehicle_registration_receipt_date as tgl_terima_stnk,
                a.vehicle_ownership_receipt_date as tgl_terima_bpkb,              
                a.notice_receipt_date as tgl_terima_notice,  
                a.plate_receipt_date as tgl_terima_no_polisi,  
                u.name as no_penyerahan_stnk,  
                w.name as no_penyerahan_notice,  
                x.name as no_penyerahan_polisi, 
                v.name as no_penyerahan_bpkb,               
                a.registration_handover_date as tgl_penyerahan_stnk,  
                a.notice_handover_date as tgl_penyerahan_notice,  
                a.ownership_handover_date as tgl_penyerahan_plat,  
                a.plate_handover_date as tgl_penyerahan_bpkb,  
                '' as no_pengurusan_stnk_bpkb,  
                '' as tgl_pengurusan_stnk_bpkb,
                invoice.name as invoice_bbn,
                (pt.description::jsonb ->> 'en_US')::text as desc_type,
                pp.default_code as kode_type,
            --    CASE WHEN a.md_reference_faktur_stnk IS NOT NULL
            --    THEN 'DGI' ELSE 'Non DGI' END,
                'Non DGI' AS source_data
                From stock_lot a 
                LEFT JOIN account_move invoice ON invoice.id = a.accure_bbn_move_id
                LEFT JOIN res_company b ON b.id = a.company_id 
                LEFT JOIN tw_vehicle_document_location c ON c.id = a.vehicle_registration_location_id 
                LEFT JOIN tw_vehicle_document_location d ON d.id = a.vehicle_ownership_location_id
                LEFT JOIN res_partner e ON e.id = a.partner_id 
                LEFT JOIN stock_location f ON f.id = a.location_id 
                LEFT JOIN res_partner g ON g.id = a.supplier_id 
                LEFT JOIN res_partner h ON h.id = a.customer_stnk_id 
                LEFT JOIN res_partner i ON i.id = a.finco_id 
                LEFT JOIN res_partner j ON j.id = a.biro_jasa_id 
                LEFT JOIN tw_dealer_sale_order k ON k.id = a.dealer_sale_order_id 
                LEFT JOIN tw_vehicle_document_request l ON l.id = a.vehicle_document_request_id 
                LEFT JOIN tw_vehicle_document_receive m ON m.id = a.vehicle_document_receive_id 
                LEFT JOIN tw_vehicle_registration_process n ON n.id = a.registration_process_id 
                LEFT JOIN tw_birojasa_billing_process o ON o.id = a.birojasa_billing_id 
            --    LEFT JOIN wtc_penyerahan_faktur p ON p.id = a.penyerahan_faktur_id 
                LEFT JOIN tw_vehicle_registration_receipt q ON q.id = a.vehicle_registration_receipt_id 
                LEFT JOIN tw_vehicle_registration_receipt r ON r.id = a.notice_receipt_id 
                LEFT JOIN tw_vehicle_registration_receipt s ON s.id = a.plate_receipt_id 
                LEFT JOIN tw_vehicle_ownership_receipt t ON t.id = a.vehicle_ownership_receipt_id 
                LEFT JOIN tw_vehicle_registration_handover u ON u.id = a.registration_handover_id 
                LEFT JOIN tw_vehicle_ownership_handover v ON v.id = a.ownership_handover_id 
                LEFT JOIN tw_vehicle_registration_handover w ON w.id = a.notice_handover_id 
                LEFT JOIN tw_vehicle_registration_handover x ON x.id = a.plate_handover_id 
            --    LEFT JOIN wtc_pengurusan_stnk_bpkb y ON y.id = a.pengurusan_stnk_bpkb_id 
                LEFT JOIN purchase_order z ON z.id = a.purchase_order_id
                LEFT JOIN product_product pp ON pp.id=a.product_id
                LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id 
                LEFT JOIN product_variant_combination as combination on combination.product_product_id = pp.id
                LEFT JOIN product_template_attribute_value as ptav on ptav.id = combination.product_template_attribute_value_id
                LEFT JOIN product_attribute_value ppv ON ppv.id = ptav.product_attribute_value_id
                {where}
            """
        
        return query
    
    def get_query_lead_time(self):
        # Always filter by allowed companies
        allowed_companies = self._get_allowed_company_ids()
        company_filter = str(tuple(allowed_companies)).replace(',)', ')')
        where = f" WHERE sl.company_id in {company_filter}"
        if self.biro_jasa_ids:
            where += " AND sl.biro_jasa_id in {}".format(str(tuple(self.biro_jasa_ids.ids)).replace(',)', ')'))
        if self.finco_ids:
            where += " AND sl.finco_id in {}".format(str(tuple(self.finco_ids.ids)).replace(',)', ')'))
        if self.customer_ids:
            where += " AND sl.partner_id in {}".format(str(tuple(self.customer_ids.ids)).replace(',)', ')'))
        if self.vehicle_registration_location_ids:
            where += " AND sl.vehicle_registration_location_id in {}".format(str(tuple(self.vehicle_registration_location_ids.ids)).replace(',)', ')'))
        if self.vehicle_ownership_location_ids:
            where += " AND sl.vehicle_ownership_location_id in {}".format(str(tuple(self.vehicle_ownership_location_ids.ids)).replace(',)', ')'))
        if self.lot_ids:
            where += " AND sl.id in {}".format(str(tuple(self.lot_ids.ids)).replace(',)', ')'))
        if self.start_date :
            where+=" AND tdso.date_order >= '%s'" % str(self.start_date)
        if self.end_date :
            where+=" AND tdso.date_order <= '%s'" % str(self.end_date)

        if self.status_lead_time:
            if self.status_lead_time == 'complete':
                where += """ 
                    AND sl.vehicle_document_receive_date IS NOT NULL
                    AND sl.vehicle_document_request_date IS NOT NULL IS NOT NULL
                    AND sl.print_date IS NOT NULL
                    AND sl.registration_process_date IS NOT NULL
                    AND sl.birojasa_billing_date IS NOT NULL
                    AND sl.notice_receipt_date IS NOT NULL
                    AND sl.vehicle_registration_receipt_date IS NOT NULL
                    AND sl.plate_receipt_date IS NOT NULL
                    AND sl.vehicle_ownership_receipt_date IS NOT NULL
                    AND sl.notice_handover_date IS NOT NULL
                    AND sl.registration_handover_date IS NOT NULL
                    AND sl.plate_handover_date IS NOT NULL
                    AND sl.ownership_handover_date IS NOT NULL
                """
            elif self.status_lead_time == 'outstanding':
                where += """ AND (
                    sl.vehicle_document_receive_date IS NULL
                    OR sl.vehicle_document_request_date IS NULL IS NULL
                    OR sl.print_date IS NULL
                    OR sl.registration_process_date IS NULL
                    OR sl.birojasa_billing_date IS NULL
                    OR sl.notice_receipt_date IS NULL
                    OR sl.vehicle_registration_receipt_date IS NULL
                    OR sl.plate_receipt_date IS NULL
                    OR sl.vehicle_ownership_receipt_date IS NULL
                    OR sl.notice_handover_date IS NULL
                    OR sl.registration_handover_date IS NULL
                    OR sl.plate_handover_date IS NULL
                    OR sl.ownership_handover_date IS NULL
                    )
                """

        query = f"""
            SELECT tdso.date_order as date_order
                , sl.name as no_engine
                , sl.chassis_number as no_chassis
                , partner.code as code_customer
                , partner.name as customer_name
                , customer.code as code_an_stnk
                , customer.name as an_stnk_name
                , partner.street as customer_address
                , sl.vehicle_document_request_date as tgl_mohon_faktur
                , age(sl.vehicle_document_request_date,tdso.date_order) as lt_mohon_faktur
                , sl.vehicle_document_receive_date as tgl_terima_faktur
                , sl.print_date as tgl_cetak_faktur
                , sl.doc_number as no_faktur
                , age(sl.vehicle_document_receive_date,tdso.date_order) as lt_terima_faktur
                , sl.registration_process_date as tgl_proses_stnk
                , birojasa.name as birojasa
                , age(sl.registration_process_date,tdso.date_order) as lt_proses_stnk
                , sl.birojasa_billing_date as tgl_tagihan_birojasa
                , age(sl.birojasa_billing_date,tdso.date_order) as lt_tagihan_birojasa
                , sl.notice_receipt_date as tgl_terima_notice
                , sl.notice_number as no_notice
                , sl.notice_date as tgl_jtp_notice
                , age(sl.notice_receipt_date,tdso.date_order) as lt_terima_notice
                , sl.vehicle_registration_receipt_date as tgl_terima_stnk
                , sl.vehicle_registration_number as no_stnk
                , sl.stnk_date as tgl_jtp_stnk
                , age(sl.vehicle_registration_receipt_date,tdso.date_order) as lt_terima_stnk
                , sl.plate_receipt_date as tgl_terima_plat
                , sl.plate_number as no_plat
                , age(sl.plate_receipt_date,tdso.date_order) as lt_terima_plat
                , sl.vehicle_ownership_receipt_date as tgl_terima_bpkb
                , sl.vehicle_ownership_number as no_bpkb
                , sl.vehicle_ownership_date as tgl_jadi_bpkb
                , sl.vehicle_ownership_order_number as no_urut
                , age(sl.vehicle_ownership_receipt_date,tdso.date_order) as lt_terima_bpkb
                , sl.notice_handover_date as tgl_penyerahan_notice
                , age(sl.notice_handover_date,tdso.date_order) as lt_penyerahan_notice
                , sl.registration_handover_date as tgl_penyerahan_stnk
                , age(sl.registration_handover_date,tdso.date_order) as lt_penyerahan_stnk
                , sl.plate_handover_date as tgl_penyerahan_plat
                , age(sl.plate_handover_date,tdso.date_order) as lt_penyerahan_plat
                , sl.ownership_handover_date as tgl_penyerahan_bpkb
                , age(sl.ownership_handover_date,tdso.date_order) as lt_penyerahan_bpkb
                , tdso.name as no_dso
                , partner.mobile
                , rc.code as branch_code
                , rc.name as branch_name
                , '['||city.code||']'|| city.name as area
                , to_char(tdso.date_order,'MM') as bulan_so
                , to_char(tdso.date_order,'YYYY') as tahun_so
                , supplier.name as main_dealer
                , finco.name as finco
                , sl.ownership_receiver as penerima_bpkb
                , '' as tgl_bayar_prbj
                , pc.name as category_name
                , (ps.name::jsonb ->> 'en_US')::text as series
            FROM stock_lot sl
            INNER JOIN tw_dealer_sale_order tdso ON tdso.id = sl.dealer_sale_order_id 
            LEFT JOIN res_partner partner ON partner.id = sl.partner_id 
            LEFT JOIN res_partner customer ON customer.id = sl.customer_stnk_id
            LEFT JOIN res_partner birojasa ON birojasa.id = sl.biro_jasa_id
            LEFT JOIN res_company rc ON rc.id = sl.company_id
            LEFT JOIN res_city city ON city.id = customer.city_id
            LEFT JOIN res_partner supplier ON supplier.id = rc.default_supplier_id
            LEFT JOIN res_partner finco ON finco.id = sl.finco_id
            LEFT JOIN product_product pp on sl.product_id = pp.id
            LEFT JOIN product_template pt on pp.product_tmpl_id = pt.id
            LEFT JOIN product_category pc on pt.categ_id = pc.id
            LEFT JOIN product_series ps ON ps.id = pp.series_id 
            {where}
            AND document_state NOTNULL 
            
        """

        return query
    
    def get_query_stock_document_registration(self):
        # Always filter by allowed companies
        allowed_companies = self._get_allowed_company_ids()
        company_filter = str(tuple(allowed_companies)).replace(',)', ')')
        where = f" AND sl.company_id in {company_filter}"
        if self.biro_jasa_ids:
            where += " AND sl.biro_jasa_id in {}".format(str(tuple(self.biro_jasa_ids.ids)).replace(',)', ')'))
        if self.finco_ids:
            where += " AND sl.finco_id in {}".format(str(tuple(self.finco_ids.ids)).replace(',)', ')'))
        if self.customer_ids:
            where += " AND sl.partner_id in {}".format(str(tuple(self.customer_ids.ids)).replace(',)', ')'))
        if self.vehicle_registration_location_ids:
            where += " AND sl.vehicle_registration_location_id in {}".format(str(tuple(self.vehicle_registration_location_ids.ids)).replace(',)', ')'))
        if self.lot_ids:
            where += " AND sl.id in {}".format(str(tuple(self.lot_ids.ids)).replace(',)', ')'))

        query = f"""
            SELECT 
                branch.code,
                branch.name as branch_name,
                partner.name as customer_stnk,
                partner.street as customer_stnk_address,
                tvdr.name as no_penerimaan,
                lokasi_stnk.name as lokasi_stnk,
                sl.vehicle_registration_receipt_date as tgl_terima_stnk,
                sl.stnk_date as tgl_stnk,
                sl.name as engine,
                sl.notice_number as notice,
                sl.plate_number as nopol,
                sl.vehicle_registration_number as no_stnk,
                partner.code as code_customer,
                tdso.name as no_so,
                partner.mobile as mobile,
                partner2.name as pemohon_name,
                age(sl.vehicle_registration_receipt_date)::text as umur,
                sls.name as salesman,
                lsng.name as finco
            FROM stock_lot as sl             
            LEFT JOIN res_partner as partner ON partner.id = sl.customer_stnk_id
            LEFT JOIN tw_vehicle_registration_receipt tvdr ON tvdr.id = sl.vehicle_registration_receipt_id 
            LEFT JOIN tw_vehicle_registration_handover tvrh ON tvrh.id = sl.registration_handover_id 
            LEFT JOIN tw_vehicle_document_location as lokasi_stnk ON lokasi_stnk.id = sl.vehicle_registration_location_id
            LEFT JOIN tw_dealer_sale_order tdso ON tdso.id = sl.dealer_sale_order_id 
            LEFT JOIN res_company as branch ON branch.id=lokasi_stnk.company_id
            LEFT JOIN res_partner as partner2 ON partner2.id = sl.partner_id 
            LEFT JOIN hr_employee sls ON sls.id = tdso.sales_id 
            LEFT JOIN res_partner lsng ON lsng.id = tdso.finco_id
            where (tvdr.id IS NOT NULL)
            AND (tvrh.id IS NULL OR tvrh.state = 'draft')
            {where}
        """
        return query
    
    def get_query_stock_ownership(self):
        # Always filter by allowed companies
        allowed_companies = self._get_allowed_company_ids()
        company_filter = str(tuple(allowed_companies)).replace(',)', ')')
        where = f" AND lot.company_id in {company_filter}"
        if self.biro_jasa_ids:
            where += " AND lot.biro_jasa_id in {}".format(str(tuple(self.biro_jasa_ids.ids)).replace(',)', ')'))
        if self.finco_ids:
            where += " AND lot.finco_id in {}".format(str(tuple(self.finco_ids.ids)).replace(',)', ')'))
        if self.customer_ids:
            where += " AND lot.partner_id in {}".format(str(tuple(self.customer_ids.ids)).replace(',)', ')'))
        if self.vehicle_ownership_location_ids:
            where += " AND lot.vehicle_ownership_location_id in {}".format(str(tuple(self.vehicle_ownership_location_ids.ids)).replace(',)', ')'))
        if self.lot_ids:
            where += " AND lot.id in {}".format(str(tuple(self.lot_ids.ids)).replace(',)', ')'))

        query = f"""
            SELECT 
                branch.code,
                branch.name as branch_name,
                partner.name as customer_stnk,
                tvor.name as no_penerimaan,
                lokasi_bpkb.name as lokasi_bpkb,
                lot.vehicle_ownership_receipt_date as tgl_terima_bpkb,
                lot.vehicle_ownership_date as tgl_bpkb,
                lot.name as engine,
                lot.vehicle_ownership_number as no_bpkb,
                invoice.name as invoice_bbn, 
                partner.mobile as mobile,
                finco.name as finco_name,
                sls.name as sales,
                partner2.name as pemohon_name,
                age(vehicle_ownership_receipt_date)::text as umur,
                EXTRACT(day from now() - lot.vehicle_ownership_receipt_date) as over_due,
                partner.street as customer_stnk_address
            from stock_lot as lot
            LEFT JOIN res_partner finco ON finco.id =lot.finco_id 
            LEFT JOIN account_move invoice ON invoice.id = lot.accure_bbn_move_id
            LEFT JOIN tw_dealer_sale_order tdso ON tdso.id = lot.dealer_sale_order_id                               
            LEFT JOIN hr_employee sls ON sls.id = tdso.sales_id 
            LEFT JOIN res_partner as partner ON partner.id=lot.customer_stnk_id
            LEFT JOIN tw_vehicle_ownership_receipt tvor ON tvor.id = lot.vehicle_ownership_receipt_id 
            LEFT JOIN tw_vehicle_ownership_handover tvoh ON tvoh.id = lot.ownership_handover_id 
            LEFT JOIN tw_vehicle_document_location as lokasi_bpkb ON lokasi_bpkb.id=lot.vehicle_ownership_location_id
            LEFT JOIN res_company as branch ON branch.id=lokasi_bpkb.company_id
            LEFT JOIN res_partner as partner2 ON partner2.id=lot.partner_id
            where (tvor.id IS NOT NULL)
            AND (tvoh.id IS NULL OR tvoh.state = 'draft')
            {where}
            """
        return query

    def action_export_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        query = ''
        if self.options == 'tracking_document':
            query = self.get_query_tracking_document()
        elif self.options == 'lead_time':
            query = self.get_query_lead_time()
        elif self.options == 'stock_registration':
            query = self.get_query_stock_document_registration()
        elif self.options == 'stock_ownership':
            query = self.get_query_stock_ownership()
        
        if query:
            self._cr.execute(query)
            result = self._cr.dictfetchall()
            
            # Get the display name from selection field
            option_label = dict(self._fields['options'].selection).get(self.options, self.options)
            title = f'Report {option_label}'
            return self.env['web.report'].sudo().generate_report(title, result)
