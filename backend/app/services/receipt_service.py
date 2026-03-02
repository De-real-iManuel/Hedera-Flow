"""
Receipt Generation Service
Generates PDF receipts for bill payments with transaction details
"""
import os
import io
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
import logging
import qrcode
from qrcode.image.pil import PilImage

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

logger = logging.getLogger(__name__)


class ReceiptService:
    """
    Service for generating PDF receipts for bill payments
    
    Requirements:
        - FR-6.10: System shall generate receipt (PDF) showing HBAR amount paid,
          fiat equivalent, exchange rate used, timestamp
        - US-7: Receipt should include transaction ID, HBAR amount paid,
          fiat equivalent at time of payment, exchange rate used, timestamp,
          Hedera Explorer link (HashScan), PDF download option
    """
    
    # HashScan explorer URLs
    HASHSCAN_BASE_URL = "https://hashscan.io/testnet"
    
    # Currency symbols
    CURRENCY_SYMBOLS = {
        'EUR': '€',
        'USD': '$',
        'INR': '₹',
        'BRL': 'R$',
        'NGN': '₦'
    }
    
    # Brand colors (from design.md)
    BRAND_BLACK = colors.HexColor('#000000')
    BRAND_PURPLE = colors.HexColor('#7C3AED')
    BRAND_GRAY = colors.HexColor('#6B7280')
    BRAND_LIGHT_GRAY = colors.HexColor('#F9FAFB')
    BRAND_SUCCESS = colors.HexColor('#10B981')
    
    def __init__(self):
        """Initialize receipt service"""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
        # Determine logo path (relative to backend directory)
        self.logo_path = self._find_logo_path()
    
    def _setup_custom_styles(self):
        """Set up custom paragraph styles for the receipt"""
        # Title style (using brand black)
        self.styles.add(ParagraphStyle(
            name='ReceiptTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=self.BRAND_BLACK,
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle style (using brand gray)
        self.styles.add(ParagraphStyle(
            name='ReceiptSubtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=self.BRAND_GRAY,
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        
        # Section header style (using brand black)
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=self.BRAND_BLACK,
            spaceAfter=8,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Label style (using brand gray)
        self.styles.add(ParagraphStyle(
            name='Label',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.BRAND_GRAY,
            spaceAfter=2
        ))
        
        # Value style (using brand black)
        self.styles.add(ParagraphStyle(
            name='Value',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=self.BRAND_BLACK,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ))
    
    def _find_logo_path(self) -> Optional[str]:
        """
        Find the Hedera Flow logo file
        
        Returns:
            Path to logo file if found, None otherwise
        """
        # Possible logo locations (relative to backend directory)
        possible_paths = [
            '../src/assets/hedera-flow-logo.png',
            'assets/hedera-flow-logo.png',
            'static/hedera-flow-logo.png',
            '../public/hedera-flow-logo.png',
        ]
        
        for path in possible_paths:
            full_path = os.path.join(os.path.dirname(__file__), '..', '..', path)
            if os.path.exists(full_path):
                logger.info(f"Found logo at: {full_path}")
                return full_path
        
        logger.warning("Logo file not found, receipt will be generated without logo")
        return None
    
    def _generate_qr_code(self, data: str) -> io.BytesIO:
        """
        Generate a QR code image for the given data
        
        Args:
            data: String data to encode in QR code (typically a URL)
        
        Returns:
            BytesIO buffer containing the QR code image
        """
        # Create QR code instance with high error correction
        qr = qrcode.QRCode(
            version=1,  # Auto-adjust size
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction (30%)
            box_size=10,
            border=4,
        )
        
        # Add data and generate
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to buffer
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer
    
    def generate_receipt_pdf(
        self,
        bill_data: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Generate a PDF receipt for a bill payment
        
        Args:
            bill_data: Dictionary containing bill and payment information:
                - bill_id: UUID of the bill
                - consumption_kwh: Energy consumption in kWh
                - base_charge: Base charge amount
                - taxes: Tax amount
                - subsidies: Subsidy amount (if any)
                - total_fiat: Total amount in fiat currency
                - currency: Currency code (EUR, USD, INR, BRL, NGN)
                - amount_hbar: HBAR amount paid
                - exchange_rate: Exchange rate used (HBAR price in fiat)
                - hedera_tx_id: Hedera transaction ID
                - consensus_timestamp: Transaction consensus timestamp
                - paid_at: Payment timestamp
                - user_email: User's email address
                - meter_id: Meter ID
            output_path: Optional file path to save PDF (if None, returns bytes)
        
        Returns:
            PDF file as bytes
        
        Raises:
            ValueError: If required bill data is missing
        """
        # Validate required fields
        required_fields = [
            'bill_id', 'total_fiat', 'currency', 'amount_hbar',
            'exchange_rate', 'hedera_tx_id', 'consensus_timestamp'
        ]
        for field in required_fields:
            if field not in bill_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Create PDF buffer
        buffer = io.BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Build PDF content
        story = []
        
        # Add header
        story.extend(self._build_header())
        
        # Add receipt info
        story.extend(self._build_receipt_info(bill_data))
        
        # Add transaction details
        story.extend(self._build_transaction_details(bill_data))
        
        # Add billing breakdown
        story.extend(self._build_billing_breakdown(bill_data))
        
        # Add payment summary
        story.extend(self._build_payment_summary(bill_data))
        
        # Add footer
        story.extend(self._build_footer(bill_data))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        # Save to file if path provided
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
            logger.info(f"Receipt saved to {output_path}")
        
        return pdf_bytes
    
    def _build_header(self) -> list:
        """Build receipt header with logo and title"""
        elements = []
        
        # Add logo if available
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                # Create logo image with appropriate size
                logo = Image(self.logo_path, width=2*inch, height=0.5*inch)
                
                # Center the logo
                logo_table = Table([[logo]], colWidths=[6.5*inch])
                logo_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                    ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
                ]))
                elements.append(logo_table)
                elements.append(Spacer(1, 0.2*inch))
                
                logger.info("Added logo to receipt header")
            except Exception as e:
                logger.error(f"Failed to add logo to receipt: {e}")
                # Continue without logo
        
        # Title
        title = Paragraph("PAYMENT RECEIPT", self.styles['ReceiptTitle'])
        elements.append(title)
        
        # Subtitle with brand tagline
        subtitle = Paragraph(
            "Hedera Flow - Blockchain-Verified Utility Payment",
            self.styles['ReceiptSubtitle']
        )
        elements.append(subtitle)
        
        # Professional divider line with brand color
        divider_table = Table([['']], colWidths=[6.5*inch])
        divider_table.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, -1), 2, self.BRAND_PURPLE),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(divider_table)
        
        # Spacing after header
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _build_receipt_info(self, bill_data: Dict[str, Any]) -> list:
        """Build receipt information section"""
        elements = []
        
        # Receipt details table
        receipt_data = [
            ['Receipt ID:', str(bill_data['bill_id'])[:8].upper()],
            ['Date Issued:', datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')],
        ]
        
        if 'user_email' in bill_data:
            receipt_data.append(['Customer:', bill_data['user_email']])
        
        if 'meter_id' in bill_data:
            receipt_data.append(['Meter ID:', bill_data['meter_id']])
        
        table = Table(receipt_data, colWidths=[1.5*inch, 4.5*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6B7280')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#000000')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _build_transaction_details(self, bill_data: Dict[str, Any]) -> list:
        """Build Hedera transaction details section with QR code"""
        elements = []
        
        # Section header
        header = Paragraph("Blockchain Transaction Details", self.styles['SectionHeader'])
        elements.append(header)
        
        # Transaction details
        tx_id = bill_data['hedera_tx_id']
        consensus_time = bill_data['consensus_timestamp']
        
        if isinstance(consensus_time, datetime):
            consensus_str = consensus_time.strftime('%B %d, %Y at %H:%M:%S UTC')
        else:
            consensus_str = str(consensus_time)
        
        # Build HashScan link
        hashscan_url = f"{self.HASHSCAN_BASE_URL}/transaction/{tx_id}"
        
        # Generate QR code for HashScan URL
        try:
            qr_buffer = self._generate_qr_code(hashscan_url)
            qr_image = Image(qr_buffer, width=1.5*inch, height=1.5*inch)
            logger.info(f"Generated QR code for transaction {tx_id}")
        except Exception as e:
            logger.error(f"Failed to generate QR code: {e}")
            qr_image = None
        
        # Transaction details table
        tx_data = [
            ['Transaction ID:', tx_id],
            ['Consensus Time:', consensus_str],
            ['Network:', 'Hedera Testnet'],
            ['Explorer Link:', hashscan_url],
        ]
        
        tx_table = Table(tx_data, colWidths=[1.5*inch, 4.5*inch])
        tx_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6B7280')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#000000')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(tx_table)
        
        # Add QR code section if generated successfully
        if qr_image:
            elements.append(Spacer(1, 0.2*inch))
            
            # QR code label
            qr_label = Paragraph(
                "Scan to view transaction on HashScan:",
                ParagraphStyle(
                    name='QRLabel',
                    parent=self.styles['Normal'],
                    fontSize=9,
                    textColor=colors.HexColor('#6B7280'),
                    alignment=TA_CENTER,
                    spaceAfter=6
                )
            )
            elements.append(qr_label)
            
            # Center the QR code
            qr_table = Table([[qr_image]], colWidths=[6*inch])
            qr_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
            ]))
            elements.append(qr_table)
        
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _build_billing_breakdown(self, bill_data: Dict[str, Any]) -> list:
        """Build itemized billing breakdown with detailed charges"""
        elements = []
        
        # Section header
        header = Paragraph("Billing Breakdown", self.styles['SectionHeader'])
        elements.append(header)
        
        currency = bill_data['currency']
        symbol = self.CURRENCY_SYMBOLS.get(currency, currency)
        
        # Build breakdown data
        breakdown_data = [
            ['Description', 'Amount'],
        ]
        
        # 1. Consumption Information
        consumption_kwh = bill_data.get('consumption_kwh', 0)
        breakdown_data.append([
            f"Energy Consumption",
            f"{float(consumption_kwh):.2f} kWh"
        ])
        
        # 2. Base/Energy Charge (with rate if available)
        base_charge = float(bill_data.get('base_charge', 0))
        if consumption_kwh > 0:
            rate_per_kwh = base_charge / float(consumption_kwh)
            breakdown_data.append([
                f"Base Charge ({rate_per_kwh:.4f} {symbol}/kWh)",
                f"{symbol}{base_charge:.2f}"
            ])
        else:
            breakdown_data.append([
                'Base Charge',
                f"{symbol}{base_charge:.2f}"
            ])
        
        # 3. Detailed breakdown from tariff_snapshot if available
        tariff_snapshot = bill_data.get('tariff_snapshot', {})
        breakdown = bill_data.get('breakdown', {})
        
        # Show rate structure details if available
        if tariff_snapshot:
            rate_type = tariff_snapshot.get('rate_structure_type', '')
            
            # For tiered rates, show tier breakdown
            if rate_type == 'tiered' and breakdown:
                tiers = breakdown.get('tiers', [])
                if tiers:
                    breakdown_data.append([
                        '  Tier Breakdown:',
                        ''
                    ])
                    for tier in tiers:
                        tier_name = tier.get('tier', 'Tier')
                        tier_kwh = tier.get('kwh', 0)
                        tier_rate = tier.get('rate', 0)
                        tier_charge = tier.get('charge', 0)
                        breakdown_data.append([
                            f"    {tier_name}: {tier_kwh:.2f} kWh @ {symbol}{tier_rate:.4f}/kWh",
                            f"{symbol}{tier_charge:.2f}"
                        ])
            
            # For time-of-use, show period breakdown
            elif rate_type == 'time_of_use' and breakdown:
                periods = breakdown.get('periods', [])
                if periods:
                    breakdown_data.append([
                        '  Time-of-Use Breakdown:',
                        ''
                    ])
                    for period in periods:
                        period_name = period.get('period', 'Period')
                        period_kwh = period.get('kwh', 0)
                        period_rate = period.get('rate', 0)
                        period_charge = period.get('charge', 0)
                        breakdown_data.append([
                            f"    {period_name}: {period_kwh:.2f} kWh @ {symbol}{period_rate:.4f}/kWh",
                            f"{symbol}{period_charge:.2f}"
                        ])
            
            # For band-based (Nigeria), show band info
            elif rate_type == 'band_based' and breakdown:
                band = breakdown.get('band', '')
                rate = breakdown.get('rate', 0)
                if band:
                    breakdown_data.append([
                        f"  Band {band} Rate",
                        f"{symbol}{rate:.4f}/kWh"
                    ])
        
        # 4. Distribution/Service Charges (if separate from base)
        distribution_charge = bill_data.get('distribution_charge', 0)
        if distribution_charge and float(distribution_charge) > 0:
            breakdown_data.append([
                'Distribution Charge',
                f"{symbol}{float(distribution_charge):.2f}"
            ])
        
        service_charge = bill_data.get('service_charge', 0)
        if service_charge and float(service_charge) > 0:
            breakdown_data.append([
                'Service Charge',
                f"{symbol}{float(service_charge):.2f}"
            ])
        
        # 5. Subtotal before taxes
        subtotal_before_tax = base_charge
        if distribution_charge:
            subtotal_before_tax += float(distribution_charge)
        if service_charge:
            subtotal_before_tax += float(service_charge)
        
        breakdown_data.append([
            'Subtotal (before taxes)',
            f"{symbol}{subtotal_before_tax:.2f}"
        ])
        
        # 6. Taxes and Fees (detailed breakdown)
        taxes = float(bill_data.get('taxes', 0))
        if taxes > 0:
            # Try to show tax breakdown if available
            tax_breakdown = bill_data.get('tax_breakdown', {})
            if tax_breakdown:
                vat = tax_breakdown.get('vat', 0)
                vat_rate = tax_breakdown.get('vat_rate', 0)
                if vat > 0:
                    breakdown_data.append([
                        f"VAT ({vat_rate * 100:.1f}%)",
                        f"{symbol}{float(vat):.2f}"
                    ])
                
                other_taxes = tax_breakdown.get('other_taxes', 0)
                if other_taxes > 0:
                    breakdown_data.append([
                        'Other Taxes & Fees',
                        f"{symbol}{float(other_taxes):.2f}"
                    ])
            else:
                # Show total taxes if breakdown not available
                breakdown_data.append([
                    'Taxes & Fees',
                    f"{symbol}{taxes:.2f}"
                ])
        
        # 7. Subsidies (shown as negative)
        subsidies = float(bill_data.get('subsidies', 0))
        if subsidies > 0:
            breakdown_data.append([
                'Subsidies',
                f"-{symbol}{subsidies:.2f}"
            ])
        
        # 8. Platform Service Charge (if applicable)
        platform_charge = bill_data.get('platform_service_charge', 0)
        if platform_charge and float(platform_charge) > 0:
            breakdown_data.append([
                'Platform Service Charge (3%)',
                f"{symbol}{float(platform_charge):.2f}"
            ])
        
        platform_vat = bill_data.get('platform_vat', 0)
        if platform_vat and float(platform_vat) > 0:
            breakdown_data.append([
                'Platform VAT',
                f"{symbol}{float(platform_vat):.2f}"
            ])
        
        # 9. Total Amount (bold separator line)
        breakdown_data.append([
            'Total Amount',
            f"{symbol}{float(bill_data['total_fiat']):.2f}"
        ])
        
        # Create table with appropriate styling
        table = Table(breakdown_data, colWidths=[4*inch, 2*inch])
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#000000')),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 9),
            ('TEXTCOLOR', (0, 1), (-1, -2), colors.HexColor('#374151')),
            ('ALIGN', (1, 1), (1, -2), 'RIGHT'),
            ('BOTTOMPADDING', (0, 1), (-1, -2), 6),
            ('TOPPADDING', (0, 1), (-1, -2), 4),
            
            # Total row
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 11),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#000000')),
            ('ALIGN', (1, -1), (1, -1), 'RIGHT'),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#000000')),
            ('TOPPADDING', (0, -1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 8),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _build_payment_summary(self, bill_data: Dict[str, Any]) -> list:
        """Build payment summary with HBAR details"""
        elements = []
        
        # Section header
        header = Paragraph("Payment Summary", self.styles['SectionHeader'])
        elements.append(header)
        
        currency = bill_data['currency']
        symbol = self.CURRENCY_SYMBOLS.get(currency, currency)
        amount_hbar = float(bill_data['amount_hbar'])
        exchange_rate = float(bill_data['exchange_rate'])
        total_fiat = float(bill_data['total_fiat'])
        
        # Payment summary data
        summary_data = [
            ['Amount Paid (HBAR):', f"{amount_hbar:.8f} ℏ"],
            ['Exchange Rate:', f"1 ℏ = {symbol}{exchange_rate:.6f}"],
            ['Fiat Equivalent:', f"{symbol}{total_fiat:.2f} {currency}"],
        ]
        
        if 'paid_at' in bill_data:
            paid_at = bill_data['paid_at']
            if isinstance(paid_at, datetime):
                paid_str = paid_at.strftime('%B %d, %Y at %H:%M UTC')
            else:
                paid_str = str(paid_at)
            summary_data.append(['Payment Date:', paid_str])
        
        table = Table(summary_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6B7280')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#000000')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F9FAFB')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.4*inch))
        
        return elements
    
    def _build_footer(self, bill_data: Dict[str, Any]) -> list:
        """Build receipt footer with verification info and branding"""
        elements = []
        
        # Professional divider line before footer
        divider_table = Table([['']], colWidths=[6.5*inch])
        divider_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(divider_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Verification badge with brand success color
        verification_text = (
            "✓ <b>BLOCKCHAIN VERIFIED</b><br/>"
            "This payment has been verified on the Hedera blockchain. "
            "You can verify this transaction independently using the transaction ID above "
            f"on HashScan: {self.HASHSCAN_BASE_URL}/transaction/{bill_data['hedera_tx_id']}"
        )
        
        verification = Paragraph(
            verification_text,
            ParagraphStyle(
                name='Verification',
                parent=self.styles['Normal'],
                fontSize=9,
                textColor=self.BRAND_SUCCESS,
                alignment=TA_CENTER,
                spaceAfter=16,
                leading=12
            )
        )
        elements.append(verification)
        
        # Brand tagline
        tagline = Paragraph(
            "<b>Hedera Flow</b> - Fair Billing for 5B+ Consumers",
            ParagraphStyle(
                name='Tagline',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=self.BRAND_BLACK,
                alignment=TA_CENTER,
                spaceAfter=8,
                fontName='Helvetica-Bold'
            )
        )
        elements.append(tagline)
        
        # Footer text with contact info
        footer_text = (
            "This receipt is generated by Hedera Flow, a blockchain-powered utility verification platform.<br/>"
            "For questions or support, please contact <b>support@hederaflow.com</b><br/>"
            "Visit us at <b>www.hederaflow.com</b>"
        )
        
        footer = Paragraph(
            footer_text,
            ParagraphStyle(
                name='Footer',
                parent=self.styles['Normal'],
                fontSize=8,
                textColor=self.BRAND_GRAY,
                alignment=TA_CENTER,
                leading=10
            )
        )
        elements.append(footer)
        
        # Powered by Hedera badge
        elements.append(Spacer(1, 0.15*inch))
        powered_by = Paragraph(
            "Powered by <b>Hedera Hashgraph</b> • Testnet",
            ParagraphStyle(
                name='PoweredBy',
                parent=self.styles['Normal'],
                fontSize=7,
                textColor=self.BRAND_PURPLE,
                alignment=TA_CENTER
            )
        )
        elements.append(powered_by)
        
        return elements


# Singleton instance
_receipt_service = None


def get_receipt_service() -> ReceiptService:
    """
    Get or create the receipt service singleton instance
    
    Returns:
        ReceiptService instance
    """
    global _receipt_service
    if _receipt_service is None:
        _receipt_service = ReceiptService()
    return _receipt_service
