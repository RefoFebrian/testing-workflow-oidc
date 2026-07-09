# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import os
import pytz
from datetime import date, datetime, time

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TWMftFilePPO(models.Model):
    _inherit = "tw.config.files"
    _description = "TW MFT File PPO"

    def _get_default_main_dealer_atpm_code(self):
        return self.env['res.company'].get_default_main_dealer_atpm_code()
    
    def _get_config_file(self, code):
        config_file_obj = self.env['tw.config.files'].search([
            ('active', '=', True),
            ('name', '=', code)
        ])
        if not config_file_obj:
            raise Warning(f"Warning!\nconfig files with Code {code} does not exists!")
        
        return config_file_obj
    
    def mft_generate_ppo_urgent(self):
        get_ppo_query = """
            SELECT
                nrfs.id AS nrfs_id,
                nrfs.urgent_po_number,
                'H2Z;'
                || TO_CHAR(nrfsl.urgent_po_date, 'DDMMYYYY') || ';'
                || 'URG;'
                || nrfsl.urgent_po_number || ';'
                || CAST(ROW_NUMBER() OVER () AS VARCHAR) || ';'
                || pt.name || ';'
                || CAST(nrfsl.qty AS VARCHAR) || ';'
                || TO_CHAR((DATE(nrfsl.urgent_po_date) + INTERVAL '10 day')::DATE, 'DDMMYYYY')
                || ';;;H2Z;'
                || COALESCE(REPLACE(b.name, 'Cabang', 'TDM'),'') || ';'
                || COALESCE(city.name,'') || ';'
                || COALESCE(kel.zip_code,'') || ';'
                || COALESCE(pt_unit.default_code,'') || ';'
                || COALESCE(lot.production_year,'') || ';'
                || COALESCE(b.code,'') || ';'
                || TO_CHAR(nrfsl.urgent_po_date, 'DDMMYYYY') || ';;'
                || COALESCE(b.mobile,'') || ';;;' AS datas
            FROM tw_nrfs nrfs
            JOIN tw_nrfs_line nrfsl ON nrfs.id = nrfsl.nrfs_id
            JOIN product_product pp ON nrfsl.product_sparepart_id = pp.id
            JOIN product_template pt ON pp.product_tmpl_id = pt.id
            JOIN res_partner p ON nrfs.branch_partner_id = p.id
            JOIN res_company b ON p.id = b.partner_id
            LEFT JOIN res_city city ON b.city_id = city.id
            LEFT JOIN res_sub_district kel ON b.sub_district_id = kel.id
            JOIN stock_lot lot ON nrfs.lot_id = lot.id
            JOIN product_product pp_unit ON lot.product_id = pp_unit.id
            JOIN product_template pt_unit ON pp_unit.product_tmpl_id = pt_unit.id
            WHERE nrfsl.is_urgent_po = True
            AND nrfsl.urgent_po_number IS NOT NULL
            AND nrfsl.urgent_po_date IS NOT NULL
            AND nrfs.is_urgent_ppo_mft = False
            AND nrfs.urgent_ppo_filename IS NULL
            AND nrfs.urgent_ppo_send_date IS NULL
            AND nrfs.is_send_to_ahm = True
        """
        self._cr.execute(get_ppo_query)
        po_ress = self._cr.dictfetchall()
        files_list = {}
        for x in po_ress:
            if x.get('datas', False):
                po_urg_no = str(x['urgent_po_number']).replace("/", "")
                name = f"AHM-H2Z-{po_urg_no}.PPO"
                value = str(x['datas']) + "\r\n"
                if not files_list.get(name, False):
                    files_list.update({name: ""})
                    self.env['tw.nrfs'].suspend_security().browse(x['nrfs_id']).write({'is_urgent_ppo_mft': True, 'urgent_ppo_filename': name, 'urgent_ppo_send_date': date.today()})
                files_list[name] += value
        if files_list:
            for k, v in files_list.items():
                config_obj = self._get_config_file('MFT-AHM')
                config_path = config_obj.local_path
                local_path = config_path + '/' + k
                f = open(local_path, "w+")
                f.write(v)
                f.close()

    def mft_generate_nrfs(self):
        get_nrfs_query = """
            SELECT
                nrfs.id,
                nrfs.act_completion_date,
                'H2Z;'
                || TO_CHAR(nrfs.nrfs_date, 'YYYYMMDD') || ';'
                || TRIM(emp.name) || ';'
                || pt.default_code || ';'
                || m_gj.value || ';'
                || m_sbb.value || ';'
                || lot.name || ';'
                || 'MH1' || lot.chassis_number || ';'
                || TO_CHAR(lot.receive_date, 'YYYYMMDD') || ';'
                || COALESCE(m_pu.value,'') || ';'
                || tsi.id_expedisi_ahm || ';'
                || pn.plate_number || ';'
                || COALESCE(nrfs.expedition_ship,'') || ';'
                || CASE
                        WHEN nrfsl.is_urgent_po = False OR nrfsl.is_urgent_po IS NULL THEN 'N;;'
                        WHEN nrfsl.is_urgent_po != False THEN CONCAT('Y;',nrfsl.urgent_po_number,';')
                   END
                || TO_CHAR(nrfs.est_completion_date, 'YYYYMMDD') || ';'
                || COALESCE(TO_CHAR(nrfs.act_completion_date, 'YYYYMMDD'),'') || ';'
                AS datas
            FROM tw_nrfs nrfs
            JOIN tw_nrfs_line nrfsl ON nrfs.id = nrfsl.nrfs_id
            JOIN hr_employee emp ON nrfs.examiner_id = emp.id
            JOIN product_product pp ON nrfsl.product_sparepart_id = pp.id
            JOIN product_template pt ON pp.product_tmpl_id = pt.id
            JOIN tw_nrfs_gejala_selection_rel gj_rel ON nrfsl.id = gj_rel.nrfs_line_id
            JOIN tw_selection m_gj ON gj_rel.gejala_id = m_gj.id
            JOIN tw_nrfs_penyebab_selection_rel sbb_rel ON nrfsl.id = sbb_rel.nrfs_line_id
            JOIN tw_selection m_sbb ON sbb_rel.penyebab_id = m_sbb.id
            JOIN stock_lot lot ON nrfs.lot_id = lot.id
            JOIN tw_stock_inbound tsi ON tsi.id = nrfs.stock_inbound_id
            JOIN tw_vehicle pn ON nrfs.vehicle_id = pn.id
            LEFT JOIN tw_selection m_pu ON nrfsl.handling_id = m_pu.id
            WHERE (nrfs.mft_nrfs = False OR nrfs.mft_nrfs IS NULL)
            AND nrfs.state IN ('confirmed','in_progress','done')
            AND nrfs.is_send_to_ahm = True
            ORDER BY nrfs.id
        """
        self._cr.execute(get_nrfs_query)
        nrfs_ress = self._cr.dictfetchall()
        # tanggal sekarang & jam sekarang
        tz = pytz.timezone(self.env.context.get('tz')) if self.env.context.get('tz') else pytz.utc
        now = pytz.utc.localize(datetime.now()).astimezone(tz)
        year_month = now.strftime('%y%m%d')
        complete_date = now.strftime('%y%m%d%H%M%S')
        filename = f'AHM-H2Z-{year_month}-{complete_date}.NRFS'
        value = ""
        ids_list = []
        done_ids_list = []
        for x in nrfs_ress:
            # check for NULL value
            if x.get('datas', False):
                # setup value
                value += str(x['datas']) + "\r\n"
                ids_list.append(x['id'])
                if x.get('act_completion_date', False):
                    done_ids_list.append(x['id'])
        # update history MFT
        nrfs_obj = self.env['tw.nrfs']
        for nrfs_id in list(set(ids_list)):
            nrfs_obj.suspend_security().browse(nrfs_id).write({
                'mft_nrfs_history_ids': [[0, 0, {
                    'nrfs_filename': filename,
                    'nrfs_send_date': date.today()
                }]]
            })
        # update status MFT
        for nrfs_id in list(set(done_ids_list)):
            nrfs_obj.suspend_security().browse(nrfs_id).write({'mft_nrfs': True})
        # send file
        if value:
            config_obj = self._get_config_file('MFT-AHM')
            config_path = config_obj.local_path
            local_path = config_path + '/' + filename
            f = open(local_path, "w+")
            f.write(value)
            f.close()
