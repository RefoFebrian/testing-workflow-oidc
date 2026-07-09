/** @odoo-module **/
// Copied from MRP Module, for more information go the MRP Module

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { parseFloatTime } from "@web/views/fields/parsers";
import { useInputField } from "@web/views/fields/input_field_hook";
import { useRecordObserver } from "@web/model/relational_model/utils";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState, onWillUpdateProps, onWillStart, onWillDestroy } from "@odoo/owl";

function formatMinutes(value) {
    if (value === false) {
        return "";
    }
    const isNegative = value < 0;
    if (isNegative) {
        value = Math.abs(value);
    }
    let min = Math.floor(value);
    let sec = Math.round((value % 1) * 60);
    sec = `${sec}`.padStart(2, "0");
    min = `${min}`.padStart(2, "0");
    return `${isNegative ? "-" : ""}${min}:${sec}`;
}

export class WoTimer extends Component {
    static template = "tw_work_order.WoTimer";
    static props = {
        value: { type: Number },
        ongoing: { type: Boolean, optional: true },
    };
    static defaultProps = { ongoing: false };

    setup() {
        this.state = useState({
            // duration is expected to be given in minutes
            duration: this.props.value,
        });
        this.lastDateTime = Date.now();
        this.ongoing = this.props.ongoing;
        onWillStart(() => {
            if (this.ongoing) {
                this._runTimer();
                this._runSleepTimer();
            }
        });
        onWillUpdateProps((nextProps) => {
            const rerun = !this.ongoing && nextProps.ongoing;
            this.ongoing = nextProps.ongoing;
            if (rerun) {
                this.state.duration = nextProps.value;
                this._runTimer();
                this._runSleepTimer();
            }
        });
        onWillDestroy(() => clearTimeout(this.timer));
    }

    get durationFormatted() {
        return formatMinutes(this.state.duration);
    }

    _runTimer() {
        this.timer = setTimeout(() => {
            if (this.ongoing) {
                this.state.duration += 1 / 60;
                this._runTimer();
            }
        }, 1000);
    }

    //updates the time when the computer wakes from sleep mode
    _runSleepTimer() {
        this.timer = setTimeout(async () => {
            const diff = Date.now() - this.lastDateTime - 10000;
            if (diff > 1000) {
                this.state.duration += diff / (1000 * 60);
            }
            this.lastDateTime = Date.now();
            this._runSleepTimer();
        }, 10000);
    }
}

class WoTimerField extends Component {
    static template = "tw_work_order.WoTimerField";
    static components = { WoTimer };
    static props = standardFieldProps;

    setup() {
        this.orm = useService("orm");
        useInputField({
            getValue: () => this.durationFormatted,
            refName: "numpadDecimal",
            parse: (v) => parseFloatTime(v),
        });

        useRecordObserver(async (record) => {
            if (!this.props.record.model.useSampleModel && record.data.state_wo === "in_progress") {
                this.duration = await this.orm.call(
                    "tw.work.order",
                    "get_duration",
                    [this.props.record.resId]
                );
            } else {
                this.duration = record.data[this.props.name];
            }
        })

        onWillDestroy(() => clearTimeout(this.timer));
    }

    get durationFormatted() {
        if (this.props.record.data[this.props.name] != this.duration && this.props.record.dirty) {
            this.duration = this.props.record.data[this.props.name];
        }
        return formatMinutes(this.duration);
    }

    get ongoing() {
        return this.props.record.data.state_wo === "in_progress";
    }
}

export const woTimerField = {
    component: WoTimerField,
    supportedTypes: ["float"],
};

// Register a new widget, preventing override mrp_timer widget
registry.category("fields").add("tw_work_order_timer", woTimerField);
registry.category("formatters").add("tw_work_order_timer", formatMinutes);
