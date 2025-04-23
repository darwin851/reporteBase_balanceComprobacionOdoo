/** @odoo-module **/

import { Component } from "@odoo/owl";

export class Button1 extends Component {
    setup() {}

    onClick(ev) {
        if (this.props.onClick) {
            this.props.onClick(ev);
        }
    }

    get buttonClasses() {
        const type = this.props.type || 'primary';
        const size = this.props.size || 'md';
        return `btn btn-${type} btn-${size} ${this.props.className || ''}`;
    }
}

Button1.template = "tgr_reports_base.Button1";
Button1.props = {
    label: { type: String, optional: true },
    icon: { type: String, optional: true },
    type: { type: String, optional: true },
    size: { type: String, optional: true },
    className: { type: String, optional: true },
    onClick: { type: Function, optional: true },
    disabled: { type: Boolean, optional: true },
    slots: { type: Object, optional: true },
};


