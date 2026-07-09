import base64
import csv
import xlsxwriter

from io import StringIO
from datetime import datetime, timedelta

from odoo import models, fields, tools

from odoo import api, fields, models

from odoo.exceptions import UserError as Warning
class TwWorkOrderReportWorkshopWizard(models.TransientModel):
    _name = "tw.report.workshop.wizard"
    _description = "Work Order Report Workshop"

    # 7: defaults methods
    def _get_default_date(self): 
        return datetime.now()

    name = fields.Char(string="Filename", readonly=True)

    options = fields.Selection(
        [
            ('detail', 'Detail'),
            ('unit_entry', 'Unit Entry'),
            ('unit_entry_by_reason', 'Unit Entry By Reason')
        ],
        string="Options",
        required=True,
        default='detail'
    )

    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options_list(['Sparepart','Service']),string="Workshop Category")

    product_ids = fields.Many2many(
        'product.product',
        'tw_work_order_report_workshop_product_rel',
        'tw_work_order_report_workshop_wizard_id',
        'product_id',
        string='Products'
    )
    available_categ_ids = fields.Many2many('product.category', string='Domain Products', compute='_compute_available_categ_ids')

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    state = fields.Selection(
        [
            ('all', 'All'),
            ('all_active', 'All Active'),
            ('sale', 'Outstanding'),
            ('done', 'Paid'),
            ('open_done', 'Outstanding & Paid'),
            ('open_done_cancel', 'Outstanding, Paid & Cancelled'),
            ('cancel', 'Cancel'),
            ('unused', 'Unused')
        ],
        help=
            "[All] → State Draft, WFA, Approved, Confirmed, Finished, Open, Done, Cancel, Unused\n"
            "[All Active] → All States without Draft, Cancel, and Unused\n"
            "[Outstanding] → State Open\n"
            "[Paid] → State Done\n"
            "[Outstanding & Paid] → State Open and Done\n"
            "[Outstanding, Paid & Cancelled] → State Open, Done, and Cancel\n"
            "[Cancel] → State Cancel\n"
            "[Unused] → State Unused\n",
        string="Work Order State",
        required=True,
        default='open_done_cancel'
    )

    company_ids = fields.Many2many(
        'res.company',
        'tw_work_order_report_workshop_branch_rel',
        'tw_work_order_report_workshop_wizard_id',
        'branch_id',
        string='Branches',
        copy=False
    )

    partner_ids = fields.Many2many(
        'res.partner',
        'tw_work_order_report_workshop_partner_rel',
        'tw_work_order_report_workshop_wizard_id',
        'partner_id',
        string='Customers',
        copy=False,
        domain=[('customer_rank', '>', 0)]
    )

    @api.onchange('division')
    def _onchange_division(self):
        self.product_ids = False

    @api.depends('division')
    def _compute_available_categ_ids(self):
        for record in self:
            categ_obj = self.env['product.category']
            if record.division:
                categ_ids = categ_obj.get_child_ids(record.division)
                record.available_categ_ids = categ_ids
            else:
                categ_ids = categ_obj.get_child_ids('Sparepart') + categ_obj.get_child_ids('Service')
                record.available_categ_ids = categ_ids

    def excel_report(self):
        start_date,end_date = self._get_date_range()
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        if self.options == 'detail' : 
            ress = self._print_excel_report()
            return self.env['web.report'].sudo().generate_report('Report Workshop',ress, data_summary_header=False, start_date=start_date, end_date=end_date,freeze_panes_column=3)
        elif self.options == 'unit_entry':
            ress = self._print_excel_report_unit_entry()
            return self.env['web.report'].sudo().generate_report('Report Work Order Unit Entry',ress, data_summary_header=False, start_date=start_date, end_date=end_date,freeze_panes_column=3)
        else:
            ress = self._print_excel_report_unit_entry_by_reason()
            return self.env['web.report'].sudo().generate_report('Report Work Order Unit Entry By Reason',ress, data_summary_header=False, start_date=start_date, end_date=end_date,freeze_panes_column=3)

    def _print_excel_report(self):
        division = self.division
        product_ids = self.product_ids.ids
        start_date = self.start_date
        end_date = self.end_date
        state = self.state
        company_ids = self.company_ids.ids
        partner_ids = self.partner_ids.ids

        query_where_wo = " WHERE 1=1"
        query_where_cancel = " WHERE tc.state = 'confirmed' "
        query_where_union = " WHERE 1=1"
        if product_ids:
            query_where_wo += " AND wol.product_id IN %s" % str(tuple(product_ids)).replace(',)', ')')
        if division:
            query_where_wo += " AND wol.division = '%s'" % str(division)
        if start_date:
            query_where_wo += " AND wo.open_date  >= '%s'" % str(start_date)
            query_where_cancel += " AND tc.date >= '%s'" % str(start_date)
        if end_date:
            query_where_wo += " AND wo.open_date  <= '%s'" % str(end_date)
            query_where_cancel += " AND tc.date <= '%s'" % str(end_date)
        if state in ['sale','done','cancel','unused']:
            query_where_wo += " AND wo.state = '%s'" % str(state)
        if state == 'open_done':
            query_where_wo += " AND wo.state IN ('sale','done')"
        if state == 'open_done_cancel':
            query_where_wo += " AND wo.state IN ('sale','done','cancel')"
        if state == 'all_active':
            query_where_wo += " AND wo.state not in  ('draft','cancel','unused')"

        if company_ids:
            query_where_wo += " AND wo.company_id IN %s" % str(tuple(company_ids)).replace(',)', ')')
            query_where_cancel += " AND tc.company_id IN %s" % str(tuple(company_ids)).replace(',)', ')')

        if partner_ids :
            query_where_wo += " AND wo.partner_id IN %s" % str(tuple(partner_ids)).replace(',)', ')')
            query_where_cancel += " AND wo.partner_id IN %s" % str(tuple(partner_ids)).replace(',)', ')')
        
        query_wo = f"""
            SELECT DISTINCT ON (wol.id) b.code AS branch_code
                , b.name AS branch_name 
                , wo.name AS workshop_number
                ,CASE
                    WHEN wo.state = 'sale' THEN 'open'
                    ELSE wo.state
                END AS state
                , wo.open_date  AS date_confirm  
                , wo_type.name AS type  
                , inv.code AS invoice_partner 
                , users.login AS login  
                , mechanic.name AS mechanic 
                , lot.plate_number AS no_polisi  
                , customer.code AS customer_code  
                , customer.name AS customer_name
                , wo.mobile AS customer_mobile  
                , unit_template.name->>'en_US' AS unit_name 
                , lot.name as engine_number  
                , lot.chassis_number as chassis_number 
                , wol.division as divisi  
                , prod_category.name as kategori 
                , prod_template.name->>'en_US' as product_name  
                , product.default_code as product_code 
                , CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE COALESCE(wol.product_uom_qty,0) END as quantity  
                , ROUND(COALESCE(wol.price_unit,0),2) as het 
                , ROUND(COALESCE(NULLIF(wol.discount,0),0),2) as discount  
                , ROUND(COALESCE(wol.price_unit,0) * (COALESCE(NULLIF(wol.discount,0),0) / 100) / (1 + COALESCE(tax.amount,0)) * CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE COALESCE(wol.product_uom_qty,0) END,2) as discount_amount  
                , ROUND(COALESCE(wol.price_unit,0) * (1 - COALESCE(NULLIF(wol.discount,0),0) / 100) / (1 + COALESCE(tax.amount,0)) * CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE COALESCE(wol.product_uom_qty,0) END,2) as dpp  
                , ROUND(COALESCE(wol.price_unit,0) * (1 - COALESCE(NULLIF(wol.discount,0),0) / 100) / (1 + COALESCE(tax.amount,0)) * COALESCE(tax.amount,0) * CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE COALESCE(wol.product_uom_qty,0) END,2) as ppn  
                , ROUND(COALESCE(ail.debit,0),2) as hpp 
                , ROUND(COALESCE ( (wol.price_unit * (1 - COALESCE(NULLIF(wol.discount,0),0) / 100) / (1 + COALESCE(tax.amount,0)) * CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE wol.product_uom_qty END) - (ail.debit / COALESCE(NULLIF(ail.quantity,0),1) * wol.qty_delivered),0),2) as gp_total  
                , ROUND(wol.product_uom_qty * ROUND(COALESCE(wol.price_unit,0),2) - ROUND(COALESCE(NULLIF(wol.discount,0),0),2),2) as total
                , ROUND(COALESCE(wol.price_unit,0) * (1 - COALESCE(NULLIF(wol.discount,0),0) / 100) / (1 + COALESCE(tax.amount,0)) * CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE COALESCE(wol.product_uom_qty,0) END,2) + ROUND(COALESCE(wol.price_unit,0) * (1 - COALESCE(NULLIF(wol.discount,0),0) / 100) / (1 + COALESCE(tax.amount,0)) * COALESCE(tax.amount,0) * CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE COALESCE(wol.product_uom_qty,0) END,2) as "Total (dengan diskon)"
                , CASE
                    WHEN pembawa.identification_number IS NOT NULL
                    OR pembawa.no_npwp IS NOT NULL
                    THEN 'ada'
                    ELSE 'tidak'
                END AS status_id_pajak
                , CASE
                    WHEN (
                        pembawa.identification_number IS NULL
                        AND pembawa.no_npwp IS NULL
                    )
                    AND wo_type.name NOT IN ('KPB', 'CLA')
                    THEN 0.01 * ROUND(COALESCE(wol.price_unit,0) * (1 - COALESCE(NULLIF(wol.discount,0),0) / 100) / (1 + COALESCE(tax.amount,0)) * CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE COALESCE(wol.product_uom_qty,0) END,2)
                    ELSE 0
                END AS nilai_penyisihan
                , COALESCE(fp.name,'') as faktur_pajak  
                , customer.street as alamat_konsumen
                , '' as nomor_batal
                , '' as alasan_batal  
                , NULL as tanggal_batal  
                , NULL as tanggal_confirm_batal
                , kec.name as kecamatan
                , coalesce (mr.name,'') as ring 
                , pembawa.name as pembawa
                , pembawa.identification_number AS no_ktp
                , pembawa.no_npwp AS npwp
                , alasan.name as alasan_ke_ahass
                , wo.is_own_dealer as dealer_sendiri
                , wo.production_year as tahun_perakitan
                , wo.create_date as create_date
                , wo.km
                , wo.sa_number as no_service_advisor
                , wo.is_washing_the_motorbike as cuci
                , wo.amount_accrue_tax as amount_accrue_tax
                , accrue.name as accrue_tax
                , COALESCE(voc_count.total_voucher, 0) AS total_voucher
            FROM tw_work_order wo  
            INNER JOIN account_move ai ON wo.name = ai.invoice_origin
            LEFT JOIN tw_work_order_line wol ON wo.id = wol.order_id 
            left join tw_selection alasan on alasan.id = wo.reason_to_ahass_id
            LEFT JOIN tw_selection wo_type on wo_type.id = wo.type_id
            LEFT JOIN account_move accrue on accrue.id = wo.accrue_tax_id
            LEFT JOIN account_tax_tw_work_order_line_rel as wot on wot.tw_work_order_line_id = wol.id
            LEFT JOIN account_tax as tax on tax.id = wot.account_tax_id
            LEFT JOIN account_move_line ail on ail.move_id = ai.id and ail.product_id = wol.product_id and ail.display_type = 'cogs' and ail.debit > 0
            LEFT JOIN res_partner inv ON ai.partner_id = inv.id   
            LEFT JOIN res_company b ON wo.company_id = b.id 
            LEFT JOIN hr_employee mechanic ON wo.mechanic_id = mechanic.id  
            left join res_users users on mechanic.user_id = users.id
            LEFT JOIN res_partner customer ON wo.customer_stnk_id = customer.id  
            LEFT JOIN tw_faktur_pajak_out fp ON wo.faktur_pajak_out_id = fp.id   
            LEFT JOIN stock_lot lot ON wo.lot_id = lot.id  
            LEFT JOIN product_product unit ON wo.product_id = unit.id   
            left join product_template unit_template on unit.product_tmpl_id = unit_template.id
            LEFT JOIN product_product product ON wol.product_id = product.id  
            LEFT JOIN product_template prod_template ON product.product_tmpl_id = prod_template.id  
            LEFT JOIN product_category prod_category ON prod_template.categ_id = prod_category.id   
            LEFT JOIN res_district kec on customer.district_id=kec.id  
            LEFT JOIN res_partner pembawa on wo.partner_id = pembawa.id
            LEFT JOIN tw_ring_kecamatan rk on rk.company_id = b.id
            LEFT JOIN tw_ring_kecamatan_line rkl on rkl.ring_kecamatan_id = rk.id and rkl.district_id = kec.id
            LEFT JOIN tw_ring mr on mr.id = rkl.ring_id
            LEFT JOIN (
                SELECT
                    work_order_id,
                    COUNT(*) AS total_voucher
                FROM tw_work_order_sales_voucher_rel
                GROUP BY work_order_id
            ) voc_count ON voc_count.work_order_id = wo.id
            {query_where_wo}
        """

        query_cancel = f"""
                        SELECT DISTINCT ON (wol.id) 
                            b.code AS kode_dealer
                            , b.name AS branch_name
                            , wo.name AS workshop_number
                            ,CASE
                                WHEN wo.state = 'sale' THEN 'open'
                                ELSE wo.state
                            END AS state
                            , wo.open_date AS tanggal
                            , wo_type.name AS type
                            , inv.code AS main_dealer
                            , users.login AS login
                            , mechanic.name AS mechanic
                            , lot.plate_number AS no_polisi
                            , customer.code AS customer_code
                            , customer.name AS customer_name
                            , wo.mobile AS customer_mobile
                            , unit_template.name->>'en_US' AS unit_name
                            , lot.name as engine_number
                            , lot.chassis_number as chassis_number
                            , wol.division as workshop_category
                            , prod_category.name as category_name
                            , prod_template.name->>'en_US' as product_name
                            , product.default_code as product_code
                            , -1 * CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE COALESCE(wol.product_uom_qty,0) END as quantity
                            , ROUND(-1 * COALESCE(wol.price_unit,0),2) as het
                            , ROUND(-1 * COALESCE(NULLIF(wol.discount,0),0),2) as discount
                            , ROUND(-1 * COALESCE(wol.price_unit,0) * (COALESCE(NULLIF(wol.discount,0),0) / 100) / (1 + COALESCE(tax.amount,0)) * CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE COALESCE(wol.product_uom_qty,0) END,2) as discount_amount
                            , ROUND(-1 * COALESCE(wol.price_unit,0) * (1 - COALESCE(NULLIF(wol.discount,0),0) / 100) / (1 + COALESCE(tax.amount,0)) * CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE COALESCE(wol.product_uom_qty,0) END,2) as dpp
                            , ROUND(-1 * COALESCE(wol.price_unit,0) * (1 - COALESCE(NULLIF(wol.discount,0),0) / 100) / (1 + COALESCE(tax.amount,0)) * COALESCE(tax.amount,0) * CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE COALESCE(wol.product_uom_qty,0) END,2) as ppn
                            , ROUND(-1 * COALESCE(ail.debit,0),2) as hpp
                            , ROUND(-1 * COALESCE ( (wol.price_unit * (1 - COALESCE(NULLIF(wol.discount,0),0) / 100) / (1 + COALESCE(tax.amount,0)) * CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE wol.product_uom_qty END) - (ail.debit / COALESCE(NULLIF(ail.quantity,0),1) * wol.qty_delivered),0),2) as gp_total
                            , ROUND(wol.product_uom_qty * ROUND(-1 * COALESCE(wol.price_unit,0),2)) - ROUND(-1 * COALESCE(wol.price_unit,0) * (COALESCE(NULLIF(wol.discount,0),0) / 100) / (1 + COALESCE(tax.amount,0)) * CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE COALESCE(wol.product_uom_qty,0) END,2) as total
                            , ROUND(-1 * COALESCE(wol.price_unit,0) * (1 - COALESCE(NULLIF(wol.discount,0),0) / 100) / (1 + COALESCE(tax.amount,0)) * CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE COALESCE(wol.product_uom_qty,0) END,2) + ROUND(-1 * COALESCE(wol.price_unit,0) * (1 - COALESCE(NULLIF(wol.discount,0),0) / 100) / (1 + COALESCE(tax.amount,0)) * COALESCE(tax.amount,0) * CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE COALESCE(wol.product_uom_qty,0) END,2) as "Total (dengan diskon)"
                            , CASE
                                WHEN pembawa.identification_number IS NOT NULL
                                OR pembawa.no_npwp IS NOT NULL
                                THEN 'ada'
                                ELSE 'tidak'
                            END AS status_id_pajak
                            , CASE
                                WHEN (
                                    pembawa.identification_number IS NULL
                                    AND pembawa.no_npwp IS NULL
                                )
                                AND wo_type.name NOT IN ('KPB', 'CLA')
                                THEN 0.01 * ROUND(-1 * COALESCE(wol.price_unit,0) * (1 - COALESCE(NULLIF(wol.discount,0),0) / 100) / (1 + COALESCE(tax.amount,0)) * CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE COALESCE(wol.product_uom_qty,0) END,2)
                                ELSE 0
                            END AS nilai_penyisihan
                            , COALESCE(fp.name,'') as faktur_pajak
                            , customer.street
                            , tc.name as nomor_batal
                            , regexp_replace(COALESCE(tc.reason, ''), '[\n\r]+', ' ', 'g') as alasan_batal
                            , tc.date as tanggal_batal
                            , tc.confirm_date as tanggal_confirm_batal
                            , kec.name as kecamatan
                            , coalesce (mr.name,'') as ring 
                            , pembawa.name as pembawa
                            , pembawa.identification_number AS no_ktp
                            , pembawa.no_npwp AS npwp
                            , alasan.name as alasan_ke_ahass
                            , wo.is_own_dealer as dealer_sendiri
                            , wo.production_year as tahun_perakitan
                            , wo.create_date as create_date
                            , wo.km
                            , wo.sa_number as no_service_advisor
                            , wo.is_washing_the_motorbike as cuci
                            , wo.amount_accrue_tax as amount_accrue_tax
                            , accrue.name as accrue_tax
                            , (COALESCE(voc_count.total_voucher, 0) * -1) AS total_voucher
                        FROM tw_work_order_cancel woc 
                        INNER JOIN tw_work_order wo ON woc.work_order_id = wo.id 
                        inner join tw_cancellation tc on woc.cancellation_id = tc.id
                        INNER JOIN account_move ai ON wo.name = ai.invoice_origin
                        left join tw_selection alasan on alasan.id = wo.reason_to_ahass_id
                        left join tw_selection wo_type on wo_type.id = wo.type_id
                        LEFT JOIN tw_work_order_line wol ON wo.id = wol.order_id
                        LEFT JOIN account_move accrue on accrue.id = wo.accrue_tax_id
                        LEFT JOIN account_tax_tw_work_order_line_rel as wot on wot.tw_work_order_line_id = wol.id
                        LEFT JOIN account_tax as tax on tax.id = wot.account_tax_id
                        LEFT JOIN account_move_line ail on ail.move_id = ai.id and ail.product_id = wol.product_id and ail.display_type = 'cogs' and ail.debit > 0
                        LEFT JOIN res_partner inv ON ai.partner_id = inv.id 
                        LEFT JOIN res_company b ON wo.company_id = b.id
                        LEFT JOIN hr_employee mechanic ON wo.mechanic_id = mechanic.id  
                        left join res_users users on mechanic.user_id = users.id
                        LEFT JOIN res_partner customer ON wo.customer_stnk_id = customer.id 
                        LEFT JOIN tw_faktur_pajak_out fp ON wo.faktur_pajak_out_id = fp.id 
                        LEFT JOIN stock_lot lot ON wo.lot_id = lot.id 
                        LEFT JOIN product_product unit ON wo.product_id = unit.id   
                        left join product_template unit_template on unit.product_tmpl_id = unit_template.id
                        LEFT JOIN product_product product ON wol.product_id = product.id 
                        LEFT JOIN product_template prod_template ON product.product_tmpl_id = prod_template.id 
                        LEFT JOIN product_category prod_category ON prod_template.categ_id = prod_category.id 
                        LEFT JOIN res_district kec on customer.district_id=kec.id  
                        LEFT JOIN res_partner pembawa on wo.partner_id = pembawa.id
                        LEFT JOIN tw_ring_kecamatan rk on rk.company_id = b.id
                        LEFT JOIN tw_ring_kecamatan_line rkl on rkl.ring_kecamatan_id = rk.id and rkl.district_id = kec.id
                        LEFT JOIN tw_ring mr on mr.id = rkl.ring_id
                        LEFT JOIN (
                            SELECT
                                work_order_id,
                                COUNT(*) AS total_voucher
                            FROM tw_work_order_sales_voucher_rel
                            GROUP BY work_order_id
                        ) voc_count ON voc_count.work_order_id = wo.id
                        {query_where_cancel}
                    """

        if state in ['all','all_active','open_done_cancel']:
            query = """
                        SELECT * 
                        FROM ((%s) UNION ALL (%s)) a %s
                        ORDER BY branch_code
                """ % (query_wo, query_cancel, query_where_union)
        elif state == 'cancel':
            query = query_cancel
        else:
            query = query_wo

        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        return ress

    def _print_excel_report_unit_entry(self): 
        start_date = self.start_date
        end_date = self.end_date
        company_ids = self.company_ids
        query_where = " WHERE 1=1"
        query_where_wo_date = ""
        query_where_woc_date = ""

        if start_date:
            query_where_wo_date += " AND wo.confirm_date BETWEEN '%s'" % str(start_date)
            query_where_woc_date += " AND tc.date BETWEEN '%s'" % str(start_date)

        if end_date:
            query_where_wo_date += " AND '%s'" % str(end_date)
            query_where_woc_date += " AND '%s'" % str(end_date)

        if company_ids :
            query_where += " AND b.id in %s" % str(tuple(company_ids)).replace(',)', ')')
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND b.id IN {str(tuple(branch)).replace(',)', ')')}"
        
        query = f"""
                    SELECT b.id as branch_id
                        , b.code as branch_code          
                        , b.name as branch_name         
                        , COALESCE(wo_unit.unit_entry,0) as unit_entry          
                        , COALESCE(wo_unit.ring_1,0) as ring_1          
                        , COALESCE(wo_unit.ring_2,0) as ring_2          
                        , COALESCE(wo_unit.ring_3,0) as ring_3          
                        , COALESCE(wo_unit.ring_4,0) as ring_4          
                        , COALESCE(wo_unit.others,0) as others          
                        , COALESCE(wo_inv.cnt_inv,0) as invoice        
                        , COALESCE(wo_jasa.amt_jasa,0) as jasa          
                        , COALESCE(wo_jasa.amt_part,0) AS part          
                        , COALESCE(wo_jasa.amt_oil,0) as oli          
                        , COALESCE(wo_jasa.amt_total,0) as total          
                        , COALESCE(wo_inv.cnt_kpb_1,0) as kpb1         
                        , COALESCE(wo_inv.cnt_kpb_2,0) as kpb2         
                        , COALESCE(wo_inv.cnt_kpb_3,0) as kpb3         
                        , COALESCE(wo_inv.cnt_kpb_4,0) as kpb4         
                        , COALESCE(wo_inv.cnt_cla,0) as claim         
                        , COALESCE(wo_jasa.qty_kpb,0) as kpb          
                        , COALESCE(wo_jasa.qty_cs,0) as cs          
                        , COALESCE(wo_jasa.qty_ls,0) as ls          
                        , COALESCE(wo_jasa.qty_or,0) as "or+"                
                        , COALESCE(wo_jasa.qty_lr,0) as lr          
                        , COALESCE(wo_jasa.qty_hr,0) as "hr+"          
                        , COALESCE(wo_jasa.qty_cla,0) as cla          
                        , COALESCE(wo_jasa.qty_total,0) as total          
                    FROM res_company b         
                    FULL OUTER JOIN         
                        (         
                        SELECT 
                            branch_id
                            , SUM(cnt_per_date) as unit_entry 
                            , SUM(ring_1) as ring_1
                            , SUM(ring_2) as ring_2
                            , SUM(ring_3) as ring_3
                            , SUM(ring_4) as ring_4
                            , SUM(others) as others
                            FROM        
                            (
                                (        
                                    SELECT wo.company_id as branch_id     
                                        , wo.open_date     
                                        , COUNT(DISTINCT wo.lot_id) AS cnt_per_date   
                                        , COUNT(DISTINCT wo.lot_id) FILTER(WHERE TRIM(mr.name) = '1') as ring_1  
                                        , COUNT(DISTINCT wo.lot_id) FILTER(WHERE TRIM(mr.name) = '2') as ring_2  
                                        , COUNT(DISTINCT wo.lot_id) FILTER(WHERE TRIM(mr.name) = '3') as ring_3  
                                        , COUNT(DISTINCT wo.lot_id) FILTER(WHERE TRIM(mr.name) = '4') as ring_4  
                                        , COUNT(DISTINCT wo.lot_id) FILTER(WHERE coalesce(TRIM(mr.name), '0') in ('5', '6', '7', '8', '0')) as others 
                                    FROM tw_work_order wo      
                                    INNER JOIN account_move ai ON wo.name = ai.invoice_origin
                                    JOIN res_partner rp ON rp.id = wo.partner_id
                                    LEFT JOIN tw_ring_kecamatan as rk on rk.company_id = wo.company_id
                                    LEFT JOIN tw_ring_kecamatan_line as rkl on rkl.ring_kecamatan_id = rk.id and rkl.district_id = rp.district_id
                                    LEFT JOIN tw_ring as mr on mr.id = rkl.ring_id
                                    WHERE wo.state IN ('sale', 'done', 'cancel')      
                                    AND wo.type <> 'WAR' AND wo.type <> 'SLS'       
                                    {query_where_wo_date} 
                                    GROUP BY wo.company_id, wo.open_date      
                                ) 
                                UNION ALL 
                                (       
                                    SELECT wo.company_id   
                                        , tc.date   
                                        , -1 * COUNT(wo.lot_id) AS cnt_per_date  
                                        , -1 * COUNT(wo.lot_id) FILTER(WHERE TRIM(mr.name) = '1') as ring_1
                                        , -1 * COUNT(wo.lot_id) FILTER(WHERE TRIM(mr.name) = '2') as ring_2  
                                        , -1 * COUNT(wo.lot_id) FILTER(WHERE TRIM(mr.name) = '3') as ring_3  
                                        , -1 * COUNT(wo.lot_id) FILTER(WHERE TRIM(mr.name) = '4') as ring_4  
                                        , -1 * COUNT(wo.lot_id) FILTER(WHERE coalesce(TRIM(mr.name), '0') in ('5', '6', '7', '8', '0')) as others 
                                    FROM tw_work_order_cancel woc    
                                    INNER JOIN tw_work_order wo ON woc.work_order_id = wo.id   
                                    INNER JOIN account_move ai ON wo.name = ai.invoice_origin
                                    inner join tw_cancellation tc on tc.id = woc.cancellation_id
                                    JOIN res_partner rp ON rp.id = wo.partner_id
                                    LEFT JOIN tw_ring_kecamatan as rk on rk.company_id = wo.company_id
                                    LEFT JOIN tw_ring_kecamatan_line as rkl on rkl.ring_kecamatan_id = rk.id and rkl.district_id = rp.district_id
                                    LEFT JOIN tw_ring as mr on mr.id = rkl.ring_id
                                    WHERE tc.state = 'confirmed' 
                                    AND wo.type <> 'WAR' AND wo.type <> 'SLS'     
                                    {query_where_woc_date}
                                    GROUP BY wo.company_id, tc.date     
                                )
                            ) lot_count        
                        GROUP BY branch_id        
                        ORDER BY branch_id        
                        ) wo_unit         
                ON b.id = wo_unit.branch_id         
                FULL OUTER JOIN         
                    (         
                        SELECT branch_id      
                            , SUM(cnt_inv) as cnt_inv     
                            , SUM(cnt_kpb_1) as cnt_kpb_1     
                            , SUM(cnt_kpb_2) as cnt_kpb_2     
                            , SUM(cnt_kpb_3) as cnt_kpb_3     
                            , SUM(cnt_kpb_4) as cnt_kpb_4     
                            , SUM(cnt_cla) as cnt_cla     
                        FROM 
                        (      
                            (   
                                SELECT wo.company_id as branch_id   
                                    , COUNT(wo.id) AS cnt_inv 
                                    , COUNT(CASE WHEN wo.type = 'KPB' AND wo.kpb_ke = '1' THEN wo.id END) AS cnt_kpb_1  
                                    , COUNT(CASE WHEN wo.type = 'KPB' AND wo.kpb_ke = '2' THEN wo.id END) AS cnt_kpb_2  
                                    , COUNT(CASE WHEN wo.type = 'KPB' AND wo.kpb_ke = '3' THEN wo.id END) AS cnt_kpb_3  
                                    , COUNT(CASE WHEN wo.type = 'KPB' AND wo.kpb_ke = '4' THEN wo.id END) AS cnt_kpb_4  
                                    , COUNT(CASE WHEN wo.type = 'CLA' THEN wo.id END) AS cnt_cla  
                                FROM tw_work_order wo  
                                INNER JOIN account_move ai ON wo.name = ai.invoice_origin
                                WHERE wo.state IN ('sale', 'done', 'cancel')  
                                {query_where_wo_date} 
                                GROUP BY wo.company_id 
                            )   
                            UNION ALL   
                            (   
                                SELECT wo.company_id
                                    , -1 * COUNT(wo.id) AS cnt_inv
                                    , -1 * COUNT(CASE WHEN wo.type = 'KPB' AND wo.kpb_ke = '1' THEN wo.id END) AS cnt_kpb_1
                                    , -1 * COUNT(CASE WHEN wo.type = 'KPB' AND wo.kpb_ke = '2' THEN wo.id END) AS cnt_kpb_2
                                    , -1 * COUNT(CASE WHEN wo.type = 'KPB' AND wo.kpb_ke = '3' THEN wo.id END) AS cnt_kpb_3
                                    , -1 * COUNT(CASE WHEN wo.type = 'KPB' AND wo.kpb_ke = '4' THEN wo.id END) AS cnt_kpb_4
                                    , -1 * COUNT(CASE WHEN wo.type = 'CLA' THEN wo.id END) AS cnt_cla
                                FROM tw_work_order_cancel woc 
                                INNER JOIN tw_work_order wo ON woc.work_order_id = wo.id 
                                INNER JOIN account_move ai ON wo.name = ai.invoice_origin
                                inner join tw_cancellation tc on tc.id = woc.cancellation_id
                                WHERE tc.state = 'confirmed'
                                {query_where_woc_date}
                                GROUP BY wo.company_id
                            )   
                        ) invoice_count       
                        GROUP BY branch_id      
                        ORDER BY branch_id      
                    ) wo_inv          
                ON b.id = wo_inv.branch_id          
                FULL OUTER JOIN         
                    (         
                        SELECT branch_id    
                            , SUM(amt_jasa) as amt_jasa   
                            , SUM(amt_part) as amt_part   
                            , SUM(amt_oil) AS amt_oil   
                            , SUM(amt_total) AS amt_total   
                            , SUM(qty_kpb) AS qty_kpb   
                            , SUM(qty_cs) AS qty_cs   
                            , SUM(qty_ls) AS qty_ls   
                            , SUM(qty_or) AS qty_or   
                            , SUM(qty_qs) AS qty_qs   
                            , SUM(qty_lr) AS qty_lr   
                            , SUM(qty_hr) AS qty_hr   
                            , SUM(qty_cla) AS qty_cla   
                            , SUM(qty_total) AS qty_total   
                        FROM (
                                (    
                                    SELECT wo.company_id as branch_id   
                                        , SUM(CASE WHEN wol.division = 'Service' THEN COALESCE(wol.price_unit,0) * (1 - COALESCE(NULLIF(wol.discount,0),0) / 100)  * COALESCE(wol.product_uom_qty,0) END) amt_jasa 
                                        , SUM(CASE WHEN wol.division = 'Sparepart' AND pc.name NOT IN ( 'OLI','OIL') THEN COALESCE(wol.price_unit,0) * (1 - COALESCE(NULLIF(wol.discount,0),0) / 100)  * wol.qty_delivered END) amt_part  
                                        , SUM(CASE WHEN wol.division = 'Sparepart' AND pc.name = 'OIL' THEN COALESCE(wol.price_unit,0) * (1 - COALESCE(NULLIF(wol.discount,0),0) / 100)  * wol.qty_delivered END) amt_oil 
                                        , SUM(COALESCE(wol.price_unit,0) * (1 - COALESCE(NULLIF(wol.discount,0),0) / 100) / (1 + COALESCE(tax.amount,0)) * CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE COALESCE(wol.product_uom_qty,0) END) amt_total  
                                        , SUM(CASE WHEN wol.division = 'Service' AND pc2.name = 'KPB' THEN COALESCE(wol.product_uom_qty,0) END) qty_kpb 
                                        , SUM(CASE WHEN wol.division = 'Service' AND pc.name = 'CS' THEN COALESCE(wol.product_uom_qty,0) END) qty_cs  
                                        , SUM(CASE WHEN wol.division = 'Service' AND pc.name = 'LS' THEN COALESCE(wol.product_uom_qty,0) END) qty_ls  
                                        , SUM(CASE WHEN wol.division = 'Service' AND pc.name = 'OR+' THEN COALESCE(wol.product_uom_qty,0) END) qty_or 
                                        , SUM(CASE WHEN wol.division = 'Service' AND pc2.name = 'QS' THEN COALESCE(wol.product_uom_qty,0) END) qty_qs 
                                        , SUM(CASE WHEN wol.division = 'Service' AND pc.name = 'LR' THEN COALESCE(wol.product_uom_qty,0) END) qty_lr  
                                        , SUM(CASE WHEN wol.division = 'Service' AND pc.name = 'HR' THEN COALESCE(wol.product_uom_qty,0) END) qty_hr  
                                        , SUM(CASE WHEN wol.division = 'Service' AND pc.name = 'CLA' THEN COALESCE(wol.product_uom_qty,0) END) qty_cla  
                                        , SUM(CASE WHEN wol.division = 'Service' THEN COALESCE(wol.product_uom_qty,0) END) qty_total  
                                    FROM tw_work_order wo  
                                    INNER JOIN account_move ai ON wo.name = ai.invoice_origin
                                    INNER JOIN tw_work_order_line wol ON wo.id = wol.order_id 
                                    LEFT JOIN account_tax_tw_work_order_line_rel as wot on wot.tw_work_order_line_id = wol.id
                                    LEFT JOIN account_tax as tax on tax.id = wot.account_tax_id
                                    LEFT JOIN product_product p ON wol.product_id = p.id  
                                    LEFT JOIN product_template pt ON p.product_tmpl_id = pt.id  
                                    LEFT JOIN product_category pc ON pt.categ_id = pc.id  
                                    LEFT JOIN product_category pc2 ON pc.parent_id = pc2.id   
                                    WHERE wo.state IN ('sale', 'done', 'cancel')  
                                    {query_where_wo_date} 
                                    GROUP BY wo.company_id   
                                    ORDER BY wo.company_id   
                                ) 
                                UNION ALL 
                                (   
                                    SELECT wo.company_id as branch_id 
                                        , -1 * SUM(CASE WHEN wol.division = 'Service' THEN COALESCE(wol.price_unit,0) * (1 - COALESCE(NULLIF(wol.discount,0),0) / 100) * COALESCE(wol.product_uom_qty,0) END) amt_jasa
                                        , -1 * SUM(CASE WHEN wol.division = 'Sparepart' AND pc.name NOT IN ( 'OLI','OIL') THEN COALESCE(wol.price_unit,0) * (1 - COALESCE(NULLIF(wol.discount,0),0) / 100)  * wol.qty_delivered END) amt_part
                                        , -1 * SUM(CASE WHEN wol.division = 'Sparepart' AND pc.name = 'OIL' THEN COALESCE(wol.price_unit,0) * (1 - COALESCE(NULLIF(wol.discount,0),0) / 100)  * wol.qty_delivered END) amt_oil
                                        , -1 * SUM(COALESCE(wol.price_unit,0) * (1 - COALESCE(NULLIF(wol.discount,0),0) / 100) / (1 + COALESCE(tax.amount,0)) * CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE COALESCE(wol.product_uom_qty,0) END) amt_total
                                        , -1 * SUM(CASE WHEN wol.division = 'Service' AND pc2.name = 'KPB' THEN COALESCE(wol.product_uom_qty,0) END) qty_kpb
                                        , -1 * SUM(CASE WHEN wol.division = 'Service' AND pc.name = 'CS' THEN COALESCE(wol.product_uom_qty,0) END) qty_cs
                                        , -1 * SUM(CASE WHEN wol.division = 'Service' AND pc.name = 'LS' THEN COALESCE(wol.product_uom_qty,0) END) qty_ls
                                        , -1 * SUM(CASE WHEN wol.division = 'Service' AND pc.name = 'OR+' THEN COALESCE(wol.product_uom_qty,0) END) qty_or
                                        , -1 * SUM(CASE WHEN wol.division = 'Service' AND pc2.name = 'QS' THEN COALESCE(wol.product_uom_qty,0) END) qty_qs
                                        , -1 * SUM(CASE WHEN wol.division = 'Service' AND pc.name = 'LR' THEN COALESCE(wol.product_uom_qty,0) END) qty_lr
                                        , -1 * SUM(CASE WHEN wol.division = 'Service' AND pc.name = 'HR' THEN COALESCE(wol.product_uom_qty,0) END) qty_hr
                                        , -1 * SUM(CASE WHEN wol.division = 'Service' AND pc.name = 'CLA' THEN COALESCE(wol.product_uom_qty,0) END) qty_cla
                                        , -1 * SUM(CASE WHEN wol.division = 'Service' THEN COALESCE(wol.product_uom_qty,0) END) qty_total
                                    FROM tw_work_order_cancel woc 
                                    INNER JOIN tw_work_order wo ON woc.work_order_id = wo.id 
                                    INNER JOIN account_move ai ON wo.name = ai.invoice_origin
                                    INNER JOIN tw_work_order_line wol ON wo.id = wol.order_id 
                                    inner join tw_cancellation tc on tc.id = woc.cancellation_id
                                    LEFT JOIN account_tax_tw_work_order_line_rel as wot on wot.tw_work_order_line_id = wol.id
                                    LEFT JOIN account_tax as tax on tax.id = wot.account_tax_id
                                    LEFT JOIN product_product p ON wol.product_id = p.id 
                                    LEFT JOIN product_template pt ON p.product_tmpl_id = pt.id 
                                    LEFT JOIN product_category pc ON pt.categ_id = pc.id 
                                    LEFT JOIN product_category pc2 ON pc.parent_id = pc2.id 
                                    WHERE tc.state = 'confirmed'
                                    {query_where_woc_date}
                                    GROUP BY wo.company_id 
                                    ORDER BY wo.company_id 
                                )
                            ) detil_count    
                        GROUP BY branch_id    
                        ORDER BY branch_id    
                    ) wo_jasa         
                ON b.id = wo_jasa.branch_id         
                {query_where}
                AND (wo_unit.branch_id > 0 OR wo_inv.branch_id > 0 OR wo_jasa.branch_id > 0)          
                ORDER BY branch_id    
            """
        self._cr.execute (query)
        ress = self._cr.dictfetchall()
        return ress
    
    def _print_excel_report_unit_entry_by_reason(self): 
        start_date = self.start_date
        end_date = self.end_date
        company_ids = self.company_ids
        query_where = " WHERE 1=1"
        query_where =" '%s' and '%s' "%(start_date,end_date)
        if not company_ids :
            query_branch_id = " is not null "
        else:
            query_branch_id = " in %s " % str(tuple(company_ids)).replace(',)', ')')

        query = f"""
                select
                    coalesce (wb.name,'') as name,
                    coalesce (alasan.name,'') as alasan_ke_ahass,
                    coalesce(sl.name,'') as location,
                    cnt_unit.cnt_unit as unit,
                    jasa.amt_jasa as jasa,
                    jasa.amt_oil as oli,
                    jasa.amt_part as part,
                    jasa.amt_total as total,
                    jasa.qty_cla as cla,
                    jasa.qty_cs as cs,
                    jasa.qty_hr as "hr+",
                    jasa.qty_kpb as kpb,
                    jasa.qty_lr as lr,
                    jasa.qty_ls as ls,
                    jasa.qty_or as "or+",
                    kpb.cnt_inv as invoice,
                    kpb.cnt_cla as claim,
                    kpb.cnt_kpb_1 as kpb1,
                    kpb.cnt_kpb_2 as kpb2,
                    kpb.cnt_kpb_3 as kpb3,
                    kpb.cnt_kpb_4 as kpb4
                from
                    tw_work_order reason
                left join tw_selection alasan on
                    alasan.id = reason.reason_to_ahass_id
                left join stock_location sl on sl.id = reason.location_id
                left join (
                    select
                        wo.reason_to_ahass_id,
                        SUM(case when wol.division = 'Service' then coalesce(wol.price_unit, 0) * (1 - coalesce(nullif(wol.discount, 0), 0) / 100) * coalesce(wol.product_uom_qty, 0) end) amt_jasa,
                        SUM(case when wol.division = 'Sparepart' and pc.name not in ( 'OLI', 'OIL') then coalesce(wol.price_unit, 0) * (1 - coalesce(nullif(wol.discount, 0), 0) / 100) * wol.qty_delivered end) amt_part,
                        SUM(case when wol.division = 'Sparepart' and pc.name = 'OIL' then coalesce(wol.price_unit, 0) * (1 - coalesce(nullif(wol.discount, 0), 0) / 100) * wol.qty_delivered end) amt_oil,
                        SUM(coalesce(wol.price_unit, 0) * (1 - coalesce(nullif(wol.discount, 0), 0) / 100) / (1 + coalesce(tax.amount, 0)) * case when wol.division = 'Sparepart' then wol.qty_delivered else coalesce(wol.product_uom_qty, 0) end) amt_total,
                        SUM(case when wol.division = 'Service' and pc2.name = 'KPB' then coalesce(wol.product_uom_qty, 0) end) qty_kpb,
                        SUM(case when wol.division = 'Service' and pc.name = 'CS' then coalesce(wol.product_uom_qty, 0) end) qty_cs,
                        SUM(case when wol.division = 'Service' and pc.name = 'LS' then coalesce(wol.product_uom_qty, 0) end) qty_ls,
                        SUM(case when wol.division = 'Service' and pc.name = 'OR+' then coalesce(wol.product_uom_qty, 0) end) qty_or,
                        SUM(case when wol.division = 'Service' and pc2.name = 'QS' then coalesce(wol.product_uom_qty, 0) end) qty_qs,
                        SUM(case when wol.division = 'Service' and pc.name = 'LR' then coalesce(wol.product_uom_qty, 0) end) qty_lr,
                        SUM(case when wol.division = 'Service' and pc.name = 'HR' then coalesce(wol.product_uom_qty, 0) end) qty_hr,
                        SUM(case when wol.division = 'Service' and pc.name = 'CLA' then coalesce(wol.product_uom_qty, 0) end) qty_cla,
                        SUM(case when wol.division = 'Service' then coalesce(wol.product_uom_qty, 0) end) qty_total
                    from
                        tw_work_order wo
                    inner join account_move ai on
                        wo.name = ai.invoice_origin
                    inner join tw_work_order_line wol on
                        wo.id = wol.order_id
                    left join account_tax_tw_work_order_line_rel as wot on
                        wot.tw_work_order_line_id = wol.id
                    left join account_tax as tax on
                        tax.id = wot.account_tax_id
                    left join product_product p on
                        wol.product_id = p.id
                    left join product_template pt on
                        p.product_tmpl_id = pt.id
                    left join product_category pc on
                        pt.categ_id = pc.id
                    left join product_category pc2 on
                        pc.parent_id = pc2.id
                    where
                        wo.state in ('sale', 'done')
                            and wo.open_date between {query_where}
                            and wo.company_id {query_branch_id}
                        group by
                            wo.reason_to_ahass_id
                )jasa on
                    reason.reason_to_ahass_id = jasa.reason_to_ahass_id
                left join (
                    select
                        kpb.reason_to_ahass_id,
                        sum(kpb.cnt_inv)cnt_inv,
                        sum(kpb.cnt_kpb_1)cnt_kpb_1,
                        sum(kpb.cnt_kpb_2)cnt_kpb_2,
                        sum(kpb.cnt_kpb_3)cnt_kpb_3,
                        sum(kpb.cnt_kpb_4)cnt_kpb_4,
                        sum(kpb.cnt_cla)cnt_cla
                    from
                        (
                        select
                            coalesce(wo.mechanic_id,
                            0)mekanik_id,
                            wo.reason_to_ahass_id,
                            COUNT(wo.id) as cnt_inv,
                            COUNT(case when wo.type = 'KPB' and wo.kpb_ke = '1' then wo.id end) as cnt_kpb_1,
                            COUNT(case when wo.type = 'KPB' and wo.kpb_ke = '2' then wo.id end) as cnt_kpb_2,
                            COUNT(case when wo.type = 'KPB' and wo.kpb_ke = '3' then wo.id end) as cnt_kpb_3,
                            COUNT(case when wo.type = 'KPB' and wo.kpb_ke = '4' then wo.id end) as cnt_kpb_4,
                            COUNT(case when wo.type = 'CLA' then wo.id end) as cnt_cla
                        from
                            tw_work_order wo
                        inner join account_move ai on
                            wo.name = ai.invoice_origin
                        where
                            wo.state in ('sale', 'done')
                                and wo.open_date between {query_where}
                                and wo.company_id {query_branch_id}
                            group by
                                wo.mechanic_id,
                                wo.reason_to_ahass_id)kpb
                    group by
                        kpb.reason_to_ahass_id
                )kpb on
                    reason.reason_to_ahass_id = kpb.reason_to_ahass_id
                left join (
                    select
                        unit.reason_to_ahass_id,
                        sum(unit.cnt_per_date)cnt_unit
                    from
                        (
                        select
                            wo.company_id,
                            wo.open_date,
                            coalesce(wo.mechanic_id,0)mekanik_id,
                            wo.reason_to_ahass_id,
                            COUNT(distinct wo.lot_id) as cnt_per_date
                        from
                            tw_work_order wo
                        inner join account_move ai on
                            wo.name = ai.invoice_origin
                        where
                            wo.state in ('sale', 'done')
                                and wo.type <> 'WAR'
                                and wo.type <> 'SLS'
                                and wo.open_date between {query_where}
                                and wo.company_id {query_branch_id}
                            group by
                                wo.company_id,
                                wo.open_date,
                                coalesce(wo.mechanic_id,
                                0),
                                wo.reason_to_ahass_id)unit
                    group by
                        unit.reason_to_ahass_id)cnt_unit on
                    reason.reason_to_ahass_id = cnt_unit.reason_to_ahass_id
                left join 
                res_company wb on
                    reason.company_id = wb.id
                where
                    reason.open_date between {query_where}
                    and reason.company_id {query_branch_id}
                group by
                    wb.name,
                    reason.reason_to_ahass_id,
                    jasa.amt_jasa,
                    jasa.amt_oil,
                    jasa.amt_part,
                    jasa.amt_total,
                    jasa.qty_cla,
                    jasa.qty_cs,
                    jasa.qty_hr,
                    jasa.qty_kpb,
                    jasa.qty_lr,
                    jasa.qty_ls,
                    jasa.qty_or,
                    jasa.qty_qs,
                    kpb.cnt_inv,
                    kpb.cnt_cla,
                    kpb.cnt_kpb_1,
                    kpb.cnt_kpb_2,
                    kpb.cnt_kpb_3,
                    kpb.cnt_kpb_4,
                    cnt_unit.cnt_unit,
                    reason.location_id,
                    alasan.name,
                    sl.name
            """ 
        self._cr.execute (query)
        ress = self._cr.dictfetchall()
        return ress

    
    def _get_date_range(self):
        if self.start_date:
            start_date = self.start_date.strftime('%Y-%m-%d')
        else:
            start_date = self._get_default_date().strftime('%Y-%m-%d')
        if self.end_date:
            end_date = self.end_date.strftime('%Y-%m-%d')
        else:
            end_date = self._get_default_date().strftime('%Y-%m-%d')
        return start_date,end_date
    
    
        
