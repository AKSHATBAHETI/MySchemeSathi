from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from textwrap import wrap
from datetime import datetime

def generate_schemes_pdf(schemes: list[dict], output_path: str, user_profile_summary: str = ""):
    """
    Generate a professional PDF with eligible schemes.
    
    Args:
        schemes: List of scheme dicts with keys: source_url, scheme_name, objective, eligibility_reason
        output_path: Path to save PDF
        user_profile_summary: Summary of user profile
    """
    # Create PDF with proper styling
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    # Define colors
    HEADER_COLOR = colors.HexColor('#1e3a8a')  # Deep blue
    ACCENT_COLOR = colors.HexColor('#2563eb')  # Medium blue
    LIGHT_GRAY = colors.HexColor('#f3f4f6')   # Light gray background
    DARK_TEXT = colors.HexColor('#111827')    # Dark gray text
    
    x = 40
    y = height - 40
    
    # ===== HEADER SECTION =====
    # Title with background
    c.setFillColor(HEADER_COLOR)
    c.rect(0, y - 50, width, 60, fill=True, stroke=False)
    
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(colors.white)
    c.drawString(x, y - 30, "Your Eligible Government Schemes")
    
    c.setFont("Helvetica", 9)
    c.drawString(x, y - 42, f"Generated on: {datetime.now().strftime('%d %B %Y')}")
    
    y -= 70
    
    # ===== USER PROFILE SECTION =====
    if user_profile_summary:
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(ACCENT_COLOR)
        c.drawString(x, y, "📋 Your Profile Information:")
        y -= 18
        
        # Profile background box
        c.setFillColor(LIGHT_GRAY)
        c.setStrokeColor(ACCENT_COLOR)
        c.setLineWidth(1)
        profile_lines = user_profile_summary.split('\n')[:6]
        profile_height = len(profile_lines) * 12 + 10
        c.rect(x, y - profile_height, width - 2*x, profile_height, fill=True, stroke=True)
        
        c.setFont("Helvetica", 9)
        c.setFillColor(DARK_TEXT)
        for line in profile_lines:
            if line.strip():
                c.drawString(x + 10, y - 8, f"• {line.strip()}")
            y -= 12
        
        y -= 15
    
    # ===== SCHEMES SECTION =====
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(HEADER_COLOR)
    c.drawString(x, y, f"✓ Found {len(schemes)} Eligible Scheme{'s' if len(schemes) != 1 else ''}")
    y -= 20
    
    # ===== SCHEMES LIST =====
    for idx, scheme in enumerate(schemes, 1):
        # Check if we need a new page
        if y < 150:
            c.showPage()
            y = height - 40
        
        # Scheme number and name box
        c.setFillColor(ACCENT_COLOR)
        c.rect(x, y - 25, width - 2*x, 28, fill=True, stroke=False)
        
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.white)
        scheme_name = scheme.get("scheme_name", "Unknown Scheme")[:50]
        c.drawString(x + 10, y - 17, f"{idx}. {scheme_name}")
        
        y -= 35
        
        # Eligibility reason
        reason = scheme.get("eligibility_reason", "")
        if reason:
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(DARK_TEXT)
            c.drawString(x, y, "Why You're Eligible:")
            y -= 12
            
            c.setFont("Helvetica", 8.5)
            c.setFillColor(colors.HexColor('#4b5563'))
            reason_text = reason[:200]
            for line in wrap(reason_text, 95):
                if y < 100:
                    c.showPage()
                    y = height - 40
                c.drawString(x + 10, y, f"→ {line}")
                y -= 10
            
            y -= 5
        
        # Scheme details
        objective = scheme.get("objective", "No details available")
        if isinstance(objective, str):
            details_text = objective[:250]
        else:
            details_text = str(objective)[:250]
        
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(ACCENT_COLOR)
        c.drawString(x, y, "Scheme Details:")
        y -= 11
        
        c.setFont("Helvetica", 8.5)
        c.setFillColor(DARK_TEXT)
        for line in wrap(details_text, 95):
            if y < 100:
                c.showPage()
                y = height - 40
            c.drawString(x + 10, y, line)
            y -= 9
        
        # Source URL
        source_url = scheme.get("source_url", "")
        if source_url:
            y -= 5
            c.setFont("Helvetica", 8)
            c.setFillColor(colors.HexColor('#2563eb'))
            url_display = source_url[:60] + "..." if len(source_url) > 60 else source_url
            c.drawString(x, y, f"Link: {url_display}")
        
        y -= 20
        
        # Divider line
        c.setStrokeColor(LIGHT_GRAY)
        c.setLineWidth(1)
        c.line(x, y, width - x, y)
        y -= 12
    
    # ===== FOOTER =====
    if y < 80:
        c.showPage()
        y = height - 40
    
    y -= 20
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor('#6b7280'))
    c.drawString(x, y, "For more information about these schemes, visit: https://www.myscheme.gov.in")
    c.drawString(x, y - 12, "Last Updated: January 2026")
    
    c.save()
    print(f"[PDF] Generated professional PDF at {output_path}")

