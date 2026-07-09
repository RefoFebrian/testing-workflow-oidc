# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwWorkOrder(models.Model):
    _inherit = "tw.work.order"

    # 7: defaults methods

    # 8: fields
    claim_number = fields.Char(string='Nomor Claim')
    claim_type = fields.Char(string='Tipe Claim', related='claim_type_id.value')
    claim_summary_html = fields.Html(
        string='Claim Distribution',
        compute='_compute_claim_summary_html',
        store=False,
    )

    # 9: relation fields
    claim_type_id = fields.Many2one('tw.selection', string="Claim Type", domain=[('type', '=', 'WorkOrderClaimType')])

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('type_id')
    def onchange_type_id(self):
        self.claim_type_id = False
        self.claim_number = False
    
    @api.onchange('claim_type_id')
    def onchange_claim_type_id(self):
        """Reset order lines and validate claim master exists for THIS branch.
        Uses _search_claim (exact branch → parent company) to prevent cross-branch match.
        """
        self.order_line = False
        for record in self:
            if not record.claim_type_id or not record.company_id:
                continue
            # Must use _search_claim so company is properly scoped (DMP won't match DDA/DDS)
            base_domain = record._build_claim_base_domain(record.claim_type_id.id)
            wo_claim_obj = record._search_claim(base_domain, [])
            if not wo_claim_obj:
                type_name = record.claim_type_id.value
                if type_name == 'KPB' and hasattr(record, 'kpb_ke') and record.kpb_ke:
                    type_name += f" Ke-{record.kpb_ke}"
                    
                raise ValidationError(
                    _("Konfigurasi 'Work Order Claim' untuk tipe '%s' di Branch '%s' tidak ditemukan."
                      "\n\nSilahkan setting terlebih dahulu di Workshop -> Configuration -> Work Order Claim"
                      ) % (type_name, record.company_id.name)
                )

    @api.depends(
        'order_line', 'order_line.claim_partner_id',
        'order_line.price_subtotal', 'order_line.price_tax',
        'order_line.display_type', 'claim_type_id', 'type_id',
    )
    def _compute_claim_summary_html(self):
        """Compute a per-claimant breakdown table for CLA-type Work Orders.

        Groups order lines by claim_partner_id:
          - Lines with claim_partner_id → charged to that partner (AHM, Main Dealer, etc.)
          - Lines without claim_partner_id → charged to Customer (paid directly)

        Renders an HTML table (subtotal + tax + total per partner) shown above tax_totals.
        Only activates when type_id.value contains 'CLA' and claim_type_id is set.
        """
        for order in self:
            type_val = str(getattr(order.type_id, 'value', '') or '').upper()
            is_cla = 'CLA' in type_val and bool(order.claim_type_id)

            if not is_cla:
                order.claim_summary_html = False
                continue

            # --- Group lines by claim partner: track subtotal & tax ---
            # Structure: {partner_id: {'name': str, 'subtotal': float, 'tax': float}}
            CUSTOMER_KEY = '__customer__'
            groups = {CUSTOMER_KEY: {'name': 'Customer', 'subtotal': 0.0, 'tax': 0.0}}

            for line in order.order_line.filtered(lambda l: not l.display_type):
                key = line.claim_partner_id.id if line.claim_partner_id else CUSTOMER_KEY
                if key not in groups:
                    groups[key] = {
                        'name': line.claim_partner_id.name,
                        'subtotal': 0.0,
                        'tax': 0.0,
                    }
                groups[key]['subtotal'] += line.price_subtotal
                groups[key]['tax'] += line.price_tax

            # Remove customer bucket if empty
            if groups[CUSTOMER_KEY]['subtotal'] == 0.0 and groups[CUSTOMER_KEY]['tax'] == 0.0:
                del groups[CUSTOMER_KEY]

            if not groups:
                order.claim_summary_html = False
                continue

            # --- Build HTML ---
            fmt = lambda amt: '{:,.2f}'.format(amt)
            sym = order.currency_id.symbol or 'Rp'

            TD = 'padding: 4px 10px; font-size: 13px;'
            TD_NUM = 'padding: 4px 10px; text-align: right; font-size: 13px;'
            TD_NUM_BOLD = 'padding: 4px 10px; text-align: right; font-size: 13px; font-weight: 600;'
            TH = 'padding: 4px 10px; font-size: 11px; color: #6c757d; text-align: right; font-weight: 600; border-bottom: 1px solid #dee2e6;'
            TH_LABEL = 'padding: 4px 10px; font-size: 11px; color: #6c757d; font-weight: 600; border-bottom: 1px solid #dee2e6;'

            header_row = f'''
                <tr>
                    <th style="{TH_LABEL}">Pihak</th>
                    <th style="{TH}">Subtotal</th>
                    <th style="{TH}">Pajak</th>
                    <th style="{TH}">Total</th>
                </tr>'''

            rows = ''
            for key, g in groups.items():
                total = g['subtotal'] + g['tax']
                label = g['name']
                suffix = '<small style="color:#6c757d; margin-left:4px;"></small>' \
                    if key == CUSTOMER_KEY else \
                    '<small style="color:#6c757d; margin-left:4px;"></small>'
                rows += f'''
                    <tr>
                        <td style="{TD}"><strong>{label}</strong>{suffix}</td>
                        <td style="{TD_NUM}">{sym} {fmt(g["subtotal"])}</td>
                        <td style="{TD_NUM}">{sym} {fmt(g["tax"])}</td>
                        <td style="{TD_NUM_BOLD}">{sym} {fmt(total)}</td>
                    </tr>'''

            html = f'''
                <div style="border: 1px solid #dee2e6; border-radius: 6px; overflow: hidden; margin-bottom: 8px;">
                    <div style="background: #f8f9fa; padding: 5px 10px; border-bottom: 1px solid #dee2e6;
                                font-weight: 700; font-size: 11px; letter-spacing: 0.5px;
                                color: #495057; text-transform: uppercase;">
                        Rincian Pembayaran
                    </div>
                    <table style="width: 100%; border-collapse: collapse;">
                        {header_row}
                        {rows}
                    </table>
                </div>
            '''

            order.claim_summary_html = html



    def _prepare_customer_stnk_id(self):
        if not self._check_payment_term_id_fields():
            return
        if self.customer_stnk_id:
            if self.type_id.value == 'REG':
                self.payment_term_id = self.customer_stnk_id.property_payment_term_id.id
            elif self.type_id.value in self._prepare_type_onchange_customer_stnk_id():
                branch = self.company_id
                if branch and branch.default_supplier_id:
                    self.payment_term_id = branch.default_supplier_id.property_payment_term_id.id
                else:
                    self.payment_term_id = 1
        else:
            self.payment_term_id = False
    # 12: override methods
    def _get_invoiceable_lines(self, final=False):
        """
        Filter invoiceable lines per partner target dari context:
        - Jika claim_partner_id ada → ambil:
            a) lines dengan claim_partner_id == pid, ATAU
            b) lines tanpa claim_partner_id namun default invoice partner order == pid
        - Jika tidak ada pid → kembalikan semua lines invoiceable (jalur standar)
        """
        lines = super()._get_invoiceable_lines(final=final)
        pid = self.env.context.get('claim_partner_id')
        if not pid:
            return lines

        def default_partner_id(l):
            # partner invoice default order (fallback)
            partner = l.order_id.partner_invoice_id or l.order_id.partner_id
            return partner.id

        return lines.filtered(
            lambda l: (
                (l.claim_partner_id and l.claim_partner_id.id == pid) or
                (not l.claim_partner_id and default_partner_id(l) == pid)
            )
        )

    def _prepare_invoice(self):
        """Override for CLA type: set partner_id from context."""
        vals = super()._prepare_invoice()
        pid = self.env.context.get('claim_partner_id')
        if pid:
            vals['partner_id'] = pid
        return vals

    def _create_invoices(self, grouped=False, final=False, date=None):
        """
        Override untuk WO tipe CLA: buat invoice terpisah per partner (claim_partner_id).
        
        Business logic:
        - Products yang ADA di master claim → invoice dengan claim journal (ke AHM/principal)
        - Products yang TIDAK ADA di master claim → invoice dengan regular journal (ke customer)
        - Jika SEMUA products ada di master claim → hanya 1 invoice (claim journal)
        - Jika ada products di luar master claim → 2 invoice (1 regular + 1 claim)
        
        Journal di-fix SETELAH invoice terbuat untuk menghindari masalah context loss.
        """
        import logging
        _logger = logging.getLogger(__name__)

        AccountMove = self.env['account.move']
        all_moves = AccountMove

        for order in self:
            type_val = str(getattr(order.type_id, 'value', '') or '').lower()
            is_claim = bool(order.claim_type_id and ('claim' in type_val or 'cla' in type_val))

            if not is_claim:
                all_moves |= super(TwWorkOrder, order)._create_invoices(
                    grouped=grouped, final=final, date=date
                )
                continue

            # Ambil konfigurasi claim
            type_claim_obj = order._get_type_claim()
            claim_journal = type_claim_obj.journal_id if type_claim_obj else False

            # Ambil regular journal dari branch setting
            account_setting = order.company_id.branch_setting_id.account_setting_id
            regular_journal = account_setting.wo_reg_journal_id if account_setting else False

            _logger.info("=== CLA _create_invoices: claim_journal=%s, regular_journal=%s ===",
                          claim_journal.name if claim_journal else None,
                          regular_journal.name if regular_journal else None)

            # Ambil invoiceable lines
            base_lines = super(TwWorkOrder, order)._get_invoiceable_lines(final=final)
            base_lines = base_lines.filtered(lambda l: not l.display_type)
            if not base_lines:
                continue

            # Tentukan target partner per line
            def target_partner_id(l):
                partner = l.claim_partner_id or order.partner_invoice_id or order.partner_id
                return partner.id

            partner_ids = sorted(set(target_partner_id(l) for l in base_lines))

            _logger.info("=== partner_ids to invoice: %s ===", partner_ids)
            _logger.info("=== lines detail: %s ===",
                          [(l.product_id.name, l.claim_partner_id.name if l.claim_partner_id else 'NO_CLAIM') for l in base_lines])

            # Buat invoice per partner
            for pid in partner_ids:
                _logger.info("=== Creating invoice for pid=%s ===", pid)
                
                moves = super(TwWorkOrder, order.with_context(
                    claim_partner_id=pid,
                ))._create_invoices(
                    grouped=False,
                    final=final,
                    date=date,
                )

                if not moves:
                    continue

                # Determine: apakah ini customer invoice atau claim invoice?
                is_customer_invoice = self._is_pid_customer_invoice(order, pid, type_claim_obj)
                
                _logger.info("=== Invoice created: move=%s, is_customer=%s, current_journal=%s ===",
                              moves.mapped('name'), is_customer_invoice,
                              moves.mapped('journal_id.name'))

                # Fix journal SETELAH invoice terbuat
                for move in moves:
                    target_journal = None
                    if is_customer_invoice and regular_journal:
                        if move.journal_id.id != regular_journal.id:
                            target_journal = regular_journal
                    elif not is_customer_invoice and claim_journal:
                        if move.journal_id.id != claim_journal.id:
                            target_journal = claim_journal

                    if target_journal:
                        _logger.info("=== FIXING journal: %s → %s ===",
                                      move.journal_id.name, target_journal.name)
                        # Step 1: Reset name agar Odoo izinkan ganti journal
                        move.sudo().write({'name': '/'})
                        # Step 2: Ganti journal
                        move.sudo().write({'journal_id': target_journal.id})
                        # Step 3: Generate sequence baru sesuai journal baru
                        code = target_journal.code
                        prefix = order.company_id.code
                        new_name = self.env['ir.sequence'].get_sequence_code(code, prefix)
                        move.sudo().write({'name': new_name})

                all_moves |= moves

        return all_moves

    @api.model
    def _is_pid_customer_invoice(self, order, pid, type_claim_obj):
        """
        Determine apakah invoice untuk pid ini adalah customer invoice (regular journal)
        atau claim invoice (claim journal).
        
        Logic: Cek apakah SEMUA products di lines untuk pid ini ada di master claim
        dengan claim_to == 'customer'. Jika ya → customer invoice (regular journal).
        Jika tidak → claim invoice (claim journal).
        """
        default_partner = (order.partner_invoice_id or order.partner_id)
        lines_for_pid = order.order_line.filtered(
            lambda l: (
                (l.claim_partner_id and l.claim_partner_id.id == pid) or
                (not l.claim_partner_id and default_partner.id == pid)
            ) and not l.display_type
        )

        if not lines_for_pid:
            return True  # Default to customer/regular if no lines

        # Cek claim_to dari master claim
        product_ids = lines_for_pid.mapped('product_id.id')
        claim_lines = type_claim_obj.claim_line_ids.filtered(
            lambda cl: cl.product_id.id in product_ids
        )

        if not claim_lines:
            # Products tidak ada di master claim → customer invoice (regular journal)
            return True

        # Semua claim lines harus claim_to == 'customer' untuk dianggap customer invoice
        return all(cl.claim_to == 'customer' for cl in claim_lines)

    def _override_combined_tax(self, vals):
        if vals.get('type_id'):
            type_id = self.env['tw.selection'].browse(vals.get('type_id'))
            if type_id.value in self._prepare_type_wo(['CLA']):
                if 'combined_tax' in self._fields:
                    vals['combined_tax'] = False

    def _get_partner_id(self, type, partner_id, company_id):
        if type in self._prepare_type_wo(['CLA']):
            branch = self.env['res.company'].browse(company_id)
            if not branch.default_supplier_id:
                raise ValidationError(_('Principle di Branch Belum di Setting'))
            return branch.default_supplier_id.id
        return partner_id

    def _override_check_type_service(self, type_service, wo_obj, driver_obj):
        payment_term_id = False
        if type_service == 'REG':
            payment_term_id = driver_obj.property_payment_term_id.id
        elif type_service in self._prepare_type_wo(['CLA']):
            if wo_obj._name == 'tw.work.order':
                branch_obj = self.env['res.company'].browse(wo_obj.company_id.id)
                payment_term_id = branch_obj.default_supplier_id.property_payment_term_id.id
        return payment_term_id if payment_term_id else 1

    def _get_combined_tax(self, vals):
        workorder_type_obj = self.env['tw.selection'].browse(vals.get('type_id'))
        if workorder_type_obj:
            if workorder_type_obj.value in self._prepare_type_wo(['CLA']):
                if 'combined_tax' in self._fields:
                    vals['combined_tax'] = True
            elif workorder_type_obj.value in ('REG', 'WAR'):
                if 'combined_tax' in self._fields:
                    vals['combined_tax'] = False

    # Prepare
    def _prepare_vals_before_create(self, vals):
        prepare = super()._prepare_vals_before_create(vals)
        return prepare

    def _prepare_type_onchange_customer_stnk_id(self, wo_type=[]):
        change_type = super()._prepare_type_onchange_customer_stnk_id(wo_type)
        if 'CLA' not in wo_type:
            wo_type.append('CLA')
        return change_type or []

    def _prepare_type_wo(self, wo_type=[]):
        prepare = super()._prepare_type_wo(wo_type)
        wo_type.append('CLA')
        return prepare

    def _validate_order(self):
        validate_order = super()._validate_order()
        if self.type_id.value == 'CLA' and self.claim_type_id:
            type_claim_obj = self._get_type_claim()

            # Validasi: minimal satu product di order_line harus sesuai dengan master claim_line_ids
            if self.order_line and type_claim_obj.claim_line_ids:
                master_product_ids = type_claim_obj.claim_line_ids.mapped('product_id.id')
                order_product_ids = self.order_line.mapped('product_id.id')

                # Cek apakah ada irisan antara product di order_line dan master claim_line_ids
                matching_products = set(order_product_ids) & set(master_product_ids)

                if not matching_products:
                    raise ValidationError(
                        _(f"At least one product in Order Line must match the master Claim Type {self.claim_type_id.value}. "
                          f"Allowed products: {', '.join(type_claim_obj.claim_line_ids.mapped('product_id.name'))}")
                    )
        return validate_order

    def _prepare_payment_term(self):
        prepare_payment_term = super()._prepare_payment_term()
        if self.partner_id and self.claim_type_id:
            type_claim_obj = self._get_type_claim()
            prepare_payment_term = type_claim_obj.payment_term_id.id or prepare_payment_term
        return prepare_payment_term
    
    def _build_claim_base_domain(self, claim_type_id):
        """Build the base domain for claim master search.

        Handles only claim_type and KPB period filtering.
        Scope (branch/area) and company resolution are handled by _search_claim.
        """
        domain = [('claim_type_id', '=', claim_type_id)]

        # Match KPB period if claim type is KPB
        if self.claim_type_id.value == 'KPB' and hasattr(self, 'kpb_ke') and self.kpb_ke:
            domain += [('kpb_period', '=', self.kpb_ke)]

        return domain

    def _search_claim(self, base_domain, extra_domain):
        """Search claim master using a 4-level scope hierarchy from specific to global.

        Priority order (stops at first result):
          1. scope=branch, company = exact branch of the WO
          2. scope=branch, company = parent/holding company
          3. scope=area,   area    = area from branch_setting.default_area_id
          4. scope=area,   area    = False (global area fallback)

        Within each scope level, unit-level filtering is applied via extra_domain.
        """
        Claim = self.env['tw.work.order.claim'].suspend_security()
        area_id = (
            self.company_id.branch_setting_id.default_area_id.id
            if self.company_id.branch_setting_id else False
        )

        # --- Level 1: Branch exact ---
        result = Claim.search(
            base_domain + [
                ('scope_type', '=', 'branch'),
                ('company_id', '=', self.company_id.id),
            ] + extra_domain, limit=1
        )
        if result:
            return result

        # --- Level 2: Branch parent/holding ---
        parent_ids = (self.company_id.parent_ids - self.company_id).ids
        if parent_ids:
            result = Claim.search(
                base_domain + [
                    ('scope_type', '=', 'branch'),
                    ('company_id', 'in', parent_ids),
                ] + extra_domain, limit=1
            )
            if result:
                return result

        # --- Level 3: Area exact (dari branch_setting) ---
        if area_id:
            result = Claim.search(
                base_domain + [
                    ('scope_type', '=', 'area'),
                    ('area_id', '=', area_id),
                ] + extra_domain, limit=1
            )
            if result:
                return result

        # --- Level 4: Area global (area_id = False = berlaku semua area) ---
        result = Claim.search(
            base_domain + [
                ('scope_type', '=', 'area'),
                ('area_id', '=', False),
            ] + extra_domain, limit=1
        )
        return result

    def _get_type_claim(self):
        """Search for the best-matching claim configuration for this WO.

        Applies a two-dimensional hierarchy:
          - Scope axis (4 levels): branch exact → holding → area exact → area global
          - Unit axis  (4 levels): variant → template → category → all

        The search iterates unit-level filters first (outer priority), and within
        each unit filter calls _search_claim which applies the scope hierarchy.
        The first non-empty result wins.
        """
        base_domain = self._build_claim_base_domain(self.claim_type_id.id)

        # Unit data from WO lot
        unit_product = self.lot_id.product_id if self.lot_id else False
        unit_tmpl = unit_product.product_tmpl_id if unit_product else False
        unit_categ = unit_product.categ_id if unit_product else False

        # Build ordered list of unit-level filter candidates (most specific first)
        unit_filters = []
        if unit_product:
            unit_filters.append([
                ('unit_apply_on', '=', 'product'),
                ('unit_product_id', '=', unit_product.id),
            ])
        if unit_tmpl:
            unit_filters.append([
                ('unit_apply_on', '=', 'product'),
                ('unit_product_tmpl_id', '=', unit_tmpl.id),
                ('unit_product_id', '=', False),
            ])
        if unit_categ:
            unit_filters.append([
                ('unit_apply_on', '=', 'category'),
                ('unit_categ_id', '=', unit_categ.id),
            ])
        # Final fallback: match all units
        unit_filters.append([('unit_apply_on', '=', 'all')])

        for unit_extra in unit_filters:
            result = self._search_claim(base_domain, unit_extra)
            if result:
                return result

        raise ValidationError(
            _("Configuration Claim Type '%s' for Branch '%s' not found.") % (
                self.claim_type_id.value, self.company_id.name
            )
        )

    def _match_claim_line(self, claim_line, product):
        """Check if a sparepart product_id in claim line matches the given product."""
        return claim_line.product_id and claim_line.product_id.id == product.id

    def action_fill_products_from_claim(self):
        """Append products from master claim to order_line (only in draft, no duplicate)."""
        self.ensure_one()
        if self.state != 'draft':
            raise ValidationError(_("Isi produk dari master claim hanya dapat dilakukan di status Draft."))
        if not self.claim_type_id:
            raise ValidationError(_("Claim Type belum dipilih."))

        type_claim_obj = self._get_type_claim()
        if not type_claim_obj.claim_line_ids:
            raise ValidationError(_("Master claim tidak memiliki produk."))

        existing_product_ids = self.order_line.mapped('product_id.id')
        added = 0
        for cl in type_claim_obj.claim_line_ids:
            # Sparepart product langsung dari product_id di claim line
            product = cl.product_id
            if not product or product.id in existing_product_ids:
                continue

            # Tentukan partner untuk line
            if cl.claim_to == 'customer':
                claim_partner = self.partner_id
            else:
                claim_partner = cl.partner_id

            self.env['tw.work.order.line'].create({
                'order_id': self.id,
                'product_id': product.id,
                'division': product.division,
                'product_uom_qty': 1,
                'claim_partner_id': claim_partner.id if claim_partner else False,
            })
            existing_product_ids.append(product.id)
            added += 1

        # TODO : karena return notifikasi, view tidak ter-refresh jadi seakan2 line nya blm tertambah
        # if added == 0:
        #     return {'type': 'ir.actions.client', 'tag': 'display_notification',
        #             'params': {'title': 'Info', 'message': 'Semua produk dari master claim sudah ada di order lines.', 'type': 'warning'}}
        # return {'type': 'ir.actions.client', 'tag': 'display_notification',
        #         'params': {'title': 'Sukses', 'message': f'{added} produk berhasil ditambahkan dari master claim.', 'type': 'success'}}
        

    

