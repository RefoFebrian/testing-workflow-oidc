# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import os
import pytz
import base64
import csv
import xlsxwriter
import calendar
from io import StringIO,BytesIO
from datetime import date, datetime, time,timedelta
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
class TwApprovalMatrixReport(models.TransientModel):
    _inherit = "tw.approval.matrix.report"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: Constraints & SQL Constraints

    # 11: Compute/Depends & On Change Methods

    # 12: Override Methods

    # 13: Action Methods   

    # 14: Private Methods
    def export_report_biaya_all(self):
        query_where = "WHERE 1=1"
        if self.company_ids:
            company_ids = self._check_child_company()
            query_where += " AND matrix.company_id IN %s" % str(tuple(company_ids)).replace(',)', ')')
        else:
            query_where += " AND matrix.company_id IN %s" % str(tuple([b.id for b in self.env.user.company_ids])).replace(',)', ')')
        if self.approval_config_ids:
            query_where += " AND config.id IN %s" % str(tuple([c.id for c in self.approval_config_ids])).replace(',)', ')')

        get_lead_query = """
            SELECT
                branch.code as branch_code
                , branch.name as branch_name
                , config.name as config_name
                , matrix.division
                , groups.name->>'en_US' as group_name
                , matrix_line.limit
            FROM tw_approval_matrix as matrix
                LEFT JOIN tw_approval_matrix_line as matrix_line on matrix_line.header_id = matrix.id
                LEFT JOIN tw_approval_config as config on config.id = matrix.form_id
                LEFT JOIN res_groups as groups on groups.id = matrix_line.group_id
                LEFT JOIN res_company as branch on branch.id = matrix.company_id
            %s
            ORDER BY branch.id,config.id
        """ % (query_where)
        self.env.cr.execute(get_lead_query)
        data =  self.env.cr.dictfetchall()
        return data,False