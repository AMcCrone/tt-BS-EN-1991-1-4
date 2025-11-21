"""
Wind Load PDF Report Generator
Generates professional PDF reports for wind load calculations per BS EN 1991-1-4
"""

import io
import json
from datetime import datetime
from typing import Dict, Any, Optional
import streamlit as st

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os


class WindLoadReport:
    """Generate a professional PDF report for wind load calculations."""
    
    def __init__(self, report_data: Dict[str, Any], project_name: Optional[str] = None):
        """
        Initialize the report generator.
        
        Parameters
        ----------
        report_data : Dict[str, Any]
            Report data dictionary from ReportExporter
        project_name : Optional[str]
            Project name to display in header
        """
        self.data = report_data
        self.project_name = project_name or report_data.get('inputs', {}).get('project_name', 'Wind Load Analysis')
        self.buffer = io.BytesIO()
        self.page_width = A4[0]
        self.page_height = A4[1]
        self.left_margin = 30
        self.right_margin = 30
        self.content_width = self.page_width - self.left_margin - self.right_margin
        self.styles = getSampleStyleSheet()
        self._register_fonts()
        self._setup_custom_styles()
    
    def _register_fonts(self):
        """Register custom Raleway fonts with fallback to Helvetica."""
        font_dir = "fonts"
        
        fonts_to_register = [
            ('Raleway-Regular', 'Raleway-Regular.ttf'),
            ('Raleway-Medium', 'Raleway-Medium.ttf'),
            ('Raleway-SemiBold', 'Raleway-SemiBold.ttf'),
            ('Raleway-Bold', 'Raleway-Bold.ttf'),
            ('Raleway-Italic', 'Raleway-Italic.ttf'),
        ]
        
        for font_name, font_file in fonts_to_register:
            font_path = os.path.join(font_dir, font_file)
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                except Exception as e:
                    print(f"Warning: Could not register font {font_name}: {e}")
        
        # Set font variables with fallback
        self.font_regular = 'Raleway-Regular' if os.path.exists(os.path.join(font_dir, 'Raleway-Regular.ttf')) else 'Helvetica'
        self.font_medium = 'Raleway-Medium' if os.path.exists(os.path.join(font_dir, 'Raleway-Medium.ttf')) else 'Helvetica-Bold'
        self.font_semibold = 'Raleway-SemiBold' if os.path.exists(os.path.join(font_dir, 'Raleway-SemiBold.ttf')) else 'Helvetica-Bold'
        self.font_bold = 'Raleway-Bold' if os.path.exists(os.path.join(font_dir, 'Raleway-Bold.ttf')) else 'Helvetica-Bold'
        self.font_italic = 'Raleway-Italic' if os.path.exists(os.path.join(font_dir, 'Raleway-Italic.ttf')) else 'Helvetica-Oblique'
    
    def _setup_custom_styles(self):
        """Create custom paragraph styles for the report."""
        if 'CustomTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='CustomTitle',
                parent=self.styles['Title'],
                fontSize=18,
                textColor=colors.black,
                spaceAfter=12,
                alignment=TA_CENTER,
                fontName=self.font_bold
            ))
        
        if 'SectionHeading' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SectionHeading',
                parent=self.styles['Heading1'],
                fontSize=14,
                textColor=colors.HexColor('#db451d'),
                spaceAfter=8,
                spaceBefore=12,
                fontName=self.font_bold,
            ))
        
        if 'SubsectionHeading' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SubsectionHeading',
                parent=self.styles['Heading2'],
                fontSize=11,
                textColor=colors.HexColor('#db451d'),
                spaceAfter=6,
                spaceBefore=8,
                fontName=self.font_semibold
            ))
        
        if 'CustomBodyText' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='CustomBodyText',
                parent=self.styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                fontName=self.font_regular
            ))
        
        if 'FooterText' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='FooterText',
                parent=self.styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER,
                fontName=self.font_regular
            ))
    
    def _header_footer(self, canvas, doc):
        """Add header and footer to each page."""
        canvas.saveState()
        
        # Header
        canvas.setStrokeColor(colors.grey)
        canvas.setLineWidth(1)
        canvas.line(self.left_margin, self.page_height - 40, 
                   self.page_width - self.right_margin, self.page_height - 40)
        
        canvas.setFont(self.font_semibold, 8)
        canvas.setFillColor(colors.grey)
        
        header_text = f"{self.project_name}: Wind Load Calculation Report"
        canvas.drawString(self.left_margin, self.page_height - 32, header_text)
        
        canvas.setFont(self.font_regular, 8)
        date_str = datetime.now().strftime("%B %d, %Y")
        canvas.drawRightString(self.page_width - self.right_margin, self.page_height - 32, date_str)
        
        # Footer
        canvas.setStrokeColor(colors.grey)
        canvas.setLineWidth(1)
        canvas.line(self.left_margin, 40, self.page_width - self.right_margin, 40)
        
        canvas.setFont(self.font_regular, 8)
        canvas.setFillColor(colors.grey)
        
        # Try to add logo - prefer PNG/JPG over SVG
        logo_added = False
        
        # Try PNG first (most compatible)
        for logo_path in ["educational/images/TT_Logo_Colour.png", 
                          "images/TT_Logo_Colour.png"]:
            if os.path.exists(logo_path):
                try:
                    from reportlab.platypus import Image as RLImage
                    # Add logo with appropriate sizing
                    logo_height = 4  # mm - adjust as needed
                    logo = RLImage(logo_path, height=logo_height*mm)
                    # Maintain aspect ratio
                    logo.drawHeight = logo_height * mm
                    logo.drawWidth = logo.imageWidth * (logo_height * mm / logo.imageHeight)
                    logo.drawOn(canvas, self.left_margin, 20)
                    logo_added = True
                    break
                except Exception as e:
                    print(f"Warning: Could not add logo from {logo_path}: {e}")
        
        # Fallback to text if no logo found
        if not logo_added:
            canvas.drawString(self.left_margin, 30, "Thornton Tomasetti")
        
        canvas.drawCentredString(self.page_width / 2, 30, f"Page {doc.page}")
        
        version = self.data.get('_metadata', {}).get('app_version', '1.0')
        canvas.drawRightString(self.page_width - self.right_margin, 30, f"Version {version}")
        
        canvas.restoreState()
    
    def _create_table(self, data, col_widths=None, style_commands=None):
        """Create a formatted table with consistent styling."""
        default_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9e8e0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), self.font_bold),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), self.font_regular),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('LINEABOVE', (0, 0), (-1, 0), 1.0, colors.HexColor('#8b9064')),
            ('LINEBELOW', (0, 0), (-1, 0), 0.7, colors.HexColor('#8b9064')),
            ('LINEBELOW', (0, -1), (-1, -1), 1.0, colors.HexColor('#8b9064')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f4ed')])
        ]
        
        if style_commands:
            default_style.extend(style_commands)
        
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle(default_style))
        return table
    
    def _add_project_info_section(self, story):
        """Add project information section."""
        story.append(Paragraph("1. Project Information", self.styles['SectionHeading']))
        
        inputs = self.data.get('inputs', {})
        data = [
            ['Parameter', 'Value'],
            ['Project Name', inputs.get('project_name', 'N/A')],
            ['Project Number', inputs.get('project_number', 'N/A')],
            ['Location', inputs.get('location', 'N/A')],
            ['Region', inputs.get('region', 'N/A')],
        ]
        
        col_widths = [self.content_width * 0.4, self.content_width * 0.6]
        table = self._create_table(data, col_widths=col_widths)
        story.append(table)
        story.append(Spacer(1, 12))
    
    def _add_geometry_section(self, story):
        """Add building geometry section."""
        story.append(Paragraph("2. Building Geometry", self.styles['SectionHeading']))
        
        inputs = self.data.get('inputs', {})
        data = [
            ['Parameter', 'Value', 'Units'],
            ['North to South Dimension', f"{inputs.get('NS_dimension', 0):.2f}", 'm'],
            ['East to West Dimension', f"{inputs.get('EW_dimension', 0):.2f}", 'm'],
            ['Building Height (z)', f"{inputs.get('z', 0):.2f}", 'm'],
        ]
        
        col_widths = [self.content_width * 0.5, self.content_width * 0.3, self.content_width * 0.2]
        table = self._create_table(data, col_widths=col_widths)
        story.append(table)
        story.append(Spacer(1, 12))
    
    def _add_terrain_section(self, story):
        """Add site and terrain parameters section."""
        story.append(Paragraph("3. Site and Terrain Parameters", self.styles['SectionHeading']))
        
        inputs = self.data.get('inputs', {})
        data = [
            ['Parameter', 'Value', 'Units'],
            ['Altitude Factor', f"{inputs.get('altitude_factor', 0):.3f}", '-'],
            ['Distance to Sea', f"{inputs.get('d_sea', 0):.2f}", 'km'],
            ['Terrain Category', inputs.get('terrain_category', 'N/A'), '-'],
            ['Air Density', f"{inputs.get('rho_air', 0):.3f}", 'kg/m³'],
        ]
        
        col_widths = [self.content_width * 0.5, self.content_width * 0.3, self.content_width * 0.2]
        table = self._create_table(data, col_widths=col_widths)
        story.append(table)
        story.append(Spacer(1, 12))
    
    def _add_wind_velocity_section(self, story):
        """Add wind velocity section."""
        story.append(Paragraph("4. Wind Velocity", self.styles['SectionHeading']))
        
        inputs = self.data.get('inputs', {})
        results = self.data.get('results', {})
        
        data = [
            ['Parameter', 'Value', 'Units'],
            ['Basic Wind Speed (Vb,map)', f"{inputs.get('V_bmap', 0):.2f}", 'm/s'],
            ['Adjusted Basic Wind Speed (Vb)', f"{inputs.get('V_b', 0):.2f}", 'm/s'],
            ['Displacement Height (hdis)', f"{results.get('h_dis', 0):.2f}", 'm'],
            ['Effective Height (z - hdis)', f"{results.get('z_minus_h_dis', 0):.2f}", 'm'],
            ['Mean Wind Velocity (vm)', f"{results.get('v_mean', 0):.2f}", 'm/s'],
        ]
        
        col_widths = [self.content_width * 0.5, self.content_width * 0.3, self.content_width * 0.2]
        table = self._create_table(data, col_widths=col_widths)
        story.append(table)
        story.append(Spacer(1, 12))
    
    def _add_wind_pressure_section(self, story):
        """Add wind pressure section."""
        story.append(Paragraph("5. Wind Pressure", self.styles['SectionHeading']))
        
        results = self.data.get('results', {})
        data = [
            ['Parameter', 'Value', 'Units'],
            ['Basic Wind Pressure (qb)', f"{results.get('q_b', 0):.2f}", 'kPa'],
            ['Peak Velocity Pressure (qp)', f"{results.get('qp_value', 0):.2f}", 'kPa'],
        ]
        
        col_widths = [self.content_width * 0.5, self.content_width * 0.3, self.content_width * 0.2]
        table = self._create_table(data, col_widths=col_widths)
        story.append(table)
        story.append(Spacer(1, 12))
    
    def _add_cp_coefficients_section(self, story):
        """Add external pressure coefficients section with direction headers."""
        story.append(Paragraph("6. External Pressure Coefficients", self.styles['SectionHeading']))
        
        results = self.data.get('results', {})
        cp_results = results.get('cp_results')
        
        if cp_results and cp_results.get('data'):
            columns = cp_results.get('columns', [])
            
            # Remove Wind Direction column and keep other columns
            filtered_columns = [col for col in columns if col.lower() != 'wind direction']
            
            # Create header row (without Wind Direction)
            header_row = filtered_columns
            data_rows = [header_row]
            
            # Track current direction for grouping
            current_direction = None
            
            for i, row_dict in enumerate(cp_results['data']):
                wind_direction = row_dict.get('Wind Direction', row_dict.get('wind direction', ''))
                
                # If direction changed, add direction header row
                if wind_direction != current_direction:
                    # Add midrule before new direction (except first)
                    if current_direction is not None:
                        data_rows.append([''] * len(filtered_columns))  # Placeholder for midrule
                    
                    current_direction = wind_direction
                    # Add direction header spanning all columns
                    direction_header = [f"{wind_direction} Elevation"] + [''] * (len(filtered_columns) - 1)
                    data_rows.append(direction_header)
                
                # Add data row (format cpe to 2 decimal places)
                row_data = []
                for col in filtered_columns:
                    value = row_dict.get(col, '')
                    # Format cpe values to 2 decimal places
                    if col.lower() == 'cpe' or col.lower() == 'cp,e':
                        try:
                            row_data.append(f"{float(value):.2f}")
                        except:
                            row_data.append(str(value))
                    else:
                        row_data.append(str(value))
                data_rows.append(row_data)
            
            # Adjust column widths - give extra width from Wind Direction to Description
            # Assuming Description is typically the first or second column
            desc_idx = next((i for i, col in enumerate(filtered_columns) 
                           if 'description' in col.lower()), 0)
            
            num_cols = len(filtered_columns)
            base_width = self.content_width / (num_cols + 0.5)  # +0.5 accounts for removed column
            col_widths = [base_width] * num_cols
            col_widths[desc_idx] = base_width * 1.5  # Give extra width to Description
            
            # Create table with custom styling for direction headers and midrules
            table = Table(data_rows, colWidths=col_widths)
            
            style_commands = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9e8e0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), self.font_bold),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTNAME', (0, 1), (-1, -1), self.font_regular),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('LINEABOVE', (0, 0), (-1, 0), 1.0, colors.HexColor('#8b9064')),
                ('LINEBELOW', (0, 0), (-1, 0), 0.7, colors.HexColor('#8b9064')),
                ('LINEBELOW', (0, -1), (-1, -1), 1.0, colors.HexColor('#8b9064')),
            ]
            
            # Add styling for direction headers and midrules
            for row_idx, row in enumerate(data_rows):
                if row_idx > 0:  # Skip header row
                    # Check if this is a direction header (first cell ends with "Elevation")
                    if isinstance(row[0], str) and row[0].endswith('Elevation'):
                        style_commands.extend([
                            ('SPAN', (0, row_idx), (-1, row_idx)),  # Span across all columns
                            ('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#f5f4ed')),
                            ('FONTNAME', (0, row_idx), (-1, row_idx), self.font_semibold),
                            ('FONTSIZE', (0, row_idx), (-1, row_idx), 10),
                            ('TOPPADDING', (0, row_idx), (-1, row_idx), 4),
                            ('BOTTOMPADDING', (0, row_idx), (-1, row_idx), 4),
                        ])
                    # Check if this is a midrule placeholder (all empty strings)
                    elif all(cell == '' for cell in row):
                        style_commands.extend([
                            ('LINEABOVE', (0, row_idx), (-1, row_idx), 0.75, colors.HexColor('#8b9064')),
                            ('TOPPADDING', (0, row_idx), (-1, row_idx), 0),
                            ('BOTTOMPADDING', (0, row_idx), (-1, row_idx), 0),
                        ])
                    else:
                        # Alternate row backgrounds for data rows
                        bg_color = colors.white if (row_idx % 2 == 1) else colors.HexColor('#f5f4ed')
                        style_commands.append(('BACKGROUND', (0, row_idx), (-1, row_idx), bg_color))
            
            table.setStyle(TableStyle(style_commands))
            story.append(table)
        else:
            story.append(Paragraph("No CP coefficient data available.", self.styles['CustomBodyText']))
        
        story.append(Spacer(1, 12))
    
    def _add_pressure_summary_section(self, story):
        """Add pressure summary section with midrules between direction changes."""
        story.append(Paragraph("7. Pressure Summary", self.styles['SectionHeading']))
        
        results = self.data.get('results', {})
        pressure_summary = results.get('pressure_summary')
        
        if pressure_summary and pressure_summary.get('data'):
            columns = pressure_summary.get('columns', [])
            
            # Remove c_dir column if it exists
            filtered_columns = [col for col in columns if col.lower() not in ['c_dir', 'cdir']]
            
            # Create header row
            header_row = filtered_columns
            data_rows = [header_row]
            
            # Track current direction for adding midrules
            current_direction = None
            
            for row_dict in pressure_summary['data']:
                # Try to find direction in the data (could be in various column names)
                wind_direction = None
                for possible_dir_col in ['Wind Direction', 'wind direction', 'Direction', 'direction', 'Elevation', 'elevation']:
                    if possible_dir_col in row_dict:
                        wind_direction = row_dict.get(possible_dir_col, '')
                        break
                
                # If direction changed and we have a direction, add midrule placeholder
                if wind_direction and wind_direction != current_direction and current_direction is not None:
                    data_rows.append([''] * len(filtered_columns))  # Placeholder for midrule
                    current_direction = wind_direction
                elif wind_direction:
                    current_direction = wind_direction
                
                # Add data row
                data_rows.append([str(row_dict.get(col, '')) for col in filtered_columns])
            
            # Calculate column widths dynamically
            num_cols = len(filtered_columns)
            col_widths = [self.content_width / num_cols] * num_cols
            
            # Create table with custom styling for midrules
            table = Table(data_rows, colWidths=col_widths)
            
            style_commands = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9e8e0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), self.font_bold),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTNAME', (0, 1), (-1, -1), self.font_regular),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('LINEABOVE', (0, 0), (-1, 0), 1.0, colors.HexColor('#8b9064')),
                ('LINEBELOW', (0, 0), (-1, 0), 0.7, colors.HexColor('#8b9064')),
                ('LINEBELOW', (0, -1), (-1, -1), 1.0, colors.HexColor('#8b9064')),
            ]
            
            # Add styling for midrule placeholders and alternating row backgrounds
            for row_idx, row in enumerate(data_rows):
                if row_idx > 0:  # Skip header row
                    # Check if this is a midrule placeholder (all empty strings)
                    if all(cell == '' for cell in row):
                        style_commands.extend([
                            ('LINEABOVE', (0, row_idx), (-1, row_idx), 0.75, colors.HexColor('#8b9064')),
                            ('TOPPADDING', (0, row_idx), (-1, row_idx), 0),
                            ('BOTTOMPADDING', (0, row_idx), (-1, row_idx), 0),
                        ])
                    else:
                        # Alternate row backgrounds for data rows
                        bg_color = colors.white if (row_idx % 2 == 1) else colors.HexColor('#f5f4ed')
                        style_commands.append(('BACKGROUND', (0, row_idx), (-1, row_idx), bg_color))
            
            table.setStyle(TableStyle(style_commands))
            story.append(table)
        else:
            story.append(Paragraph("No pressure summary data available.", self.styles['CustomBodyText']))
        
        story.append(Spacer(1, 12))
    
    def _add_summary_text(self, story):
        """Add summary text section."""
        story.append(Paragraph("8. Summary", self.styles['SectionHeading']))
        
        results = self.data.get('results', {})
        inputs = self.data.get('inputs', {})
        
        summary_text = f"""
        This report presents wind load calculations for <b>{self.project_name}</b> located in 
        <b>{inputs.get('location', 'N/A')}</b>, {inputs.get('region', 'N/A')}, 
        in accordance with BS EN 1991-1-4.
        <br/><br/>
        The building has dimensions of {inputs.get('NS_dimension', 0):.1f}m (N-S) × 
        {inputs.get('EW_dimension', 0):.1f}m (E-W) with a height of {inputs.get('z', 0):.1f}m. 
        The site is located in terrain category <b>{inputs.get('terrain_category', 'N/A')}</b>, 
        at {inputs.get('d_sea', 0):.1f}km from the sea.
        <br/><br/>
        The basic wind speed (Vb,map) of {inputs.get('V_bmap', 0):.2f} m/s was adjusted using an 
        altitude factor of {inputs.get('altitude_factor', 0):.3f}, resulting in an adjusted basic 
        wind speed (Vb) of {inputs.get('V_b', 0):.2f} m/s.
        <br/><br/>
        <b>Key Results:</b>
        <br/>
        • Peak velocity pressure: <b>{results.get('qp_value', 0):.2f} kPa</b>
        <br/>
        • Mean wind velocity: <b>{results.get('v_mean', 0):.2f} m/s</b>
        <br/>
        • Basic wind pressure: <b>{results.get('q_b', 0):.2f} kPa</b>
        <br/><br/>
        External pressure coefficients and corresponding wind pressures for all building elevations 
        are provided in the preceding sections. These values should be used for the detailed design 
        of the building's structural and cladding systems.
        """
        
        story.append(Paragraph(summary_text, self.styles['CustomBodyText']))
        story.append(Spacer(1, 12))
    
    def generate(self):
        """Generate the complete PDF report."""
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=self.right_margin,
            leftMargin=self.left_margin,
            topMargin=60,
            bottomMargin=60
        )
        
        story = []
        
        # Title page
        story.append(Spacer(1, 40))
        story.append(Paragraph("Wind Load Calculation Report", self.styles['CustomTitle']))
        story.append(Paragraph("BS EN 1991-1-4", self.styles['CustomTitle']))
        story.append(Spacer(1, 12))
        
        # Report info
        metadata = self.data.get('_metadata', {})
        report_date = datetime.fromisoformat(metadata.get('exported_at', datetime.now().isoformat()))
        
        story.append(Paragraph(
            f"<b>Report Generated:</b> {report_date.strftime('%B %d, %Y at %H:%M')}",
            self.styles['CustomBodyText']
        ))
        story.append(Paragraph(
            f"<b>Application:</b> Wind Load Calculator v{metadata.get('app_version', '1.0')}",
            self.styles['CustomBodyText']
        ))
        story.append(Paragraph(
            f"<b>Project:</b> {self.project_name}",
            self.styles['CustomBodyText']
        ))
        
        story.append(Spacer(1, 24))
        
        # Add all sections
        self._add_project_info_section(story)
        self._add_geometry_section(story)
        self._add_terrain_section(story)
        self._add_wind_velocity_section(story)
        self._add_wind_pressure_section(story)
        self._add_cp_coefficients_section(story)
        self._add_pressure_summary_section(story)
        self._add_summary_text(story)
        
        # Build PDF
        doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        
        self.buffer.seek(0)
        return self.buffer


def create_wind_load_pdf(report_data: Dict[str, Any], project_name: Optional[str] = None) -> io.BytesIO:
    """
    Create a PDF report from wind load calculation data.
    
    Parameters
    ----------
    report_data : Dict[str, Any]
        Report data dictionary from ReportExporter
    project_name : Optional[str]
        Project name to display in header
    
    Returns
    -------
    io.BytesIO
        Buffer containing the PDF report
    """
    report = WindLoadReport(report_data, project_name)
    return report.generate()


def add_wind_pdf_download_button(
    report_data: Dict[str, Any],
    filename: str = "wind_load_report.pdf",
    button_label: str = "📄 Download PDF Report",
    project_name: Optional[str] = None
):
    """
    Add a download button to the Streamlit sidebar for the PDF report.
    
    Parameters
    ----------
    report_data : Dict[str, Any]
        The report data dictionary from ReportExporter
    filename : str
        The filename for the downloaded PDF file
    button_label : str
        The label for the download button
    project_name : Optional[str]
        Project name to include in header
    """
    try:
        pdf_buffer = create_wind_load_pdf(report_data, project_name)
        
        st.sidebar.download_button(
            label=button_label,
            data=pdf_buffer,
            file_name=filename,
            mime="application/pdf",
            help="Download complete wind load calculation report as PDF"
        )
    except Exception as e:
        st.sidebar.error(f"PDF generation failed: {str(e)}")
        st.sidebar.exception(e)
