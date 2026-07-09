# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging

from datetime import datetime
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

_MONTHS_AHEAD = 3

def _post_init_hook(env):
    """

    Strategy:
      1. Rename original → _old
      2. CREATE ... PARTITION BY RANGE (create_date) — NO primary key
      3. Create monthly partitions covering all existing data
      4. Create default partition (catch-all)
      5. Bulk-copy data from _old into the partitioned table
      6. Re-create indexes
      7. Drop _old
      
    Run the partitioning migration for both tw_api_log_detail and tw_api_log.
    Order matters: we do detail first, then header just in case.
    """
    
    # 1. Migrate Detail
    _partition_table(
        env=env,
        parent_table='tw_api_log_detail',
        additional_indexes=['api_log_id']
    )
    
    # 2. Migrate Header
    _partition_table(
        env=env,
        parent_table='tw_api_log',
        additional_indexes=[]
    )


def _partition_table(env, parent_table, additional_indexes):
    cr = env.cr
    old_table = f"{parent_table}_old"
    default_partition = f"{parent_table}_default"

    # ----- guard: skip if already partitioned -----
    cr.execute("""
        SELECT relkind FROM pg_catalog.pg_class
        WHERE relname = %s AND relnamespace = 'public'::regnamespace
    """, (parent_table,))
    row = cr.fetchone()
    if row and row[0] == 'p':          # 'p' = partitioned table
        _logger.info("Table %s is already partitioned — skipping migration.", parent_table)
        return

    _logger.info("Starting partitioning migration for %s …", parent_table)

    # ---- step 1: rename ----
    cr.execute(f"ALTER TABLE {parent_table} RENAME TO {old_table}")

    # ---- step 2: create partitioned table (NO PK) ----
    cr.execute(f"""
        CREATE TABLE {parent_table} (
            LIKE {old_table}
            INCLUDING DEFAULTS
        ) PARTITION BY RANGE (create_date)
    """)

    # ---- step 3: determine date range from existing data ----
    cr.execute(f"SELECT MIN(create_date), MAX(create_date) FROM {old_table}")
    min_date, max_date = cr.fetchone()

    if min_date and max_date:
        start = datetime(min_date.year, min_date.month, 1)
        end = datetime(max_date.year, max_date.month, 1) + relativedelta(months=1 + _MONTHS_AHEAD)

        current = start
        while current < end:
            next_month = current + relativedelta(months=1)
            partition_name = f"{parent_table}_{current.year}_{current.month:02d}"

            cr.execute(f"""
                CREATE TABLE {partition_name}
                PARTITION OF {parent_table}
                FOR VALUES FROM (%s) TO (%s)
            """, (current.strftime('%Y-%m-%d'), next_month.strftime('%Y-%m-%d')))

            _logger.info("Created partition %s", partition_name)
            current = next_month

    # ---- step 4: default partition ----
    cr.execute(f"""
        CREATE TABLE {default_partition}
        PARTITION OF {parent_table}
        DEFAULT
    """)

    # ---- step 5: migrate data ----
    _logger.info("Migrating data from %s to partitioned %s …", old_table, parent_table)
    cr.execute(f"INSERT INTO {parent_table} SELECT * FROM {old_table}")
    cr.execute(f"SELECT count(*) FROM {parent_table}")
    count = cr.fetchone()[0]
    _logger.info("Migrated %s rows into %s.", count, parent_table)

    # ---- step 6: re-create indexes ----
    cr.execute(f"CREATE INDEX idx_{parent_table}_id ON {parent_table} (id)")
    cr.execute(f"CREATE INDEX idx_{parent_table}_create_date ON {parent_table} (create_date)")
    for idx_field in additional_indexes:
        cr.execute(f"CREATE INDEX idx_{parent_table}_{idx_field} ON {parent_table} ({idx_field})")

    # ---- step 7: re-attach sequence and transfer ownership ----
    cr.execute(f"""
        SELECT pg_get_serial_sequence('{old_table}', 'id')
    """)
    seq = cr.fetchone()
    if seq and seq[0]:
        seq_name = seq[0]
        # 7a: Ensure parent and partitions use the sequence
        cr.execute(f"""
            ALTER TABLE {parent_table}
            ALTER COLUMN id SET DEFAULT nextval(%s::regclass)
        """, (seq_name,))

        # 7b: Transfer sequence ownership to the new parent table
        cr.execute(f"ALTER SEQUENCE {seq_name} OWNED BY {parent_table}.id")

        # 7c: Remove default from old table to break dependency
        cr.execute(f"ALTER TABLE {old_table} ALTER COLUMN id DROP DEFAULT")

        _logger.info("Re-attached sequence %s to %s.id and transferred ownership.", seq_name, parent_table)

    # ---- step 8: drop old table ----
    cr.execute(f"DROP TABLE {old_table}")
    _logger.info("Dropped %s. Migration complete.", old_table)
