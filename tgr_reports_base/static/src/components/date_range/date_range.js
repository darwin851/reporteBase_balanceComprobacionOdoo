/** @odoo-module */
import { Component } from "@odoo/owl";
import { useRef } from "@odoo/owl";

export class TgrDateRangePicker extends Component {
  static template = 'tgr_reports_base.TgrDateRangePicker';
  static props = {
    defaultStartDate: { type: String, optional: true },
    defaultEndDate: { type: String, optional: true },
    buttonLabel: { type: String, optional: true, default: "Rango de Fechas" },
    onRangeChange: { type: Function, optional: false },
    buttonMinWidth: { type: String, optional: true },
  };
  static defaultProps ={
    buttonMinWidth:'200px'
  }
    setup() {
        this.startDateRef = useRef("startDate");
        this.endDateRef = useRef("endDate");
    }

    onDateChange() {
        const startDate = this.startDateRef.el.value;
        const endDate = this.endDateRef.el.value;
        
        this.props.onRangeChange({
            startDate: startDate,
            endDate: endDate
        });
    }
}

