import base64
import io
import logging
from datetime import datetime

import xlsxwriter

from odoo import models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ExcelReportMixin(models.AbstractModel):
    """
    Mixin para la generación de reportes Excel reutilizables.
    Este modelo abstracto proporciona métodos base que pueden ser heredados
    por otros modelos para generar reportes Excel personalizados.
    """
    _name = 'tgr.report.mixin'
    _description = 'Mixin para Reportes Excel'

    def _get_report_name(self, report_data):
        return f"Reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def _get_workbook_options(self):
        """
        Obtiene las opciones para el libro de trabajo.
        Puede ser sobrescrito por modelos hijos para personalizar las opciones.
        
        :return: Diccionario con opciones para xlsxwriter
        """
        return {
            'in_memory': True,
            'strings_to_numbers': True,
        }

    def _get_column_width(self, column_index):
        """
        Obtiene el ancho de una columna.
        Puede ser sobrescrito por modelos hijos para personalizar el ancho.
        
        :param column_index: Índice de la columna
        :return: Ancho de la columna
        """
        return 15  # Ancho predeterminado

    def _get_default_formats(self, workbook):
        """
        Crea y devuelve los formatos básicos para el reporte.
        Puede ser sobrescrito por modelos hijos para agregar más formatos.
        
        :param workbook: Objeto workbook de xlsxwriter
        :return: Diccionario con formatos
        """
        formats = {
            'header': workbook.add_format({
                'bold': True,
                'align': 'center',
                'valign': 'vcenter',
                'font_size': 12,
                'bg_color': '#CCCCCC',
                'border': 1,
            }),
            'header_merged': workbook.add_format({
                'bold': True,
                'align': 'center',
                'valign': 'vcenter',
                'font_size': 12,
                'bg_color': '#CCCCCC',
                'border': 1,
            }),
            'title': workbook.add_format({
                'bold': True,
                'align': 'center',
                'valign': 'vcenter',
                'font_size': 14,
                'bg_color': '#AAAAAA',
                'border': 1,
            }),
            'text': workbook.add_format({
                'align': 'left',
                'valign': 'vcenter',
                'font_size': 10,
                'border': 1,
            }),
            'monetary': workbook.add_format({
                'align': 'right',
                'valign': 'vcenter',
                'font_size': 10,
                'num_format': '#,##0.00',
                'border': 1,
            }),
            'monetary_bold': workbook.add_format({
                'bold': True,
                'align': 'right',
                'valign': 'vcenter',
                'font_size': 10,
                'num_format': '#,##0.00',
                'border': 1,
            }),
            'number': workbook.add_format({
                'align': 'right',
                'valign': 'vcenter',
                'font_size': 10,
                'num_format': '0',
                'border': 1,
            }),
            'date': workbook.add_format({
                'align': 'center',
                'valign': 'vcenter',
                'font_size': 10,
                'num_format': 'dd/mm/yyyy',
                'border': 1,
            }),
            'footer': workbook.add_format({
                'bold': True,
                'align': 'right',
                'valign': 'vcenter',
                'font_size': 11,
                'bg_color': '#DDDDDD',
                'border': 1,
            }),
        }
        return formats

    def _get_format_for_value(self, formats, column_type):
        """
        Obtiene el formato adecuado según el tipo de columna.
        
        :param formats: Diccionario de formatos
        :param column_type: Tipo de valor (monetary, percentage, date, etc.)
        :return: Formato adecuado para el tipo de dato
        """
        if column_type == 'monetary':
            return formats['monetary']
        elif column_type == 'percentage':
            return formats['percentage']
        elif column_type == 'date':
            return formats['date']
        elif column_type == 'number':
            return formats['number']
        else:
            return formats['text']

    def _prepare_worksheet(self, workbook, report_data):
        """
        Prepara la hoja de trabajo y retorna la hoja y los formatos.
        Puede ser sobrescrito por modelos hijos para crear múltiples hojas.
        
        :param workbook: Objeto workbook de xlsxwriter
        :param report_data: Diccionario con datos del reporte
        :return: Tupla (worksheet, formats)
        """
        worksheet = workbook.add_worksheet(self._get_report_name(report_data)[:31])
        formats = self._get_default_formats(workbook)
        
        # Configurar anchos de columna
        if 'header' in report_data and report_data['header']:
            for i, _ in enumerate(report_data['header']):
                worksheet.set_column(i, i, self._get_column_width(i))
        
        return worksheet, formats

    def _write_title(self, worksheet, formats, report_data):
        """
        Escribe el título del reporte.
        Puede ser sobrescrito por modelos hijos para personalizar.
        
        :param worksheet: Hoja de trabajo
        :param formats: Diccionario de formatos
        :param report_data: Diccionario con datos del reporte
        :return: Siguiente fila para escribir (después del título)
        """
        if 'title' in report_data and report_data['title']:
            title = report_data['title']
            title_cols = 1
            if 'header' in report_data and report_data['header']:
                title_cols = len(report_data['header'])
            
            worksheet.merge_range(0, 0, 0, title_cols - 1, title, formats['title'])
            return 1
        return 0

    def _write_multi_header(self, worksheet, formats, report_data, start_row):
        """
        Escribe encabezados múltiples (para reportes con encabezados complejos).
        
        :param worksheet: Hoja de trabajo
        :param formats: Diccionario de formatos
        :param report_data: Diccionario con datos del reporte
        :param start_row: Fila inicial para escribir los encabezados
        :return: Siguiente fila para escribir (después de los encabezados)
        """
        current_row = start_row
        
        # Si hay encabezados múltiples
        if 'header_0' in report_data and report_data['header_0']:
            col = 0
            for header in report_data['header_0']:
                name = header.get('name', '')
                colspan = header.get('colspan', 1)
                if colspan > 1:
                    worksheet.merge_range(current_row, col, current_row, col + colspan - 1, name, formats['header_merged'])
                else:
                    worksheet.write(current_row, col, name, formats['header'])
                col += colspan
            current_row += 1
        
        # Encabezado principal
        if 'header' in report_data and report_data['header']:
            for col, header in enumerate(report_data['header']):
                worksheet.write(current_row, col, header, formats['header'])
            current_row += 1
        
        return current_row

    def _write_body(self, worksheet, formats, report_data, start_row):
        """
        Escribe el cuerpo del reporte.
        Puede ser sobrescrito por modelos hijos para personalizar.
        
        :param worksheet: Hoja de trabajo
        :param formats: Diccionario de formatos
        :param report_data: Diccionario con datos del reporte
        :param start_row: Fila inicial para escribir el cuerpo
        :return: Siguiente fila para escribir (después del cuerpo)
        """
        current_row = start_row
        if 'lines' in report_data and report_data['lines']:
            for line in report_data['lines']:
                code = line.get('code','')
                name = line.get('name', '')
                level = line.get('level', 0)
                
                worksheet.write(current_row, 0, code, formats['text'])
                # Aplicar sangría según el nivel
                indented_name = '    ' * level + name
                worksheet.write(current_row, 1, indented_name, formats['text'])
                
                # Escribir columnas
                if 'columns' in line and line['columns']:
                    for col, column in enumerate(line['columns'], 2):
                        value = column.get('no_format', column.get('name', ''))
                        figure_type = column.get('figure_type', 'text')
                        fmt = self._get_format_for_value(formats, figure_type)
                        worksheet.write(current_row, col, value, fmt)
                
                current_row += 1
        
        return current_row

    def _write_footer(self, worksheet, formats, report_data, start_row):
        """
        Escribe el pie del reporte.
        Puede ser sobrescrito por modelos hijos para personalizar.
        
        :param worksheet: Hoja de trabajo
        :param formats: Diccionario de formatos
        :param report_data: Diccionario con datos del reporte
        :param start_row: Fila inicial para escribir el pie
        :return: Ninguno
        """
        if 'footer' in report_data and report_data['footer']:
            footer = report_data['footer']
            worksheet.merge_range(start_row, 0,start_row,1, footer.get('name', 'Total'), formats['footer'])
            
            if 'columns' in footer and footer['columns']:
                for col, column in enumerate(footer['columns'], 2):
                    value = column.get('no_format', column.get('name', ''))
                    figure_type = column.get('figure_type', 'text')
                    worksheet.write(start_row, col, value, formats['monetary_bold'] if figure_type == 'monetary' else formats['footer'])

    def tgr_generate_excel_report(self, report_data):
        """
        Método principal para generar el reporte Excel.
        
        :param report_data: Diccionario con los datos del reporte
        :return: Tupla (nombre_archivo, archivo_b64)
        """
        try:
            # Crear archivo en memoria
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, self._get_workbook_options())
            
            # Preparar hoja y formatos
            worksheet, formats = self._prepare_worksheet(workbook, report_data)
            
            # Escribir titulo
            current_row = self._write_title(worksheet, formats, report_data)
            
            # Escribir encabezados
            current_row = self._write_multi_header(worksheet, formats, report_data, current_row)
            
            # Escribir cuerpo del reporte
            current_row = self._write_body(worksheet, formats, report_data, current_row)
            
            # Escribir pie del reporte
            self._write_footer(worksheet, formats, report_data, current_row)
            
            # Cerrar workbook
            workbook.close()
            
            # Obtener contenido y convertir a base64
            excel_data = output.getvalue()
            excel_b64 = base64.b64encode(excel_data)
            
            report_name = f"{self._get_report_name(report_data)}.xlsx"
            
            return report_name, excel_b64
            
        except Exception as e:
            _logger.exception("Error al generar el reporte Excel")
            raise UserError(f"Error al generar el reporte Excel: {str(e)}")
