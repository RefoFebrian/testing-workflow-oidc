/** @odoo-module */

import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";

class BirthdayDialog extends Component {
    static template = "tw_boom_dashboard.BirthdayDialog";
    static components = { Dialog };
    static props = {
        title: { type: String },
        birthdayData: { type: Array },
        close: { type: Function },
    };
}

export class BirthdayChart extends Component {
    setup() {
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        const label = this.props.record.is_birthday && this.props.record.birthday_message
            ? this.props.record.birthday_message
            : "Employee's Birthday";
        this.state = useState({
            label: label
        });
    }

    async onClick() {
        const result = await this.orm.call("tw.boom.task", "get_birthdays_only", []);
        const birthdayData = result.other_birthday || [];

        this.dialog.add(BirthdayDialog, {
            title: "Born today!",
            birthdayData: birthdayData,
        });
    }
}

BirthdayChart.template = "tw_boom_dashboard.BirthdayChart";
