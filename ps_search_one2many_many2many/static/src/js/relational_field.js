/** @odoo-module **/


import { registry } from "@web/core/registry";
import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";

export class PsSearchOption extends X2ManyField {
    onInputKeyUp(event) {

        let value = event.currentTarget.value.toLowerCase();
        let rows = document.querySelectorAll(".o_list_table tr");

        rows.forEach((row, index) => {
            if (index === 0) return;
            let text = row.textContent.toLowerCase();
            let isMatch = text.includes(value);
            row.style.display = isMatch ? "" : "none";
        });
    }
}

PsSearchOption.template = "PsSearchOptionTemplate";

export const SearchOption = {
    ...x2ManyField,
    component: PsSearchOption,
};

registry.category("fields").add("search_section_and_note_one2many", SearchOption);
