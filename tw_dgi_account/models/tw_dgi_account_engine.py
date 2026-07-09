# -*- coding: utf-8 -*-

# 1: imports of python lib
import json

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, api
from odoo.exceptions import UserError as Warning

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwDgiAccountEngine(models.AbstractModel):
    _name = "tw.dgi.account.engine"
    _description = "DGI Account Engine for Request Payload Building"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    @api.model
    def build_payload_from_template(self, record, template):
        """
        Build a JSON payload from an Odoo record based on the provided template.

        :param record: The Odoo record (e.g., tw.dealer.sale.order or tw.work.order).
        :param template: The JSON template dictionary defining the structure.
        :return: A dictionary representing the built payload.
        """
        if not template:
            return {}

        return self._build_node(record, template)

    def _build_node(self, record, node):
        if isinstance(node, dict):
            # Cek apakah ini definisi array (contoh array handling untuk H23)
            # Misalnya convention: "_array_source": "order_line", "_item_template": {...}
            if "_array_source" in node and "_item_template" in node:
                return self._build_array(record, node)
            
            # Jika bukan array khusus, proses sebagai dictionary biasa
            result = {}
            for key, val in node.items():
                result[key] = self._build_node(record, val)
            return result
        elif isinstance(node, list):
            return [self._build_node(record, item) for item in node]
        elif isinstance(node, str):
            # Mencoba mengekstrak nilai dari record berdasarkan string mapping (misal: "partner_id.name")
            return self._extract_value_or_literal(record, node)
        else:
            # Tipe lain (int, float, bool) dikembalikan apa adanya
            return node

    def _extract_value_or_literal(self, record, mapping_str):
        """
        Extracts value from the record based on mapping_str (dot-notation supported).
        If the mapping_str is wrapped in quotes in the template or doesn't match any field, 
        it can be treated as a literal if required, but usually, it's safer to check if the field exists.
        
        Untuk membedakan field Odoo vs Literal String (seperti "Cash", "0"),
        kita cek apakah level pertama dari dot-notation ada di record._fields.
        Jika tidak ada, anggap sebagai string literal.
        """
        if not mapping_str:
            return ""
            
        parts = mapping_str.split('.')
        first_part = parts[0]
        
        # Check if the first part is a valid field on the current record
        if first_part not in record._fields:
            # Asumsi ini adalah string literal (misal: "Cash", "0", "Close")
            return mapping_str

        # Navigasi object record
        current_obj = record
        for part in parts:
            if not current_obj:
                return ""
                
            try:
                # Handle method or property
                if hasattr(current_obj, part):
                    val = getattr(current_obj, part)
                    # Jika relasi (Many2one dll), kita maju ke record berikutnya
                    # Kecuali ini part terakhir, kita kembalikan recordset/id sesuai kebutuhan, 
                    # Biasanya dipanggil dengan .name atau .default_code
                    if hasattr(val, '_name'): 
                        # Jika relasi tapi tidak ada properti lanjutan yang diminta, kita coba extract id atau name
                        if part == parts[-1]:
                            return val.display_name if val else ""
                        else:
                            current_obj = val
                    else:
                        # Value biasa
                        current_obj = val
                else:
                    return ""
            except Exception:
                return ""

        # Format datetimes/dates if necessary, or return as is (Odoo ORM handles simple types)
        # Jika hasil akhirnya adalah False/None Odoo, return empty string agar aman di JSON
        return current_obj if current_obj is not False and current_obj is not None else ""

    def _build_array(self, record, array_node):
        """
        Builds an array of objects based on a one2many/many2many field.
        """
        source_field = array_node.get("_array_source")
        item_template = array_node.get("_item_template")
        filter_domain = array_node.get("_filter") # optional filter, e.g. [('division', '=', 'Service')]
        
        if not source_field or source_field not in record._fields:
            return []
            
        lines = getattr(record, source_field)
        
        # Simple local filtering based on python eval if _filter is provided as string representation of domain list
        # For simplicity, if _filter is a dict mapping field name to expected value
        if filter_domain and isinstance(filter_domain, dict):
            for f_name, f_val in filter_domain.items():
                lines = lines.filtered(lambda l: getattr(l, f_name) == f_val)

        result = []
        for line in lines:
            result.append(self._build_node(line, item_template))
            
        return result
