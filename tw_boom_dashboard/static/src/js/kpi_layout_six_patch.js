/** @odoo-module **/

import { KPIView } from "@synconics_bi_dashboard/components/KPIView/KPIView";
import { KpiLayoutSix } from "../components/KPILayouts/KpiLayoutSix/KpiLayoutSix";

// Directly add KpiLayoutSix to KPIView's static components
// This is the correct way to extend components in Owl
KPIView.components = {
    ...KPIView.components,
    KpiLayoutSix,
};
