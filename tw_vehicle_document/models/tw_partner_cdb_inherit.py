from odoo import api, models, fields

class PartnerCDB(models.Model):
    _inherit = "tw.partner.cdb"

    # jembatan context → field
    context_is_edit_cdb_lot = fields.Boolean(
        string="Ctx: Edit CDB Lot",
        compute="_compute_ctx_flags",
    )

    @api.depends_context('is_edit_cdb_lot')  # akan recompute bila context key berubah
    def _compute_ctx_flags(self):
        flag = bool(self.env.context.get('is_edit_cdb_lot'))
        for rec in self:
            rec.context_is_edit_cdb_lot = flag

    def action_save_cdb(self):
        self.ensure_one()
        # Update the state directly
        if self.env.context.get('is_edit_cdb_lot'):
            self.env['stock.lot'].suspend_security().browse(self._context.get('default_lot_id')).action_confirm_cdb()
        return {'type': 'ir.actions.act_window_close'}