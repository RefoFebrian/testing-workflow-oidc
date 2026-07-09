/** @odoo-module */

import { Component, useState, onWillUpdateProps } from "@odoo/owl";

export class GreetingChart extends Component {
    setup() {
        this.state = useState({
            content: this.props.record.custom_content || this.props.record.dynamic_content || "Selamat Datang!",
        });

        onWillUpdateProps((nextProps) => {
            this.state.content = nextProps.record.custom_content || nextProps.record.dynamic_content || "Selamat Datang!";
        });
    }
}

GreetingChart.template = "tw_boom_dashboard.GreetingChart";
