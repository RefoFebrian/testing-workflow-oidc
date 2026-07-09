import warnings
from odoo.exceptions import UserError

class UserError(UserError):
    """
    Custom Error when installed tw_web
    
    Generic error managed by the client.

    Typically when the user tries to do something that has no sense given the current
    state of a record. Semantically comparable to the generic 400 HTTP status codes.
    """

    def __init__(self, title ,message):
        """
        :param message: exception message and frontend modal content
        """
        super().__init__(title,message)