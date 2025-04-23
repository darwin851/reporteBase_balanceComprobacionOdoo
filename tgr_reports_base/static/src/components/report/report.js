/** @odoo-module */

import { Component, useRef, onMounted } from "@odoo/owl";
import { TgrLine } from "../line/line";
import { TgrCell } from "../cell/cell";

export class TgrReport extends Component {
    static template = "tgr_reports_base.TgrReport";
    static components = { TgrLine, TgrCell};
    
    static props = {
        reportName: { type: String, optional: true },
        data: Object,
    };
    
    setup() {
        this.tableRef = useRef("table");
        this.props.data = this.props.data || {};
        this.props.data.header = this.props.data.header || []; 
        this.props.data.lines = this.props.data.lines || [];
        this.props.data.footer = this.props.data.footer || {};
        this.props.data.footer.columns = this.props.data.footer.columns || [];

        onMounted(() => {
            // Aquí podría ir código para inicializar funcionalidades 
            // como expandir/colapsar filas, exportar a Excel, etc.
            console.log("Reporte montado:", this.props.reportName);
        });
    }
}
