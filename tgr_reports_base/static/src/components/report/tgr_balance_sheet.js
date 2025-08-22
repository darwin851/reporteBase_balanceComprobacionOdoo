/** @odoo-module */

import { Component, onMounted } from "@odoo/owl";

export class TgrBalanceSheet extends Component {
    static template = "tgr_reports_base.TgrBalanceSheet";
    static props = {
        assets: { type: Array, optional: true },       // [{id, code, name, amount, amount_fmt, type, level}]
        liabilities: { type: Array, optional: true },  // idem
        totals: { type: Object, optional: true },      // { assets: {value, text}, liabilities: {value, text} }
    };

    setup() {
        onMounted(() => {
            // Debug útil en el navegador
            console.log("TgrBalanceSheet mounted", {
                assets: this.props.assets?.length ?? 0,
                liabilities: this.props.liabilities?.length ?? 0,
                totals: this.props.totals,
            });
        });
    }
}
