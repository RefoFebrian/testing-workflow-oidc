from odoo import models, fields, api, tools

class TWDealerSPKReport(models.Model):
    _name = "tw.dealer.spk.report"
    _description = "Dealer SPK Report"
    _auto = False
    _order = "date desc"

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Branch',
        readonly=True
    )

    division = fields.Selection(
        selection=[('Sparepart', 'Sparepart')],
        string='Division',
        required=True
    )

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        readonly=True
    )

    finco_id = fields.Many2one(
        comodel_name='res.partner',
        string='Finco',
        readonly=True
    )

    sales_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Sales Person',
        readonly=True
    )

    date = fields.Date(
        string='Order Date',
        readonly=True
    )

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        readonly=True
    )

    name = fields.Char(
        string='SPK',
        readonly=True
    )

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('progress', 'SPK'),
            ('so', 'Sales Order'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        readonly=True
    )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    min(l.id) as id,
                    l.date_order::date as date,
                    l.company_id, 
                    l.division,
                    l.partner_id,
                    l.finco_id,
                    l.sales_id,
                    s.product_id,
                    l.name,
                    l.state                    
                FROM tw_dealer_spk_line s
                    JOIN tw_dealer_spk l ON (s.spk_id=l.id)  
                GROUP BY
                    l.company_id,
                    l.date_order::date,
                    l.division,
                    l.partner_id,
                    l.finco_id,
                    l.sales_id,
                    s.product_id,
                    l.name,
                    l.state
            )
        """)