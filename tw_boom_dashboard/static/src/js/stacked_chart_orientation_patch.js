/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { useEffect } from "@odoo/owl";
import { StackedColumnChart } from "@synconics_bi_dashboard/components/StackedColumnChart/StackedColumnChart";

// Add orientation prop support  
StackedColumnChart.props = {
    ...StackedColumnChart.props,
    orientation: { optional: true, type: String },
    data: { optional: true, type: Object },
    show_legend: { optional: true, type: Boolean },
};

// Store original methods
const superRenderStackedColumnChart = StackedColumnChart.prototype.render_stacked_column_chart;
const superSetup = StackedColumnChart.prototype.setup;

patch(StackedColumnChart.prototype, {
    setup() {
        superSetup.call(this);

        // Add reactivity to orientation prop for both dashboard and preview
        useEffect(
            () => {
                this.render_stacked_column_chart();
            },
            () => [this.props.orientation, this.props.data?.chart_orientation]
        );
    },

    async render_stacked_column_chart() {
        // Get orientation from direct prop OR from data object (preview mode)
        const orientation = this.props.orientation || this.props.data?.chart_orientation || 'vertical';
        console.log('StackedColumnChart orientation:', orientation);

        // If horizontal, we need to swap axes
        if (orientation === 'horizontal') {
            await this.render_horizontal_stacked_chart();
        } else {
            // Default vertical rendering
            await superRenderStackedColumnChart.apply(this, arguments);

            // Add legend after rendering if enabled
            this._addLegendIfNeeded();
        }
    },

    /**
     * Add legend to the chart if show_legend is enabled
     */
    _addLegendIfNeeded() {
        const showLegend = this.props.show_legend || this.props.data?.show_legend;

        if (showLegend && this.root) {
            // Find the chart container - in stacked charts it's the first child of the root container
            const chartContainer = this.root.container.children.values.find(
                (child) => child instanceof am5xy.XYChart
            );

            if (chartContainer && chartContainer.series.length > 0) {
                var legend = chartContainer.children.push(
                    am5.Legend.new(this.root, {
                        centerX: am5.p50,
                        x: am5.p50,
                        layout: this.root.horizontalLayout,
                    })
                );
                legend.data.setAll(chartContainer.series.values);
            }
        }
    },

    async render_horizontal_stacked_chart() {
        var data = this.props.recordSets;
        if (this.root) {
            this.root.dispose();
        }
        if (typeof data == "object" && !Array.isArray(data)) {
            this.state.isError = true;
            this.state.errorMessage = data.message;
            return;
        }

        this.state.isError = false;
        this.state.errorMessage = false;
        this.root = am5.Root.new("stacked_column_chart__" + this.props.chartId);
        const theme = this.themeMap[this.props.theme];
        this.root.setThemes([theme.new(this.root)]);

        const formatLabel = (text, maxLength = 15) => {
            if (!text) return text;
            if (typeof text !== "string") return text;
            if (text.length <= maxLength) return text;
            return text.substring(0, maxLength - 3) + "...";
        };

        // Apply formatting to data
        data = data.map((item) => ({
            ...item,
            category: formatLabel(item.category),
        }));

        // Create chart with HORIZONTAL layout (swapped axes)
        var chart = this.root.container.children.push(
            am5xy.XYChart.new(this.root, {
                panX: false,
                panY: false,
                wheelX: "panY",
                wheelY: "zoomY",
                paddingLeft: 0,
                layout: this.root.verticalLayout,
            }),
        );

        chart.set(
            "scrollbarY",
            am5.Scrollbar.new(this.root, {
                orientation: "vertical",
            }),
        );

        // Y-Axis is now Category (horizontal bars grow from left)
        var yRenderer = am5xy.AxisRendererY.new(this.root, {
            inversed: true,
            cellStartLocation: 0.1,
            cellEndLocation: 0.9,
            minorGridEnabled: true,
        });

        var yAxis = chart.yAxes.push(
            am5xy.CategoryAxis.new(this.root, {
                categoryField: "category",
                renderer: yRenderer,
                tooltip: am5.Tooltip.new(this.root, {}),
            }),
        );

        yRenderer.labels.template.setAll({
            paddingRight: 10,
        });

        yAxis.data.setAll(data);

        // X-Axis is now Value
        var xAxis = chart.xAxes.push(
            am5xy.ValueAxis.new(this.root, {
                min: 0,
                renderer: am5xy.AxisRendererX.new(this.root, {
                    strokeOpacity: 0.1,
                }),
            }),
        );

        var self = this;

        function makeSeries(name, fieldName) {
            var series = chart.series.push(
                am5xy.ColumnSeries.new(self.root, {
                    name: name,
                    stacked: true,
                    xAxis: xAxis,
                    yAxis: yAxis,
                    valueXField: fieldName,  // Changed from valueYField
                    categoryYField: "category",  // Changed from categoryXField
                }),
            );

            series.columns.template.setAll({
                tooltipText: "{name}, {categoryY}: {valueX}",
                tooltipX: am5.percent(90),
                height: am5.percent(80),
            });
            series.data.setAll(data);

            series.appear();

            series.columns.template.events.on("click", function (ev) {
                if (self.props.update_chart) {
                    self.props.update_chart(
                        parseInt(self.props.chartId),
                        "stackedcolumn_chart",
                        ev.target.dataItem.dataContext,
                    );
                }
            });

            series.bullets.push(function () {
                return am5.Bullet.new(self.root, {
                    sprite: am5.Label.new(self.root, {
                        text: "{valueX}",
                        fill: self.root.interfaceColors.get("alternativeText"),
                        centerY: am5.p50,
                        centerX: am5.p50,
                        populateText: true,
                    }),
                });
            });
        }

        let keys = Object.keys(data[0]).filter(
            (k) => k !== "category" && k !== "record_id" && k !== "isSubGroupBy",
        );
        for (var key = 0; key < keys.length; key++) {
            makeSeries(keys[key], keys[key]);
        }

        // Add legend if enabled
        const showLegend = this.props.show_legend || this.props.data?.show_legend;
        if (showLegend) {
            var legend = chart.children.push(
                am5.Legend.new(this.root, {
                    centerX: am5.p50,
                    x: am5.p50,
                    layout: this.root.horizontalLayout,
                })
            );
            legend.data.setAll(chart.series.values);
        }

        chart.appear(1000, 100);

        let exporting = am5plugins_exporting.Exporting.new(this.root, {
            filePrefix: "my_chart",
            dataSource: chart.series.getIndex(0),
        });
        this.root.events.once("frameended", () => {
            if (this.props.export) {
                this.props.export(exporting);
            }
        });
    }
});
