/** @odoo-module */

import { Component, useState, onWillUpdateProps } from "@odoo/owl";

export class QuoteChart extends Component {
    setup() {
        this.state = useState({
            content: "",
            author: "",
        });
        this.updateState(this.props);
        onWillUpdateProps((nextProps) => {
            this.updateState(nextProps);
        });
    }

    updateState(props) {
        this.state.content = props.record.custom_content || props.record.dynamic_content || "No quote for today.";
        this.state.author = props.record.custom_author || props.record.dynamic_author || "";
    }
}

QuoteChart.template = "tw_boom_dashboard.QuoteChart";
