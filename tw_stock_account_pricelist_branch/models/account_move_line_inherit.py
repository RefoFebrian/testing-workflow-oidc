# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.osv import expression

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class AccountMoveLineInherit(models.Model):
    _inherit = "account.move.line"
    
    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    # TODO: Dimatikan. Try default odoo schema of handling different price in valuation
    # @api.model_create_multi
    # def create(self, vals_list):
    #     move_obj = False
    #     for vals in vals_list:
    #         if 'move_id' in vals:
    #             if move_obj:
    #                 if move_obj.id != vals.get('move_id'):
    #                     move_obj = self.move_id.browse(vals.get('move_id'))
    #             else:
    #                 move_obj = self.move_id.browse(vals.get('move_id'))
    #         if move_obj:
    #             stock_move_obj = move_obj.stock_move_id
    #             if stock_move_obj:
    #                 if stock_move_obj.picking_type_id.code == 'incoming' and stock_move_obj.procure_method == 'make_to_stock':
    #                     if stock_move_obj.lot_ids:
    #                         balance = self._get_price_stock_journal_unit(stock_move_obj, vals)
    #                         if balance:
    #                             vals['balance'] = balance
    #     create = super(AccountMoveLineInherit, self).create(vals_list)

    #     return create

    # 13: action methods

    # 14: private methods
    # TODO: Dimatikan. Try default odoo schema of handling different price in valuation
    # def _get_price_stock_journal_unit(self, stock_move_obj, vals):
    #     balance = vals.get('balance')
    #     lot_obj = stock_move_obj.lot_ids[0]
    #     if lot_obj.supplier_invoice_id:
    #         product_price_from_inv = lot_obj.supplier_invoice_id.amount_total
    #         balance = product_price_from_inv if balance > 0 else -1*product_price_from_inv
    #     else:
    #         product_price_from_pricelist = False
    #         branch_config = self.env['tw.branch.setting'].search([('company_id','=',stock_move_obj.company_id.id)], limit=1)
    #         if branch_config.pricelist_purchase_unit_id:
    #             product_price_from_pricelist = self.env['product.pricelist']._price_get(stock_move_obj.product_id, stock_move_obj.product_uom_qty)[branch_config.pricelist_purchase_unit_id.id] * vals.get('quantity')
    #         if not product_price_from_pricelist:
    #             raise Warning(f'Product {stock_move_obj.product_id.name} tidak ada dalam Pricelist Beli Unit')
    #         balance = product_price_from_pricelist if balance > 0 else -1*product_price_from_pricelist

    #     return balance