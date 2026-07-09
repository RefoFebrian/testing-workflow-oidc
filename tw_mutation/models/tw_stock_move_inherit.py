# models/stock_move_override.py
from odoo import models, api, _
from odoo.exceptions import UserError as Warning

class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_price_unit(self):
        # FIX : Saat mutasi dari branch A ke B, Valuation yang digunakan branch B seharusnya adalah valuation dari branch A
        self.ensure_one()
        picking = self.sudo().picking_id
        if picking and picking.mutation_order_id and picking.picking_type_id.code == 'incoming':
            if self.product_id.lot_valuated:
                domain = [
                    ('stock_move_id.picking_id.mutation_order_id', '=', picking.mutation_order_id.id),
                    ('stock_move_id.picking_id.picking_type_id.code', '=', 'outgoing'),
                ]
                res = {}
                for lot in self.lot_ids:
                    svl = self.env['stock.valuation.layer'].sudo().search(domain + [('lot_id', '=', lot.id)], limit=1)
                    if svl:
                        res[lot] = abs(svl.unit_cost)
                if res:
                    super_res = super()._get_price_unit()
                    for lot in self.lot_ids:
                        if lot not in res:
                            res[lot] = super_res.get(lot) or self.price_unit
                    return res

        return super()._get_price_unit()

    def _get_accounting_data_for_valuation(self):
        """Override account valuation untuk mutation order.

        Mengganti acc_src dan acc_dest dengan mutation_account_id
        dari product category saat picking terkait mutation order (MO).
        """
        res = super(StockMove, self)._get_accounting_data_for_valuation()
        journal_id, acc_src, acc_dest, acc_valuation = res

        # Gunakan sudo untuk bypass multi-company record rules
        picking = self.sudo().picking_id
        if not picking or not picking.mutation_order_id:
            return journal_id, acc_src, acc_dest, acc_valuation

        categ_acc = self.product_id.categ_id.mutation_account_id
        if not categ_acc:
            raise Warning(_(
                "Kategori produk '%s' untuk product '%s' belum diatur 'Account Mutation'. "
                "Mohon isi field 'Account Mutation' pada product category tersebut karena ini diperlukan untuk MO."
            ) % (self.product_id.categ_id.name, self.product_id.display_name))

        # Gunakan mutation account untuk kedua sisi:
        # - acc_src: dipakai sebagai credit account pada IN move (WH/IN)
        # - acc_dest: dipakai sebagai debit account pada OUT move (WH/OUT)
        acc_src = categ_acc.id
        acc_dest = categ_acc.id

        return journal_id, acc_src, acc_dest, acc_valuation

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id, svl_id, description):
        """Override untuk menambahkan intercompany journal lines pada MO.

        Forward flow (WH/IN, transit → internal):
        1. Debit: Stock Valuation (receiver company)
        2. Credit: Mutation Account (sender company)
        3. Debit: Intercompany Account Sender (sender company)
        4. Credit: Intercompany Account Receiver (receiver company)

        Return flow (Return WH/IN, internal → transit):
        1. Debit: Mutation Account (sender company)
        2. Credit: Stock Valuation (receiver company)
        3. Debit: Intercompany Account Receiver (receiver company)
        4. Credit: Intercompany Account Sender (sender company)

        Hanya berlaku untuk MO, transaksi lain tidak terpengaruh.
        """
        res = super()._prepare_account_move_line(
            qty, cost, credit_account_id, debit_account_id, svl_id, description
        )

        picking = self.sudo().picking_id
        if not picking or not picking.mutation_order_id:
            return res

        # Detect direction: forward (transit→internal) or return (internal→transit)
        is_forward = self.location_id.usage == 'transit'
        is_return = (
            self.location_dest_id.usage == 'transit'
            and self.origin_returned_move_id
        )

        if not is_forward and not is_return:
            return res

        mutation_order = picking.mutation_order_id
        sender_company = mutation_order.company_id
        receiver_company = picking.company_id

        # Tidak perlu intercompany jika sender = receiver
        if sender_company == receiver_company:
            return res

        # Update credit/debit line: set company_id ke sender company
        # Agar _create_intercompany_move bisa mendeteksi beda company
        if is_forward:
            # Forward: credit line = sender company
            for item in res:
                credit_val = item[2].get('credit', 0)
                balance_val = item[2].get('balance', 0)
                if credit_val > 0 or balance_val < 0:
                    item[2]['company_id'] = sender_company.id
                    break
        else:
            # Return: debit line = sender company (reverse of forward)
            for item in res:
                debit_val = item[2].get('debit', 0)
                balance_val = item[2].get('balance', 0)
                if debit_val > 0 or balance_val > 0:
                    item[2]['company_id'] = sender_company.id
                    break

        # Intercompany lines (line 3 & 4) ditangani oleh _create_intercompany_move di _post
        return res

    # -------------------------------------------------------------------------
    # PRIVATE
    # -------------------------------------------------------------------------
    def _check_quantity(self):
        """Override to merge duplicate quants before serial number validation.

        Mutation orders process many serial numbers in one transaction,
        which can trigger Odoo's SKIP LOCKED concurrency protection in
        _update_available_quantity(), creating temporary duplicate quants.

        We merge these duplicates before running the standard check
        to prevent false-positive 'serial number already assigned' errors.
        """
        mutation_moves = self.filtered(
            lambda m: m.picking_id and m.picking_id.sudo().mutation_order_id
        )
        if mutation_moves:
            # Targeted merge: search affected quants, then call _merge_quants
            # on the recordset so it filters by location_id + product_id
            quants_to_merge = self.env["stock.quant"].sudo().search([
                ("product_id", "in", mutation_moves.product_id.ids),
                ("location_id", "child_of", mutation_moves.location_dest_id.ids),
                ("lot_id", "in", mutation_moves.lot_ids.ids),
            ])
            if quants_to_merge:
                quants_to_merge._merge_quants()
        return super()._check_quantity()

    def _should_skip_serial_auto_assign(self):
        """Check if serial auto-assignment should be skipped for this move.

        Returns True for moves belonging to mutation order / sale order pickings.
        Can be extended to add more conditions.
        """
        is_skip = super()._should_skip_serial_auto_assign()
        if self.picking_id and self.picking_id.mutation_order_id and self._is_first_move_from_route():
            is_skip = True
        return is_skip
    
    def _get_new_picking_values(self):
        res = super()._get_new_picking_values()
        for record in self:
            picking_ids = record.move_orig_ids.picking_id.ids
            if not picking_ids:
                continue

            picking_obj = self.env['stock.picking'].suspend_security().search([
                ('id', 'in', picking_ids),
                ('mutation_order_id', '!=', False),
            ], limit=1)
            if picking_obj:
                res.update({
                    'mutation_order_id': picking_obj.mutation_order_id.id,
                })

        return res


