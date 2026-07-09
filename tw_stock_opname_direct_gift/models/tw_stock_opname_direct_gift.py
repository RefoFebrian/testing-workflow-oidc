# 1: imports of python lib
import datetime
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, api, fields
from odoo.exceptions import UserError


# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwStockOpnameDirectGift(models.Model):
    _name = "tw.stock.opname.direct.gift"
    _description = "TW Stock Opname Direct Gift"
    _inherit = ['tw.attachment.mixin']

    # 7: defaults methods
    @api.model
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    @api.model
    def _get_default_datetime(self):
        return datetime.datetime.now()

    # 8: fields
    name = fields.Char('Name', compute='_compute_name', store=True, index=True, readonly=True)
    date = fields.Date('Tanggal SO', default=_get_default_date)
    post_date = fields.Datetime('Posted on')
    generate_date = fields.Datetime('Generate on')
    state = fields.Selection([('draft', 'Draft'), ('open', 'Open'), ('posted', 'Posted')], default='draft')
    division = fields.Selection([('umum', 'Umum')], default='umum')
    note_bakso = fields.Text('Note')
    is_pilot = fields.Boolean(string='Is Pilot?', compute='_compute_is_pilot', store=True)

    # 9: relation fields
    company_id = fields.Many2one('res.company', 'Branch', index=True)
    pdi_id = fields.Many2one('hr.employee', 'PDI', domain="[('company_id', '=', company_id)]")
    adh_id = fields.Many2one('hr.employee', 'ADH', domain="[('job_id.name', 'in', ('ADMINISTRATION HEAD','ADMINISTRATION HEAD MD')), ('company_id', '=', company_id)]")
    soh_id = fields.Many2one('hr.employee', 'SOH', domain="[('job_id.name', 'in', ('SALES OPERATION HEAD', 'BRANCH HEAD')), ('company_id', '=', company_id)]")
    post_uid = fields.Many2one('res.users', 'Posted by')
    detail_ids = fields.One2many('tw.stock.opname.direct.gift.line', 'opname_id')
    other_dg_ids = fields.One2many('tw.stock.opname.direct.gift.other', 'opname_id')


    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('company_id')
    def _compute_name(self):
        for rec in self:
            if not rec.company_id:
                rec.name = False
                continue

            sequence_code = 'SODG'
            branch_code = rec.company_id.code or ''
            rec.name = rec.env['ir.sequence'].get_sequence_code(sequence_code, branch_code)

    @api.depends('company_id')
    def _compute_is_pilot(self):
        for rec in self:
            is_pilot = False
            if rec.company_id:
                pilot_branches = rec.env['tw.pilot.project'].sudo().search([
                    ('name', '=', 'ATTACHMENT STOCK OPNAME'),
                    ('active', '=', True),
                    ('company_ids', 'in', rec.company_id.id)
                ])
                if pilot_branches:
                    is_pilot = True
            rec.is_pilot = is_pilot

    @api.onchange('company_id')
    def onchange_is_pilot(self):
        self.is_pilot = False
        self.pdi_id = False
        self.adh_id = False
        self.soh_id = False

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            check = self.suspend_security().search([
                ('company_id', '=', vals['company_id']),
                ('state', '!=', 'posted')
            ])
            if check:
                raise UserError('Perhatian! Masih ada stock opname yang belum selesai.')

            if 'attachment_ids' in vals:
                model_id = self.env['ir.model'].suspend_security().search([('model', '=', self._name)])
                for data in vals['attachment_ids']:
                    data[2]['form_id'] = model_id.id

        return super(TwStockOpnameDirectGift, self).create(vals)

    def write(self, vals):
        if 'attachment_ids' in vals:
            model_id = self.env['ir.model'].suspend_security().search([('model','=',self._name)])
            for data in vals['attachment_ids']:
                if data[2]:
                    data[2]['form_id'] = model_id.id

        return super(TwStockOpnameDirectGift, self).write(vals)

    def unlink(self):
        for data in self:
            if data.state != "draft":
                raise UserError("Tidak bisa menghapus data yang berstatus selain draft!")
        return super(TwStockOpnameDirectGift, self).unlink()

    # 13: action methods
    def action_generate_stock(self):
        if self.generate_date:
            raise UserError('DG Stock telah terbentuk. Silahkan refresh halaman ini!')

        query = """
            SELECT
                quant.product_id,
                quant.product_name,
                quant.qty_titipan,
                quant.qty_stock,
                DATE_PART('days', NOW() - quant.in_date)::int AS aging,
                COALESCE(CAST(pp.standard_price ->> CAST(b.id AS TEXT) AS float), 0.00) AS harga_satuan
            FROM (
                SELECT
                    l.company_id,
                    l.warehouse_id,
                    p.default_code,
                    p.id AS product_id,
                    t.name AS product_name,
                    SUM(
                        CASE
                            WHEN q.consolidated_date IS NULL THEN q.quantity
                            ELSE 0
                        END
                    ) AS qty_titipan,
                    SUM(
                        CASE
                            WHEN q.consolidated_date IS NOT NULL THEN q.quantity
                            ELSE 0
                        END
                    ) AS qty_stock,
                    MIN(q.in_date) AS in_date,
                    t.categ_id
                FROM stock_quant q
                INNER JOIN stock_location l
                    ON q.location_id = l.id
                   AND l.usage IN ('internal', 'transit', 'nrfs')
                LEFT JOIN product_product p
                    ON q.product_id = p.id
                LEFT JOIN product_template t
                    ON p.product_tmpl_id = t.id
                GROUP BY
                    l.id,
                    p.id,
                    t.id,
                    t.categ_id
            ) AS quant
            LEFT JOIN product_category c
                ON quant.categ_id = c.id
            LEFT JOIN res_company b
                ON quant.company_id = b.id
            LEFT JOIN product_product pp
                ON pp.id = quant.product_id
            WHERE
                (
                    c.parent_path LIKE (
                        SELECT parent_path || id || '/%%'
                        FROM product_category
                        WHERE name = 'Direct Gift'
                        LIMIT 1
                    )
                    OR c.id = (
                        SELECT id
                        FROM product_category
                        WHERE name = 'Direct Gift'
                        LIMIT 1
                    )
                )
                AND b.id = %d
        """ % (self.company_id.id)
        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()
        lines = []
        for res in ress:
            product_name = res.get('product_name')
            if isinstance(product_name, dict):
                product_name = list(product_name.values())[0]

            lines.append([0, False, {
                'product_id': res.get('product_id'),
                'name': product_name,
                'unit_price': res.get('harga_satuan'),
                'qty': res.get('qty_titipan') + res.get('qty_stock'),
                'amount': res.get('harga_satuan'),
                'aging': res.get('aging')
            }])
        self.suspend_security().write({
            'generate_date': self._get_default_datetime(),
            'detail_ids': lines,
            'state': 'open',
        })

    def action_post(self):
        self.suspend_security().write({
            'post_uid': self._uid,
            'post_date': self._get_default_datetime(),
            'state': 'posted',
        })

    def action_print_validasi(self):
        active_ids = self.env.context.get('active_ids', [])
        user = self.env['res.users'].suspend_security().browse(self._uid).name
        detail_ids = []
        other_dg_ids = []

        for other in self.other_dg_ids:
            other_dg_ids.append({
                'nama_product':other.product_name,
                'qty_fisik_baik':other.qty_physical_good,
                'qty_fisik_rusak':other.qty_physical_broken,
                'qty_fisik_total':other.qty_physical_total,
                'saldo_log_book':other.balance_log_book,
            })
        tot_qty = 0
        tot_amount = 0
        tot_qty_fisik_baik = 0
        tot_qty_fisik_rusak = 0
        tot_qty_fisik_total = 0
        tot_amount_total = 0
        tot_selisih_qty = 0
        tot_selisih_amount = 0
        tot_saldo_log_book = 0
        tot_other_baik = 0
        tot_other_rusak = 0
        tot_other_total = 0
        tot_other_log_book = 0

        for line in self.detail_ids:
            detail_ids.append({
                'product': line.product_id.display_name if line.product_id else '',
                'harga_satuan':line.unit_price,
                'qty':line.qty,
                'amount':line.amount,
                'qty_fisik_baik':line.qty_physical_good,
                'qty_fisik_rusak':line.qty_physical_broken,
                'qty_fisik_total':line.qty_physical_total,
                'amount_total':line.amount_total,
                'selisih_qty':line.diff_qty,
                'selisih_amount':line.diff_amount,
                'saldo_log_book':line.balance_log_book,
                'aging':line.aging,
            })
            tot_qty += line.qty
            tot_amount += line.amount
            tot_qty_fisik_baik += line.qty_physical_good
            tot_qty_fisik_rusak += line.qty_physical_broken
            tot_qty_fisik_total += line.qty_physical_total
            tot_amount_total += line.amount_total
            tot_selisih_qty += line.diff_qty
            tot_selisih_amount += line.diff_amount
            tot_saldo_log_book += line.balance_log_book

        for other in self.other_dg_ids:
            tot_other_baik += other.qty_physical_good
            tot_other_rusak += other.qty_physical_broken
            tot_other_total += other.qty_physical_total
            tot_other_log_book += other.balance_log_book

        datas = {
            'ids': active_ids,
            'user': user,
            'date': (datetime.datetime.now() + datetime.timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S'),
            'name': str(self.name),
            'company_id': str(self.company_id.display_name if self.company_id else ''),
            'division': self.division,
            'tgl_so': self.date,
            'pdi_id': self.pdi_id,
            'soh_id': self.soh_id,
            'adh_id': self.adh_id,
            'detail_ids': detail_ids,
            'other_dg_ids': other_dg_ids,
            'create_uid': self.create_uid.name,
            'create_date': (self.create_date + relativedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S') if self.create_date else '',
            'tot_qty': tot_qty,
            'tot_amount': tot_amount,
            'tot_qty_fisik_baik': tot_qty_fisik_baik,
            'tot_qty_fisik_rusak': tot_qty_fisik_rusak,
            'tot_qty_fisik_total': tot_qty_fisik_total,
            'tot_amount_total': tot_amount_total,
            'tot_selisih_qty': tot_selisih_qty,
            'tot_selisih_amount': tot_selisih_amount,
            'tot_saldo_log_book': tot_saldo_log_book,
            'tot_other_baik': tot_other_baik,
            'tot_other_rusak': tot_other_rusak,
            'tot_other_total': tot_other_total,
            'tot_other_log_book': tot_other_log_book,
        }

        return self.env.ref('tw_stock_opname_direct_gift.action_tw_so_dg_print_validasi').report_action(self, data={'ids': self.ids})

    def action_bakso(self):
        form_id = self.env.ref('tw_stock_opname_direct_gift.view_tw_stock_opname_bakso_dg_wizard').id

        return {
            'type': 'ir.actions.act_window',
            'name': 'Berita Acara SO',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tw.stock.opname.bakso.dg',
            'context': {'default_opname_id': self.id, 'default_note_bakso': self.note_bakso},
            'views': [(form_id, 'form')],
            'target': 'new'
        }

    # 14: private methods