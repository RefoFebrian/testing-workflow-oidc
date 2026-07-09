/** @odoo-module **/

import { FormDashboardPreviewComponent } from "@synconics_bi_dashboard/js/form_dashboard_preview";
import { patch } from "@web/core/utils/patch";

patch(FormDashboardPreviewComponent.prototype, {
    setup() {
        super.setup();
        const superUpdateRecordSets = this.updateRecordSets;

        // We need to patch handling of new fields in preparation of data
        // Currently base uses a monolithic 'useEffect' which is hard to hook into cleanly without re-writing.
        // However, it calls 'updateRecordSets' with prepared data. 

        // ALTERNATIVE: Patch 'updateRecordSets' and MERGE our new data fields from 'props.record.data'.
        // 'updateRecordSets' signature: (recordId, chart_type, name, data)
        this.updateRecordSets = async (recordId, chart_type, name, data) => {
            // Inject our new fields into 'data' before sending to backend
            if (this.props.record && this.props.record.data) {
                const recData = this.props.record.data;

                // Header styling fields
                data.header_font_size = recData.header_font_size;
                data.header_font_color = recData.header_font_color;
                data.header_font_weight = recData.header_font_weight;
                data.header_font_style = recData.header_font_style;
                data.font_weight_bold = recData.font_weight_bold;
                data.font_style = recData.font_style;
                data.font_family_id = recData.font_family_id;
                data.header_font_family_id = recData.header_font_family_id;

                // Progress Bar fields
                data.progress_source_type = recData.progress_source_type;
                data.progress_value_field_id = recData.progress_value_field_id;
                data.progress_target_field_id = recData.progress_target_field_id;
                data.progress_value_domain = recData.progress_value_domain;
                data.progress_target_domain = recData.progress_target_domain;
                data.progress_value_query = recData.progress_value_query;
                data.progress_target_query = recData.progress_target_query;
                data.progress_target_manual = recData.progress_target_manual;
                data.progress_color = recData.progress_color;
                data.progress_bg_color = recData.progress_bg_color;
                data.progress_label_format = recData.progress_label_format;
                data.progress_show_label = recData.progress_show_label;

                // Filter fields
                data.filter_type = recData.filter_type;
                data.filter_field_id = recData.filter_field_id;
                data.filter_model_id = recData.filter_model_id;
                data.filter_label = recData.filter_label;
                data.filter_placeholder = recData.filter_placeholder;
                data.filter_date_field_id = recData.filter_date_field_id;

                // KPI color fields
                data.kpi_data1_color = recData.kpi_data1_color;
                data.kpi_data2_color = recData.kpi_data2_color;

                // Chart orientation field
                data.chart_orientation = recData.chart_orientation;

                // List measure fields with custom fields (measure_color, label_name, measure_domain)
                // Override base mapping to include our custom fields
                if (recData.list_measure_ids && recData.list_measure_ids.records) {
                    data.list_measure_ids = recData.list_measure_ids.records
                        .filter((measure) => measure.data.list_measure_id)
                        .map((res) => {
                            return {
                                id: res.data.id,
                                list_measure_id: res.data.list_measure_id[0],
                                value_type: res.data.value_type,
                                label_name: res.data.label_name,
                                measure_domain: res.data.measure_domain,
                                measure_color: res.data.measure_color || '#000000',
                            };
                        });
                }
            }
            await superUpdateRecordSets.call(this, recordId, chart_type, name, data);
        }
    },
});
