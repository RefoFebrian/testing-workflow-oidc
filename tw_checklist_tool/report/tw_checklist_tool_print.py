# -*- coding: utf-8 -*-
# 1: imports of python lib
import time
import json
import base64
from dateutil.relativedelta import relativedelta
from datetime import date, datetime, timedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwChecklistToolPrint(models.AbstractModel):
    _name = "report.tw_checklist_tool.print_checklist_tool_id"
    _description = "Checklist Tool Print"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    @api.model
    def _get_report_values(self, docids, data=None):
        if not docids and data and data.get('id'):
            docids = [data['id']]

        if not docids:
            return {}

        ids_tuple = tuple(docids)
        if len(ids_tuple) == 1:
            ids_clause = "= %s" % ids_tuple[0]
        else:
            ids_clause = "IN %s" % (ids_tuple,)

        lang = self.env.user.lang or 'en_US'

        query = """
                WITH aggregated_states AS (
                    SELECT
                        tct.id AS checklist_id,
                        tct.name AS checklist_number,
                        he.name AS pic_name,
                        categ_master_tool.name AS category,
                        pp.default_code AS product_code,
                        pp.id as product_product_id,
                        COALESCE(pt.name->>%s, pt.name->>'en_US', pt.name->>'id_ID') AS product_name,
                        tmtl.name as location_name,
                        master_tool.id as master_tool_id,
                        TO_CHAR(cl.date, 'YYYY-MM-DD') AS date,
                        cl.week::text AS week,
                        CASE 
                            WHEN tctl.tools_state = 'baik' THEN 'v'
                            WHEN tctl.tools_state = 'rusak' THEN 'R'
                            WHEN tctl.tools_state = 'hilang' THEN 'H'
                            WHEN tctl.tools_state = 'tidak_ada' THEN 'X'
                            ELSE ''
                        END AS state,
                        COALESCE(group_check.name->>%s, group_check.name->>'en_US', ' ') AS group_checked,
                        CASE 
                            WHEN wal.state = 'approve' THEN 'OK'
                            ELSE ''
                        END AS checked_pic
                    FROM tw_checklist_tools_line cl
                    LEFT JOIN tw_checklist_tools_detail tctl ON tctl.line_checklist_id = cl.id
                    LEFT JOIN tw_checklist_tools tct ON cl.checklist_id = tct.id
                    LEFT JOIN tw_selection categ_master_tool ON tct.category_master_tool_id = categ_master_tool.id
                    LEFT JOIN tw_master_tools master_tool on tctl.master_tool_id = master_tool.id
                    LEFT JOIN tw_selection tmtl on master_tool.location_id = tmtl.id
                    LEFT JOIN product_product pp ON tctl.product_id = pp.id
                    LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                    LEFT JOIN (
                        SELECT wal.*
                        FROM tw_approval_line wal
                        JOIN ir_model im ON wal.model_id = im.id
                        WHERE im.model = 'tw.checklist.tools'
                        ORDER BY wal.limit asc
                    ) wal ON wal.transaction_id = tct.id
                    LEFT JOIN res_groups group_check on wal.group_id = group_check.id
                    LEFT JOIN hr_employee he ON he.id = tct.pic_id 
                    WHERE tct.id {ids_clause}
                ),
                product_aggregates AS (
                    SELECT
                        checklist_id,
                        checklist_number,
                        pic_name,
                        category,
                        product_code,
                        product_name,
                        product_product_id,
                        location_name,
                        master_tool_id,
                        STRING_AGG(DISTINCT date, ', ') AS dates,
                        STRING_AGG(DISTINCT week, ', ') AS weeks,
                        STRING_AGG(
                            date || ': ' || state,
                            ', '
                        ) AS states_by_date,
                        STRING_AGG(
                            week || ': ' || state,
                            ', '
                        ) AS states_by_week,
                        STRING_AGG(DISTINCT group_checked || ': ' || checked_pic,
                            ', '
                        ) AS checked_by
                    FROM aggregated_states
                    GROUP BY checklist_id, checklist_number, pic_name, category, product_code, product_name, location_name, master_tool_id, product_product_id
                ),
                detail_aggregates AS (
                    SELECT
                        checklist_id,
                        checklist_number,
                        pic_name,
                        category,
                        dates,
                        weeks,
                        JSON_AGG(
                            JSON_BUILD_OBJECT(
                                'master_tool_id', master_tool_id,
                                'product_product_id', product_product_id,
                                'description', product_name,
                                'product_code', product_code,
                                'location_name', location_name,
                                'states_by_date', states_by_date,
                                'states_by_week', states_by_week
                            )
                        )
                        AS detail_checklist,
                        checked_by
                    FROM product_aggregates
                    GROUP BY checklist_id, checklist_number, pic_name, category, dates, weeks, checked_by
                )
                SELECT
                    checklist_id,
                    checklist_number AS ct_number,
                    pic_name,
                    category,
                    dates,
                    weeks,
                    detail_checklist,
                    checked_by
                FROM detail_aggregates
                ORDER BY ct_number
            """.format(ids_clause=ids_clause)

        self.env.cr.execute(query, (lang, lang))
        aggregated_data = self.env.cr.dictfetchall()

        product_ids = set()
        master_tool_ids = set()

        for data_item in aggregated_data:
            data_item['detail_checklist_list'] = data_item.get('detail_checklist') or []
            for detail in data_item['detail_checklist_list']:
                p_id = detail.get('product_product_id')
                m_id = detail.get('master_tool_id')
                if p_id and m_id:
                    product_ids.add(p_id)
                    master_tool_ids.add(m_id)

        lines_map = {}
        if product_ids and master_tool_ids:
            lines = self.env['tw.master.tools.line'].sudo().search([
                ('product_id', 'in', list(product_ids)),
                ('master_tools_id', 'in', list(master_tool_ids))
            ])
            for line in lines:
                key = (line.product_id.id, line.master_tools_id.id)
                if key not in lines_map:
                    lines_map[key] = line

        file_cache = {}

        for data_item in aggregated_data:
            for detail in data_item['detail_checklist_list']:
                line = lines_map.get((detail.get('product_product_id'), detail.get('master_tool_id')))
                fname = line.filename if line else False

                if fname and fname not in file_cache:
                    try:
                        file_cache[fname] = self.env['tw.config.files'].sudo().get_file(fname)
                    except Exception:
                        file_cache[fname] = False
                
                img_data = file_cache.get(fname)

                detail.update({
                    'master_tool_line_id': line.id if fname else False,
                    'filename': fname or False,
                    'has_photo': bool(img_data),
                    'image_data': img_data or False,
                    'image_mime': ('image/png' if fname.lower().endswith('.png') else 'image/jpeg') if img_data else False
                })


        return {
            'doc_ids': docids,
            'doc_model': 'tw.checklist.tools',
            'docs': aggregated_data,
            'Date': (datetime.now() + relativedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S"),
        }