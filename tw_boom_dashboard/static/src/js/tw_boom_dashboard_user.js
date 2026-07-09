/** @odoo-module **/

import { registry } from "@web/core/registry";
import { loadJS } from '@web/core/assets';
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { rpc } from "@web/core/network/rpc";
const { Component, useRef, useState, mount, onWillStart, onMounted } = owl;
import { _t } from "@web/core/l10n/translation";

/**
 * Component for displaying the birthday list in a dialog
 */
class BirthdayDialog extends Component {
    static template = "TWBoomDashboardUser.BirthdayDialog";
    static components = { Dialog };
}

export class TWBoomDashboardUser extends Component {
    static template = "TWBoomDashboardUser";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.dialog = useService("dialog");
        this.rpc = rpc;

        this.state = useState({
            loading: true,
            welcomeData: {},
            taskStatus: {},
            taskCategories: [],
            taskDone: {},
            taskAges: {},
            leaderboard: [],
            taskList: [],
        });

        onWillStart(async () => {
            await this.loadDashboardData();
        });
    }

    /**
     * Handle click on birthday text to show detail dialog
     */
    onClickDetailBirthDay(event) {
        console.log("Birthday link clicked!");
        event.preventDefault();
        const birthdayData = this.state.welcomeData.birthdayInfo?.other_birthday || [];
        console.log("Birthday data:", birthdayData);

        this.dialog.add(BirthdayDialog, {
            title: _t("Born today!"),
            birthdayData: birthdayData,
        });
    }

    /**
     * Load all dashboard data
     */
    async loadDashboardData() {
        this.state.loading = true;
        try {
            await Promise.all([
                this.loadWelcomeData(),
                this.loadTaskStatus(),
                this.loadTaskCategories(),
                // this.loadTaskDone(),
                // this.loadTaskAges(),
                // this.loadLeaderboard(),
                // this.loadTaskList(),
            ]);
        } catch (error) {
            console.error("Error loading dashboard data:", error);
        } finally {
            this.state.loading = false;
        }
    }

    /**
     * Load welcome text and user info
     */
    async loadWelcomeData() {
        try {
            const result = await this.orm.call(
                "tw.boom.task",
                "action_welcome_text",
                []
            );
            if (result.status === 1 && result.data.length >= 2) {
                this.state.welcomeData = {
                    userInfo: result.data[0],
                    birthdayInfo: result.data[1],
                };
            }
        } catch (error) {
            console.error("Error loading welcome data:", error);
        }
    }

    /**
     * Load task status
     */
    async loadTaskStatus() {
        try {
            const result = await this.orm.call(
                "tw.boom.task",
                "action_task_status",
                []
            );

            if (result.status === 1 && result.data.length > 0) {
                this.state.taskStatus = result.data[0];
            }
        } catch (error) {
            console.error("Error loading task status:", error);
        }
    }

    /**
     * Load task categories
     */
    async loadTaskCategories() {
        try {
            const result = await this.orm.call(
                "tw.boom.task",
                "action_task_by_category",
                []
            );

            if (result.status === 1 && result.data.length > 0) {
                this.state.taskCategories = result.data;
            }
        } catch (error) {
            console.error("Error loading task categories:", error);
        }
    }
}

// Register the component as a client action
registry.category("actions").add("tw_boom_dashboard_boom_user", TWBoomDashboardUser);