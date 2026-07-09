import { patch } from "@web/core/utils/patch";
import { DateTimePicker } from "@web/core/datetime/datetime_picker";
import { today } from "@web/core/l10n/dates";

patch(DateTimePicker.prototype, {
    get todayButtonLabel() {
        return this.props.type === "datetime" ? "Now" : "Today";
    },
    selectToday() {
        const valueIndex = this.props.focusedDateIndex || 0;
        let value = today();

        if (this.props.type === "datetime") {
            const now = luxon.DateTime.local();
            let hour = now.hour;
            let minute = now.minute;
            let second = now.second;

            const rounding = this.props.rounding !== undefined ? this.props.rounding : 5;
            if (rounding > 1) {
                minute = Math.round(minute / rounding) * rounding;
                if (minute >= 60) {
                    minute = 0;
                    hour = (hour + 1) % 24;
                }
            }

            const timeValue = [hour, minute, second];
            if (this.is12HourFormat) {
                timeValue[0] = hour % 12;
            }
            if (this.meridiems) {
                timeValue.push(hour >= 12 ? "PM" : "AM");
            }

            const newTimeValues = [...this.state.timeValues];
            newTimeValues[valueIndex] = timeValue.map(String);
            this.state.timeValues = newTimeValues;
            value = now;
        }

        this.validateAndSelect(value, valueIndex, "date");
    }
});
