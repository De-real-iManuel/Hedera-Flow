"""
Receipt generation service for prepaid token purchases.
Generates PDF receipts with QR codes and blockchain verification.
"""
from datetime import datetime
from typing import Dict, Any
import qrcode
from io import BytesIO
import base64

class ReceiptService:
    """Generate receipts for token purchases"""
    
    def generate_token_receipt(self, token_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate a formatted receipt for a prepaid token purchase.
        
        Args:
            token_data: Token information from database
            
        Returns:
            Dictionary with text, html, and qr_code formats
        """
        # Extract data
        token_id = token_data['token_id']
        sts_token = token_data.get('sts_token')
        amount_fiat = token_data['amount_paid_fiat']
        amount_hbar = token_data.get('amount_paid_hbar', 0)
        currency = token_data['currency']
        units = token_data['units_purchased']
        tariff_rate = token_data['tariff_rate']
        exchange_rate = token_data['exchange_rate']
        hedera_tx_id = token_data.get('hedera_tx_id', 'Pending')
        hcs_topic_id = token_data.get('hcs_topic_id', 'N/A')
        issued_at = token_data['issued_at']
        expires_at = token_data['expires_at']
        status = token_data['status']
        
        # Generate HashScan link
        hashscan_link = self._generate_hashscan_link(hedera_tx_id)
        
        # Generate QR code
        qr_code_data = self._generate_qr_code(token_id, hashscan_link)
        
        # Generate text receipt
        text_receipt = self._generate_text_receipt(
            token_id, sts_token, amount_fiat, amount_hbar, currency, units,
            tariff_rate, exchange_rate, hedera_tx_id, hcs_topic_id,
            issued_at, expires_at, status, hashscan_link
        )
        
        # Generate HTML receipt
        html_receipt = self._generate_html_receipt(
            token_id, amount_fiat, amount_hbar, currency, units,
            tariff_rate, exchange_rate, hedera_tx_id, hcs_topic_id,
            issued_at, expires_at, status, hashscan_link, qr_code_data
        )
        
        return {
            'text': text_receipt,
            'html': html_receipt,
            'qr_code': qr_code_data,
            'hashscan_link': hashscan_link
        }
    
    def _generate_text_receipt(
        self, token_id: str, sts_token: str, amount_fiat: float, amount_hbar: float,
        currency: str, units: float, tariff_rate: float, exchange_rate: float,
        hedera_tx_id: str, hcs_topic_id: str, issued_at: datetime,
        expires_at: datetime, status: str, hashscan_link: str
    ) -> str:
        """Generate plain text receipt"""
        
        sts_section = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STS TOKEN (FOR PHYSICAL METER)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STS Token:     {sts_token}
Instructions:  Enter this 20-digit token into your
               electricity meter keypad to load units.
""" if sts_token else ""
        
        return f"""
🌊 HEDERA FLOW - Token Purchase Confirmed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PAYMENT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Amount:        {currency} {amount_fiat:,.2f}
Paid with:     {amount_hbar:.6f} HBAR
Exchange Rate: {exchange_rate:.2f} {currency}/HBAR
Transaction:   {hedera_tx_id[:20]}...
{sts_section}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOKEN DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Token ID:      {token_id}
Units:         {units:.2f} kWh
Tariff:        {tariff_rate:.2f} {currency}/kWh
Status:        {status.upper()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BLOCKCHAIN VERIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Network:       Hedera Testnet
HCS Topic:     {hcs_topic_id}
Status:        ✓ Verified & Immutable

View on HashScan:
{hashscan_link}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VALIDITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Issued:        {issued_at.strftime('%d %b %Y, %H:%M UTC')}
Expires:       {expires_at.strftime('%d %b %Y, %H:%M UTC')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Need help? support@hederaflow.com
Powered by Hedera Hashgraph 🌊
"""
    
    def _generate_html_receipt(
        self, token_id: str, amount_fiat: float, amount_hbar: float,
        currency: str, units: float, tariff_rate: float, exchange_rate: float,
        hedera_tx_id: str, hcs_topic_id: str, issued_at: datetime,
        expires_at: datetime, status: str, hashscan_link: str, qr_code: str
    ) -> str:
        """Generate HTML receipt for email"""
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #00D4AA 0%, #0080FF 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .section {{ background: #f8f9fa; padding: 20px; margin: 10px 0; border-radius: 5px; }}
        .section-title {{ font-weight: bold; color: #333; margin-bottom: 10px; font-size: 14px; text-transform: uppercase; }}
        .detail-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e0e0e0; }}
        .detail-label {{ color: #666; }}
        .detail-value {{ font-weight: bold; color: #333; }}
        .token-id {{ font-size: 24px; font-weight: bold; color: #00D4AA; text-align: center; padding: 20px; background: white; border-radius: 5px; margin: 20px 0; }}
        .verification-badge {{ background: #00D4AA; color: white; padding: 10px 20px; border-radius: 20px; display: inline-block; margin: 10px 0; }}
        .qr-code {{ text-align: center; padding: 20px; }}
        .button {{ background: #00D4AA; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0; }}
        .footer {{ text-align: center; color: #666; padding: 20px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🌊 HEDERA FLOW</h1>
        <p>Token Purchase Confirmed</p>
    </div>
    
    <div class="token-id">{token_id}</div>
    
    <div class="section">
        <div class="section-title">Payment Details</div>
        <div class="detail-row">
            <span class="detail-label">Amount</span>
            <span class="detail-value">{currency} {amount_fiat:,.2f}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Paid with</span>
            <span class="detail-value">{amount_hbar:.6f} HBAR</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Exchange Rate</span>
            <span class="detail-value">{exchange_rate:.2f} {currency}/HBAR</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Transaction</span>
            <span class="detail-value" style="font-size: 10px;">{hedera_tx_id[:30]}...</span>
        </div>
    </div>
    
    <div class="section">
        <div class="section-title">Token Details</div>
        <div class="detail-row">
            <span class="detail-label">Units Purchased</span>
            <span class="detail-value">{units:.2f} kWh</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Tariff Rate</span>
            <span class="detail-value">{tariff_rate:.2f} {currency}/kWh</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Status</span>
            <span class="detail-value">{status.upper()}</span>
        </div>
    </div>
    
    <div class="section">
        <div class="section-title">Blockchain Verification</div>
        <div style="text-align: center;">
            <span class="verification-badge">✓ Verified & Immutable</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Network</span>
            <span class="detail-value">Hedera Testnet</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">HCS Topic</span>
            <span class="detail-value">{hcs_topic_id}</span>
        </div>
        <div style="text-align: center; margin-top: 20px;">
            <a href="{hashscan_link}" class="button">View on HashScan</a>
        </div>
    </div>
    
    <div class="section">
        <div class="section-title">Validity</div>
        <div class="detail-row">
            <span class="detail-label">Issued</span>
            <span class="detail-value">{issued_at.strftime('%d %b %Y, %H:%M UTC')}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Expires</span>
            <span class="detail-value">{expires_at.strftime('%d %b %Y, %H:%M UTC')}</span>
        </div>
    </div>
    
    <div class="qr-code">
        <p style="color: #666; font-size: 12px;">Scan to verify on blockchain</p>
        <img src="data:image/png;base64,{qr_code}" alt="QR Code" style="max-width: 200px;">
    </div>
    
    <div class="footer">
        <p>Need help? <a href="mailto:support@hederaflow.com">support@hederaflow.com</a></p>
        <p>Powered by Hedera Hashgraph 🌊</p>
    </div>
</body>
</html>
"""
    
    def _generate_hashscan_link(self, hedera_tx_id: str) -> str:
        """Generate HashScan link for transaction"""
        if not hedera_tx_id or hedera_tx_id == 'Pending':
            return "https://hashscan.io/testnet"
        
        # Handle EVM format (0x...)
        if hedera_tx_id.startswith('0x'):
            return f"https://hashscan.io/testnet/transaction/{hedera_tx_id}"
        
        # Handle native Hedera format (0.0.xxx@timestamp)
        return f"https://hashscan.io/testnet/transaction/{hedera_tx_id}"
    
    def _generate_qr_code(self, token_id: str, hashscan_link: str) -> str:
        """Generate QR code with token verification link"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(hashscan_link)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return img_str
