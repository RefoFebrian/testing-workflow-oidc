# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import re

from datetime import datetime
from dateutil.relativedelta import relativedelta

# 3: imports of odoo
from odoo import api, fields, models
from odoo.exceptions import UserError

# 6: Import of unknown third party lib
_logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

_TABLE_HEADER = 'tw_api_log'
_TABLE_DETAIL = 'tw_api_log_detail'
_MONTHS_AHEAD = 3

# Matches both tw_api_log_2025_04 and tw_api_log_detail_2025_04
# as well as older y2025m04 formats.
_PARTITION_PATTERN = re.compile(
    r'^(tw_api_log(?:_detail)?)_(?:y)?(\d{4})[m_](\d{2})$'
)


class ApiLogPartition(models.Model):
    _name = "tw.api.log.partition"
    _description = "API Log Partition Manager"
    _order = "date_from desc"
    _rec_name = "name"

    # 8: fields
    name = fields.Char(string="Partition Name", readonly=True)
    partition_type = fields.Selection([
        ('header', 'API Log (Header)'),
        ('detail', 'API Log Detail (Lines)')
    ], string="Type", readonly=True)
    date_from = fields.Date(string="From", readonly=True)
    date_to = fields.Date(string="To", readonly=True)
    row_count = fields.Integer(string="Row Count", readonly=True)
    size_mb = fields.Float(string="Size (MB)", digits=(12, 2), readonly=True)
    is_default = fields.Boolean(string="Default Partition", readonly=True)

    # 10: constraints & sql constraints
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Partition name must be unique.'),
    ]

    # 13: action methods

    def action_sync_partitions(self):
        """
        Query pg_catalog to discover all child partitions of both
        tw_api_log and tw_api_log_detail and upsert them into this model.
        """
        cr = self.env.cr

        # Build a map of existing records by name
        existing = {rec.name: rec for rec in self.search([])}
        seen_names = set()

        tables_to_scan = [
            (_TABLE_HEADER, 'header'),
            (_TABLE_DETAIL, 'detail')
        ]

        for parent_table, p_type in tables_to_scan:
            # Fetch all child partitions for the current parent table
            cr.execute("""
                SELECT
                    child.relname                                                AS partition_name,
                    pg_get_expr(child.relpartbound, child.oid, true)             AS bound_expr,
                    pg_total_relation_size(child.oid)                            AS total_bytes
                FROM pg_catalog.pg_inherits  inh
                JOIN pg_catalog.pg_class     parent ON inh.inhparent = parent.oid
                JOIN pg_catalog.pg_class     child  ON inh.inhrelid  = child.oid
                WHERE parent.relname = %s
                ORDER BY child.relname
            """, (parent_table,))

            discovered = cr.fetchall()

            for partition_name, bound_expr, total_bytes in discovered:
                seen_names.add(partition_name)

                date_from, date_to, is_default = self._parse_bound_expr(
                    partition_name, bound_expr
                )

                # Get row count
                cr.execute(f'SELECT count(*) FROM "{partition_name}"')
                row_count = cr.fetchone()[0]

                vals = {
                    'name': partition_name,
                    'partition_type': p_type,
                    'date_from': date_from,
                    'date_to': date_to,
                    'row_count': row_count,
                    'size_mb': round(total_bytes / (1024 * 1024), 2),
                    'is_default': is_default,
                }

                if partition_name in existing:
                    existing[partition_name].write(vals)
                else:
                    self.create(vals)

        # Remove records whose partitions no longer exist
        stale = self.search([('name', 'not in', list(seen_names))])
        if stale:
            stale.unlink()

        return True

    def action_detach_and_drop(self):
        """Detach the partition from the parent table, then drop it."""
        self.ensure_one()
        if self.is_default:
            raise UserError("Cannot drop the default partition.")

        if self.partition_type == 'header':
            # Prevent dropping header if detail still exists for the same period
            detail_exists = self.search([
                ('partition_type', '=', 'detail'),
                ('date_from', '=', self.date_from),
                ('date_to', '=', self.date_to),
                ('is_default', '=', False)
            ], limit=1)
            
            if detail_exists:
                raise UserError(
                    f"Cannot drop the Header partition ({self.name}) while the corresponding "
                    f"Detail partition ({detail_exists.name}) still exists. "
                    f"Please drop the Detail partition first."
                )

        cr = self.env.cr
        parent_table = _TABLE_HEADER if self.partition_type == 'header' else _TABLE_DETAIL

        _logger.info("Detaching partition %s from %s …", self.name, parent_table)

        cr.execute(
            f'ALTER TABLE {parent_table} DETACH PARTITION "{self.name}"'
        )
        cr.execute(f'DROP TABLE IF EXISTS "{self.name}"')

        _logger.info("Dropped partition %s.", self.name)
        self.unlink()
        return True

    def action_ensure_future_partitions(self):
        """
        Create monthly partitions for the next N months if they
        do not exist yet. Called by cron or manually.
        """
        cr = self.env.cr
        today = fields.Date.context_today(self)
        current = datetime(today.year, today.month, 1)

        tables_to_scan = [
            (_TABLE_HEADER, 'header'),
            (_TABLE_DETAIL, 'detail')
        ]

        for _i in range(_MONTHS_AHEAD + 1):
            next_month = current + relativedelta(months=1)
            
            for parent_table, p_type in tables_to_scan:
                partition_name = (
                    f"{parent_table}_{current.year}_{current.month:02d}"
                )

                # Check if partition already exists
                cr.execute("""
                    SELECT 1 FROM pg_catalog.pg_class
                    WHERE relname = %s
                      AND relnamespace = 'public'::regnamespace
                """, (partition_name,))

                if not cr.fetchone():
                    cr.execute(f"""
                        CREATE TABLE "{partition_name}"
                        PARTITION OF {parent_table}
                        FOR VALUES FROM (%s) TO (%s)
                    """, (
                        current.strftime('%Y-%m-%d'),
                        next_month.strftime('%Y-%m-%d'),
                    ))
                    _logger.info("Created future partition %s", partition_name)

            current = next_month

        # Refresh the list
        self.action_sync_partitions()
        return True

    # 14: private methods

    @staticmethod
    def _parse_bound_expr(partition_name, bound_expr):
        """
        Parse the partition bound expression returned by PostgreSQL.

        Examples:
          'FOR VALUES FROM (''2025-03-01 00:00:00'') TO (''2025-04-01 00:00:00'')'
          'DEFAULT'

        Returns (date_from, date_to, is_default).
        """
        if bound_expr.strip().upper() == 'DEFAULT':
            return None, None, True

        # Match FROM ('<timestamp>') TO ('<timestamp>')
        match = re.search(
            r"FROM \('([^']+)'\) TO \('([^']+)'\)",
            bound_expr,
        )
        if match:
            date_from = fields.Date.to_date(match.group(1)[:10])
            date_to = fields.Date.to_date(match.group(2)[:10])
            return date_from, date_to, False

        # Fallback: try to infer from partition name
        name_match = _PARTITION_PATTERN.match(partition_name)
        if name_match:
            year, month = int(name_match.group(2)), int(name_match.group(3))
            date_from = datetime(year, month, 1).date()
            date_to = (datetime(year, month, 1) + relativedelta(months=1)).date()
            return date_from, date_to, False

        return None, None, False
