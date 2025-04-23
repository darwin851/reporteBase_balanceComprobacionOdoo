/** @odoo-module */

import { Component } from "@odoo/owl";

export class TgrCell extends Component {
    static template = "tgr_reports_base.TgrCell";
    static props = {
        cell: Object,
    };

    // Método simplificado para determinar si un tipo es numérico
    isNumeric(type) {
        return ['float', 'integer', 'monetary', 'percentage'].includes(type);
    }

    // Método simplificado para obtener las clases CSS de la celda
    get cellClasses() {
        let classes = "";

        if (this.props.cell.figure_type === 'date')
            classes += " date";

        if (this.props.cell.figure_type === 'string')
            classes += " text";

        if (this.isNumeric(this.props.cell.figure_type)) {
            classes += " numeric text-end";

            if (this.props.cell.no_format !== undefined) {
                if (this.props.cell.no_format === 0)
                    classes += " muted";
                else if (this.props.cell.no_format < 0)
                    classes += " text-danger";
            }
        }

        if (this.props.cell.class)
            classes += ` ${this.props.cell.class}`;

        return classes;
    }
}
