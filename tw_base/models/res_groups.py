# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, SUPERUSER_ID, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class GroupsImplied(models.Model):
    _inherit = "res.groups"

    # ? Inherit explanation : Ensure that when a user is removed from a group (Group A), 
    # they are also safely removed from any groups implied by Group A (e.g., Group B), 
    # unless they inherit Group B from another source.
    def write(self, values):
        # Capture old implied groups & users (if applicable) before the write
        old_implied_groups = {g.id: g.implied_ids.ids for g in self}
        old_users = {g.id: g.users.ids for g in self} if 'users' in values else {}
        
        res = super(GroupsImplied, self).write(values)

        if 'implied_ids' in values:
            for group in self:
                # Calculate removed implied groups
                current_implied_ids = group.implied_ids.ids
                previously_implied_ids = old_implied_groups.get(group.id, [])
                removed_implied_ids = set(previously_implied_ids) - set(current_implied_ids)
                
                if removed_implied_ids:
                    removed_groups = self.browse(list(removed_implied_ids))
                    for removed_group in removed_groups:
                        # Find users who are in the removed group
                        users_to_check = group.users & removed_group.users
                        
                        for user in users_to_check:
                            self._safely_remove_user_from_group(user, group, removed_group)

        if 'users' in values:
            for group in self:
                # Calculate removed users
                current_users = group.users.ids
                removed_user_ids = set(old_users.get(group.id, [])) - set(current_users)
                
                if removed_user_ids:
                    removed_users = self.env['res.users'].browse(list(removed_user_ids))
                    for user in removed_users:
                        # Ensure we check the *implied* groups of the group attempting to remove users from
                        for target_group in group.trans_implied_ids:
                            self._safely_remove_user_from_group(user, group, target_group)
                                
        return res
    
    def _safely_remove_user_from_group(self, user, parent_group, target_group):
        """
        Safely remove user from target_group if they only inherited it via parent_group.
        """
        # Efficient check: Does any of the user's OTHER groups have this target_group in their transitive implied ids?
        user_other_groups = user.groups_id - parent_group
        if target_group not in user_other_groups.trans_implied_ids:
            # The user only had access to 'target_group' because of 'parent_group'.
            # Now that 'parent_group' no longer implies 'target_group' (or user lost 'parent_group'), 
            # we remove the user from 'target_group'.
            user.write({'groups_id': [fields.Command.unlink(target_group.id)]})
            self.env.registry.clear_cache('groups')
            target_group._check_one_user_type()


class UsersImplied(models.Model):
    _inherit = "res.users"

    def write(self, values):
        old_groups = {u.id: u.groups_id.ids for u in self} if 'groups_id' in values else {}
        
        res = super(UsersImplied, self).write(values)

        if 'groups_id' in values:
            for user in self:
                current_groups = user.groups_id.ids
                removed_group_ids = set(old_groups.get(user.id, [])) - set(current_groups)
                
                if removed_group_ids:
                    removed_groups = self.env['res.groups'].browse(list(removed_group_ids))
                    for group in removed_groups:
                        for target_group in group.trans_implied_ids:
                             group._safely_remove_user_from_group(user, group, target_group)
        return res
