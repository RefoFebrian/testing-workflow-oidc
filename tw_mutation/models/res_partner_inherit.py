from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = "res.partner"
    
    route_type = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External'),
    ], string='Route Type')
    
    @api.model
    def _get_default_route_type(self):
        """
        Get default route type from context or configuration
        """
        return self.env.context.get('default_route_type', 'external')
    
    @api.model
    def default_get(self, fields_list):
        """
        Override to add default values from context
        """
        res = super(ResPartner, self).default_get(fields_list)
        
        # Add default route type from context if not set
        if 'route_type' in fields_list and 'route_type' not in res:
            res['route_type'] = self._get_default_route_type()
            
        return res
