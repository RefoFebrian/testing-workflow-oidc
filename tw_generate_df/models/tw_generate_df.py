# -*- coding: utf-8 -*-
import base64
import csv

from datetime import datetime
from io import StringIO
from odoo import models, fields, api
from odoo.exceptions import UserError as Warning


class tw_generate_df(models.TransientModel):
    _name = "tw.generate.df"
    _description = "Generate DF"

    date = fields.Date(string="Tanggal", required=True)
    name = fields.Char('Nama File' ,readonly=True)
    bank_type = fields.Selection([('permata', 'Permata'), ('bri', 'BRI')], string="Bank Type",default='permata', required=True)
    file = fields.Binary(string="File")

    def action_generate(self):
        fp = StringIO()
        if self.bank_type == 'permata':
            # report_data = self._generate_df_permata(fp)
            # report_name = "DF Permata"
            csv_bytes = self._generate_df_permata(fp)
            csv_bytes = csv_bytes.encode('utf-8')
            file_data_bytes_b64 = base64.b64encode(csv_bytes)
            file_data_str_b64 = file_data_bytes_b64.decode('utf-8')
            return self.export_to_csv(file_data_str_b64)
        else:
            report_data = self._generate_df_bri()
            report_name = "Report_DF_BRI"

            #kirim kan ke web report
            return self.env['web.report'].sudo().generate_report(
            report_name,
            report_data,
            header_title=False, 
            auto_filter=False, 
            bottom_remark=False, 
            show_total_footer=False, 
            data_summary_header=False, 
            data_summary_header_col_size=False, 
            freeze_panes_column=3, 
            remove_all_styling=True
        )

    def _generate_df_permata(self, fp):
        param = self.env['ir.config_parameter'].sudo()
        beneficiary_account = param.get_param('tw_generate_df.permata_account_beneficiary_account')
        partner_id = param.get_param('tw_generate_df.permata_account_partner_id')
        md_code = self.env['res.company'].sudo().get_default_main_dealer_code()

        if not beneficiary_account:
            beneficiary_account = '00701209087'
        if not partner_id:
            partner_id = "'A0163','A0164'"

        query = """
        SELECT TO_CHAR(inv.date, 'MM/DD/YYYY') AS tgl_invoice
            , TO_CHAR(inv.date, 'MMDDYY') ||
                CASE WHEN LENGTH(inv.name) = 18 THEN SUBSTRING(inv.name, 14) ELSE SUBSTRING(inv.name, 17) END ||
                CASE WHEN ROW_NUMBER() OVER (PARTITION BY inv.id ORDER BY ail.id asc) < 10 THEN '0' ||
                CAST(ROW_NUMBER() OVER (PARTITION BY inv.id ORDER BY ail.id asc) AS varchar)
                ELSE CAST(ROW_NUMBER() OVER (PARTITION BY inv.id ORDER BY ail.id asc) AS varchar) 
            END AS no_invoice
            , CAST(ail.price_unit AS integer) AS invoice_amount
            , TO_CHAR(inv.invoice_date_due, 'DD/MM/YY') AS invoice_maturity_date
            , partner.rl_permata_number AS rl_source_account
            , '' AS vl_source_account
            , '' AS giro_source_account
            , {beneficiary_account} AS benefeciary_account_number
            , 'IDR' AS currency
            , CAST(ail.price_unit AS integer) AS rl_disbursement_amount
            , '' AS vl_disbursement_amount
            , '' AS giro_disbursement_amount
            , 'DISB' AS message
            , '' AS additional_message
            , pick.lot_name AS engine_number
            , pick.chassis_number AS chassis_number
            , TO_CHAR(inv.invoice_date_due, 'DD/MM/YY') AS disbursement_date
            , CASE WHEN partner.code in ({partner_id}) THEN 'TDMFINANCING2' ELSE 'TDMFINANCING' END AS community_code
            , partner.code AS member_code
            , 'PB' AS transfer_type
        FROM tw_sale_order so
        INNER JOIN (
            SELECT so.id AS so_id,
                inv.id AS inv_id,
                SUM(invl.quantity) AS quantity
            FROM tw_sale_order so
            INNER JOIN account_move inv 
                ON so.name = inv.ref
                AND inv.move_type = 'out_invoice'
                AND inv.state = 'posted'
                AND inv.payment_state = 'not_paid'
            INNER JOIN account_move_line invl 
                ON invl.move_id = inv.id
                and invl.display_type = 'product'
            INNER JOIN LATERAL (
                SELECT ml.move_id,
                    MAX(ml.full_reconcile_id) AS full_reconcile_id,
                    MAX(ml.matching_number) AS matching_number
                FROM account_move_line ml
                WHERE ml.move_id = inv.id
                GROUP BY ml.move_id
            ) aml ON inv.id = aml.move_id
            WHERE inv.division = 'Unit'
                AND inv.date <= '{date}'
                AND aml.matching_number IS NULL
                AND aml.full_reconcile_id IS NULL
            GROUP BY so.id, inv.id
        ) inv_qty ON so.id = inv_qty.so_id
        INNER JOIN (
            SELECT so.id,
                so.name,
                MAX(pick.date_done) AS date_done,
                SUM(sol.qty_delivered) AS quantity
            FROM tw_sale_order so
                INNER JOIN tw_sale_order_line sol ON sol.order_id = so.id
                INNER JOIN stock_picking pick ON so.name = pick.origin AND pick.state = 'done'
                INNER JOIN stock_move move ON move.picking_id = pick.id  and move.product_id = sol.product_id
                INNER JOIN (
                    SELECT move_id from stock_move_line move_line
                    WHERE move_line.lot_id IS NOT NULL 
                    GROUP BY move_id
                    ) AS ml ON ml.move_id = move.id
                JOIN stock_picking_type as spt on spt.id = pick.picking_type_id
            WHERE pick.division = 'Unit'
                AND pick.date_done <= to_timestamp('{date} 23:59:59', 'YYYY-MM-DD HH24:MI:SS') + interval '7 hours'
                AND spt.code ='outgoing'
            GROUP BY so.id, so.name
        ) sj_qty ON so.id = sj_qty.id 
            AND inv_qty.quantity >= sj_qty.quantity 
            AND sj_qty.date_done + interval '7 hours' BETWEEN '{date} 00:00:00' AND '{date} 23:59:59'
        INNER JOIN lateral(
            SELECT move.product_id as product_id,lot.name as lot_name,lot.chassis_number as chassis_number from stock_picking pick 
            INNER JOIN stock_move move ON move.picking_id = pick.id  
            INNER JOIN stock_move_line move_line ON move_line.move_id = move.id AND move_line.lot_id IS NOT NULL 
            INNER JOIN stock_lot lot ON lot.id = move_line.lot_id 
            JOIN stock_picking_type as spt on spt.id = pick.picking_type_id
            WHERE pick.state = 'done' AND spt.code ='outgoing' AND pick.origin = so.name 
        ) as pick on 1=1
        INNER JOIN product_product product ON product.id = pick.product_id 
        LEFT JOIN tw_sale_order_line sol ON sol.order_id = so.id AND sol.product_id = pick.product_id
        LEFT JOIN res_company b ON so.company_id = b.id
        LEFT JOIN res_partner partner ON so.partner_id = partner.id
        LEFT JOIN account_move inv ON inv.invoice_origin = so.name AND inv.move_type = 'out_invoice' 
        LEFT JOIN account_move_line ail ON inv.id = ail.move_id AND ail.product_id = product.id AND ail.display_type = 'product'
        WHERE b.code = '{md_code}'
            AND so.division = 'Unit'
            AND so.state IN ('sale', 'done')
        ORDER BY so.date_order, so.id
        """.format(date=str(self.date),beneficiary_account=beneficiary_account,partner_id=partner_id,md_code=md_code)

        self.env.cr.execute(query, (self.date,))
        rows = self.env.cr.fetchall()
        if not rows:
            raise Warning('Data tidak ada...')
       
        writer = csv.writer(fp, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow([
            'SUBJECT',
            'INVOICE NO',
            'INVOICE AMOUNT',
            'INVOICE MATURITY DATE',
            'RL SOURCE ACCOUNT',
            'VL SOURCE ACCOUNT',
            'GIRO SOURCE ACCOUNT',
            'BENEFICIARY ACCOUNT NO',
            'CCY',
            'RL DISBURSEMENT AMOUNT',
            'VL DISBURSEMENT AMOUNT',
            'GIRO DISBURSEMENT AMOUNT',
            'MESSAGE',
            'ADDITIONAL MESSAGE',
            'ID1',
            'ID2',
            'DISBURSEMENT DATE',
            'COMMUNITY CODE',
            'MEMBER CODE',
            'TRANSFER TYPE',
        ])
            
        for res in rows:
            writer.writerow(res)
        
        return fp.getvalue()

    def _generate_df_bri(self):
        param = self.env['ir.config_parameter'].sudo()
        beneficiary_account = param.get_param('tw_generate_df.account_bri')

        if not beneficiary_account:
            beneficiary_account = ''

        query = """
            SELECT DISTINCT am."name" AS invoice_number,
                'DF' AS payment_method,
                rp.rl_bri_number AS client_id,
                '{beneficiary_account}' AS beneficiary_account,
                'IDR' AS currency,
                am.amount_total AS amount,
                TO_CHAR(am.invoice_date_due, 'DD/MM/YYYY') AS "Disbursement_Date (Due Date)",
                TO_CHAR((am.invoice_date_due + INTERVAL '30 days')::date, 'DD/MM/YYYY') AS settlement_date,
                '' AS sharing_limit_date,
                REGEXP_REPLACE(am.note , E'<[^>]+>', ' ', 'g' ) AS description,
                so.date_order
            FROM tw_sale_order so
                INNER JOIN (
                    SELECT am.id
                        , am.name
                        , aml.ref
                        , am.invoice_date_due
                        , am.amount_total
                        , am.partner_id
                        , am.state
                        , am.payment_state,
                        am.note
                    FROM account_move am 
                    INNER JOIN account_move_line aml ON aml.move_id = am.id
                    WHERE aml.full_reconcile_id IS NULL
                    GROUP BY am.id, aml.ref
                ) am ON am.ref = so.name
                LEFT JOIN (
                    SELECT p.name AS picking
                        , sp.name AS packing
                        , p.origin
                    FROM stock_picking p
                    LEFT JOIN stock_move sp ON sp.picking_id = p.id 
                    WHERE p.state = 'done'
                    AND sp.state = 'done'
                    AND sp.date::date = '{date}'
                ) sj ON sj.origin = so.name
                LEFT JOIN res_partner rp ON rp.id = am.partner_id
            WHERE am.payment_state = 'not_paid'
                and am.state = 'posted'
                AND so.division = 'Sparepart'
                AND sj.packing IS NOT NULL
                AND so.state IN ('sale','done')
            ORDER BY am.name ASC
        """.format(date=str(self.date),beneficiary_account=beneficiary_account)

        self.env.cr.execute(query, (self.date,))
        rows = self.env.cr.dictfetchall()

        result = []
        for r in rows:
            result.append({
                "payment_method": r["payment_method"],
                "invoice_number": r["invoice_number"],
                "invoice_number": r["invoice_number"],
                "client_id": r["client_id"],
                "beneficiary_account": beneficiary_account,
                "currency": r["currency"],
                "amount": r["amount"],
                "disbursement_date": r["disbursement_date"],
                "settlement_date": r["settlement_date"],
                "sharing_limit_date": r["sharing_limit_date"],
                "description": r["description"],
            })

        return result

    def export_to_csv(self,datas):
        date_generate = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        filename = 'Report_DF_Permata_%s.csv' % (date_generate.replace(" ","_").replace(":","-"))
        self.write({'file': datas, 'name': filename})
     
        download_url = '/web/content/%s/%s/file?download=true' % (self._name, self.id)
    
        return {
            'type': 'ir.actions.act_url',
            'url': download_url,
            'target': 'new',
        }
    

        

