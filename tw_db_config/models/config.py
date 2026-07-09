# -*- coding: utf-8 -*-
import psycopg2


class DictCursor(psycopg2.extensions.cursor):
    """A cursor that returns rows as dictionaries"""

    def __init__(self, *args, **kwargs):
        super(DictCursor, self).__init__(*args, **kwargs)
        self._row_dict = None

    def dictfetchall(self):
        """Fetch all rows as a list of dictionaries"""
        desc = self.description
        return [
            dict(zip([col[0] for col in desc], row))
            for row in self.fetchall()
        ]

    def dictfetchone(self):
        """Fetch one row as a dictionary"""
        desc = self.description
        row = self.fetchone()
        if row:
            return dict(zip([col[0] for col in desc], row))
        return None