/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { KpiLayoutOne } from "@synconics_bi_dashboard/components/KPILayouts/KpiLayoutOne/KpiLayoutOne";
import { KpiLayoutTwo } from "@synconics_bi_dashboard/components/KPILayouts/KpiLayoutTwo/KpiLayoutTwo";
import { KpiLayoutThree } from "@synconics_bi_dashboard/components/KPILayouts/KpiLayoutThree/KpiLayoutThree";
import { KpiLayoutFour } from "@synconics_bi_dashboard/components/KPILayouts/KpiLayoutFour/KpiLayoutFour";
import { KpiLayoutFive } from "@synconics_bi_dashboard/components/KPILayouts/KpiLayoutFive/KpiLayoutFive";

// Patch KpiLayoutOne to use our custom template
KpiLayoutOne.template = "tw_boom_dashboard.KpiLayoutOneCustom";

// For now, other layouts use same pattern - we only override LayoutOne as primary
// If needed, add more custom templates for other layouts
