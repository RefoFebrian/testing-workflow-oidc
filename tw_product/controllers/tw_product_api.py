#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib
import functools
import werkzeug.wrappers
try:
    import simplejson as json
except ImportError:
    import json
import logging
_logger = logging.getLogger(__name__)
from datetime import timedelta,datetime,date
from dateutil.relativedelta import relativedelta
# 2: import of known third party lib
from odoo.addons.rest_api.rest_exception import invalid_response
from odoo.addons.rest_api.controllers.main import check_valid_token, valid_response
# 3:  imports of odoo
import odoo
from odoo import models, fields, api, _
from odoo import http

# 4:  imports from odoo modules
from odoo.http import request
from odoo.http import Response
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError

# 5: local imports

# 6: Import of unknown third party lib

class ControllerREST(http.Controller):
    @http.route('/api/master/<version>/get_product', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_product(self, version, **post):
        LIMIT = 10
        OFFSET = 0
        WHERE = "WHERE pp.active = TRUE"
        division = post.get('division')
        if not division:
            return invalid_response(400, 'division is required')

        if post.get('limit', False):
            LIMIT = int(post['limit'])
        if post.get('offset', False):
            OFFSET = int(post['offset'])

        if post.get('type',False):
            categ_obj = self.env['product.category'].search([('parent_id','child_of',post['type'])])
            categ_ids = str(tuple([categ.id for categ in categ_obj])).replace(',)', ')')
            WHERE += f" AND cat.id IN {categ_ids}"
        if post.get('string', False):
            WHERE += f" AND (pt.default_code ilike '%%{post['string']}%%' or pt.name->>'en_US' ilike '%%{post['string']}%%')"

        query = f"""
            SELECT 
                pp.id as id
                , pav.name->>'en_US' as warna
                , pav.code as code_warna
                , pt.name->>'en_US' as nama_produk
                , pt.default_code as code
            FROM product_product pp
            JOIN product_template as pt on pt.id = pp.product_tmpl_id
            JOIN product_variant_combination as combination on combination.product_product_id = pp.id
            JOIN product_template_attribute_value as ptav on ptav.id = combination.product_template_attribute_value_id
            JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
            {WHERE} 
            AND pt.division = '{division}'
            ORDER BY pt.name ASC
            LIMIT {LIMIT}
            OFFSET {OFFSET}
        """
        request._cr.execute(query)
        ress = request._cr.dictfetchall()
        
        return valid_response(200, ress)
    
    @http.route('/api/master/<version>/product_unit', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def product_unit(self, version, **post):
        LIMIT = 10
        OFFSET = 0
        WHERE = "WHERE pp.active = TRUE AND pt.division = 'Unit'"
        uid = request.session.uid

        company_id = False
        employee = request.env['hr.employee'].sudo().search([('user_id','=',uid)],limit=1)
        company_id = employee.company_id.id

        if post.get('limit', False):
            LIMIT = int(post['limit'])
        if post.get('offset', False):
            OFFSET = int(post['offset'])

        if post.get('type',False):
            categ_obj = self.env['product.category'].search([('parent_id','child_of',post['type'])])
            categ_ids = str(tuple([categ.id for categ in categ_obj])).replace(',)', ')')
            WHERE += f" AND cat.id IN {categ_ids}"
        if post.get('string', False):
            WHERE += f" AND (pt.default_code ilike '%%{post['string']}%%' or pt.name->>'en_US' ilike '%%{post['string']}%%')"

        query = """
            SELECT 
                pp.id as id
                , pav.name->>'en_US' as warna
                , pav.code as code_warna
                , pt.name->>'en_US' as nama_produk
                , pt.default_code as code
                , COALESCE(price.price,0) + COALESCE(price_bbn.price,0) as price
                , pt.name->>'en_US'||' (OTR RP '|| trim(to_char(round(COALESCE(price.price,0)* 1.1 + COALESCE(price_bbn.price,0),0),'999,999,999'))||') ' as nama
            FROM product_product pp
            JOIN product_template as pt on pt.id = pp.product_tmpl_id
            JOIN product_variant_combination as combination on combination.product_product_id = pp.id
            JOIN product_template_attribute_value as ptav on ptav.id = combination.product_template_attribute_value_id
            JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
            LEFT JOIN (
                SELECT 
                    item.product_tmpl_id as product_tmpl_id
                    , item.fixed_price as price
                FROM res_company rc
                left join tw_branch_setting tbs on rc.id = tbs.company_id 
                INNER JOIN product_pricelist list ON list.id = tbs.pricelist_sale_unit_id
                INNER JOIN product_pricelist_item item ON item.pricelist_id = list.id
                WHERE rc.id = %s
                and item.date_end >= now()
                GROUP BY item.product_tmpl_id,item.fixed_price
            ) price ON price.product_tmpl_id = pt.id
            LEFT JOIN (
                SELECT 
                    item.product_tmpl_id as product_tmpl_id
                    , item.fixed_price as price
                FROM res_company rc
                left join tw_branch_setting tbs on rc.id = tbs.company_id 
                INNER JOIN product_pricelist list ON list.id = tbs.pricelist_sale_bbn_hitam_id
                INNER JOIN product_pricelist_item item ON item.pricelist_id = list.id AND item.date_end is null
                WHERE rc.id = %s
                and item.date_end >= now()
                GROUP BY item.product_tmpl_id,item.fixed_price
            ) price_bbn ON price_bbn.product_tmpl_id = pt.id
            %s
            AND pt.division = 'Unit' 
            ORDER BY pt.name ASC
            LIMIT %d
            OFFSET %d
        """ % (company_id,company_id, WHERE, LIMIT, OFFSET)
        request._cr.execute(query)
        ress = request._cr.dictfetchall()
        
        return valid_response(200, ress)

    @http.route('/api/master/<version>/get_product_extras', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_product_extras(self, version, **post):

        limit = int(post.get('limit', 10))
        offset = int(post.get('offset', 0))

        where_clauses = ["categ.complete_name ILIKE %s"]
        params = ["%Extras%"]

        if post.get('string'):
            where_clauses.append("pt.name ->> 'en_US' ILIKE %s")
            params.append(f"%{post['string']}%")

        where_sql = " AND ".join(where_clauses)

        query = f"""
            SELECT
                pt.id,
                pt.name ->> 'en_US' AS name
            FROM product_template pt
            JOIN product_category categ ON pt.categ_id = categ.id
            WHERE {where_sql}
            LIMIT %s OFFSET %s
        """

        params.extend([limit, offset])
        request._cr.execute(query, params)

        ress = request._cr.dictfetchall()
        return valid_response(200, ress)
