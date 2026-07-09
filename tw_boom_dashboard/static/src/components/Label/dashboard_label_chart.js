/** @odoo-module */

import { Component, useState, onWillUpdateProps } from "@odoo/owl";

export class LabelChart extends Component {
    setup() {
        this.state = useState({
            content: this.props.record.label_text || "",
            fontSize: this.props.record.font_size || "14",
            fontColor: this.props.record.font_color || "#000000",
            fontWeight: this.props.record.font_weight_bold || this.props.record.font_weight || 400,
            fontStyle: this.props.record.font_style || "normal",
            textAlign: this.props.record.text_align || "center",
            backgroundColor: this.props.record.background_color || "transparent",
            fontFamily: this.props.record.font_family || "Arial",
        });

        onWillUpdateProps((nextProps) => {
            this.state.content = nextProps.record.label_text || "";
            this.state.fontSize = nextProps.record.font_size || "14";
            this.state.fontColor = nextProps.record.font_color || "#000000";
            this.state.fontWeight = nextProps.record.font_weight_bold || nextProps.record.font_weight || 400;
            this.state.fontStyle = nextProps.record.font_style || "normal";
            this.state.textAlign = nextProps.record.text_align || "center";
            this.state.backgroundColor = nextProps.record.background_color || "transparent";
            this.state.fontFamily = nextProps.record.font_family || "Arial";
        });
    }

    get style() {
        return `
            display: flex;
            align-items: center;
            justify-content: ${this.getJustifyContent(this.state.textAlign)};
            width: 100%;
            height: 100%;
            font-size: ${this.state.fontSize}px;
            color: ${this.state.fontColor};
            font-weight: ${this.state.fontWeight};
            font-style: ${this.state.fontStyle};
            text-align: ${this.state.textAlign};
            background-color: ${this.state.backgroundColor};
            border-radius: 10px;
            padding: 10px;
            box-sizing: border-box;
            font-family: ${this.state.fontFamily};
        `;
    }

    getJustifyContent(align) {
        if (align === 'left') return 'flex-start';
        if (align === 'right') return 'flex-end';
        return 'center';
    }
}

LabelChart.template = "tw_boom_dashboard.LabelChart";
