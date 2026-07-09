from odoo import api, models, _, fields
from odoo.exceptions import UserError

class TwWorkOrderPackage(models.Model):
    _inherit = "tw.work.order"

    area_id = fields.Many2one('res.area', related='company_id.branch_setting_id.default_area_id', string='Area')
    service_package_ids = fields.Many2many('tw.service.package', 'tw_work_order_service_package_rel', 'work_order_id', 'service_package_id', string='Paket', domain="[('active', '=', True), ('is_priority', '=', False), ('company_id', 'parent_of', company_id), '|', ('area_id', '=', False), ('area_id', '=', area_id)]")
    service_package_priority_ids = fields.Many2many('tw.service.package', string='Paket Prioritas', domain="[('active', '=', True), ('is_priority', '=', True), ('company_id', 'parent_of', company_id), '|', ('area_id', '=', False), ('area_id', '=', area_id)]")

    def _handle_package_change(self, selected_packages, is_priority):
        for wo in self:
            previous_packages = wo.order_line.mapped('service_package_id').filtered(lambda sp: sp.is_priority is is_priority)
            
            removed_packages = previous_packages - selected_packages
            added_packages = selected_packages - previous_packages

            for removed_package in removed_packages:
                for pline in removed_package.line_ids:
                    existing_line = wo.order_line.filtered(lambda l: l.product_id == pline.product_id and l.service_package_id == removed_package)

                    if existing_line:
                        existing_line[0].product_uom_qty -= pline.quantity
                        existing_line[0].service_package_id = False

                        if existing_line[0].product_uom_qty <= 0:
                            wo.order_line = [(2, existing_line[0].id)]

            for added_package in added_packages:
                for pline in added_package.line_ids.filtered(lambda l: l.active):
                    existing_line = wo.order_line.filtered(lambda l: l.product_id == pline.product_id and not l.service_package_id)

                    if existing_line:
                        existing_line[0].product_uom_qty += pline.quantity
                        existing_line[0].service_package_id = added_package.id

                        price_unit = 0
                        pricelist = self.env['product.pricelist']
                        if existing_line[0].division == 'Service':
                            pricelist = wo.company_id.branch_setting_id.pricelist_service_id
                            if pricelist:
                                price_unit = pricelist.with_company(wo.company_id.id)._price_get_by_category_service(existing_line[0].product_id,existing_line[0].product_uom_qty,category_service=existing_line[0].order_id.product_id.product_tmpl_id.service_category_id.id)[pricelist.id]
                        elif existing_line[0].division == 'Sparepart':
                            pricelist = wo.company_id.branch_setting_id.pricelist_sale_sparepart_id
                            if pricelist:
                                price_unit = \
                                pricelist.with_company(wo.company_id.id)._price_get(existing_line[0].product_id, existing_line[0].product_uom_qty)[pricelist.id]

                        if not pricelist:
                            raise UserError(_(f'{existing_line[0].division} Pricelist not found for branch {wo.company_id.branch_setting_id.name}!'))

                        existing_line[0].price_unit = price_unit
                    else:
                        price_unit = 0
                        pricelist = self.env['product.pricelist']
                        if pline.division == 'Service':
                            pricelist = wo.company_id.branch_setting_id.pricelist_service_id
                            if pricelist:
                                price_unit = pricelist.with_company(wo.company_id.id)._price_get_by_category_service(pline.product_id, pline.quantity,category_service=wo.product_id.product_tmpl_id.service_category_id.id)[pricelist.id]
                        elif pline.division == 'Sparepart':
                            pricelist = wo.company_id.branch_setting_id.pricelist_sale_sparepart_id
                            if pricelist:
                                price_unit = pricelist.with_company(wo.company_id.id)._price_get(pline.product_id, pline.quantity)[pricelist.id]

                        if not pricelist:
                            raise UserError(_(f'{pline.division} Pricelist not found for branch {wo.company_id.branch_setting_id.name}!'))

                        line_vals = {
                            'product_id': pline.product_id.id,
                            'division': pline.division,
                            'discount': pline.discount,
                            'product_uom_qty': pline.quantity,
                            'price_unit': price_unit,
                            'service_package_id': added_package.id,
                        }
                        if 'warranty' in self.env['tw.work.order.line']._fields:
                            line_vals['warranty'] = pline.product_id.product_tmpl_id.categ_id.warranty

                        wo.order_line = [(0, 0, line_vals)]
                        
        self.order_line._set_location()
        for line in self.order_line:
            if line.division == 'Sparepart' and line.product_id and line.location_id:
                line.qty_available = line.get_quantity_available(line.order_id.company_id.id, line.product_id.id, line.division, line.location_id.id)

    @api.onchange('service_package_ids')
    def _onchange_service_package_ids(self):
        self._handle_package_change(self.service_package_ids, is_priority=False)

    @api.onchange('service_package_priority_ids')
    def _onchange_service_package_priority_ids(self):
        self._handle_package_change(self.service_package_priority_ids, is_priority=True)

    @api.onchange('order_line')
    def _onchange_order_line(self):
        packages_in_lines = self.order_line.mapped('service_package_id')
        priority_package_ids = packages_in_lines.filtered(lambda p: p.is_priority).ids
        standard_package_ids = packages_in_lines.filtered(lambda p: not p.is_priority).ids

        self.service_package_priority_ids = [(6, 0, priority_package_ids)]
        self.service_package_ids = [(6, 0, standard_package_ids)]
