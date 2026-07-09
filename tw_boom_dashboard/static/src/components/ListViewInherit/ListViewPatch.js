/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ListView } from "@synconics_bi_dashboard/components/ListView/ListView";

patch(ListView.prototype, {
    /**
     * @override
     * Patching setup to override openRecords for better navigation
     */
    setup() {
        super.setup();

        // Override openRecords for better navigation
        this.openRecords = async (ev, currentIds) => {
            this.action.doAction({
                type: "ir.actions.act_window",
                name: this.state.chartName,
                res_model: this.state.dataModel,
                views: [[false, "list"], [false, "form"]],
                domain: [["id", "in", Object.values(currentIds)]],
                target: "current",
            });
        };
    }
});
