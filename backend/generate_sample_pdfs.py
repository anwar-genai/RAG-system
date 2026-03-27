"""
Sample PDF Generator for RAG Knowledge Base

This script creates sample PDF documents for testing the RAG system.
Run this script from the backend directory after installing dependencies.
"""

from pathlib import Path
import sys

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.colors import HexColor
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
except ImportError:
    print("Error: reportlab is not installed.")
    print("Install it with: pip install reportlab")
    sys.exit(1)


def create_company_handbook():
    """Create a sample Company Handbook PDF"""
    kb_path = Path(__file__).parent / "knowledge_base"
    kb_path.mkdir(exist_ok=True)
    
    pdf_path = kb_path / "Company_Handbook.pdf"
    
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Add title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#667eea'),
        spaceAfter=30,
        alignment=TA_LEFT
    )
    story.append(Paragraph("COMPANY HANDBOOK 2026", title_style))
    story.append(Spacer(1, 12))
    
    # Introduction
    story.append(Paragraph("Welcome to Our Company", styles['Heading2']))
    story.append(Spacer(1, 12))
    intro_text = """Lorem ipsum dolor sit amet, consectetur adipiscing elit. Our company has been in business for over 20 years, 
    providing high-quality services to our valued clients. We believe in fostering a culture of innovation, collaboration, and excellence. 
    This handbook outlines our core values, policies, and procedures to help you succeed in your role."""
    story.append(Paragraph(intro_text, styles['BodyText']))
    story.append(Spacer(1, 20))
    
    # Core Values
    story.append(Paragraph("Core Values", styles['Heading2']))
    story.append(Spacer(1, 12))
    values = [
        "Integrity: We conduct our business with honesty and transparency.",
        "Innovation: We embrace new ideas and continuous improvement.",
        "Collaboration: We work together to achieve common goals.",
        "Excellence: We strive for the highest quality in everything we do.",
        "Customer Focus: We prioritize the needs and satisfaction of our clients.",
    ]
    for value in values:
        story.append(Paragraph(f"• {value}", styles['BodyText']))
    story.append(Spacer(1, 20))
    
    # Work Policies
    story.append(Paragraph("Work Policies", styles['Heading2']))
    story.append(Spacer(1, 12))
    work_policy = """Work hours are typically 9 AM to 5 PM, Monday through Friday. Flexible work arrangements may be available 
    upon approval. All employees are expected to maintain professional conduct and adhere to our code of ethics. Remote work is permitted 
    up to 3 days per week for eligible positions."""
    story.append(Paragraph(work_policy, styles['BodyText']))
    story.append(Spacer(1, 20))
    
    # Benefits
    story.append(Paragraph("Employee Benefits", styles['Heading2']))
    story.append(Spacer(1, 12))
    benefits = [
        "Comprehensive health insurance coverage",
        "401(k) retirement plan with company match",
        "Annual performance bonuses",
        "Professional development opportunities",
        "Paid time off: 3 weeks vacation + 10 holidays",
        "Gym membership subsidy",
        "Mental health counseling services",
    ]
    for benefit in benefits:
        story.append(Paragraph(f"• {benefit}", styles['BodyText']))
    
    doc.build(story)
    print(f"[OK] Created: {pdf_path}")


def create_product_guide():
    """Create a sample Product Guide PDF"""
    kb_path = Path(__file__).parent / "knowledge_base"
    kb_path.mkdir(exist_ok=True)
    
    pdf_path = kb_path / "Product_Guide.pdf"
    
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Add title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#764ba2'),
        spaceAfter=30,
        alignment=TA_LEFT
    )
    story.append(Paragraph("PRODUCT GUIDE v2.0", title_style))
    story.append(Spacer(1, 12))
    
    # Overview
    story.append(Paragraph("Product Overview", styles['Heading2']))
    story.append(Spacer(1, 12))
    overview = """Our flagship product is a comprehensive cloud-based platform designed to streamline business operations. 
    It integrates with your existing systems and provides real-time analytics, automated reporting, and advanced collaboration features."""
    story.append(Paragraph(overview, styles['BodyText']))
    story.append(Spacer(1, 20))
    
    # Key Features
    story.append(Paragraph("Key Features", styles['Heading2']))
    story.append(Spacer(1, 12))
    features = [
        "Real-time Data Synchronization: Keep all your data synchronized across devices and locations.",
        "Advanced Analytics: Get powerful insights with our AI-driven analytics engine.",
        "Role-Based Access: Granular permission controls for team members.",
        "Mobile App: Full functionality on iOS and Android platforms.",
        "API Integration: Easy integration with third-party applications.",
        "24/7 Support: Dedicated support team available round the clock.",
    ]
    for feature in features:
        story.append(Paragraph(f"• {feature}", styles['BodyText']))
    story.append(Spacer(1, 20))
    
    # Pricing
    story.append(Paragraph("Pricing Plans", styles['Heading2']))
    story.append(Spacer(1, 12))
    pricing = """Starter Plan: $29/month - Basic features, up to 5 users.
    Professional Plan: $79/month - Advanced features, up to 50 users.
    Enterprise Plan: Custom pricing - Unlimited users, dedicated support."""
    story.append(Paragraph(pricing, styles['BodyText']))
    story.append(Spacer(1, 20))
    
    # Getting Started
    story.append(Paragraph("Getting Started", styles['Heading2']))
    story.append(Spacer(1, 12))
    steps = [
        "Sign up for an account at www.example.com",
        "Verify your email address",
        "Complete your company profile",
        "Invite team members",
        "Configure your workspace",
        "Import your data",
    ]
    for i, step in enumerate(steps, 1):
        story.append(Paragraph(f"{i}. {step}", styles['BodyText']))
    
    doc.build(story)
    print(f"[OK] Created: {pdf_path}")


def create_faq_document():
    """Create a sample FAQ PDF"""
    kb_path = Path(__file__).parent / "knowledge_base"
    kb_path.mkdir(exist_ok=True)
    
    pdf_path = kb_path / "FAQ.pdf"
    
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Add title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#667eea'),
        spaceAfter=30,
        alignment=TA_LEFT
    )
    story.append(Paragraph("FREQUENTLY ASKED QUESTIONS", title_style))
    story.append(Spacer(1, 12))
    
    faqs = [
        ("What payment methods do you accept?", 
         "We accept all major credit cards (Visa, MasterCard, American Express), bank transfers, and PayPal."),
        ("Is there a free trial?", 
         "Yes, we offer a 14-day free trial with full access to all features. No credit card required."),
        ("Can I cancel anytime?", 
         "Absolutely. You can cancel your subscription at any time without penalties or hidden fees."),
        ("Do you offer data export?", 
         "Yes, you can export all your data in CSV or JSON format at any time."),
        ("What about data security?", 
         "We use military-grade encryption and comply with GDPR, HIPAA, and SOC 2 standards."),
        ("How often is the platform updated?", 
         "We release new features and improvements every two weeks. All updates are automatic."),
        ("Is there a mobile app?", 
         "Yes, our mobile app is available for iOS and Android with full feature parity."),
        ("What is your uptime guarantee?", 
         "We guarantee 99.9% uptime with 24/7 monitoring and support."),
    ]
    
    for question, answer in faqs:
        story.append(Paragraph(f"Q: {question}", styles['Heading3']))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"A: {answer}", styles['BodyText']))
        story.append(Spacer(1, 12))
    
    doc.build(story)
    print(f"[OK] Created: {pdf_path}")


if __name__ == "__main__":
    print("\n" + "="*50)
    print("Sample PDF Generator for RAG Knowledge Base")
    print("="*50 + "\n")
    
    try:
        create_company_handbook()
        create_product_guide()
        create_faq_document()
        
        print("\n" + "="*50)
        print("All sample PDFs created successfully!")
        print("="*50)
        print("\nGenerated files:")
        print("  1. Company_Handbook.pdf")
        print("  2. Product_Guide.pdf")
        print("  3. FAQ.pdf")
        print("\nThese files are now in backend/knowledge_base/")
        print("Restart the Django server to load them into the RAG system.")
        print("")
        
    except Exception as e:
        print(f"\nError creating PDFs: {e}")
        sys.exit(1)
