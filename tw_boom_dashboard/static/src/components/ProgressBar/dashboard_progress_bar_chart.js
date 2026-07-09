/** @odoo-module */

import { Component, useState, onWillUpdateProps } from "@odoo/owl";

export class ProgressBarChart extends Component {
    setup() {
        const record = this.props.record || {};
        this.state = useState({
            percentage: record.percentage || 0,
            progressValue: record.progress_value || 0,
            targetValue: record.target_value || 100,
            progressColor: record.progress_color || "#4CAF50",
            progressBgColor: record.progress_bg_color || "#e0e0e0",
            labelFormat: record.progress_label_format || "percentage",
            showLabel: record.progress_show_label !== false,
            fontSize: record.font_size || "14",
            fontColor: record.font_color || "#333333",
            fontWeight: record.font_weight || "bold",
            fontStyle: record.font_style || "normal",
            fontFamily: record.font_family || "Arial",
            backgroundColor: record.background_color || "transparent",
            name: record.name || "",
        });

        onWillUpdateProps((nextProps) => {
            const rec = nextProps.record || {};
            this.state.percentage = rec.percentage || 0;
            this.state.progressValue = rec.progress_value || 0;
            this.state.targetValue = rec.target_value || 100;
            this.state.progressColor = rec.progress_color || "#4CAF50";
            this.state.progressBgColor = rec.progress_bg_color || "#e0e0e0";
            this.state.labelFormat = rec.progress_label_format || "percentage";
            this.state.showLabel = rec.progress_show_label !== false;
            this.state.fontSize = rec.font_size || "14";
            this.state.fontColor = rec.font_color || "#333333";
            this.state.fontWeight = rec.font_weight || "bold";
            this.state.fontStyle = rec.font_style || "normal";
            this.state.fontFamily = rec.font_family || "Arial";
            this.state.backgroundColor = rec.background_color || "transparent";
            this.state.name = rec.name || "";
        });
    }

    get containerStyle() {
        return `display: flex; flex-direction: column; justify-content: center; width: 100%; height: 100%; padding: 15px; box-sizing: border-box; background-color: ${this.state.backgroundColor}; border-radius: 10px; font-family: ${this.state.fontFamily};`;
    }

    get labelStyle() {
        return `font-size: ${this.state.fontSize}px; color: ${this.state.fontColor}; font-weight: ${this.state.fontWeight}; font-style: ${this.state.fontStyle}; margin-bottom: 8px;`;
    }

    get progressContainerStyle() {
        return `width: 100%; height: 24px; background-color: ${this.state.progressBgColor}; border-radius: 12px; overflow: hidden; position: relative;`;
    }

    get progressBarStyle() {
        const lightColor = this.adjustColor(this.state.progressColor, 20);
        return `width: ${this.state.percentage}%; height: 100%; background: linear-gradient(90deg, ${this.state.progressColor}, ${lightColor}); border-radius: 12px; transition: width 0.5s ease-in-out; display: flex; align-items: center; justify-content: flex-end; padding-right: 8px;`;
    }

    get progressLabelStyle() {
        const size = Math.max(parseInt(this.state.fontSize) - 2, 10);
        return `font-size: ${size}px; color: white; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);`;
    }

    get labelText() {
        switch (this.state.labelFormat) {
            case 'value':
                return this.formatNumber(this.state.progressValue);
            case 'value_target':
                return `${this.formatNumber(this.state.progressValue)} / ${this.formatNumber(this.state.targetValue)}`;
            case 'percentage':
            default:
                return `${this.state.percentage}%`;
        }
    }

    formatNumber(num) {
        if (typeof num !== 'number') return '0';
        return num.toLocaleString('id-ID');
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
}

ProgressBarChart.template = "tw_boom_dashboard.ProgressBarChart";
