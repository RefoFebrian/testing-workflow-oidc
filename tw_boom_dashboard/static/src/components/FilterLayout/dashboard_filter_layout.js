/** @odoo-module */

import { Component, useState, onWillUpdateProps, onMounted } from "@odoo/owl";

export class FilterLayout extends Component {
    setup() {
        const record = this.props.record || {};
        this.state = useState({
            filterType: record.filter_type || "employee",
            filterTechnicalName: record.filter_technical_name || "",
            filterLabel: record.filter_label || "Filter",
            filterPlaceholder: record.filter_placeholder || "Select...",
            filterOptions: record.filter_options || [],
            dateField: record.date_field || null,
            selectedValue: null,
            searchText: "",
            showDropdown: false,
            dateStart: record.filter_date_start_default || null,
            dateEnd: record.filter_date_end_default || null,
            fontSize: record.font_size || "14",
            fontColor: record.font_color || "#333333",
            fontFamily: record.font_family || "Arial",
            backgroundColor: record.background_color || "transparent",
        });

        // Emit filter change on mount if defaults are present
        // Use setTimeout to ensure parent (DashboardAmcharts) is mounted and listening
        onMounted(() => {
            if (this.state.dateStart || this.state.dateEnd) {
                setTimeout(() => {
                    this._emitFilterChange();
                }, 100);
            }
        });

        onWillUpdateProps((nextProps) => {
            const rec = nextProps.record || {};
            this.state.filterType = rec.filter_type || "employee";
            this.state.filterTechnicalName = rec.filter_technical_name || "";
            this.state.filterLabel = rec.filter_label || "Filter";
            this.state.filterPlaceholder = rec.filter_placeholder || "Select...";
            this.state.filterOptions = rec.filter_options || [];
            this.state.dateField = rec.date_field || null;
            this.state.dateStart = rec.filter_date_start_default || null;
            this.state.dateEnd = rec.filter_date_end_default || null;
            this.state.fontSize = rec.font_size || "14";
            this.state.fontColor = rec.font_color || "#333333";
            this.state.fontFamily = rec.font_family || "Arial";
            this.state.backgroundColor = rec.background_color || "transparent";
        });
    }

    get containerStyle() {
        return `display: flex; flex-direction: column; width: 100%; height: 100%; padding: 12px; box-sizing: border-box; background-color: ${this.state.backgroundColor}; border-radius: 10px; font-family: ${this.state.fontFamily};`;
    }

    get labelStyle() {
        return `font-size: ${this.state.fontSize}px; color: ${this.state.fontColor}; font-weight: 500; margin-bottom: 6px;`;
    }

    get inputStyle() {
        const size = Math.max(parseInt(this.state.fontSize) - 2, 12);
        return `font-size: ${size}px; font-family: ${this.state.fontFamily};`;
    }

    get filteredOptions() {
        const options = this.state.filterOptions || [];
        if (!this.state.searchText) {
            return options;
        }
        const search = this.state.searchText.toLowerCase();
        return options.filter((opt) =>
            opt && opt.name && opt.name.toLowerCase().includes(search)
        );
    }

    onSearchInput(ev) {
        this.state.searchText = ev.target.value;
        this.state.showDropdown = true;
    }

    onInputFocus() {
        this.state.showDropdown = true;
    }

    onInputBlur() {
        setTimeout(() => {
            this.state.showDropdown = false;
        }, 200);
    }

    selectOption(opt) {
        if (!opt) return;
        this.state.selectedValue = opt.id;
        this.state.searchText = opt.name;
        this.state.showDropdown = false;
        this._emitFilterChange();
    }

    clearFilter() {
        this.state.selectedValue = null;
        this.state.searchText = "";
        this.state.dateStart = null;
        this.state.dateEnd = null;
        this._emitFilterChange();
    }

    onDateStartChange(ev) {
        this.state.dateStart = ev.target.value;
        this._emitFilterChange();
    }

    onDateEndChange(ev) {
        this.state.dateEnd = ev.target.value;
        this._emitFilterChange();
    }

    onManualInputChange(ev) {
        this.state.searchText = ev.target.value;
        this._emitFilterChange();
    }

    _emitFilterChange() {
        const filterData = {
            filterType: this.state.filterType,
            filterTechnicalName: this.state.filterTechnicalName,
            dateField: this.state.dateField,
            value: this.state.selectedValue,
            dateStart: this.state.dateStart,
            dateEnd: this.state.dateEnd,
            textValue: this.state.searchText,
        };

        try {
            const el = this.el || (this.__owl__ && this.__owl__.bdom && this.__owl__.bdom.el);
            if (el) {
                const event = new CustomEvent('dashboard-filter-change', {
                    bubbles: true,
                    detail: filterData
                });
                el.dispatchEvent(event);
            }
        } catch (e) {
            console.warn('Could not emit filter change event:', e);
        }
    }
}

FilterLayout.template = "tw_boom_dashboard.FilterLayout";
