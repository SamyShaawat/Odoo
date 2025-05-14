/** @odoo-module */

import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

async function executeCommissionReportDownload({ env, action }) {
    env.services.ui.block();
    const url = `/commission_reports/${action.data.output_format}/${action.data.report_name}`;
    const data = action.data;
    try {
      await download({ url, data });
    } finally {
      env.services.ui.unblock();
    }
}

registry
    .category("action_handlers")
    .add('ir_actions_commission_report_download', executeCommissionReportDownload);
