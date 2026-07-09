from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class TWProductCategory(models.Model):
    _inherit = "product.category"

    serial_number_length = fields.Integer(string="Serial Number Length", default=12, help='Mandatory Length of Serial Number registered in this category')
    chassis_number_length = fields.Integer(string="Chassis Number Length", default=14, help='Mandatory Length of Chassis Number registered in this category')
    root_category_id = fields.Many2one('product.category', string='Root Category', compute='_compute_root_category_id', store=True)
    tracking = fields.Selection(
        selection=[('serial', 'Serial Number'), ('serial_chassis', 'Serial & Chassis Number')], 
        string='Tracking', store=True, compute='_compute_tracking', recursive=True,
        help='Tracking Lot by Serial Number or (Serial Number and Chassis Number)'
    )

    @api.depends('parent_id', 'parent_id.tracking')
    def _compute_tracking(self):
        for rec in self:
            if rec.parent_id and rec.parent_id.tracking:
                rec.tracking = rec.parent_id.tracking
            else:
                rec.tracking = False

    @api.depends('parent_id')
    def _compute_root_category_id(self):
        for category in self:
            if category.parent_path:
            # The path string looks like "1/5/12/". 
                # Split by '/' and take the first element.
                root_id = int(category.parent_path.split('/')[0])
                category.root_category_id = root_id
            else:
                # If no parent path, it is likely the root itself or new
                category.root_category_id = category.id

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'serial_number_length' in vals:
                if vals['serial_number_length'] < 0:
                    raise Warning(_('Length Serial Number must be greater than or equal to 0'))
            if 'chassis_number_length' in vals:
                if vals['chassis_number_length'] < 0:
                    raise Warning(_('Length Chassis Number must be greater than or equal to 0'))
                    
        return super(TWProductCategory, self).create(vals_list)

    def _get_child_ids(self, categ_id):
        """Recursive method to fetch all child IDs of a given category."""
        child_ids = self.search([('parent_id', '=', categ_id)])
        res = child_ids.ids
        for child in child_ids:
            res += child._get_child_ids(child.id)
        return res

    def get_child_ids(self, parent_categ_name):
        """Get all child category IDs of a category by its name."""
        parent_categ = self.search([('name', '=', parent_categ_name)], limit=1)
        if not parent_categ:
            return []
        return [parent_categ.id] + parent_categ._get_child_ids(parent_categ.id)

    def get_child_by_ids(self, ids):
        """Get all child category IDs for a given list of category IDs."""
        if isinstance(ids, int):
            ids = [ids]
        child_ids = self.browse(ids)
        res = child_ids.ids
        for categ in child_ids:
            res += categ._get_child_ids(categ.id)
        return res

    def get_root_name(self, ids):
        """Get the root category name of each category in ids list."""
        root_name = ""
        for categ in self.browse(ids):
            while categ.parent_id:
                categ = categ.parent_id
            if not root_name:
                root_name = categ.name
            elif root_name != categ.name:
                return False  # Different root names in the list
        return root_name

    def is_parent_name(self, ids, parent_name):
        """Check if the parent name of the category is the specified name."""
        if len(ids) > 1:
            return False
        category = self.browse(ids[0])
        while category.name != parent_name:
            if category.parent_id:
                category = category.parent_id
            else:
                return False
        return True
    
    