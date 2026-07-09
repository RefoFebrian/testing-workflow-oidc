# 1: imports of python lib
from datetime import datetime
import logging
try:
    import simplejson as json
except ImportError:
    import json
_logger = logging.getLogger(__name__)

# 2: import of known third party lib
from odoo.addons.tw_api.controllers.main import invalid_response, valid_response
from odoo.addons.rest_api.controllers.main import check_valid_token

# 3:  imports of odoo
from odoo import http

# 4:  imports from odoo modules
from odoo.http import request

# 5: local imports

# 6: Import of unknown third party lib


class ControllerREST(http.Controller):

    @http.route('/api/approval/<version>/get_waiting_approval', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_waiting_approval(self, version, **params):
        try:
            user_obj = request.env['res.users'].sudo().browse(request.session.uid)

            limit = int(params.get('limit', 10))
            offset = int(params.get('offset', 0))

            company_ids_str = str(tuple(user_obj.company_ids.ids)).replace(',)', ')')
            query = f"""
                SELECT DISTINCT
                    al.id,
                    al.transaction_no,
                    al.transaction_id,
                    im.model,
                    ac.name as form_name,
                    rc.name as branch,
                    al.division,
                    al.value,
                    TO_CHAR(al.create_date, 'YYYY-MM-DD HH24:MI:SS') as date,
                    al.info,
                    (SELECT COUNT(DISTINCT al2.transaction_id)
                     FROM tw_approval_line al2
                     INNER JOIN res_groups_users_rel rgur2 ON al2.group_id = rgur2.gid
                     WHERE al2.state = 'approved'
                       AND al2.is_must_approve = True
                       AND rgur2.uid = {user_obj.id}
                       AND al2.company_id IN {company_ids_str}) as approved_count
                FROM tw_approval_line al
                LEFT JOIN ir_model im ON al.model_id = im.id
                LEFT JOIN tw_approval_config ac ON al.config_id = ac.id
                LEFT JOIN res_company rc ON al.company_id = rc.id
                INNER JOIN res_groups_users_rel rgur ON al.group_id = rgur.gid
                WHERE al.state = 'open'
                    AND al.is_must_approve = True
                    AND rgur.uid = {user_obj.id}
                    AND al.company_id IN {company_ids_str}
                ORDER BY al.id DESC
                LIMIT {limit} OFFSET {offset}
            """
            request._cr.execute(query)
            data = request._cr.dictfetchall()
            
            # Extract approved_count from first row (same value for all rows)
            approved_count = data[0]['approved_count'] if data else 0
            
            return valid_response(200, {
                'waiting_approvals': data,
                'approved_count': approved_count
            })
        except Exception as e:
            return invalid_response(500, 'Internal Server Error', str(e))

    @http.route('/api/approval/<version>/get_approval_detail', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_approval_info(self, version, **params):
        try:
            id = params.get('id')
            if not id:
                return invalid_response(400, 'Parameter is missing', 'Parameter id is required')

            def clean_val(v):
                if not v: return v
                if isinstance(v, dict):
                    return v.get('en_US') or next(iter(v.values()), v)
                if isinstance(v, str) and v.startswith('{') and "'en_US':" in v:
                    try:
                        import ast
                        d = ast.literal_eval(v)
                        if isinstance(d, dict):
                            return d.get('en_US') or next(iter(d.values()), v)
                    except:
                        pass
                return v

            # 1. Get info for the specific line to find the transaction
            query_base = f"""
                SELECT al.transaction_id, al.model_id, im.model, al.transaction_no
                FROM tw_approval_line al
                LEFT JOIN ir_model im ON al.model_id = im.id
                WHERE al.id = {int(id)}
            """
            request._cr.execute(query_base)
            base_info = request._cr.dictfetchone()

            if not base_info:
                return invalid_response(404, 'Data Not Found', 'Approval line not found')

            # 2. Get all lines for this transaction (the matrix/history)
            query_matrix = f"""
                SELECT 
                    al.id,
                    rg.name as group_name,
                    rp.name as approver_name,
                    al.state,
                    al.value,
                    al.limit,
                    al.division,
                    TO_CHAR(al.create_date, 'YYYY-MM-DD HH24:MI:SS') as date,
                    al.reason,
                    al.info,
                    al.is_must_approve,
                    al.is_mandatory_approve
                FROM tw_approval_line al
                LEFT JOIN res_groups rg ON al.group_id = rg.id
                LEFT JOIN res_users ru ON al.approver_id = ru.id
                LEFT JOIN res_partner rp ON ru.partner_id = rp.id
                WHERE al.transaction_id = {base_info['transaction_id']}
                    AND al.model_id = {base_info['model_id']}
                ORDER BY al.id ASC
            """
            request._cr.execute(query_matrix)
            matrix = request._cr.dictfetchall()
            
            # Clean matrix results
            for m in matrix:
                for key in m:
                    m[key] = clean_val(m[key])
            
            # 3. Get dynamic record info using SQL
            model_name = base_info['model']
            record_id = base_info['transaction_id']
            table_name = model_name.replace('.', '_')
            
            # Define a list of potential fields to fetch - this can be expanded based on common fields across models
            potential_fields = [
                'company_id', 'partner_id', 'supplier_id', 'dealer_id', 'division', 
                'date', 'tanggal', 'create_date', 'amount', 'value', 'total', 'periode', 
                'description', 'memo', 'journal_id', 'credit_limit_unit', 
                'part_hotline', 'service_advisor_id', 
                'mechanic_id', 'alasan_ke_ahass', 'koprol_code', 'cetak_kwitansi',
                'name','state','origin','reference','user_id','employee_id',
                'note', 'account_id'
            ]
            
            # Step 1: Get field metadata (labels, types, relations)
            query_meta = """
                SELECT name, field_description as label, ttype, relation
                FROM ir_model_fields
                WHERE model = %s AND name = ANY(%s)
            """
            request._cr.execute(query_meta, (model_name, potential_fields))
            meta_list = request._cr.dictfetchall()

            if not meta_list:
                return valid_response(200, {
                    'record_info': [{"name": "Nomor Transaksi", "value": base_info['transaction_no']}],
                    'approval_matrix': matrix
                })
            
            meta_map = {m['name']: m for m in meta_list}
            ordered_fields = [f for f in potential_fields if f in meta_map]
            
            # Step 2: Identify which related tables have a 'name' column for many2one display
            rel_tables = list(set([m['relation'].replace('.', '_') for m in meta_list if m['ttype'] == 'many2one' and m['relation']]))
            tables_with_name = []
            if rel_tables:
                query_cols = "SELECT DISTINCT table_name FROM information_schema.columns WHERE table_name = ANY(%s) AND column_name = 'name'"
                request._cr.execute(query_cols, (rel_tables,))
                tables_with_name = [r['table_name'] for r in request._cr.dictfetchall()]
            
            # Step 3: Fetch Selection labels
            query_sel = """
                SELECT f.name as field_name, s.value, s.name as label
                FROM ir_model_fields_selection s
                JOIN ir_model_fields f ON s.field_id = f.id
                WHERE f.model = %s AND f.name = ANY(%s)
            """
            request._cr.execute(query_sel, (model_name, ordered_fields))
            sel_list = request._cr.dictfetchall()
            sel_map = {(s['field_name'], s['value']): s['label'] for s in sel_list}
            
            # Step 4: Construct and execute the main data query
            select_parts = []
            joins = []
            for i, field in enumerate(ordered_fields):
                m = meta_map[field]
                if m['ttype'] == 'many2one' and m['relation']:
                    rel_table = m['relation'].replace('.', '_')
                    if rel_table in tables_with_name:
                        alias = f"r{i}"
                        select_parts.append(f"{alias}.name as {field}_val")
                        joins.append(f"LEFT JOIN {rel_table} {alias} ON {table_name}.{field} = {alias}.id")
                    else:
                        select_parts.append(f"{table_name}.{field}::text as {field}_val")
                else:
                    select_parts.append(f"{table_name}.{field}::text as {field}_val")
            
            final_query = f"SELECT {', '.join(select_parts)} FROM {table_name} {' '.join(joins)} WHERE {table_name}.id = %s"
            request._cr.execute(final_query, (record_id,))
            record_values = request._cr.dictfetchone()
            
            if not record_values:
                 return invalid_response(404, 'Data Not Found', 'Transaction record not found')

            # Step 5: Format the final response
            record_info = []
            record_info.append({
                "name": "Nomor Transaksi",
                "value": base_info['transaction_no']
            })
            
            for field in ordered_fields:
                val = record_values.get(f"{field}_val")
                if val is None or val == 'None' or val == '':
                    continue
                
                m = meta_map[field]
                # Special handling for selection labels
                if m['ttype'] == 'selection':
                    val = sel_map.get((field, val), val)
                
                record_info.append({
                    "name": clean_val(m['label']),
                    "value": clean_val(str(val))
                })

            return valid_response(200, {
                'record_info': record_info,
                'approval_matrix': matrix
            })
        except Exception as e:
            return invalid_response(500, 'Internal Server Error', str(e))

    @http.route('/api/approval/<version>/post_approve', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_approve(self, version, **post):
        uid = request.session.uid

        # Support both single line_id and multiple line_ids
        line_ids = post.get('line_ids', [])
        if not line_ids and post.get('line_id'):
            line_ids = [post.get('line_id')]
        
        if not line_ids:
            info = "Mandatory request in body: line_id or line_ids!"
            error = "Missing mandatory fields"
            _logger.error(info)
            return invalid_response(400, error, info)

        # Convert to list of integers
        try:
            line_ids = [int(lid) for lid in (line_ids if isinstance(line_ids, list) else [line_ids])]
        except:
            info = "Format line_id/line_ids Tidak Sesuai"
            error = "format_line_id_tidak_sesuai"
            _logger.error(info)
            return invalid_response(400, error, info)

        results = []
        success_count = 0
        failed_count = 0

        try:
            for line_id in line_ids:
                result = {
                    'line_id': line_id,
                    'status': 'failed',
                    'message': ''
                }
                
                try:
                    query_line = f"""
                        SELECT al.id, al.state, al.transaction_id, im.model,
                        CASE WHEN rgur.uid IS NOT NULL THEN True ELSE False END as is_mygroup
                        FROM tw_approval_line al
                        LEFT JOIN ir_model im ON al.model_id = im.id
                        LEFT JOIN res_groups_users_rel rgur ON al.group_id = rgur.gid AND rgur.uid = {uid}
                        WHERE al.id = {line_id}
                    """
                    request._cr.execute(query_line)
                    line = request._cr.dictfetchone()

                    if not line:
                        result['message'] = "Approval line not found"
                        results.append(result)
                        failed_count += 1
                        continue
                        
                    if line['state'] != 'open':
                        result['message'] = f"Approval line is already {line['state']}"
                        results.append(result)
                        failed_count += 1
                        continue

                    if not line['is_mygroup']:
                        result['message'] = "You do not have permission to approve this line"
                        results.append(result)
                        failed_count += 1
                        continue

                    model_name = line['model']
                    trx_id = line['transaction_id']
                    trx = request.env[model_name].sudo().browse(trx_id)
                    
                    if not trx.exists():
                        result['message'] = f"Transaction {model_name} with ID {trx_id} not found"
                        results.append(result)
                        failed_count += 1
                        continue

                    approval_status = request.env['tw.approval.matrix'].sudo().approve(trx, user_id=uid)
                    
                    if approval_status == 0:
                        result['message'] = "You do not have permission to approve this transaction at this stage"
                        results.append(result)
                        failed_count += 1
                        continue
                    
                    if approval_status == 1:
                        table_name = model_name.replace('.', '_')
                        query_update = f"UPDATE {table_name} SET approval_state = 'approved' WHERE id = {trx_id}"
                        request._cr.execute(query_update)
                        
                        query_check = f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}' AND column_name = 'state'"
                        request._cr.execute(query_check)
                        if request._cr.fetchone():
                            request._cr.execute(f"UPDATE {table_name} SET state = 'approved' WHERE id = {trx_id}")
                    
                    result['status'] = 'success'
                    result['message'] = 'Approved'
                    result['approval_status'] = approval_status
                    success_count += 1
                    
                except Exception as e:
                    result['message'] = str(e)
                    failed_count += 1
                
                results.append(result)

            return valid_response(200, {
                'summary': {
                    'total': len(line_ids),
                    'success': success_count,
                    'failed': failed_count
                },
                'details': results
            })
            
        except Exception as e:
            request._cr.rollback()
            info = str(e)
            error = "Internal Server Error"
            _logger.error(info)
            return invalid_response(500, error, info)

    @http.route('/api/approval/<version>/post_reject', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_reject(self, version, **post):
        try:
            post = json.loads(request.httprequest.get_data(as_text=True))
            line_id = post.get('line_id')
            reason = post.get('reason')
            uid = request.session.uid
            
            if not line_id or not reason:
                return invalid_response(400, 'Parameter is missing', 'Parameters line_id and reason are required')
            
            query_line = f"""
                SELECT al.id, al.state, al.transaction_id, im.model,
                CASE WHEN rgur.uid IS NOT NULL THEN True ELSE False END as is_mygroup
                FROM tw_approval_line al
                LEFT JOIN ir_model im ON al.model_id = im.id
                LEFT JOIN res_groups_users_rel rgur ON al.group_id = rgur.gid AND rgur.uid = {uid}
                WHERE al.id = {int(line_id)}
            """
            request._cr.execute(query_line)
            line = request._cr.dictfetchone()

            if not line:
                return invalid_response(400, 'Data Not Found', 'Approval line not found')

            if not line['is_mygroup']:
                return invalid_response(400, 'Unauthorized', 'You do not have permission to reject this line')

            model_name = line['model']
            trx_id = line['transaction_id']
            trx = request.env[model_name].sudo().browse(trx_id)
            
            if not trx.exists():
                return invalid_response(400, 'Data Not Found', f'Transaction {model_name} with ID {trx_id} not found')

            status = request.env['tw.approval.matrix'].sudo().reject(trx, reason, user_id=uid)
            if status == 1:
                table_name = model_name.replace('.', '_')
                query_update = f"UPDATE {table_name} SET approval_state = 'rejected', state = 'draft' WHERE id = {trx_id}"
                request._cr.execute(query_update)
                return valid_response(200, {'status': 'success'})
            else:
                return invalid_response(400, 'Failed', 'Rejection failed or you do not have permission')
                
        except Exception as e:
            request._cr.rollback()
            return invalid_response(500, 'Internal Server Error', str(e))
