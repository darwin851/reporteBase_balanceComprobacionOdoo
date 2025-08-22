/** @odoo-module */
const {Component} = owl;
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {useRef, useState} from "@odoo/owl";
import {BlockUI} from "@web/core/ui/block_ui";
import {download} from "@web/core/network/download";

import {Button1} from "@tgr_reports_base/components/button/button"
import {TgrDateRangePicker} from "@tgr_reports_base/components/date_range/date_range"
import {TgrReport} from "@tgr_reports_base/components/report/report"
import {TgrSelector} from "@tgr_reports_base/components/selector/selector"
import {TgrBalanceSheet} from "@tgr_reports_base/components/report/tgr_balance_sheet";


const actionRegistry = registry.category("actions");
const today = luxon.DateTime.now();
let monthNamesShort = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Set", "Oct", "Nov", "Dic"]

class AccountTrialBalance extends owl.Component {
    static components = {Button1, TgrDateRangePicker, TgrSelector, TgrBalanceSheet};

    async setup() {
        super.setup(...arguments);

        this.initial_render = true;
        this.orm = useService('orm');
        this.rpc = useService("rpc");
        this.action = useService('action')
        // Configurar fechas por defecto (inicio y fin del mes actual)
        const startOfMonth = new Date(today.year, today.month - 1, 1);
        const endOfMonth = new Date(today.year, today.month, 0);

        const defaultStartDate = startOfMonth.toISOString().split('T')[0]; // formato YYYY-MM-DD
        const defaultEndDate = endOfMonth.toISOString().split('T')[0]; // formato YYYY-MM-DD
        this.state = useState({
            isLoading: true,
            error: null,
            dateRange: {startDate: defaultStartDate, endDate: defaultEndDate},
            data: {
                assets: [],
                liabilities: [],
                totals: {assets: {value: 0, text: "0.00"}, liabilities: {value: 0, text: "0.00"}},
                journal_ids: []
            },
            journals: [],
            selectedJournals: [],
        });
        await this.load_data();
    }

    async onDateRangeChange(range) {
        this.state.dateRange = range
        await this.applyFilter()
    }

    async onJournalSelection(selectedJournals) {
        console.log("Diarios seleccionados:", selectedJournals);
        this.state.selectedJournals = selectedJournals
        await this.applyFilter()
    }

    async load_data() {
        try {
            this.state.isLoading = true;
            const res = await this.orm.call(
                'l10n_sv.account.trial.balance.sheet', 'view_report', [], {context: {filter_balance_sheet: true}}
            );
            this.state.data = res || this.state.data;
            this.state.journals = this.state.data.journal_ids || [];
            console.log("AccountTrialBalance -> data:", {
                assets: this.state.data.assets?.length,
                liabilities: this.state.data.liabilities?.length,
                totals: this.state.data.totals,
            });
        } catch (e) {
            this.state.error = e.message || String(e);
        } finally {
            this.state.isLoading = false;
        }
    }


    async applyFilter(val, ev, is_delete) {
        this.state.data = await this.orm.call('l10n_sv.account.trial.balance.sheet', 'get_filter_values', [
            this.state.dateRange.startDate,
            this.state.dateRange.endDate,
            this.state.selectedJournals
        ], {
            context: {
                filter_balance_sheet: true
            }
        });
        this.state.journals = this.state.data.journal_ids
        console.log(this.state.data.journal_ids)
    }

    async exportToExcel() {
        try {
            // Codificamos los datos como JSON para pasarlos al controlador
            const encodedData = encodeURIComponent(JSON.stringify(this.state.data));

            // Construimos la URL completa
            const result = await this.rpc(`/web/tgr_excel_report/generate/l10n_sv.account.trial.balance`, {
                report_data: this.state.data
            });
            this._downloadBase64File(result.data, result.name, result.mimetype)

            // Abrimos la URL en una nueva ventana/pestaña para descargar el archivo
        } catch (error) {
            console.error("Error al exportar a Excel:", error);
            this.notificationService.add(
                this.env._t("Error al exportar a Excel: ") + error.message,
                {type: "danger"}
            );
        } finally {
            // this.state.isExporting = false;
        }
    }

    async printPdf(ev) {
        console.log(this.state.data)
        console.log(this.state.selectedJournals)
        /**
         * Asynchronously generates and prints a PDF report.
         * Triggers an action to generate a PDF report based on the current state and settings.
         *
         * @param {Event} ev - Event object triggering the PDF report generation.
         * @returns {Promise} A promise that resolves after the PDF report action is triggered.
         */
        ev.preventDefault();
        var self = this;
        var action_title = self.props.action.display_name;
        var data_filters = ''
        if (self.state.selectedJournals) {
            const sj = self.state.selectedJournals
            const js = self.state.data.journal_ids
            data_filters = sj
                .map(index => js.find(item => item.id === index))
                .map(item => item.name)
                .join(', ');

        }
        console.log(data_filters)
        return self.action.doAction({
            'type': 'ir.actions.report',
            'report_type': 'qweb-pdf',
            'report_name': 'tgr_l10n_sv_balance_sheet.trial_balance_sheet',
            'report_file': 'tgr_l10n_sv_balance_sheet.trial_balance_sheet',
            'data': {
                'data': self.state.data,
                'title': action_title,
                'data_filters': data_filters,
                'report_name': self.props.action.display_name
            },
            'display_name': self.props.action.display_name,
        });
    }


    _downloadBase64File(base64Data, filename, mimeType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') {
        // Convertir base64 a blob
        const byteCharacters = atob(base64Data);
        const byteArrays = [];

        for (let offset = 0; offset < byteCharacters.length; offset += 512) {
            const slice = byteCharacters.slice(offset, offset + 512);

            const byteNumbers = new Array(slice.length);
            for (let i = 0; i < slice.length; i++) {
                byteNumbers[i] = slice.charCodeAt(i);
            }

            const byteArray = new Uint8Array(byteNumbers);
            byteArrays.push(byteArray);
        }

        const blob = new Blob(byteArrays, {type: mimeType});

        // Crear URL del blob
        const blobUrl = URL.createObjectURL(blob);

        // Crear enlace temporal y simular clic
        const downloadLink = document.createElement('a');
        downloadLink.href = blobUrl;
        downloadLink.download = filename;
        document.body.appendChild(downloadLink);
        downloadLink.click();

        // Limpiar
        document.body.removeChild(downloadLink);
        URL.revokeObjectURL(blobUrl);
    }
}

AccountTrialBalance.template = 'account_balance_sheet_template'
actionRegistry.add("a_b_s", AccountTrialBalance)
