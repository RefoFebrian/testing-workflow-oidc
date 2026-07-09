# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AttachmentMixin(models.AbstractModel):
    _name = "tw.attachment.mixin"
    _description = "Attachment Mixin"

    @api.model
    def _compute_attachment_context(self):
        """Compute the context for the attachment_ids field."""
        return {'default_res_model': self._name, 'default_type':'binary'}

    @api.model
    def _get_attachment_domain(self):
        """Get the domain for the attachment_ids field."""
        return [('res_model', '=', self._name)]

    @api.model
    def _get_attachment_context(self):
        """Get the context for the attachment_ids field."""
        return self._compute_attachment_context()

    attachment_ids = fields.One2many(
        'tw.attachment', 'res_id',
        string='Attachments',
        domain="[('res_model', '=', 'dummy')]",  # Will be overridden in _setup_complete
        context="{}",  # Will be overridden in _setup_complete
        auto_join=True
    )

    @api.model
    def _setup_complete(self):
        """Override to set the correct domain and context after model setup."""
        super()._setup_complete()
        # Update the domain and context with the correct model name
        self._fields['attachment_ids'].domain = self._get_attachment_domain()
        self._fields['attachment_ids'].context = self._get_attachment_context()