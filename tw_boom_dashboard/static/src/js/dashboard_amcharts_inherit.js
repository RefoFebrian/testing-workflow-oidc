/** @odoo-module **/

import { DashboardAmcharts } from "@synconics_bi_dashboard/js/dashboard_amcharts";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation"; // Standard translation import
const { Component, onWillStart } = owl;

// Define BirthdayDialog locally since it's small and used only here
class BirthdayDialog extends Component {
    static template = "TWBoomDashboardUser.BirthdayDialog";
    static components = { Dialog };
}

// Register the template for BirthdayDialog if it's not already in XML. 
// Wait, the user probably needs the XML template for this dialog too.
// I will assume "TWBoomDashboardUser.BirthdayDialog" is in tw_boom_dashboard_user.xml.
// I need to check if that XML is loaded. The manifest says I removed standard views? 
// No, I need to make sure the XML for the dialog is loaded.

const superSetup = DashboardAmcharts.prototype.setup;
patch(DashboardAmcharts.prototype, {
    setup() {
        superSetup.call(this);
        const { onMounted, onWillUnmount } = owl;

        // Store ORM service for use in async methods
        this.orm = useService('orm');

        // Extend state
        if (!this.state.welcomeData) {
            this.state.welcomeData = { userInfo: {} };
        }
        if (!this.state.employees) {
            this.state.employees = [];
        }
        // NEW: Replace single selectedEmployee with generic dashboardFilters
        if (!this.state.dashboardFilters) {
            this.state.dashboardFilters = {};
        }
        // Keep for backward compatibility (greeted charts, etc.)
        if (!this.state.selectedEmployee) {
            this.state.selectedEmployee = null;
        }

        onWillStart(async () => {
            await this.loadWelcomeData();
            await this.loadEmployees();
        });

        // Listen for filter change events from FilterLayout component
        // Using document since the event bubbles up
        this._filterChangeHandler = (event) => {
            this.onDashboardFilterChange(event);
        };
        document.addEventListener('dashboard-filter-change', this._filterChangeHandler);

        onMounted(() => {
            if (this.grid) {
                this.grid.setStatic(false);
                this.grid.float(true);

                // Add responsiveness
                const updateColumns = () => {
                    const width = window.innerWidth;
                    if (width < 768) {
                        this.grid.column(1, 'none');
                    } else if (width < 1200) {
                        this.grid.column(18, 'none');
                    } else {
                        this.grid.column(36, 'none');
                    }
                    // Ensure static state is preserved after column changes
                    this.grid.setStatic(!this.state.editMode);
                };

                window.addEventListener('resize', updateColumns);

                // Initial configuration
                this.grid.cellHeight(30);
                this.grid.opts.margin = 2;
                this.grid.opts.verticalMargin = 2;

                updateColumns();
            }
        });

        // Cleanup event listener on unmount
        onWillUnmount(() => {
            if (this._filterChangeHandler) {
                document.removeEventListener('dashboard-filter-change', this._filterChangeHandler);
            }
        });
    },
    // ... rest of the methods

    async loadWelcomeData() {
        try {
            const result = await this.orm.call(
                "tw.boom.task",
                "action_welcome_text",
                []
            );
            if (result && result.status === 1 && result.data.length >= 2) {
                this.state.welcomeData = {
                    userInfo: result.data[0],
                    birthdayInfo: result.data[1],
                };
            }
        } catch (error) {
            console.error("Error loading welcome data:", error);
            // Initialize with empty to avoid crashes
            this.state.welcomeData = {
                userInfo: { greet: 'Hello', name: 'User', job: 'Position' },
                birthdayInfo: {}
            };
        }
    },

    async loadEmployees() {
        try {
            // Call the action_get_employee method from tw.boom.task model
            const employees = await this.orm.call(
                "tw.boom.task",
                "action_get_employee",
                []
            );
            this.state.employees = employees || [];
        } catch (error) {
            console.error("Error loading employees:", error);
            this.state.employees = [];
        }
    },

    onClickDetailBirthDay(event) {
        event.preventDefault();
        const birthdayData = this.state.welcomeData?.birthdayInfo?.other_birthday || [];

        this.dialog.add(BirthdayDialog, {
            title: _t("Born today!"),
            body: _t("List of employees with birthday today"), // Dialog usually takes body or we render contents
            birthdayData: birthdayData, // Pass data to our custom component
        });
    },

    onEmployeeFilterChange(event) {
        /**
         * Handle employee filter change
         * Updates the dashboard to filter data by selected employee
         */
        const employeeId = event.target.value;
        if (employeeId) {
            // Filter charts by employee_id
            this.state.selectedEmployee = parseInt(employeeId);
            console.log('Filtering dashboard by employee:', employeeId);
        } else {
            // Reset filter to show all employees
            this.state.selectedEmployee = null;
            console.log('Clearing employee filter - showing all data');
        }
        // Refresh charts with new filter (don't open in edit mode)
        this.refreshCharts();
    },

    get getFilteredEmployees() {
        if (!this.state.employeeSearch || this.state.selectedEmployee) {
            return this.state.employees;
        }
        const search = this.state.employeeSearch.toLowerCase();
        return this.state.employees.filter((emp) =>
            emp.name.toLowerCase().includes(search)
        );
    },

    onEmployeeSearch(ev) {
        this.state.employeeSearch = ev.target.value;
        if (this.state.selectedEmployee) {
            this.state.selectedEmployee = null;
        }
        this.state.showDropdown = true;
    },

    onInputFocus() {
        this.state.showDropdown = true;
    },

    onInputBlur() {
        setTimeout(() => {
            this.state.showDropdown = false;
        }, 200);
    },

    selectEmployee(emp) {
        this.state.selectedEmployee = emp.id;
        this.state.employeeSearch = emp.name;
        this.state.showDropdown = false;
        this.refreshCharts();
    },

    clearEmployeeFilter() {
        this.state.selectedEmployee = null;
        this.state.employeeSearch = "";
        this.refreshCharts();
    },

    onDashboardFilterChange(event) {
        /**
         * Handle filter change events from FilterLayout component
         * Stores filter values in dashboardFilters state and triggers chart refresh
         */
        const detail = event.detail || {};
        console.log('### DASHBOARD: Filter change received:', detail);

        const filterType = detail.filterType;
        if (!filterType) return;

        // Use technical name as key if provided, otherwise fall back to filter type
        // This allows multiple filters of the same type (e.g. many2one) to coexist
        const filterKey = detail.filterTechnicalName || filterType;

        // Create a new object for dashboardFilters to trigger OWL reactivity
        const nextFilters = { ...this.state.dashboardFilters };

        // Store the filter value in the dashboardFilters object
        if (filterType === 'date_range') {
            // Date range: store start/end separately
            nextFilters.date_start = detail.dateStart || null;
            nextFilters.date_end = detail.dateEnd || null;
            nextFilters.date_range = !!(detail.dateStart || detail.dateEnd);
        } else {
            // For employee, many2one, selection, manual
            if (detail.value) {
                nextFilters[filterKey] = detail.value;
            } else if (detail.textValue) {
                nextFilters[filterKey] = detail.textValue;
            } else {
                // Clear the filter
                console.log(`### DASHBOARD: Clearing filter of key: ${filterKey}`);
                delete nextFilters[filterKey];
            }
        }

        // Apply updated filters to state
        this.state.dashboardFilters = nextFilters;

        // For backward compatibility with employee filter
        if (filterType === 'employee') {
            this.state.selectedEmployee = detail.value ? parseInt(detail.value) : null;
        }

        console.log('### DASHBOARD: Updated filters:', this.state.dashboardFilters);
        this.refreshCharts();
    },

    refreshCharts() {
        /**
         * Refresh all charts with current filters.
         * We increment reloadKey to force DashboardChartWrapper components 
         * to trigger their onWillUpdateProps logic.
         */
        console.log('### DASHBOARD: Refreshing charts, current reloadKey:', this.reloadKey.value);
        this.reloadKey.value += 1;
    }
});
