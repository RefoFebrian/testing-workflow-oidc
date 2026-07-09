/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { AreaChart } from "@synconics_bi_dashboard/components/AreaChart/AreaChart";
import { BarChart } from "@synconics_bi_dashboard/components/BarChart/BarChart";
import { ColumnChart } from "@synconics_bi_dashboard/components/ColumnChart/ColumnChart";
import { DoughnutChart } from "@synconics_bi_dashboard/components/DoughnutChart/DoughnutChart";
import { FunnelChart } from "@synconics_bi_dashboard/components/FunnelChart/FunnelChart";
import { PyramidChart } from "@synconics_bi_dashboard/components/PyramidChart/PyramidChart";
import { LineChart } from "@synconics_bi_dashboard/components/LineChart/LineChart";
import { PieChart } from "@synconics_bi_dashboard/components/PieChart/PieChart";
import { RadarChart } from "@synconics_bi_dashboard/components/RadarChart/RadarChart";
import { StackedColumnChart } from "@synconics_bi_dashboard/components/StackedColumnChart/StackedColumnChart";
import { RadialChart } from "@synconics_bi_dashboard/components/RadialChart/RadialChart";
import { ScatterChart } from "@synconics_bi_dashboard/components/ScatterChart/ScatterChart";
import { MapChart } from "@synconics_bi_dashboard/components/MapChart/MapChart";
import { MeterChart } from "@synconics_bi_dashboard/components/MeterChart/MeterChart";

const chartConfigs = [
    { comp: AreaChart, method: "render_area_chart" },
    { comp: BarChart, method: "render_bar_chart" },
    { comp: ColumnChart, method: "render_column_chart" },
    { comp: DoughnutChart, method: "render_doughnut_chart" },
    { comp: FunnelChart, method: "render_funnel_chart" },
    { comp: PyramidChart, method: "render_pyramid_chart" },
    { comp: LineChart, method: "render_line_chart" },
    { comp: PieChart, method: "render_pie_chart" },
    { comp: RadarChart, method: "render_radar_chart" },
    { comp: StackedColumnChart, method: "render_stackedcolumn_chart" },
    { comp: RadialChart, method: "render_radial_chart" },
    { comp: ScatterChart, method: "render_scatter_chart" },
    { comp: MapChart, method: "render_map_chart" },
    { comp: MeterChart, method: "render_meter_chart" },
];

chartConfigs.forEach(({ comp, method }) => {
    // 1. Patch static props to allow color_palette
    if (comp.props) {
        comp.props = {
            ...comp.props,
            color_palette: { optional: true, type: [String, Boolean] },
        };
    }

    // Capture original method
    const superChartMethod = comp.prototype[method];

    // 2. Patch prototype to apply colors during render
    patch(comp.prototype, {
        [method]() {
            const originalSetThemes = am5.Root.prototype.setThemes;
            const self = this;

            // Wrap global setThemes briefly to inject our custom palette
            am5.Root.prototype.setThemes = function (themes) {
                if (self.props.color_palette) {
                    const colorsStr = self.props.color_palette.split(',')
                        .map(c => c.trim())
                        .filter(c => c.startsWith('#'));

                    if (colorsStr.length > 0) {
                        const myTheme = am5.Theme.new(this);
                        const colors = colorsStr.map(c => am5.color(c));

                        // Rule for the ColorSet itself
                        myTheme.rule("ColorSet").setAll({
                            colors: colors,
                            reuse: true
                        });

                        // Ensure XYChart, PieChart, and PercentChart pick it up
                        const chartRule = {
                            colors: am5.ColorSet.new(this, {
                                colors: colors,
                                reuse: true
                            })
                        };
                        myTheme.rule("XYChart").setAll(chartRule);
                        myTheme.rule("PieChart").setAll(chartRule);
                        myTheme.rule("PercentChart").setAll(chartRule);
                        myTheme.rule("RadarChart").setAll(chartRule);

                        themes.push(myTheme);
                    }
                }
                return originalSetThemes.call(this, themes);
            };

            try {
                return superChartMethod.apply(this, arguments);
            } finally {
                // Restore global method
                am5.Root.prototype.setThemes = originalSetThemes;
            }
        }
    });
});
