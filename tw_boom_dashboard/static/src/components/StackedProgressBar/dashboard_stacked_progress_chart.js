/** @odoo-module */

import { Component, useState, onWillUpdateProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class StackedProgressBarChart extends Component {
    setup() {
        this.action = useService("action");
        const record = this.props.record || {};

        this.state = useState({
            // Group By Support
            isGrouped: record.is_grouped || false,
            groups: record.groups || [],
            // Single Bar Fallback
            segments: record.segments || [],
            total: record.total || 0,
            // Styling
            showLegend: record.show_legend !== false,
            showPercentage: record.show_percentage !== false,
            fontSize: record.font_size || "14",
            fontColor: record.font_color || "#333333",
            fontWeight: record.font_weight || "700",
            fontStyle: record.font_style || "normal",
            fontFamily: record.font_family || "Arial",
            backgroundColor: record.background_color || "transparent",
            model: record.model || "",
            name: record.name || "",
        });

        onWillUpdateProps((nextProps) => {
            const rec = nextProps.record || {};
            // Group By Support
            this.state.isGrouped = rec.is_grouped || false;
            this.state.groups = rec.groups || [];
            // Single Bar Fallback
            this.state.segments = rec.segments || [];
            this.state.total = rec.total || 0;
            // Styling
            this.state.showLegend = rec.show_legend !== false;
            this.state.showPercentage = rec.show_percentage !== false;
            this.state.fontSize = rec.font_size || "14";
            this.state.fontColor = rec.font_color || "#333333";
            this.state.fontWeight = rec.font_weight || "700";
            this.state.fontStyle = rec.font_style || "normal";
            this.state.fontFamily = rec.font_family || "Arial";
            this.state.backgroundColor = rec.background_color || "transparent";
            this.state.model = rec.model || "";
            this.state.name = rec.name || "";
        });
    }

    get containerStyle() {
        return `display: flex; flex-direction: column; width: 100%; height: 100%; padding: 15px; box-sizing: border-box; background-color: ${this.state.backgroundColor}; border-radius: 10px; font-family: ${this.state.fontFamily}; overflow-y: auto;`;
    }

    get titleStyle() {
        return `font-size: ${parseInt(this.state.fontSize) + 4}px; color: ${this.state.fontColor}; font-weight: ${this.state.fontWeight}; font-style: ${this.state.fontStyle}; margin-bottom: 12px;`;
    }

    get legendStyle() {
        return `display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 10px;`;
    }

    get progressContainerStyle() {
        return `width: 100%; height: 28px; background-color: #e0e0e0; border-radius: 14px; overflow: hidden; display: flex;`;
    }

    get groupContainerStyle() {
        return `display: flex; flex-direction: column; gap: 12px; flex: 1;`;
    }

    getGroupLabelStyle() {
        return `font-size: ${parseInt(this.state.fontSize)}px; color: ${this.state.fontColor}; font-weight: ${this.state.fontWeight}; margin-bottom: 4px;`;
    }

    getSegmentStyle(segment) {
        const lightColor = this.adjustColor(segment.color, 15);
        return `width: ${segment.percentage}%; height: 100%; background: linear-gradient(90deg, ${segment.color}, ${lightColor}); display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.3s ease;`;
    }

    getSegmentTextStyle() {
        return `font-size: ${Math.max(parseInt(this.state.fontSize) - 2, 10)}px; color: white; font-weight: ${this.state.fontWeight}; text-shadow: 0 1px 2px rgba(0,0,0,0.3);`;
    }

    getLegendBadgeStyle(color) {
        return `display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; background-color: ${color}22; border-radius: 12px; font-size: ${Math.max(parseInt(this.state.fontSize) - 2, 11)}px; font-weight: ${this.state.fontWeight}; font-style: ${this.state.fontStyle};`;
    }

    getLegendDotStyle(color) {
        return `width: 10px; height: 10px; border-radius: 50%; background-color: ${color};`;
    }

    adjustColor(hex, percent) {
        if (!hex || typeof hex !== 'string') return '#6CAF70';
        try {
            const num = parseInt(hex.replace('#', ''), 16);
            const amt = Math.round(2.55 * percent);
            const R = Math.min(255, (num >> 16) + amt);
            const G = Math.min(255, ((num >> 8) & 0x00FF) + amt);
            const B = Math.min(255, (num & 0x0000FF) + amt);
            return `#${(1 << 24 | R << 16 | G << 8 | B).toString(16).slice(1)}`;
        } catch (e) {
            return '#6CAF70';
        }
    }

    onSegmentClick(segment) {
        if (!this.state.model || !segment.domain) return;

        // Open list view with filtered domain
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: segment.name,
            res_model: this.state.model,
            views: [[false, 'list'], [false, 'form']],
            domain: segment.domain,
            target: 'new',
        });
    }
}

StackedProgressBarChart.template = "tw_boom_dashboard.StackedProgressBarChart";

