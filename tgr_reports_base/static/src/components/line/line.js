/** @odoo-module */

import { Component } from "@odoo/owl";
import {TgrCell} from "../cell/cell"

export class TgrLine extends Component {
    static template = "tgr_reports_base.TgrLine";
    static components = {TgrCell};

    static props = {
        lineIndex: Number,
        line: Object,
    };

    // Método simplificado para obtener las clases CSS de la línea
    get lineClasses() {
        let classes = ('level' in this.props.line) ? `line_level_${this.props.line.level}` : 'line_level_default';

        if (!this.props.line.visible)
            classes += " d-none";

        if (this.props.line.class)
            classes += ` ${this.props.line.class}`;

        return classes;
    }
}
