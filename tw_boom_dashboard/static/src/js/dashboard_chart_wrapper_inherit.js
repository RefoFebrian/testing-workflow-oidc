/** @odoo-module **/

import { DashboardChartWrapper } from "@synconics_bi_dashboard/js/dashboard_chart_wrapper";
import { GreetingChart } from "../components/Greeting/dashboard_greeting_chart";
import { QuoteChart } from "../components/Quote/dashboard_quote_chart";
import { BirthdayChart } from "../components/Birthday/dashboard_birthday_chart";
import { LabelChart } from "../components/Label/dashboard_label_chart";
import { ProgressBarChart } from "../components/ProgressBar/dashboard_progress_bar_chart";
import { FilterLayout } from "../components/FilterLayout/dashboard_filter_layout";
import { StackedProgressBarChart } from "../components/StackedProgressBar/dashboard_stacked_progress_chart";
import { patch } from "@web/core/utils/patch";
import { onWillUpdateProps } from "@odoo/owl";

// Register components and props
DashboardChartWrapper.components = {
    ...DashboardChartWrapper.components,
    GreetingChart,
    QuoteChart,
    BirthdayChart,
    LabelChart,
    ProgressBarChart,
    FilterLayout,
    StackedProgressBarChart,
};

DashboardChartWrapper.props = {
    ...DashboardChartWrapper.props,
    color_palette: { optional: true, type: [String, Boolean] },
    dashboard_filters: { optional: true, type: Object },
    chart_orientation: { optional: true, type: [String, Boolean] },
    show_legend: { optional: true, type: Boolean },
};

const superSetup = DashboardChartWrapper.prototype.setup;
const superUpdateRecordSets = DashboardChartWrapper.prototype.update_record_sets;

patch(DashboardChartWrapper.prototype, {
    setup() {
        // Store current dashboard filters (stringified) for change detection
        this.currentDashboardFilters = JSON.stringify(this.props.dashboard_filters || {});
        this._pendingFilters = null;

        onWillUpdateProps((nextProps) => {
            // Detect dashboard_filters change and trigger data reload
            const nextFilters = nextProps.dashboard_filters || {};
            const nextFiltersStr = JSON.stringify(nextFilters);

            if (this.currentDashboardFilters !== nextFiltersStr) {
                const chartId = nextProps.chartId || this.props.chart?.id || this.state.chartId;
                console.log(`### WRAPPER (${chartId}): Detected filter change - reloading data`, nextFilters);

                this.currentDashboardFilters = nextFiltersStr;
                this._pendingFilters = nextFilters; // Sync for both my call and base call

                if (chartId && this.state.chart_type) {
                    this.update_record_sets(chartId, this.state.chart_type, false, this.state.name, undefined, nextFilters);
                }
            }
        });

        superSetup.call(this);
        this.state.color_palette = this.props.color_palette || false;
        this.state.header_font_size = 22;
        this.state.header_font_color = false;
        this.state.header_font_weight = 700;
        this.state.header_font_style = 'normal';
        this.state.font_weight_bold = 700;
        this.state.font_style = 'normal';
        this.state.font_family = 'Arial';
        this.state.header_font_family = 'Arial';
        this.state.chart_orientation = this.props.chart_orientation || 'vertical';
        this.state.show_legend = this.props.show_legend || false;
    },

    async update_record_sets(recordId, chart_type, isDirty, name, data, dashboard_filters) {
        // Prepare extra_action with dashboard_filters
        const extra_action = {};

        // Priority: Passed arg > Pending filters > Current Props
        const filters = dashboard_filters || this._pendingFilters || this.props.dashboard_filters || {};

        // Explicitly include dashboard_filters key if it exists in source (even if empty)
        // This is crucial for the backend reset logic
        extra_action.dashboard_filters = filters;

        console.log(`### WRAPPER (${recordId}): Calling get_chart_data with filters:`, filters);

        let recordSets = await this.orm.call(
            "dashboard.chart",
            "get_chart_data",
            [parseInt(recordId)],
            {
                chart_type,
                name,
                isDirty,
                data,
                extra_action
            },
        );

        // KPI Error Handling from base
        if (
            ["kpi", "tile"].includes(chart_type) &&
            typeof recordSets === "object" &&
            recordSets !== null &&
            !Array.isArray(recordSets) &&
            "type" in recordSets
        ) {
            this.state.isKpiError = true;
        } else {
            this.state.isKpiError = false;
        }
        this.state.recordSets = recordSets;

        // Extract font CSS values from recordSets (which come from get_chart_data)
        if (recordSets && !this.state.isKpiError) {
            this.state.font_family = recordSets.font_family || 'Arial';
            this.state.header_font_family = recordSets.header_font_family || 'Arial';
            console.log('Font families set:', {
                font_family: this.state.font_family,
                header_font_family: this.state.header_font_family
            });
        }

        // Color Palette Logic (Merged from base + inherit)
        let chart_data = await this.orm.searchRead(
            "dashboard.chart",
            [["id", "=", parseInt(recordId)]],
            ["background_color", "color_palette", "header_font_size",
                "header_font_color", "header_font_weight", "header_font_style",
                "font_weight_bold", "font_style", "chart_orientation",
                "filter_date_start_default", "filter_date_end_default"],
        );
        if (chart_data.length) {
            this.state.background_color = chart_data[0].background_color;
            this.state.color_palette = chart_data[0].color_palette;
            this.state.header_font_size = chart_data[0].header_font_size;
            this.state.header_font_color = chart_data[0].header_font_color;
            this.state.header_font_weight = chart_data[0].header_font_weight;
            this.state.header_font_style = chart_data[0].header_font_style;
            this.state.font_weight_bold = chart_data[0].font_weight_bold;
            this.state.font_style = chart_data[0].font_style;
            this.state.chart_orientation = chart_data[0].chart_orientation || 'vertical';
        }
    }
});
