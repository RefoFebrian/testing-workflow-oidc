# -*- coding: utf-8 -*-
import re
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class tw_e_faktur_pajak_coretax(models.TransientModel):
    """E-Faktur Pajak Core Tax Report Wizard.
    
    This wizard generates E-Faktur Pajak report for Core Tax system
    using the web_report utility for Excel generation.
    """

    _name = "tw.e.faktur.coretax.pajak.wizard"
    _description = "E-Faktur Pajak Core Tax"

    # 8: Fields
    state = fields.Selection(
        selection=[
            ('all', 'ALL'),
            ('open', 'Open'),
            ('closed', 'Closed')
        ],
        string="Status",
        default='open'
    )
    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    no_faktur = fields.Char('No. Faktur')
    ref = fields.Char('No Transaksi')
    partner_ids = fields.Many2many(
        'res.partner',
        'tw_report_efaktur_coretax_partner_rel',
        'tw_e_faktur_pajak_wizard_id',
        string="Partners"
    )

    # 10: Constraints
    @api.constrains('start_date', 'end_date')
    def _check_date_range(self):
        """Validate that start_date is not greater than end_date."""
        for rec in self:
            if rec.start_date and rec.end_date and rec.start_date > rec.end_date:
                raise UserError(_("Start Date tidak boleh lebih besar dari End Date."))

    # 14: Private Methods
    def _clean_npwp_data(self, value):
        """Clean and format NPWP data to 22-digit format."""
        if not value:
            return '0000000000000000000000'
        no_npwp = re.sub(r'\D', '', value)
        no_npwp += '000000'
        no_npwp = '0' + no_npwp
        return no_npwp[-22:]

    def _build_query_where_clause(self):
        """Build WHERE clause for the SQL query based on filter parameters."""
        query_where = 'WHERE 1=1 '
        
        if self.state == 'open':
            query_where += "AND twpo.name is null AND twpo.state = 'open'"
        elif self.state == 'closed':
            query_where += "AND twpo.state = 'close'"
        elif self.state == 'all':
            query_where += "AND twpo.state in ('open','close')"

        if self.start_date and self.end_date:
            query_where += " AND twpo.date BETWEEN '%s' AND '%s'" % (
                str(self.start_date), str(self.end_date)
            )

        if self.partner_ids:
            query_where += " AND twpo.partner_id in %s" % str(
                tuple(self.partner_ids.ids)).replace(',)', ')')

        if self.no_faktur:
            query_where += " AND regexp_replace(twpo.name, '[^0-9]+', '', 'g') = '%s'" % str(self.no_faktur)

        if self.ref:
            query_where += " AND twpo.ref = '%s'" % str(self.ref)

        return query_where

    def _get_header_data(self, query_where):
        """Fetch header data for Faktur sheet."""
        query = """
        SELECT 
            DISTINCT twpo.id AS header_id,
            ROW_NUMBER() OVER (ORDER BY twpo.create_date ASC) AS baris,
            twpo.transaction_id AS id_trx,
            im.model AS model,
            TO_CHAR(twpo.date, 'MM/DD/YYYY') AS tgl_faktur,
            'normal' AS jenis_faktur,
            twpo.ref AS referensi,
            COALESCE(
                CASE 
                    WHEN rp.is_company = True THEN rp.no_npwp
                    ELSE NULL 
                END, 
                '-') AS npwp_nik_pembeli,
            CASE WHEN rp.no_npwp IS NOT NULL AND rp.is_company = True THEN 'TIN' ELSE 'National ID' END AS jenis_id_pembeli,
            CASE 
                WHEN rp.is_company = True THEN COALESCE(rp.identification_number, '-') 
                WHEN rp.no_npwp IS NOT NULL THEN '-' 
                ELSE COALESCE(rp.identification_number, '-') 
            END AS nomor_dokumen_pembeli,
            rp.name AS nama_pembeli,
            CONCAT(rp.street, ' RT/RW ', rp.rt, '/', rp.rw, ' Kel. ', rsd.name, ' Kec. ', rd.name, ' Kab. ', rc.name) AS alamat_pembeli,
            '' AS email_pembeli,
            RPAD(COALESCE(COALESCE(rp.no_npwp, rp.identification_number), '000000000000000'), 22, '0') AS id_tku_pembeli,
            CASE 
                WHEN (
                    SELECT COALESCE(SUM(tfpol.untaxed_amount), 0)
                    FROM tw_faktur_pajak_out_line tfpol
                    WHERE tfpol.faktur_pajak_out_id = twpo.id
                ) = twpo.untaxed_amount 
                THEN '010' 
            ELSE '040' 
        END AS kode_transaksi
        FROM tw_faktur_pajak_out twpo
        LEFT JOIN res_partner rp ON rp.id = twpo.partner_id
        LEFT JOIN res_city rc ON rc.id = rp.city_id
        LEFT JOIN res_district rd ON rd.id = rp.district_id
        LEFT JOIN res_sub_district rsd ON rsd.id = rp.sub_district_id
        LEFT JOIN ir_model im ON im.id = twpo.model_id
        LEFT JOIN tw_faktur_pajak_out_line line ON line.faktur_pajak_out_id = twpo.id 
        {query_where}
        GROUP BY header_id, rp.no_npwp, rp.identification_number, rp.name, rp.street, 
                 rp.rt, rp.rw, rsd.name, rd.name, rc.name, rp.email, im.model, rp.is_company
        ORDER BY baris
        """.format(query_where=query_where)

        self._cr.execute(query)
        return self._cr.dictfetchall()

    def _get_detail_data(self, query_where):
        """Fetch detail data for DetailFaktur sheet."""
        query = """
        WITH header_baris AS (
            SELECT 
            DISTINCT twpo.id AS header_id,
            ROW_NUMBER() OVER (ORDER BY twpo.create_date ASC) AS baris
            FROM tw_faktur_pajak_out twpo
            LEFT JOIN tw_faktur_pajak_out_line line ON line.faktur_pajak_out_id = twpo.id 
            {query_where}
        )
        SELECT 
            hb.baris AS "Baris",
            tfpol.kode_barang AS "Barang / Jasa",
            CASE WHEN tfpol.uom = 'UM.0018' THEN '871100' WHEN tfpol.uom = 'UM.0021' THEN '870800' ELSE '200104' END AS "Kode Barang Jasa",
            COALESCE(pp.default_code, tfpol.product_name) AS "Nama Barang/Jasa",
            tfpol.uom AS "Nama Satuan Ukur",
            tfpol.amount AS "Harga Satuan",
            tfpol.qty AS "Jumlah Barang Jasa",
            tfpol.total_discount AS "Total Diskon",
            tfpol.untaxed_amount AS "DPP",
            tfpol.untaxed_amount AS "DPP Nilai Lain",
            '1' AS "Tarif PPN",
            tfpol.ppn AS "PPN",
            0 AS "Tarif PPnBM",
            0 AS "PPnBM"
        FROM tw_faktur_pajak_out_line tfpol
        JOIN header_baris hb ON tfpol.faktur_pajak_out_id = hb.header_id
        LEFT JOIN tw_faktur_pajak_out_line_account_tax_rel tax_rel ON tax_rel.tw_faktur_pajak_out_line_id = tfpol.id
        LEFT JOIN account_tax at2 ON at2.id = tax_rel.account_tax_id
        LEFT JOIN product_product pp ON pp.id = tfpol.product_id
        GROUP BY hb.baris, tfpol.faktur_pajak_out_id, tfpol.amount, at2.amount, pp.default_code, tfpol.product_name,
                 tfpol.uom, tfpol.qty, tfpol.total_discount, tfpol.untaxed_amount, tfpol.ppn, tfpol.kode_barang, at2.tax_base_amount
        ORDER BY hb.baris
        """.format(query_where=query_where)

        self._cr.execute(query)
        return self._cr.dictfetchall()

    def _prepare_header_for_report(self, raw_header_data):
        """Prepare header data with id_tku_penjual lookup."""
        header_data = []
        for row in raw_header_data:
            # Lookup id_tku_penjual from source model
            id_tku_penjual = ''
            try:
                source_record = self.env[row['model']].suspend_security().search(
                    [('id', '=', row['id_trx'])], limit=1
                )
                if source_record and source_record.company_id:
                    id_tku_penjual = self._clean_npwp_data(source_record.company_id.no_npwp)
            except Exception as e:
                _logger.warning("Failed to lookup id_tku_penjual: %s", e)
                id_tku_penjual = self._clean_npwp_data(None)

            header_data.append({
                'Baris': row['baris'],
                'Tanggal Faktur': row['tgl_faktur'],
                'Jenis Faktur': row['jenis_faktur'],
                'Kode Transaksi': row['kode_transaksi'],
                'Keterangan Tambahan': '',
                'Dokumen Pendukung': '',
                'Referensi': row['referensi'] or '',
                'Cap Fasilitas': '',
                'ID TKU Penjual': id_tku_penjual,
                'NPWP/NIK Pembeli': row['npwp_nik_pembeli'],
                'Jenis ID Pembeli': row['jenis_id_pembeli'],
                'Negara Pembeli': 'IDN',
                'Nomor Dokumen Pembeli': row['nomor_dokumen_pembeli'],
                'Nama Pembeli': row['nama_pembeli'],
                'Alamat Pembeli': row['alamat_pembeli'],
                'Email Pembeli': row['email_pembeli'],
                'ID TKU Pembeli': row['id_tku_pembeli'],
            })
        return header_data

    # 13: Action Methods
    def action_print_report(self):
        """Generate E-Faktur Pajak Core Tax Excel report."""
        self.ensure_one()

        # Date range validation
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        # Build query conditions
        query_where = self._build_query_where_clause()

        # Fetch data
        raw_header_data = self._get_header_data(query_where)
        detail_data = self._get_detail_data(query_where)

        if not raw_header_data or not detail_data:
            raise UserError(_("Data tidak tersedia."))

        # Prepare header data with id_tku_penjual lookup
        header_data = self._prepare_header_for_report(raw_header_data)

        # Generate multi-sheet report
        data_sheet = {
            'Faktur': header_data,
            'DetailFaktur': detail_data
        }

        return self.env['web.report'].generate_report(
            report_name='eFaktur Pajak Coretax',
            data=header_data,
            data_sheet=data_sheet,
            start_date=self.start_date,
            end_date=self.end_date,
            capitalize=False,
            numbering=False,
            show_total_footer=False
        )
