# -*- coding: utf-8 -*-

from odoo import models, fields


class TWActivityPlanLineDGIInherit(models.Model):
    """Extend tw.activity.atl.btl.line with DGI integration field.

    Field ini ditempatkan di module tw_dgi_lead sesuai prinsip modular
    field placement — field yang dikonsumsi oleh DGI harus berada di
    module yang menggunakannya, bukan di base module tw_activity_atl_btl.

    Field activity_md_id digunakan sebagai kunci lookup saat mapping
    idEvent dari response DGI prospect ke field activity_plan_id di tw.lead.
    """

    _inherit = "tw.activity.atl.btl.line"

    # -------------------------------------------------------------------------
    # FIELDS
    # -------------------------------------------------------------------------
    activity_md_id = fields.Char(
        string="MD Event ID",
        help="ID Event dari DGI (idEvent) yang digunakan sebagai kunci lookup "
             "saat sinkronisasi leads — menghubungkan lead ke BTL line ini.",
    )
