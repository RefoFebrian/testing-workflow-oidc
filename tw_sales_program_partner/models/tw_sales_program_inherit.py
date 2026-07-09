# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwSalesProgramInherit(models.Model):
    _inherit = "tw.sales.program"

    # 7: defaults methods

    # 8: fields
    subsidy_type = fields.Selection([
        ('fix', 'Fix'),
        ('non', 'Non Fix')
    ], string='Tipe Subsidi')

    # 9: relation fields
    finco_id = fields.Many2many('res.partner', 'tw_sales_program_finco_rel', 'sales_program_id', 'finco_id', string='Finco', domain=[('category_id.name', '=', 'Finance Company')])

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    def init(self):
        super().init()
        self.env.cr.execute("""
            SELECT EXISTS (
                SELECT 1
                  FROM information_schema.columns
                 WHERE table_name = 'tw_sales_program'
                   AND column_name = 'finco_id'
            )
        """)
        has_legacy_finco_column = self.env.cr.fetchone()[0]
        self.env.cr.execute("SELECT to_regclass('tw_sales_program_finco_rel')")
        has_finco_rel = bool(self.env.cr.fetchone()[0])
        if has_legacy_finco_column and has_finco_rel:
            self.env.cr.execute("""
                INSERT INTO tw_sales_program_finco_rel (sales_program_id, finco_id)
                SELECT id, finco_id
                  FROM tw_sales_program
                 WHERE finco_id IS NOT NULL
                ON CONFLICT DO NOTHING
            """)

    # 13: action methods

    # 14: private methods