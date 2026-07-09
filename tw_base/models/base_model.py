from odoo import api, models, _, SUPERUSER_ID
from odoo.exceptions import UserError as Warning
from odoo.tools.misc import unquote

class BaseModel(models.AbstractModel):
    _inherit = "base"
    
    @api.model
    @api.readonly
    def get_views(self, views, options=None):
        """
            Restrict access to a menu, when user with no access try to access it with URL
        """
        options = options or {}
        action_id = options.get('action_id')
        if action_id:
            menu = self.env['ir.ui.menu'].sudo().with_user(SUPERUSER_ID).search([('action', '=', 'ir.actions.act_window,%d' % int(action_id))], limit=1)
            if menu:
                group_ids = tuple(menu.groups_id.ids)
                if group_ids:
                    self._cr.execute(
                        """SELECT 1 FROM res_groups_users_rel WHERE uid=%s AND gid IN %s""",
                        (self._uid, group_ids)
                    )
                    is_has_access = bool(self._cr.fetchone())
                    if not is_has_access:
                        raise Warning('Perhatian ! \n Anda tidak memiliki akses ke menu %s.'%(menu.name))
        return super(BaseModel, self).get_views(views, options)
    

    def _check_company_domain(self, companies):
        """Domain to be used for company consistency between records regarding this model.

        :param companies: the allowed companies for the related record
        :type companies: BaseModel or list or tuple or int or unquote
        """
        if not companies:
            return [('company_id', '=', False)]

        if isinstance(companies, unquote):
            # Use 'parent_of' operator to include the company itself AND its parent companies.
            # This replaces the old 'company_id.parent_id.id' traversal which crashes in Odoo 18's
            # web client JS evaluator ("Cannot read properties of undefined (reading 'id')").
            return ['|', ('company_id', '=', False), ('company_id', 'parent_of', companies)]
        
        if isinstance(companies, (int, list, tuple)):
            companies = self.env['res.company'].browse(companies)
        
        if isinstance(companies, models.BaseModel):
            # On the server side, we can safely include the parent company.
            all_companies = companies | companies.mapped('parent_id')
            return [('company_id', 'in', all_companies.ids + [False])]

        # Fallback for other cases
        def to_company_ids(companies):
            if isinstance(companies, models.BaseModel):
                return companies.ids
            elif isinstance(companies, (list, tuple)):
                return list(companies)
            return [companies]

        return [('company_id', 'in', to_company_ids(companies) + [False])]