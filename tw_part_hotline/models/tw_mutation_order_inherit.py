# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning, ValidationError

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class MutationOrder(models.Model):
    _inherit = "tw.mutation.order"

    @api.constrains('location_id')
    def _check_location_id(self):
        if self.company_id and self.division:
            if self.division == 'Sparepart' and self.stock_distribution_id:
                get_locs_query = """
                    SELECT 
                        tsd.location_id,
                        l.complete_name
                    FROM tw_stock_distribution tsd
                    JOIN stock_location l ON tsd.location_id = l.id
                    LEFT JOIN tw_selection ts ON ts.id = l.type_id
                    LEFT JOIN tw_purchase_order_type pot ON pot.id = tsd.purchase_order_type_id
                    WHERE tsd.company_id = %s
                    AND tsd.division = 'Sparepart'
                    AND pot.name = %s
                    AND tsd.is_add_from_hotline = %s
                """
                params = (
                    self.company_id.id,
                    self.stock_distribution_id.purchase_order_type_id.name,
                    self.stock_distribution_id.is_add_from_hotline
                )
                self._cr.execute(get_locs_query, params)
                loc_ress = self._cr.fetchall()
                loc_ids = []
                loc_names = ""
                for x in loc_ress:
                    loc_ids.append(x[0])
                    loc_names += str(x[1]) + ", "
                if loc_ress:
                    if self.location_id.id not in loc_ids:
                        from_hotline = " (dari Hotline)" if self.stock_distribution_id.is_add_from_hotline else ""
                        raise ValidationError('Lokasi yang sesuai untuk tipe distribusi %s%s adalah %s.' % (self.stock_distribution_id.purchase_order_type_id.name, from_hotline, loc_names[:-2]))