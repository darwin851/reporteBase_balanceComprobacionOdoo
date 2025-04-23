import json
import logging
from odoo import http
from odoo.http import request, content_disposition, Response
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ExcelReportController(http.Controller):
    """
    Controlador para manejar la generación de reportes Excel.
    """
    
    @http.route('/web/tgr_excel_report/generate/<string:model_name>', type='json', auth='user', csrf=False)
    def generate_excel_report(self,model_name, **kw):
        """
        Ruta para generar reportes Excel.
        :param model: Modelo del reporte (ej. 'report.balance.comprobacion.excel')
        :param report_data: Datos del reporte en formato JSON
        :return: Archivo Excel para descargar
        """
        try:
            report_data = kw.get('report_data')
            report_generator = request.env[model_name]
            report_generator = report_generator.sudo()

            report_name, excel_b64 = report_generator.tgr_generate_excel_report(report_data)
            return {
                'success': True,
                'name': report_name,
                'data':excel_b64.decode('utf-8'),
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            }
            
        except Exception as e:
            _logger.exception("Error al generar el reporte Excel")
            return request.render('http_routing.http_error', {
                'status_code': 400,
                'status_message': f"Error: {str(e)}"
            })

