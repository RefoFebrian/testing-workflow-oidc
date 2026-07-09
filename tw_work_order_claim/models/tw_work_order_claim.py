# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwWorkOrderClaim(models.Model):
    _name = "tw.work.order.claim"
    _description = "TW Work Order Claim"
    _order = "id desc"

    # 7: defaults methods

    # 8: fields
    active = fields.Boolean(string='Active', default=True)
    display_name = fields.Char(compute='_compute_display_name', store=True, index=True)

    scope_type = fields.Selection([
        ('branch', 'Branch'),
        ('area', 'Area'),
    ], string='Scope By', default='branch', required=True,
        help=(
            "Branch: konfigurasi claim terikat pada satu branch spesifik.\n"
            "Area: konfigurasi claim berlaku untuk semua branch dalam satu area."
        )
    )

    # 9: relation fields
    company_id = fields.Many2one(
        'res.company', string='Branch',
        default=lambda self: self.env.company,
        help=(
            'Saat Scope By = Branch: pilih branch spesifik, atau Holding Company (H2Z) '
            'agar berlaku ke semua branch.\n'
            'Saat Scope By = Area: otomatis diisi Holding Company.'
        )
    )
    area_id = fields.Many2one(
        'res.area', string='Area',
        help='Diisi saat Scope By = Area. Claim berlaku untuk semua branch dalam area ini.'
    )
    claim_type_id = fields.Many2one(
        'tw.selection', string="Claim Type",
        domain=[('type', '=', 'WorkOrderClaimType'), ('active', '=', True)]
    )
    claim_type = fields.Char(string='Claim Type String', related='claim_type_id.value')
    journal_id = fields.Many2one(
        'account.journal', string='Journal',
        domain="[('company_id', '=', company_id)] if company_id else []"
    )
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Term')
    date_start = fields.Date(string='Effective From', help='Jika diisi, claim hanya berlaku mulai tanggal ini')
    date_end = fields.Date(string='Effective To', help='Jika diisi, claim hanya berlaku sampai tanggal ini')
    kpb_period = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4')
    ], string='KPB Ke-', help='Periode KPB (ke-1, ke-2, dst). Diisi khusus jika Claim Type adalah KPB.')

    # Unit product filter — menentukan unit motor apa yang di-cover oleh claim ini
    unit_apply_on = fields.Selection([
        ('all', 'All Units'),
        ('product', 'Product'),
        ('category', 'Category'),
    ], string='Apply To', default='all', required=True,
        help='Tentukan apakah claim berlaku untuk semua unit, produk/varian spesifik, atau kategori unit')
    unit_product_tmpl_id = fields.Many2one(
        'product.template', string='Product',
        domain=[('division', '=', 'Unit')]
    )
    unit_product_id = fields.Many2one(
        'product.product', string='Variant',
        domain="[('product_tmpl_id', '=', unit_product_tmpl_id), ('division', '=', 'Unit')]"
    )
    unit_categ_id = fields.Many2one('product.category', string='Category')
    claim_line_ids = fields.One2many(
        'tw.work.order.claim.line', 'claim_id', string='Claim Sparepart Items'
    )

    # 10: constraints & sql constraints
    @api.constrains(
        'scope_type', 'claim_type_id', 'company_id', 'area_id',
        'unit_apply_on', 'unit_product_id', 'unit_product_tmpl_id', 'unit_categ_id',
        'date_start', 'date_end', 'kpb_period',
    )
    def _check_unique_claim_scope(self):
        """Ensure no duplicate claim master for the same scope combination.

        Branch scope: uniqueness = claim_type + company_id + unit + kpb_period + period
        Area scope:   uniqueness = claim_type + area_id   + unit + kpb_period + period
        """
        for rec in self:
            # Build base domain per scope_type
            if rec.scope_type == 'branch':
                scope_domain = [
                    ('scope_type', '=', 'branch'),
                    ('company_id', '=', rec.company_id.id),
                    ('area_id', '=', False),
                ]
            else:  # area
                scope_domain = [
                    ('scope_type', '=', 'area'),
                    ('area_id', '=', rec.area_id.id if rec.area_id else False),
                ]

            domain = [
                ('id', '!=', rec.id),
                ('claim_type_id', '=', rec.claim_type_id.id),
                ('unit_apply_on', '=', rec.unit_apply_on),
                ('kpb_period', '=', rec.kpb_period),
            ] + scope_domain

            # Unit-specific scope
            if rec.unit_apply_on == 'product':
                domain += [
                    ('unit_product_tmpl_id', '=', rec.unit_product_tmpl_id.id if rec.unit_product_tmpl_id else False),
                    ('unit_product_id', '=', rec.unit_product_id.id if rec.unit_product_id else False),
                ]
            elif rec.unit_apply_on == 'category':
                domain += [('unit_categ_id', '=', rec.unit_categ_id.id if rec.unit_categ_id else False)]

            duplicates = self.suspend_security().search(domain)
            if not duplicates:
                continue

            # Check date range overlap (null periode = berlaku selamanya = pasti overlap)
            for dup in duplicates:
                # Both have no period → definite overlap
                if not rec.date_start and not dup.date_start:
                    raise ValidationError(
                        _("Sudah ada konfigurasi Claim dengan scope yang sama:\n%s") % dup.display_name
                    )
                # One has no period → berlaku selamanya, pasti overlap dengan period apapun
                if not rec.date_start or not dup.date_start:
                    raise ValidationError(
                        _("Sudah ada konfigurasi Claim dengan scope yang sama:\n%s") % dup.display_name
                    )
                # Both have periods: check overlap
                rec_end = rec.date_end or fields.Date.today().replace(year=9999)
                dup_end = dup.date_end or fields.Date.today().replace(year=9999)
                if rec.date_start <= dup_end and rec_end >= dup.date_start:
                    raise ValidationError(
                        _("Periode konfigurasi Claim overlap dengan konfigurasi yang sudah ada:\n%s") % dup.display_name
                    )

    @api.constrains('scope_type', 'company_id', 'area_id')
    def _check_scope_fields(self):
        """Validate that required fields are set per scope_type."""
        for rec in self:
            if rec.scope_type == 'branch' and not rec.company_id:
                raise ValidationError(_("Branch harus diisi saat Scope By = Branch."))
            if rec.scope_type == 'area' and not rec.area_id:
                raise ValidationError(_("Area harus diisi saat Scope By = Area."))

    @api.constrains('claim_line_ids')
    def _check_claim_line_ids(self):
        for record in self:
            if not record.claim_line_ids:
                raise ValidationError(_("Claim Line is required."))

    # 11: compute/depends & on change methods
    @api.depends(
        'scope_type', 'company_id', 'area_id',
        'claim_type_id', 'date_start', 'date_end', 'kpb_period'
    )
    def _compute_display_name(self):
        """Compute display name combining claim type, KPB period, scope and period."""
        for record in self:
            parts = []
            if record.claim_type_id:
                name = record.claim_type_id.name
                if record.claim_type_id.value == 'KPB' and record.kpb_period:
                    name += f' Ke-{record.kpb_period}'
                parts.append(name)

            if record.scope_type == 'branch':
                if record.company_id:
                    parts.append(record.company_id.name)
            else:  # area
                if record.area_id:
                    parts.append(f'Area: {record.area_id.name}')
                else:
                    parts.append('Area: (Semua)')

            if record.date_start and record.date_end:
                parts.append(f"{record.date_start} s/d {record.date_end}")
            record.display_name = ' - '.join(parts) if parts else '/'

    @api.onchange('scope_type')
    def _onchange_scope_type(self):
        """Switch between Branch and Area scope — mutually exclusive."""
        if self.scope_type == 'branch':
            # Reset area when switching to branch
            self.area_id = False
        elif self.scope_type == 'area':
            # Auto-fill company_id with holding company to satisfy Odoo multi-company rules
            holding = self._get_holding_company()
            if holding:
                self.company_id = holding
            self.area_id = False  # reset so user explicitly picks

    @api.onchange('unit_apply_on')
    def _onchange_unit_apply_on(self):
        """Clear irrelevant unit filter fields when apply_on changes."""
        for rec in self:
            if rec.unit_apply_on != 'product':
                rec.unit_product_tmpl_id = False
                rec.unit_product_id = False
            if rec.unit_apply_on != 'category':
                rec.unit_categ_id = False

    @api.onchange('unit_product_tmpl_id')
    def _onchange_unit_product_tmpl_id(self):
        """Reset variant when template changes."""
        self.unit_product_id = False

    # 12: private helpers
    def _get_holding_company(self):
        """Return the top-level holding company (no parent) for area-scope claims.

        Used to populate company_id automatically when scope_type switches to 'area',
        ensuring Odoo multi-company record rules remain satisfied.
        """
        return self.env['res.company'].sudo().search(
            [('parent_id', '=', False)], order='id asc', limit=1
        )