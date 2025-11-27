import io
from datetime import datetime
from typing import Dict, Any, Optional
import streamlit as st
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Image
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# Import the StateManager
from outputs.state_manager import StateManager


class WindLoadReport:
    """Generate a professional PDF report for wind load calculations."""
    
    def __init__(self, project_name: Optional[str] = None):
        """
        Initialize the report generator.
        
        Parameters
        ----------
        project_name : Optional[str]
            Project name to display in header
        """
        # Get data from StateManager
        self.manager = StateManager()
        self.inputs = self.manager.get_pdf_inputs()
        self.results = self.manager.get_pdf_results()
        
        # Use project name from parameter or from inputs
        self.project_name = project_name or self.inputs.get("project_name", "Wind Load Project")
        
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
        """Register custom Raleway fonts."""
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
        
        self.font_regular = 'Raleway-Regular' if os.path.exists(os.path.join(font_dir, 'Raleway-Regular.ttf')) else 'Helvetica'
        self.font_semibold = 'Raleway-SemiBold' if os.path.exists(os.path.join(font_dir, 'Raleway-SemiBold.ttf')) else 'Helvetica-Bold'
        self.font_bold = 'Raleway-Bold' if os.path.exists(os.path.join(font_dir, 'Raleway-Bold.ttf')) else 'Helvetica-Bold'
        
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
        
        # Try to add logo
        logo_paths = ["educational/images/TT_Logo_Colour.png", "TT_Logo_Colour.png"]
        logo_added = False
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                try:
                    from reportlab.platypus import Image as RLImage
                    logo_height = 3  # mm
                    logo = RLImage(logo_path, height=logo_height*mm)
                    logo.drawHeight = logo_height * mm
                    logo.drawWidth = logo.imageWidth * (logo_height * mm / logo.imageHeight)
                    logo.drawOn(canvas, self.left_margin, 20)
                    logo_added = True
                    break
                except Exception as e:
                    print(f"Warning: Could not add logo: {e}")
        
        if not logo_added:
            canvas.drawString(self.left_margin, 30, "Thornton Tomasetti")
        
        canvas.drawCentredString(self.page_width / 2, 30, f"Page {doc.page}")
        canvas.drawRightString(self.page_width - self.right_margin, 30, "v1.0")
        
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
        
        data = [
            ['Parameter', 'Value'],
            ['Project Name', self.inputs.get('project_name', 'N/A')],
            ['Project Number', self.inputs.get('project_number', 'N/A')],
            ['Location', self.inputs.get('location', 'N/A')],
            ['Region', self.inputs.get('region', 'N/A')],
        ]
        
        col_widths = [self.content_width * 0.4, self.content_width * 0.6]
        table = self._create_table(data, col_widths=col_widths)
        story.append(table)
        story.append(Spacer(1, 12))
    
    def _add_building_geometry_section(self, story):
        """Add building geometry section."""
        story.append(Paragraph("2. Building Geometry", self.styles['SectionHeading']))
        
        data = [
            ['Parameter', 'Value', 'Units'],
            ['North-South Dimension', f"{self.inputs.get('NS_dimension', 0.0):.2f}", 'm'],
            ['East-West Dimension', f"{self.inputs.get('EW_dimension', 0.0):.2f}", 'm'],
            ['Building Height (z)', f"{self.inputs.get('z', 0.0):.2f}", 'm'],
        ]
        
        col_widths = [self.content_width * 0.5, self.content_width * 0.3, self.content_width * 0.2]
        table = self._create_table(data, col_widths=col_widths)
        story.append(table)
        story.append(Spacer(1, 12))
    
    def _add_site_parameters_section(self, story):
        """Add site parameters section."""
        story.append(Paragraph("3. Site Parameters", self.styles['SectionHeading']))
        
        data = [
            ['Parameter', 'Value', 'Units'],
            ['Altitude', f"{self.inputs.get('altitude', 0.0):.0f}", 'm'],
            ['Altitude Factor (c_alt)', f"{self.inputs.get('c_alt', 0.0):.3f}", '-'],
            ['Distance to Sea', f"{self.inputs.get('d_sea', 0.0):.0f}", 'km'],
            ['Terrain Category', self.inputs.get('terrain_category', 'N/A'), '-'],
            ['Air Density', f"{self.inputs.get('rho_air', 0.0):.2f}", 'kg/m³'],
        ]
        
        col_widths = [self.content_width * 0.5, self.content_width * 0.3, self.content_width * 0.2]
        table = self._create_table(data, col_widths=col_widths)
        story.append(table)
        story.append(Spacer(1, 12))
    
    def _add_basic_wind_pressure_section(self, story):
        """Add basic wind pressure section."""
        story.append(Paragraph("4. Basic Wind Pressure", self.styles['SectionHeading']))
        
        data = [
            ['Parameter', 'Value', 'Units'],
            ['Basic Wind Speed (map)', f"{self.inputs.get('V_bmap', 0.0):.2f}", 'm/s'],
            ['Basic Wind Speed (v_b)', f"{self.results.get('V_b', 0.0):.2f}", 'm/s'],
            ['Basic Wind Pressure (q_b)', f"{self.results.get('q_b', 0.0):.3f}", 'kPa'],
        ]
        
        col_widths = [self.content_width * 0.5, self.content_width * 0.3, self.content_width * 0.2]
        table = self._create_table(data, col_widths=col_widths)
        story.append(table)
        story.append(Spacer(1, 12))
    
    def _add_peak_wind_pressure_section(self, story):
        """Add peak wind pressure section."""
        story.append(Paragraph("5. Peak Wind Pressure", self.styles['SectionHeading']))
        
        # Helper function to safely format values
        def format_factor(key):
            value = self.results.get(key, 0.0)
            if value == 0.0:
                return 'N/A'
            return f"{value:.3f}"
        
        # Displacement height
        story.append(Paragraph("5.1 Displacement Height", self.styles['SubsectionHeading']))
        disp_data = [
            ['Parameter', 'Value', 'Units'],
            ['h_dis', f"{self.results.get('h_dis', 0.0):.2f}", 'm'],
            ['z - h_dis', f"{self.results.get('z_minus_h_dis', 0.0):.2f}", 'm'],
        ]
        
        col_widths = [self.content_width * 0.5, self.content_width * 0.3, self.content_width * 0.2]
        table = self._create_table(disp_data, col_widths=col_widths)
        story.append(table)
        story.append(Spacer(1, 8))
        
        # Check if this is UK region for UK-specific factors
        region = self.inputs.get('region', '')
        if region == 'United Kingdom':
            # UK National Annex factors
            story.append(Paragraph("5.2 National Annex Factors", self.styles['SubsectionHeading']))
            
            uk_data = [
                ['Factor', 'Value', 'Description'],
                ['c_ez', format_factor('c_ez'), 'Exposure factor at height z'],
                ['c_eT', format_factor('c_eT'), 'Turbulence factor'],
                ['I_vz', format_factor('i_vz'), 'Turbulence intensity at height z'],
                ['k_iT', format_factor('k_iT'), 'Terrain factor'],
                ['c_rz', format_factor('c_rz'), 'Roughness factor at height z'],
                ['c_rT', format_factor('c_rT'), 'Terrain factor for roughness'],
            ]
            
            col_widths_uk = [self.content_width * 0.2, self.content_width * 0.2, self.content_width * 0.6]
            table_uk = self._create_table(uk_data, col_widths=col_widths_uk)
            story.append(table_uk)
            story.append(Spacer(1, 8))
            
            # Orography factor if significant
            is_orography_significant = self.inputs.get('is_orography_significant', False)
            if is_orography_significant:
                story.append(Paragraph("5.3 Orography Factor", self.styles['SubsectionHeading']))
                
                orog_data = [
                    ['Factor', 'Value', 'Description'],
                    ['c_o', format_factor('c_o'), 'Orography factor'],
                ]
                
                table_orog = self._create_table(orog_data, col_widths=col_widths_uk)
                story.append(table_orog)
                story.append(Spacer(1, 8))
            
            # Mean wind velocity if calculated (z > 50m with orography)
            v_mean = self.results.get('v_mean', 0.0)
            if v_mean > 0.0:
                section_num = "5.4" if is_orography_significant else "5.3"
                story.append(Paragraph(f"{section_num} Mean Wind Velocity", self.styles['SubsectionHeading']))
                
                v_mean_data = [
                    ['Parameter', 'Value', 'Units'],
                    ['v_m(z)', f"{v_mean:.2f}", 'm/s'],
                ]
                table_v_mean = self._create_table(v_mean_data, col_widths=col_widths)
                story.append(table_v_mean)
                story.append(Spacer(1, 8))
        
        else:
            # Non-UK regions: Mean wind velocity factors
            story.append(Paragraph("5.2 Mean Wind Velocity", self.styles['SubsectionHeading']))
            
            mean_data = [
                ['Parameter', 'Value', 'Units'],
                ['z_0', format_factor('z_0'), 'm'],
                ['z_min', format_factor('z_min'), 'm'],
                ['k_r', format_factor('k_r'), '-'],
                ['c_r(z)', format_factor('c_rz'), '-'],
                ['v_m(z)', f"{self.results.get('v_mean', 0.0):.2f}", 'm/s'],
            ]
            
            table_mean = self._create_table(mean_data, col_widths=col_widths)
            story.append(table_mean)
            story.append(Spacer(1, 8))
            
            # Peak velocity pressure factors
            story.append(Paragraph("5.3 Peak Velocity Pressure", self.styles['SubsectionHeading']))
            
            peak_data = [
                ['Parameter', 'Value', 'Units'],
                ['I_v(z)', format_factor('i_vz'), '-'],
                ['q_p(z)', f"{self.results.get('qp_value', 0.0):.3f}", 'kPa'],
            ]
            
            table_peak = self._create_table(peak_data, col_widths=col_widths)
            story.append(table_peak)
            story.append(Spacer(1, 8))
        
        # Final peak velocity pressure result (for UK only, if not already shown above)
        if region == 'United Kingdom':
            v_mean = self.results.get('v_mean', 0.0)
            is_orography_significant = self.inputs.get('is_orography_significant', False)
            
            if v_mean > 0.0 and is_orography_significant:
                section_num = "5.5"
            elif v_mean > 0.0:
                section_num = "5.4"
            elif is_orography_significant:
                section_num = "5.4"
            else:
                section_num = "5.3"
            
            story.append(Paragraph(f"{section_num} Peak Velocity Pressure", self.styles['SubsectionHeading']))
            qp_data = [
                ['Parameter', 'Value', 'Units'],
                ['q_p(z)', f"{self.results.get('qp_value', 0.0):.3f}", 'kPa'],
            ]
            
            table_qp = self._create_table(qp_data, col_widths=col_widths)
            story.append(table_qp)
            story.append(Spacer(1, 8))
        
        story.append(Spacer(1, 4))
    
    def _add_external_pressure_coefficients_section(self, story):
        """Add external pressure coefficients section with inset and funnelling subsections."""
        story.append(Paragraph("6. External Pressure Coefficients", self.styles['SectionHeading']))
        
        # Inset Zone subsection if applicable
        inset_enabled = self.inputs.get('inset_enabled', False)
        if inset_enabled:
            story.append(Paragraph("6.1 Inset Zone", self.styles['SubsectionHeading']))
            
            inset_data = [
                ['Parameter', 'Value', 'Units'],
                ['Inset Height', f"{self.inputs.get('inset_height', 0.0):.2f}", 'm'],
                ['North Offset', f"{self.inputs.get('north_offset', 0.0):.2f}", 'm'],
                ['South Offset', f"{self.inputs.get('south_offset', 0.0):.2f}", 'm'],
                ['East Offset', f"{self.inputs.get('east_offset', 0.0):.2f}", 'm'],
                ['West Offset', f"{self.inputs.get('west_offset', 0.0):.2f}", 'm'],
            ]
            
            col_widths = [self.content_width * 0.5, self.content_width * 0.3, self.content_width * 0.2]
            table_inset = self._create_table(inset_data, col_widths=col_widths)
            story.append(table_inset)
            story.append(Spacer(1, 8))
        
        # Funnelling subsection if applicable
        consider_funnelling = self.inputs.get('consider_funnelling', False)
        if consider_funnelling:
            subsection_num = "6.2" if inset_enabled else "6.1"
            story.append(Paragraph(f"{subsection_num} Funnelling", self.styles['SubsectionHeading']))
            
            funnelling_data = [
                ['Parameter', 'Value', 'Units'],
                ['North Gap', f"{self.inputs.get('north_gap', 0.0):.2f}", 'm'],
                ['South Gap', f"{self.inputs.get('south_gap', 0.0):.2f}", 'm'],
                ['East Gap', f"{self.inputs.get('east_gap', 0.0):.2f}", 'm'],
                ['West Gap', f"{self.inputs.get('west_gap', 0.0):.2f}", 'm'],
            ]
            
            col_widths = [self.content_width * 0.5, self.content_width * 0.3, self.content_width * 0.2]
            table_funnelling = self._create_table(funnelling_data, col_widths=col_widths)
            story.append(table_funnelling)
            story.append(Spacer(1, 8))
        
        # Main pressure coefficients table
        subsection_label = "6.3" if (inset_enabled and consider_funnelling) else ("6.2" if (inset_enabled or consider_funnelling) else "6.1")
        story.append(Paragraph(f"{subsection_label} Pressure Coefficients by Zone", self.styles['SubsectionHeading']))
        
        # Get cp_results from results dictionary
        cp_results_data = self.results.get('cp_results')
        
        if cp_results_data and cp_results_data.get('_type') == 'dataframe':
            # Deserialize the DataFrame
            df = self.manager.deserialize_dataframe(cp_results_data)
            
            if df is not None and not df.empty:
                # Group by wind direction
                if 'Wind Direction' in df.columns:
                    # Create table data with wind direction as group headers
                    table_data = []
                    
                    # Get all columns except Wind Direction
                    other_cols = [col for col in df.columns if col != 'Wind Direction']
                    
                    # Add main header row
                    table_data.append(other_cols)
                    
                    # Group by wind direction
                    grouped = df.groupby('Wind Direction', sort=False)
                    
                    for wind_dir, group in grouped:
                        # Add wind direction header row (spanning all columns)
                        dir_header = [f"{wind_dir}"] + [''] * (len(other_cols) - 1)
                        table_data.append(dir_header)
                        
                        # Add data rows for this wind direction
                        for idx, row in group.iterrows():
                            row_data = []
                            for col in other_cols:
                                val = row[col]
                                # Round cp,e values to 2 decimal places
                                if 'cp,e' in col or 'cp_e' in col.lower():
                                    try:
                                        row_data.append(f"{float(val):.2f}")
                                    except:
                                        row_data.append(str(val))
                                else:
                                    row_data.append(str(val))
                            table_data.append(row_data)
                    
                    # Calculate column widths
                    num_cols = len(other_cols)
                    # Give more width to description column (assuming it's the first)
                    col_widths = [self.content_width * 0.35] + [self.content_width * 0.65 / (num_cols - 1)] * (num_cols - 1)
                    
                    # Create custom styling for wind direction headers
                    custom_style = []
                    
                    # Track row indices for wind direction headers
                    row_idx = 1  # Start after main header
                    for wind_dir, group in grouped:
                        # Style for wind direction row
                        custom_style.extend([
                            ('SPAN', (0, row_idx), (-1, row_idx)),  # Merge all columns
                            ('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#d3d2c8')),
                            ('FONTNAME', (0, row_idx), (-1, row_idx), self.font_bold),
                            ('FONTSIZE', (0, row_idx), (-1, row_idx), 10),
                            ('LINEBELOW', (0, row_idx), (-1, row_idx), 1.0, colors.HexColor('#8b9064')),
                        ])
                        
                        # Move to next set of rows
                        row_idx += 1 + len(group)
                        
                        # Add line below last row of this direction group
                        if row_idx < len(table_data):
                            custom_style.append(
                                ('LINEBELOW', (0, row_idx - 1), (-1, row_idx - 1), 1.5, colors.HexColor('#8b9064'))
                            )
                    
                    table = self._create_table(table_data, col_widths=col_widths, style_commands=custom_style)
                    story.append(table)
                    story.append(Spacer(1, 12))
                else:
                    # Fallback if no Wind Direction column
                    table_data = [list(df.columns)]
                    for idx, row in df.iterrows():
                        row_data = []
                        for col in df.columns:
                            val = row[col]
                            if 'cp,e' in col or 'cp_e' in col.lower():
                                try:
                                    row_data.append(f"{float(val):.2f}")
                                except:
                                    row_data.append(str(val))
                            else:
                                row_data.append(str(val))
                        table_data.append(row_data)
                    
                    num_cols = len(df.columns)
                    col_widths = [self.content_width / num_cols] * num_cols
                    table = self._create_table(table_data, col_widths=col_widths)
                    story.append(table)
                    story.append(Spacer(1, 12))
            else:
                story.append(Paragraph(
                    "<i>External pressure coefficient data not available.</i>",
                    self.styles['CustomBodyText']
                ))
                story.append(Spacer(1, 12))
        else:
            story.append(Paragraph(
                "<i>External pressure coefficient data not available.</i>",
                self.styles['CustomBodyText']
            ))
            story.append(Spacer(1, 12))
    
    def _add_pressure_summary_section(self, story):
        """Add pressure summary section from summary_df DataFrame."""
        story.append(Paragraph("7. Pressure Summary", self.styles['SectionHeading']))
        
        # Get pressure_summary from results dictionary
        pressure_summary_data = self.results.get('pressure_summary')
        
        if pressure_summary_data and pressure_summary_data.get('_type') == 'dataframe':
            # Deserialize the DataFrame
            df = self.manager.deserialize_dataframe(pressure_summary_data)
            
            if df is not None and not df.empty:
                # Convert DataFrame to table data
                table_data = [list(df.columns)]
                
                # Data rows - format numeric values to 2 decimal places
                for idx, row in df.iterrows():
                    formatted_row = []
                    for col_name, val in row.items():
                        try:
                            if isinstance(val, (int, float)):
                                formatted_row.append(f"{val:.2f}")
                            else:
                                formatted_row.append(str(val))
                        except:
                            formatted_row.append(str(val))
                    table_data.append(formatted_row)
                
                # Create table with appropriate column widths
                num_cols = len(df.columns)
                col_widths = [self.content_width / num_cols] * num_cols
                
                table = self._create_table(table_data, col_widths=col_widths)
                story.append(table)
                story.append(Spacer(1, 12))
            else:
                story.append(Paragraph(
                    "<i>Pressure summary data not available.</i>",
                    self.styles['CustomBodyText']
                ))
                story.append(Spacer(1, 12))
        else:
            story.append(Paragraph(
                "<i>Pressure summary data not available.</i>",
                self.styles['CustomBodyText']
            ))
            story.append(Spacer(1, 12))
    
    def _add_summary_section(self, story):
        """Add overall summary section."""
        story.append(Paragraph("8. Summary", self.styles['SectionHeading']))
        
        # Create summary of key results
        summary_text = f"""
        This wind load calculation has been performed in accordance with EN 1991-1-4 
        for the {self.inputs.get('region', 'specified')} region.
        """
        
        story.append(Paragraph(summary_text, self.styles['CustomBodyText']))
        story.append(Spacer(1, 8))
        
        # Key results summary
        story.append(Paragraph("8.1 Key Results", self.styles['SubsectionHeading']))
        
        key_results_data = [
            ['Parameter', 'Value', 'Units'],
            ['Basic Wind Speed (V_b)', f"{self.inputs.get('v_b', 0.0):.2f}", 'm/s'],
            ['Basic Wind Pressure (q_b)', f"{self.results.get('q_b', 0.0):.3f}", 'kPa'],
            ['Peak Velocity Pressure (q_p)', f"{self.results.get('qp_value', 0.0):.3f}", 'kPa'],
        ]
        
        # Add mean wind velocity if calculated
        v_mean = self.results.get('v_mean', 0.0)
        if v_mean > 0.0:
            key_results_data.insert(3, ['Mean Wind Velocity (v_m)', f"{v_mean:.2f}", 'm/s'])
        
        col_widths = [self.content_width * 0.5, self.content_width * 0.3, self.content_width * 0.2]
        table = self._create_table(key_results_data, col_widths=col_widths)
        story.append(table)
        story.append(Spacer(1, 12))
        
        # Design recommendations
        story.append(Paragraph("8.2 Design Recommendations", self.styles['SubsectionHeading']))
        recommendations = f"""
        The peak velocity pressure of <b>{self.results.get('qp_value', 0.0):.3f} kPa</b> should be used 
        in combination with the external pressure coefficients provided in Section 6 to determine 
        the wind loads on the building facades.
        <br/><br/>
        For detailed facade design, refer to the pressure summary in Section 7 which provides 
        the wind pressures for different building zones and directions.
        """
        
        story.append(Paragraph(recommendations, self.styles['CustomBodyText']))
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
        story.append(Spacer(1, 12))
        
        # Add standard reference based on region
        region = self.inputs.get('region', '')
        if region == 'United Kingdom':
            reference_text = "BS EN 1991-1-4, United Kingdom National Annex, and PD 6688"
        else:
            reference_text = "BS EN 1991-1-4"
        
        story.append(Paragraph(
            f"<i>{reference_text}</i>",
            self.styles['CustomBodyText']
        ))
        story.append(Spacer(1, 12))
        
        # Report info
        story.append(Paragraph(
            f"<b>Report Generated:</b> {datetime.now().strftime('%B %d, %Y at %H:%M')}",
            self.styles['CustomBodyText']
        ))
        story.append(Paragraph(
            f"<b>Project:</b> {self.project_name}",
            self.styles['CustomBodyText']
        ))
        story.append(Spacer(1, 24))
        
        # Add all sections
        self._add_project_info_section(story)
        self._add_building_geometry_section(story)
        self._add_site_parameters_section(story)
        self._add_basic_wind_pressure_section(story)
        self._add_peak_wind_pressure_section(story)
        self._add_external_pressure_coefficients_section(story)
        self._add_pressure_summary_section(story)
        self._add_summary_section(story)
        
        # Build PDF
        doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        
        self.buffer.seek(0)
        return self.buffer


def create_pdf_report(project_name: Optional[str] = None) -> io.BytesIO:
    """
    Create a PDF report from current session state.
    
    Parameters
    ----------
    project_name : Optional[str]
        Project name to display in header
    
    Returns
    -------
    io.BytesIO
        Buffer containing the PDF report
    """
    report = WindLoadReport(project_name)
    return report.generate()


def add_pdf_download_button(
    filename: Optional[str] = None,
    button_label: str = "📄 Download PDF",
    project_name: Optional[str] = None
):
    """
    Add a download button to the Streamlit sidebar for the PDF report.
    Uses StateManager to automatically get data from session state.
    
    Parameters
    ----------
    filename : Optional[str]
        The filename for the downloaded PDF file. Auto-generated if None.
    button_label : str
        The label for the download button
    project_name : Optional[str]
        Project name to include in header
    """
    # Check if required data exists
    if not hasattr(st.session_state, 'inputs') or not st.session_state.inputs:
        st.sidebar.warning("⚠️ No data available. Complete calculations first.")
        return
    
    # Generate filename if not provided
    if filename is None:
        proj_name = project_name or st.session_state.inputs.get("project_name", "Wind_Load")
        safe_name = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in proj_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"{safe_name}_Report_{timestamp}.pdf"
    
    try:
        pdf_buffer = create_pdf_report(project_name)
        
        st.sidebar.download_button(
            label=button_label,
            data=pdf_buffer,
            file_name=filename,
            mime="application/pdf",
            help="Download wind load calculation report as PDF",
            use_container_width=True
        )
    except Exception as e:
        st.sidebar.error(f"❌ PDF generation failed: {str(e)}")
        # Show detailed error in expander for debugging
        with st.sidebar.expander("🔍 Error details"):
            st.exception(e)
