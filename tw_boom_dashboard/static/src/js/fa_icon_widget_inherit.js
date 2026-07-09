/** @odoo-module **/

import { FaIconField } from "@synconics_bi_dashboard/js/fa_icon_widget";
import { patch } from "@web/core/utils/patch";

patch(FaIconField.prototype, {
    setup() {
        super.setup();
        // Add custom icons to the top of the list
        this.icons.unshift(
            "check-circle",
            "times-circle"
        );
    }
});
