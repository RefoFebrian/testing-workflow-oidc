# -*- coding: utf-8 -*-

from odoo import fields, models

class ResCompany(models.Model):
    _inherit = "res.company"

    # Tax ex/included in prices
    account_price_include = fields.Selection(
        selection=[('tax_included', 'Tax Included'), ('tax_excluded', 'Tax Excluded')],
        string='Default Sales Price Include',
        default='tax_included',
        required=True,
        help="Default on whether the sales price used on the product and invoices with this Company includes its taxes."
    )

    def _get_user_fiscal_lock_date(self, journal, ignore_exceptions=False):
        """Get the fiscal lock date for this company (depending on the affected journal) accounting for potential user exceptions
        :param bool ignore_exceptions: Whether we ignore exceptions or not
        :return the lock date
        """
        company = self.with_context(ignore_exceptions=ignore_exceptions)
        if not company:
            company = self.env.company[0].with_context(ignore_exceptions=ignore_exceptions)
        lock = max(company.user_fiscalyear_lock_date, company.user_hard_lock_date)
        if journal.type == 'sale':
            lock = max(company.user_sale_lock_date, lock)
        elif journal.type == 'purchase':
            lock = max(company.user_purchase_lock_date, lock)
        return lock