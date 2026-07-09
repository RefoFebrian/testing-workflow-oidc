from odoo import models, fields, api
from odoo.exceptions import UserError as Warning
from datetime import datetime, timedelta

import json
import requests
import itertools


class TwBudgetProposal(models.Model):
    _name = "tw.budget.proposal"
    _description = "Budget Proposal"

    name = fields.Char('Name')
    division = fields.Char('Division')
    reference = fields.Char('No. Proposal Koprol')
    is_tender = fields.Boolean('Tender', default=True)

    company_id = fields.Many2one('res.company', string="Branch")
    budget_proposal_ids = fields.One2many('tw.budget.proposal.line', 'budget_proposal_id', string='Detail Budget Proposal')

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            company_id = values.get('company_id', self.default_get(['company_id']).get('company_id'))
            branch_obj = self.env['res.company'].browse(company_id)
            seq_name = self.with_company(company_id).env['ir.sequence'].get_sequence_code('BUDGET/PROPOSAL', branch_obj.code)
            values['name'] = seq_name
        return super(TwBudgetProposal, self).create(vals_list)
    
    def unlink(self):
        raise Warning("Dilarang Menghapus Data Budget Proposal!")

    def get_api_config(self,code):
        config_obj = self.env['tw.api.configuration'].sudo().search([
            ('code', '=', 'koprol')
        ], limit=1)
        if not config_obj:
            raise Warning('Configuration API Koprol Belum di setting.')
        
        endpoint = self.env['tw.api.config.endpoint'].sudo().search([
            ('code', '=', code),
            ('config_id', '=', config_obj.id),
        ], limit=1)
        if not endpoint:
            raise Warning('Endpoint Get Proposal Belum di setting.')
        
        return config_obj, endpoint
    
    def get_access_token(self):
        users = self.env['res.users'].sudo().search([('login', '=', 'api_koprol')], limit=1)
        if not users.oauth_access_token or datetime.now() > datetime.strptime(users.expired_date,
        "%Y-%m-%d %H:%M:%S"):
            users.get_azure_access_token()
        return users.oauth_access_token

    def scheduller_get_budget_proposal(self, branch_code=None, division_code=None, department_code=None, transaction_date=None):
        config_obj, endpoint = self.get_api_config('get_all_proposal')
    
        url = "%s%s" % (config_obj.base_url , endpoint.name)
        headers = { "Authorization": "Bearer {token}".format(token=self.get_access_token()) }

        transaction_date = transaction_date or datetime.now().strftime('%Y-%m-%d')

        # Ambil semua branch_code jika tidak ada pada parameter
        if not branch_code:
            branch_code = self.env['res.company'].sudo().search([]).mapped('code')

        # Ambil semua department_code jika tidak ada pada parameter
        if not department_code:
            department_code = self.env['hr.department'].sudo().search([]).mapped('id')

        list_division_code = ['Unit', 'Sparepart', 'Umum'] if not division_code else division_code

        for code, dept_code, div_code in itertools.product(branch_code, department_code, list_division_code):
            body, content = self.get_budget_koprol(url, headers, code, div_code, dept_code, transaction_date)

            if content.get('code') == 200 and content.get('data'):
                self.create_budget_proposal(content['data'])
                self.create_log('Success GET All Budget Proposal From Koprol', url, body, content)
            else:
                self.create_log('Failed GET All Budget Proposal From Koprol', url, body, content)

    def get_budget_koprol(self, url, headers, branch_code, division_code, department_code, transaction_date):
        body = {
            "company_code": "14",
            "branch_code": str(branch_code),
            "division_code": str(division_code),
            "department_code": str(department_code),
            "transaction_date": str(transaction_date)
        }
        try:
            response = requests.post(url, json=body, headers=headers)
            return body, json.loads(response.content)
        except Exception as e:
            return body, {'code': 500, 'error': str(e)}
        
    def send_update_budget_koprol(self,body):
        config_obj, endpoint = self.get_api_config('update_proposal')
        url = "%s%s" % (config_obj.base_url , endpoint.name)
        headers = { "Authorization": "Bearer {token}".format(token=self.get_access_token()) }
        
        response = requests.post(url, json=body, headers=headers)
        content = json.loads(response.content)
        if content.get('code') == 200 and content.get('data'):
            self.process_detail_budget_line(content['data'])
            self.create_log('Success Update Budget Proposal on Koprol', url, body, content)
        else:
            message = 'Failed Update Budget Proposal on Koprol'
            self.create_log(message, url, body, content)
            self._cr.commit()
            raise Warning(message)
    
    def process_detail_budget_line(self, data):
        bp_line = self.env['tw.budget.proposal.line'].sudo().search([
            ('budget_proposal_id.reference', '=', data['proposal_no_koprol']),
            ('budget_proposal_id.company_id.code', '=', data['branch_code']),
            ('proposal_category_code', '=', data['proposal_category_code'])
        ], limit=1)

        if bp_line:
            bp_line.write({
                'initial_budget_amount': data.get('initial_budget_amount', 0),
                'reserved_budget_amount': data.get('reserved_budget_amount', 0),
                'realization_budget_amount': data.get('realization_budget_amount', 0),
                'available_budget_amount': data.get('available_budget_amount', 0)
            })

    def create_budget_proposal(self, data):
        for item in data:
            header = item['header']
            detail = item['detail']

            budget_obj = self.sudo().search([('reference', '=', header['proposal_no_koprol'])], limit=1)
            branch_obj = self.env['res.company'].sudo().search([('code', '=', header['branch_code'])], limit=1)

            vals = {
                'reference': header['proposal_no_koprol'],
                'division': header['division_code'],
                'is_tender': header['is_tender'],
                'company_id': branch_obj.id if branch_obj else False,
            }

            if budget_obj:
                budget_obj.sudo().write(vals)
                for line in detail:
                    line.update({ 
                        'proposal_no_koprol': header['proposal_no_koprol'],
                        'branch_code': header['branch_code']
                     })
                    self.process_detail_budget_line(line)
            else:
                budget_line = []
                for line in detail:
                    budget_line.append([0,False,{
                        'proposal_category_code': line['proposal_category_code'] if line.get('proposal_category_code') else '',
                        'proposal_category_name': line['proposal_category_name'] if line.get('proposal_category_name') else '',
                        'initial_budget_amount': line['initial_budget_amount'] if line.get('initial_budget_amount') else 0,
                        'reserved_budget_amount': line['reserved_budget_amount'] if line.get('reserved_budget_amount') else 0,
                        'realization_budget_amount': line['realization_budget_amount'] if line.get('realization_budget_amount') else 0,
                        'available_budget_amount': line['available_budget_amount'] if line.get('available_budget_amount') else 0
                    }])

                vals['budget_proposal_ids'] = budget_line
                self.env['tw.budget.proposal'].sudo().create(vals)

    def create_log(self, name, url, body, content):
        self.env['tw.api.log'].sudo().create({
            'name': name,
            'type': 'incoming',
            'url': url,
            'request': body,
            'response_code': content.get('code'),
            'response': content,
        })

