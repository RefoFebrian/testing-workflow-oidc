# -*- coding: utf-8 -*-

# 1: imports of python lib
from collections import defaultdict

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.tools import float_compare, float_is_zero

# 5: local imports

# 6: Import of unknown third party lib

class AccountMoveInherit(models.Model):
    _inherit = "account.move"

    # TODO: Skema KPB + No KPB
    def _invoice_paid_hook(self):
        res = super(AccountMoveInherit, self)._invoice_paid_hook()
        
        # Cari semua Work Order yang terkait dengan invoice yang baru saja lunas
        todo_orders = self.env['tw.work.order']
        for invoice in self.filtered(lambda move: move.is_invoice()):
            for line in invoice.invoice_line_ids:
                if line.work_order_line_ids:
                    todo_orders |= line.work_order_line_ids.mapped('order_id')

        for order in todo_orders:
            # Cari semua invoice terkait (Reguler maupun Claim) yang tidak di-cancel
            # Kita cari melalui relasi pada order lines
            related_invoices = order.order_line.mapped('invoice_lines.move_id').filtered(
                lambda m: m.is_invoice() and m.state != 'cancel'
            )

            # Cek apakah SEMUA invoice yang ada sudah berstatus 'paid' atau 'in_payment'
            # Jika ada yang belum lunas (not_paid / partial), jangan selesaikan WO dulu
            if related_invoices and all(inv.payment_state in ('paid', 'in_payment') for inv in related_invoices):
                order.message_post(body=_("Semua Invoice (Reguler & Claim) telah lunas. Work Order diselesaikan secara otomatis."))
                order.action_done()
            elif related_invoices:
                unpaid_invoices = related_invoices.filtered(lambda m: m.payment_state not in ('paid', 'in_payment'))
                order.message_post(body=_(
                    "Invoice %s lunas. Menunggu pelunasan invoice lainnya: %s sebelum Work Order dapat diselesaikan.",
                    self.name,
                    ", ".join(unpaid_invoices.mapped('name'))
                ))
        return res