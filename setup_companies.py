#!/usr/bin/env python3
"""
Setup script to initialize the RAG system with sample company data.
Run this script to create sample companies and their documents.
"""

import os
from pathlib import Path
from rag_agent import CompanyRAGAgent

def create_sample_companies():
    """Create sample company data for demonstration."""
    
    # Sample company data
    companies_data = {
        "TechCorp": {
            "company_overview.txt": """
TechCorp - Leading AI and Machine Learning Solutions

About TechCorp:
TechCorp is a cutting-edge technology company founded in 2020, specializing in artificial intelligence and machine learning solutions for businesses of all sizes.

What We Do:
- Develop AI-powered software solutions for businesses
- Provide machine learning consulting services
- Create custom automation tools for enterprises
- Offer data analytics and business intelligence solutions
- Build chatbots and virtual assistants
- Develop computer vision applications

Our Services:
1. AI Consulting: Strategic guidance on AI implementation
2. Custom ML Models: Tailored machine learning solutions
3. Data Pipeline Development: End-to-end data processing systems
4. AI Training and Support: Educational programs for your team

Company Information:
- Founded: 2020
- Headquarters: San Francisco, CA
- Employees: 150
- Industries Served: Healthcare, Finance, Retail, Manufacturing
- Annual Revenue: $25M
            """,
            
            "company_policies.txt": """
TechCorp Company Policies

Work Arrangements:
- Remote Work Policy: Employees can work remotely up to 3 days per week
- Flexible Hours: Core hours 10 AM - 3 PM, flexible start and end times
- Office Requirements: Must be in office for team meetings on Wednesdays

Time Off and Benefits:
- Vacation Policy: 25 days of paid vacation per year
- Sick Leave: 10 days of paid sick leave annually
- Personal Days: 5 personal days per year
- Health Insurance: Comprehensive health, dental, and vision coverage
- Retirement: 401(k) with 4% company matching

Professional Development:
- Training Budget: Each employee gets $2000 annual budget for professional development
- Conference Attendance: Encouraged with company sponsorship
- Internal Learning: Weekly tech talks and learning sessions
- Certification Support: Company pays for relevant certifications

Code of Conduct:
- Confidentiality: All employees must maintain strict confidentiality of client data
- Integrity: Act with honesty and transparency in all business dealings
- Diversity: Commitment to inclusive and diverse workplace
- Data Security: Follow all cybersecurity protocols and best practices

Performance Reviews:
- Frequency: Quarterly check-ins and annual comprehensive reviews
- Promotion Criteria: Based on performance, leadership, and technical skills
- Feedback Culture: Regular 360-degree feedback encouraged
            """
        },
        
        "GreenEnergy": {
            "company_overview.txt": """
GreenEnergy Solutions - Sustainable Power for Tomorrow

About GreenEnergy Solutions:
GreenEnergy Solutions is a renewable energy company founded in 2015, dedicated to creating sustainable power generation solutions and helping businesses transition to clean energy.

What We Do:
- Design and install solar panel systems for residential and commercial properties
- Develop large-scale wind energy projects
- Provide energy storage solutions and battery systems
- Offer energy efficiency consulting and audits
- Implement smart grid technologies
- Develop renewable energy financing solutions

Our Services:
1. Solar Installation: Complete solar panel system design and installation
2. Wind Energy: Wind turbine development and maintenance
3. Energy Storage: Battery systems for energy storage and grid stability
4. Consulting: Energy efficiency audits and sustainability planning
5. Maintenance: Ongoing maintenance and monitoring services

Project Portfolio:
- 500+ Solar installations completed
- 15 Wind farms developed
- 2 GW of renewable energy capacity installed
- Serving 50,000+ customers across Texas and surrounding states

Company Information:
- Founded: 2015
- Headquarters: Austin, TX
- Employees: 300
- Service Areas: Texas, Oklahoma, New Mexico, Louisiana
- Annual Revenue: $150M
            """,
            
            "company_policies.txt": """
GreenEnergy Solutions Company Policies

Environmental Commitment:
- Carbon Neutral Goal: Achieve carbon neutral operations by 2025
- Sustainability: All company operations must minimize environmental impact
- Green Transportation: Electric vehicle fleet and charging stations
- Waste Reduction: Zero waste to landfill policy

Work Arrangements:
- Remote Work: Flexible remote work arrangements available
- Field Work: Safety protocols mandatory for all field operations
- Flexible Schedule: Compressed work weeks available (4x10 schedule)

Safety Policies:
- Field Safety: All field workers must complete monthly safety training
- Equipment Standards: Only certified and maintained equipment allowed
- Emergency Procedures: Comprehensive emergency response protocols
- Safety Reporting: Immediate reporting of all safety incidents required

Employee Benefits:
- Health Coverage: Comprehensive health, dental, and vision insurance
- Retirement: 401(k) with 6% company matching
- Stock Options: Employee stock option program available
- Vacation: 20 days paid vacation, increasing with tenure
- Education: $3000 annual education reimbursement

Professional Development:
- Technical Training: Regular training on latest renewable energy technologies
- Certifications: Company-sponsored industry certifications
- Leadership Development: Management training programs
- Safety Certifications: OSHA and industry-specific safety training

Diversity and Inclusion:
- Equal Opportunity: Commitment to equal employment opportunities
- Inclusive Culture: Regular diversity and inclusion training
- Community Engagement: Local community involvement and volunteer programs
            """
        },
        
        "FinanceFirst": {
            "company_overview.txt": """
FinanceFirst Bank - Your Trusted Financial Partner

About FinanceFirst Bank:
FinanceFirst Bank is a regional community bank founded in 1985, providing comprehensive financial services to individuals, families, and businesses across the Midwest.

What We Do:
- Personal Banking: Checking, savings, loans, and mortgage services
- Business Banking: Commercial loans, merchant services, and cash management
- Investment Services: Wealth management and financial planning
- Digital Banking: Online and mobile banking platforms
- Insurance Services: Life, auto, and property insurance
- Trust Services: Estate planning and trust management

Our Services:
1. Retail Banking: Full-service banking for individuals and families
2. Commercial Banking: Comprehensive business financial solutions
3. Mortgage Lending: Home loans and refinancing services
4. Investment Management: Portfolio management and financial planning
5. Digital Services: Award-winning online and mobile banking

Branch Network:
- 45 Branch locations across Illinois, Indiana, and Wisconsin
- 200+ ATMs in our network
- 24/7 Customer service hotline
- Comprehensive digital banking platform

Company Information:
- Founded: 1985
- Headquarters: Chicago, IL
- Employees: 800
- Assets: $5.2 Billion
- Customers: 150,000+
- FDIC Insured and Equal Housing Lender
            """,
            
            "company_policies.txt": """
FinanceFirst Bank Company Policies

Regulatory Compliance:
- Banking Regulations: Strict adherence to all federal and state banking laws
- Privacy Policy: Comprehensive customer data protection protocols
- Anti-Money Laundering: Robust AML compliance and monitoring
- Fair Lending: Equal opportunity lending practices

Customer Service Standards:
- Response Time: Customer inquiries answered within 24 hours
- Problem Resolution: Issues resolved within 5 business days
- Service Hours: Branches open Monday-Friday 9 AM-5 PM, Saturday 9 AM-1 PM
- Digital Support: 24/7 online and mobile banking support

Employee Policies:
- Work Schedule: Standard business hours with some weekend branch coverage
- Professional Development: $2500 annual training budget per employee
- Banking Certifications: Required industry certifications paid by company
- Code of Ethics: Strict ethical standards and conflict of interest policies

Benefits Package:
- Health Insurance: Premium health, dental, and vision coverage
- Retirement: 401(k) with 5% company matching and pension plan
- Vacation: 15-25 days based on tenure, plus holidays
- Banking Benefits: Free banking services and preferred loan rates

Security and Risk Management:
- Information Security: Comprehensive cybersecurity training and protocols
- Fraud Prevention: Regular fraud awareness training for all employees
- Physical Security: Strict access controls and security procedures
- Business Continuity: Comprehensive disaster recovery and continuity plans

Professional Standards:
- Licensing: Required banking licenses and continuing education
- Confidentiality: Strict customer information confidentiality requirements
- Dress Code: Professional business attire required
- Community Involvement: Encouraged participation in local community activities
            """
        }
    }
    
    try:
        # Create RAG agent
        agent = CompanyRAGAgent()
        
        print("Setting up sample companies...")
        
        # Add documents for each company
        for company_name, documents in companies_data.items():
            print(f"\nSetting up {company_name}...")
            
            for filename, content in documents.items():
                agent.add_company_document(company_name, content, filename)
                print(f"  Added {filename}")
        
        print(f"\n✅ Successfully set up {len(companies_data)} companies!")
        print("\nAvailable companies:")
        for company in agent.list_available_companies():
            print(f"  - {company}")
        
        print("\nYou can now ask questions like:")
        print("  - 'What does TechCorp do?'")
        print("  - 'What is GreenEnergy's vacation policy?'")
        print("  - 'What services does FinanceFirst Bank offer?'")
        
    except Exception as e:
        print(f"❌ Error setting up companies: {e}")

if __name__ == "__main__":
    create_sample_companies()
