/** @odoo-module **/

import { Component, useState, useEffect, markup } from "@odoo/owl";

export class KpiLayoutSix extends Component {
    static template = "tw_boom_dashboard.KpiLayoutSix";
    static props = {
        data: Object,
    };

    setup() {
        this.state = useState({
            data: this.props.data,
            kpi_icon: "",
        });
        useEffect(
            () => {
                this.state.data = this.props.data;
                if (this.state.data && this.state.data.default_icon) {
                    this.state.kpi_icon = markup(this.state.data.default_icon);
                }
            },
            () => [this.props.data],
        );
    }
}
