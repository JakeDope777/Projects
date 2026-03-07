"""
Industry Domain Profiles

Pre-configured research profiles for different industries. Each domain
profile contains industry-specific research parameters, relevant KPIs,
typical competitors, SWOT/PESTEL factors, persona templates, and
trend monitoring keywords.
"""

from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Domain profile registry
# ---------------------------------------------------------------------------

DOMAIN_PROFILES: dict[str, dict] = {

    # -----------------------------------------------------------------------
    # 1. Tech / SaaS
    # -----------------------------------------------------------------------
    "tech_saas": {
        "id": "tech_saas",
        "name": "Tech / SaaS",
        "description": (
            "Software-as-a-Service and technology companies. Covers B2B and B2C "
            "software, cloud platforms, developer tools, and AI/ML products."
        ),
        "research_parameters": {
            "search_keywords": [
                "SaaS", "cloud computing", "software platform", "API",
                "developer tools", "enterprise software", "AI ML",
                "digital transformation", "automation",
            ],
            "news_categories": ["technology", "business"],
            "trends_timeframe": "today 12-m",
            "trends_geo": "",
            "data_refresh_interval_hours": 24,
        },
        "kpis": [
            {"name": "MRR", "full_name": "Monthly Recurring Revenue", "unit": "USD", "benchmark_range": "varies by stage"},
            {"name": "ARR", "full_name": "Annual Recurring Revenue", "unit": "USD", "benchmark_range": "varies by stage"},
            {"name": "Churn Rate", "full_name": "Monthly Churn Rate", "unit": "%", "benchmark_range": "2-5% monthly"},
            {"name": "CAC", "full_name": "Customer Acquisition Cost", "unit": "USD", "benchmark_range": "varies"},
            {"name": "LTV", "full_name": "Customer Lifetime Value", "unit": "USD", "benchmark_range": "LTV:CAC > 3:1"},
            {"name": "NRR", "full_name": "Net Revenue Retention", "unit": "%", "benchmark_range": "100-130%"},
            {"name": "DAU/MAU", "full_name": "Daily/Monthly Active Users Ratio", "unit": "ratio", "benchmark_range": "20-50%"},
            {"name": "NPS", "full_name": "Net Promoter Score", "unit": "score", "benchmark_range": "30-70"},
            {"name": "Time to Value", "full_name": "Time to First Value", "unit": "days", "benchmark_range": "< 7 days"},
            {"name": "Expansion Revenue", "full_name": "Expansion Revenue %", "unit": "%", "benchmark_range": "20-40%"},
        ],
        "typical_competitors": [
            "Salesforce", "HubSpot", "Slack", "Zoom", "Notion",
            "Atlassian", "Datadog", "Snowflake", "MongoDB", "Twilio",
        ],
        "swot_factors": {
            "typical_strengths": [
                "Scalable cloud infrastructure",
                "Recurring revenue model",
                "Network effects and ecosystem lock-in",
                "Rapid iteration and deployment cycles",
                "Global reach with low marginal cost",
            ],
            "typical_weaknesses": [
                "High customer acquisition costs",
                "Dependency on cloud providers (AWS, GCP, Azure)",
                "Talent competition in engineering",
                "Complex enterprise sales cycles",
                "Technical debt accumulation",
            ],
            "common_opportunities": [
                "AI/ML integration and automation",
                "Vertical SaaS specialisation",
                "International market expansion",
                "Platform ecosystem development",
                "Usage-based pricing models",
            ],
            "known_threats": [
                "Open-source alternatives",
                "Big tech platform competition",
                "Economic downturn reducing IT budgets",
                "Data privacy regulations (GDPR, CCPA)",
                "Cybersecurity risks and breaches",
            ],
        },
        "pestel_factors": {
            "political": ["Government tech regulation", "Data sovereignty laws", "Export controls on AI"],
            "economic": ["VC funding cycles", "IT budget trends", "Cloud spending growth"],
            "social": ["Remote work adoption", "Digital literacy trends", "Developer community growth"],
            "technological": ["AI/ML advancement", "Edge computing", "Quantum computing threats"],
            "environmental": ["Data centre energy consumption", "Carbon neutrality commitments"],
            "legal": ["Software licensing compliance", "Patent litigation", "GDPR/CCPA compliance"],
        },
        "persona_templates": [
            {"archetype": "CTO / VP Engineering", "focus": "Technical evaluation, scalability, integration"},
            {"archetype": "Product Manager", "focus": "Feature velocity, user experience, analytics"},
            {"archetype": "Developer / IC", "focus": "API quality, documentation, developer experience"},
            {"archetype": "CFO / Finance", "focus": "TCO, ROI, contract flexibility"},
        ],
        "trend_keywords": [
            "SaaS trends", "cloud computing growth", "AI software",
            "developer tools", "no-code low-code", "API economy",
        ],
    },

    # -----------------------------------------------------------------------
    # 2. E-commerce / Retail
    # -----------------------------------------------------------------------
    "ecommerce_retail": {
        "id": "ecommerce_retail",
        "name": "E-commerce / Retail",
        "description": (
            "Online and omnichannel retail businesses. Covers D2C brands, "
            "marketplaces, retail technology, and consumer goods."
        ),
        "research_parameters": {
            "search_keywords": [
                "e-commerce", "online retail", "D2C", "marketplace",
                "omnichannel", "consumer goods", "retail technology",
                "shopping trends", "supply chain",
            ],
            "news_categories": ["business", "technology"],
            "trends_timeframe": "today 12-m",
            "trends_geo": "",
            "data_refresh_interval_hours": 12,
        },
        "kpis": [
            {"name": "GMV", "full_name": "Gross Merchandise Value", "unit": "USD", "benchmark_range": "varies"},
            {"name": "AOV", "full_name": "Average Order Value", "unit": "USD", "benchmark_range": "$50-150"},
            {"name": "Conversion Rate", "full_name": "Website Conversion Rate", "unit": "%", "benchmark_range": "2-5%"},
            {"name": "Cart Abandonment", "full_name": "Cart Abandonment Rate", "unit": "%", "benchmark_range": "60-80%"},
            {"name": "ROAS", "full_name": "Return on Ad Spend", "unit": "ratio", "benchmark_range": "3:1 - 5:1"},
            {"name": "CLV", "full_name": "Customer Lifetime Value", "unit": "USD", "benchmark_range": "varies"},
            {"name": "Repeat Purchase Rate", "full_name": "Repeat Purchase Rate", "unit": "%", "benchmark_range": "20-40%"},
            {"name": "Inventory Turnover", "full_name": "Inventory Turnover Ratio", "unit": "ratio", "benchmark_range": "4-8x"},
            {"name": "Shipping Cost %", "full_name": "Shipping as % of Revenue", "unit": "%", "benchmark_range": "5-15%"},
            {"name": "NPS", "full_name": "Net Promoter Score", "unit": "score", "benchmark_range": "40-70"},
        ],
        "typical_competitors": [
            "Amazon", "Shopify", "Walmart", "Target", "Alibaba",
            "eBay", "Etsy", "Wayfair", "Chewy", "SHEIN",
        ],
        "swot_factors": {
            "typical_strengths": [
                "Direct customer relationships and data",
                "Scalable digital storefront",
                "Personalisation capabilities",
                "Lower overhead than physical retail",
                "Global market access",
            ],
            "typical_weaknesses": [
                "High customer acquisition costs",
                "Shipping and logistics complexity",
                "Product return management",
                "Dependency on advertising platforms",
                "Price transparency and competition",
            ],
            "common_opportunities": [
                "Social commerce and live shopping",
                "AI-powered personalisation",
                "Subscription and membership models",
                "Sustainable and ethical products",
                "Cross-border e-commerce expansion",
            ],
            "known_threats": [
                "Amazon and marketplace dominance",
                "Rising ad costs (Meta, Google)",
                "Supply chain disruptions",
                "Consumer privacy changes (iOS, cookies)",
                "Counterfeit and fraud risks",
            ],
        },
        "pestel_factors": {
            "political": ["Trade tariffs and import duties", "Consumer protection regulations", "Cross-border trade policies"],
            "economic": ["Consumer spending trends", "Inflation impact on purchasing", "Currency fluctuations"],
            "social": ["Sustainability consciousness", "Mobile-first shopping", "Social media influence on purchases"],
            "technological": ["AR/VR try-before-you-buy", "AI recommendations", "Headless commerce"],
            "environmental": ["Packaging waste regulations", "Carbon footprint of shipping", "Sustainable sourcing"],
            "legal": ["Consumer data protection", "Product safety regulations", "Advertising standards"],
        },
        "persona_templates": [
            {"archetype": "Bargain Hunter", "focus": "Price comparison, deals, coupons"},
            {"archetype": "Brand Loyalist", "focus": "Quality, brand values, loyalty programs"},
            {"archetype": "Convenience Shopper", "focus": "Fast shipping, easy returns, mobile UX"},
            {"archetype": "Conscious Consumer", "focus": "Sustainability, ethical sourcing, transparency"},
        ],
        "trend_keywords": [
            "e-commerce trends", "online shopping growth", "D2C brands",
            "social commerce", "retail technology", "supply chain",
        ],
    },

    # -----------------------------------------------------------------------
    # 3. Healthcare
    # -----------------------------------------------------------------------
    "healthcare": {
        "id": "healthcare",
        "name": "Healthcare",
        "description": (
            "Healthcare industry including healthtech, telemedicine, pharma, "
            "medical devices, health insurance, and wellness."
        ),
        "research_parameters": {
            "search_keywords": [
                "healthcare", "healthtech", "telemedicine", "digital health",
                "pharmaceutical", "medical devices", "health insurance",
                "patient care", "clinical trials",
            ],
            "news_categories": ["health", "science", "technology"],
            "trends_timeframe": "today 12-m",
            "trends_geo": "",
            "data_refresh_interval_hours": 24,
        },
        "kpis": [
            {"name": "Patient Satisfaction", "full_name": "Patient Satisfaction Score", "unit": "score", "benchmark_range": "80-95%"},
            {"name": "Patient Acquisition Cost", "full_name": "Cost per New Patient", "unit": "USD", "benchmark_range": "$200-500"},
            {"name": "Readmission Rate", "full_name": "30-Day Readmission Rate", "unit": "%", "benchmark_range": "< 15%"},
            {"name": "Telehealth Adoption", "full_name": "Telehealth Visit %", "unit": "%", "benchmark_range": "15-40%"},
            {"name": "Revenue per Patient", "full_name": "Average Revenue per Patient", "unit": "USD", "benchmark_range": "varies"},
            {"name": "Clinical Trial Success", "full_name": "Phase Transition Rate", "unit": "%", "benchmark_range": "varies by phase"},
            {"name": "Regulatory Approval Time", "full_name": "Time to Approval", "unit": "months", "benchmark_range": "6-24 months"},
            {"name": "Claims Denial Rate", "full_name": "Insurance Claims Denial Rate", "unit": "%", "benchmark_range": "5-10%"},
        ],
        "typical_competitors": [
            "UnitedHealth Group", "CVS Health", "Teladoc", "Amwell",
            "Epic Systems", "Cerner", "Philips Healthcare", "Medtronic",
            "Johnson & Johnson", "Pfizer",
        ],
        "swot_factors": {
            "typical_strengths": [
                "Essential service with inelastic demand",
                "High barriers to entry (regulation, expertise)",
                "Strong IP and patent portfolios",
                "Government funding and subsidies",
                "Growing ageing population demand",
            ],
            "typical_weaknesses": [
                "Heavy regulatory burden",
                "Long product development cycles",
                "Legacy IT systems and interoperability",
                "High liability and malpractice risks",
                "Workforce shortages",
            ],
            "common_opportunities": [
                "Telemedicine and remote patient monitoring",
                "AI-assisted diagnostics and treatment",
                "Personalised medicine and genomics",
                "Mental health and wellness market growth",
                "Value-based care models",
            ],
            "known_threats": [
                "Regulatory changes and compliance costs",
                "Cybersecurity threats to patient data",
                "Drug pricing pressure and reform",
                "Pandemic preparedness requirements",
                "Big tech entry into healthcare",
            ],
        },
        "pestel_factors": {
            "political": ["Healthcare reform policies", "FDA regulation changes", "Government funding priorities"],
            "economic": ["Healthcare spending as % of GDP", "Insurance market dynamics", "Drug pricing pressures"],
            "social": ["Ageing population demographics", "Mental health awareness", "Health equity movements"],
            "technological": ["AI diagnostics", "Wearable health devices", "Electronic health records"],
            "environmental": ["Pharmaceutical waste management", "Hospital energy efficiency", "Climate impact on health"],
            "legal": ["HIPAA compliance", "Clinical trial regulations", "Medical liability laws"],
        },
        "persona_templates": [
            {"archetype": "Healthcare Administrator", "focus": "Efficiency, compliance, cost reduction"},
            {"archetype": "Physician / Clinician", "focus": "Patient outcomes, workflow, evidence-based tools"},
            {"archetype": "Patient / Consumer", "focus": "Access, affordability, convenience"},
            {"archetype": "Health Plan Executive", "focus": "Risk management, member satisfaction, cost containment"},
        ],
        "trend_keywords": [
            "healthcare trends", "telemedicine growth", "digital health",
            "AI healthcare", "patient experience", "health technology",
        ],
    },

    # -----------------------------------------------------------------------
    # 4. Finance / Fintech
    # -----------------------------------------------------------------------
    "finance_fintech": {
        "id": "finance_fintech",
        "name": "Finance / Fintech",
        "description": (
            "Financial services and fintech companies. Covers banking, "
            "payments, lending, insurance, wealth management, and crypto."
        ),
        "research_parameters": {
            "search_keywords": [
                "fintech", "digital banking", "payments", "lending",
                "insurtech", "wealth management", "cryptocurrency",
                "blockchain", "financial services", "neobank",
            ],
            "news_categories": ["business", "technology"],
            "trends_timeframe": "today 12-m",
            "trends_geo": "",
            "data_refresh_interval_hours": 12,
        },
        "kpis": [
            {"name": "AUM", "full_name": "Assets Under Management", "unit": "USD", "benchmark_range": "varies"},
            {"name": "NIM", "full_name": "Net Interest Margin", "unit": "%", "benchmark_range": "2-4%"},
            {"name": "Cost-to-Income", "full_name": "Cost-to-Income Ratio", "unit": "%", "benchmark_range": "40-60%"},
            {"name": "NPL Ratio", "full_name": "Non-Performing Loan Ratio", "unit": "%", "benchmark_range": "< 3%"},
            {"name": "TPV", "full_name": "Total Payment Volume", "unit": "USD", "benchmark_range": "varies"},
            {"name": "Take Rate", "full_name": "Payment Take Rate", "unit": "%", "benchmark_range": "1-3%"},
            {"name": "CAC", "full_name": "Customer Acquisition Cost", "unit": "USD", "benchmark_range": "$50-300"},
            {"name": "Fraud Rate", "full_name": "Transaction Fraud Rate", "unit": "%", "benchmark_range": "< 0.1%"},
            {"name": "App DAU", "full_name": "Daily Active Users", "unit": "count", "benchmark_range": "varies"},
            {"name": "Regulatory Capital", "full_name": "Capital Adequacy Ratio", "unit": "%", "benchmark_range": "> 10.5%"},
        ],
        "typical_competitors": [
            "Stripe", "Square (Block)", "PayPal", "Plaid", "Robinhood",
            "Revolut", "Chime", "Wise", "Coinbase", "Klarna",
        ],
        "swot_factors": {
            "typical_strengths": [
                "Superior user experience vs traditional banks",
                "Lower operational costs through automation",
                "Data-driven underwriting and risk models",
                "Agile product development",
                "API-first architecture and embedded finance",
            ],
            "typical_weaknesses": [
                "Regulatory complexity and compliance costs",
                "Trust deficit vs established institutions",
                "Profitability challenges in early stages",
                "Dependency on banking partners",
                "Limited product breadth",
            ],
            "common_opportunities": [
                "Embedded finance and BaaS",
                "Underbanked and unbanked populations",
                "Open banking and API ecosystems",
                "AI-powered financial advisory",
                "Cross-border payments and remittances",
            ],
            "known_threats": [
                "Regulatory crackdowns and licensing requirements",
                "Big bank digital transformation",
                "Interest rate environment changes",
                "Cybersecurity and fraud risks",
                "Crypto market volatility and regulation",
            ],
        },
        "pestel_factors": {
            "political": ["Financial regulation changes", "Central bank digital currencies", "Anti-money laundering policies"],
            "economic": ["Interest rate environment", "Inflation trends", "Credit market conditions"],
            "social": ["Financial literacy trends", "Cashless society adoption", "Trust in digital finance"],
            "technological": ["Blockchain and DeFi", "AI risk assessment", "Real-time payments infrastructure"],
            "environmental": ["ESG investing growth", "Green finance regulations", "Climate risk in lending"],
            "legal": ["PSD2/Open Banking regulations", "KYC/AML requirements", "Consumer lending laws"],
        },
        "persona_templates": [
            {"archetype": "Digital-Native Consumer", "focus": "Mobile-first, instant access, low fees"},
            {"archetype": "Small Business Owner", "focus": "Cash flow management, lending, payments"},
            {"archetype": "CFO / Finance Director", "focus": "Treasury management, compliance, reporting"},
            {"archetype": "Retail Investor", "focus": "Portfolio management, education, low-cost trading"},
        ],
        "trend_keywords": [
            "fintech trends", "digital banking", "embedded finance",
            "open banking", "cryptocurrency regulation", "neobank growth",
        ],
    },

    # -----------------------------------------------------------------------
    # 5. Real Estate
    # -----------------------------------------------------------------------
    "real_estate": {
        "id": "real_estate",
        "name": "Real Estate",
        "description": (
            "Real estate industry including proptech, property management, "
            "commercial and residential real estate, and construction tech."
        ),
        "research_parameters": {
            "search_keywords": [
                "real estate", "proptech", "property management",
                "commercial real estate", "residential real estate",
                "construction technology", "smart buildings",
                "real estate investment", "housing market",
            ],
            "news_categories": ["business"],
            "trends_timeframe": "today 12-m",
            "trends_geo": "",
            "data_refresh_interval_hours": 24,
        },
        "kpis": [
            {"name": "Occupancy Rate", "full_name": "Property Occupancy Rate", "unit": "%", "benchmark_range": "90-97%"},
            {"name": "Cap Rate", "full_name": "Capitalisation Rate", "unit": "%", "benchmark_range": "4-10%"},
            {"name": "NOI", "full_name": "Net Operating Income", "unit": "USD", "benchmark_range": "varies"},
            {"name": "Price per Sq Ft", "full_name": "Average Price per Square Foot", "unit": "USD/sqft", "benchmark_range": "varies by market"},
            {"name": "Days on Market", "full_name": "Average Days on Market", "unit": "days", "benchmark_range": "20-60 days"},
            {"name": "Rental Yield", "full_name": "Gross Rental Yield", "unit": "%", "benchmark_range": "4-8%"},
            {"name": "Vacancy Rate", "full_name": "Market Vacancy Rate", "unit": "%", "benchmark_range": "3-10%"},
            {"name": "Lead-to-Close", "full_name": "Lead-to-Close Conversion Rate", "unit": "%", "benchmark_range": "1-5%"},
        ],
        "typical_competitors": [
            "Zillow", "Redfin", "Realtor.com", "Compass", "Opendoor",
            "CoStar Group", "CBRE", "JLL", "WeWork", "Airbnb",
        ],
        "swot_factors": {
            "typical_strengths": [
                "Tangible asset with intrinsic value",
                "Multiple revenue streams (rent, appreciation, fees)",
                "Tax advantages and depreciation benefits",
                "Local market expertise and relationships",
                "Leverage through mortgage financing",
            ],
            "typical_weaknesses": [
                "Capital-intensive operations",
                "Illiquid asset class",
                "Geographic concentration risk",
                "Maintenance and operational complexity",
                "Slow technology adoption",
            ],
            "common_opportunities": [
                "Proptech innovation and digital transformation",
                "Remote work driving suburban/secondary market demand",
                "Sustainable and green building demand",
                "Real estate tokenisation and fractional ownership",
                "Senior living and healthcare facilities",
            ],
            "known_threats": [
                "Interest rate increases affecting affordability",
                "Economic recession reducing demand",
                "Remote work reducing office space demand",
                "Climate change and natural disaster risks",
                "Regulatory changes (rent control, zoning)",
            ],
        },
        "pestel_factors": {
            "political": ["Zoning and land use regulations", "Housing policy changes", "Property tax reforms"],
            "economic": ["Mortgage interest rates", "Housing affordability index", "Construction cost inflation"],
            "social": ["Urbanisation vs suburbanisation", "Remote work impact", "Demographic shifts"],
            "technological": ["Virtual tours and 3D modelling", "Smart home technology", "Blockchain for titles"],
            "environmental": ["Green building standards", "Climate risk assessment", "Energy efficiency mandates"],
            "legal": ["Rent control legislation", "Fair housing compliance", "Landlord-tenant laws"],
        },
        "persona_templates": [
            {"archetype": "First-Time Homebuyer", "focus": "Affordability, guidance, mortgage options"},
            {"archetype": "Real Estate Investor", "focus": "ROI, cap rates, portfolio diversification"},
            {"archetype": "Commercial Tenant", "focus": "Location, lease terms, amenities"},
            {"archetype": "Property Manager", "focus": "Efficiency, tenant satisfaction, maintenance"},
        ],
        "trend_keywords": [
            "real estate trends", "proptech", "housing market",
            "commercial real estate", "smart buildings", "property technology",
        ],
    },

    # -----------------------------------------------------------------------
    # 6. Education
    # -----------------------------------------------------------------------
    "education": {
        "id": "education",
        "name": "Education",
        "description": (
            "Education industry including edtech, online learning, K-12, "
            "higher education, corporate training, and lifelong learning."
        ),
        "research_parameters": {
            "search_keywords": [
                "edtech", "online learning", "e-learning", "education technology",
                "LMS", "corporate training", "higher education",
                "K-12 education", "lifelong learning", "upskilling",
            ],
            "news_categories": ["technology", "general"],
            "trends_timeframe": "today 12-m",
            "trends_geo": "",
            "data_refresh_interval_hours": 24,
        },
        "kpis": [
            {"name": "Enrollment Rate", "full_name": "Student Enrollment Growth", "unit": "%", "benchmark_range": "5-15% YoY"},
            {"name": "Completion Rate", "full_name": "Course Completion Rate", "unit": "%", "benchmark_range": "5-15% (MOOC), 60-90% (paid)"},
            {"name": "Student Satisfaction", "full_name": "Student Satisfaction Score", "unit": "score", "benchmark_range": "4.0-4.5/5.0"},
            {"name": "CAC", "full_name": "Student Acquisition Cost", "unit": "USD", "benchmark_range": "$50-500"},
            {"name": "LTV", "full_name": "Student Lifetime Value", "unit": "USD", "benchmark_range": "varies"},
            {"name": "Content Engagement", "full_name": "Average Time on Platform", "unit": "minutes/day", "benchmark_range": "15-45 min"},
            {"name": "Instructor Rating", "full_name": "Average Instructor Rating", "unit": "score", "benchmark_range": "4.0-4.8/5.0"},
            {"name": "Employment Rate", "full_name": "Graduate Employment Rate", "unit": "%", "benchmark_range": "70-95%"},
        ],
        "typical_competitors": [
            "Coursera", "Udemy", "Khan Academy", "Duolingo", "Byju's",
            "2U", "Chegg", "Pearson", "McGraw-Hill", "Blackboard",
        ],
        "swot_factors": {
            "typical_strengths": [
                "Scalable content delivery",
                "Global accessibility and reach",
                "Data-driven learning personalisation",
                "Lower cost than traditional education",
                "Flexible learning schedules",
            ],
            "typical_weaknesses": [
                "Low completion rates for free courses",
                "Credential recognition challenges",
                "Limited hands-on and social learning",
                "Content quality consistency",
                "Digital divide and accessibility issues",
            ],
            "common_opportunities": [
                "AI-powered adaptive learning",
                "Corporate upskilling and reskilling demand",
                "Micro-credentials and stackable certificates",
                "Emerging market education access",
                "VR/AR immersive learning experiences",
            ],
            "known_threats": [
                "Traditional institution resistance",
                "Content commoditisation",
                "Regulatory accreditation requirements",
                "Student data privacy concerns",
                "Economic downturns affecting discretionary education spending",
            ],
        },
        "pestel_factors": {
            "political": ["Education policy reforms", "Government funding for edtech", "Accreditation standards"],
            "economic": ["Student debt crisis", "Corporate training budgets", "Education spending trends"],
            "social": ["Lifelong learning culture", "Skills gap awareness", "Digital native expectations"],
            "technological": ["AI tutoring systems", "VR/AR classrooms", "Learning analytics"],
            "environmental": ["Reduced commuting through online learning", "Digital vs physical textbooks"],
            "legal": ["Student data privacy (FERPA, COPPA)", "Accessibility compliance (ADA)", "IP and content licensing"],
        },
        "persona_templates": [
            {"archetype": "Career Changer", "focus": "New skills, career outcomes, flexibility"},
            {"archetype": "University Student", "focus": "Affordability, credentials, peer learning"},
            {"archetype": "Corporate L&D Manager", "focus": "ROI, scalability, compliance training"},
            {"archetype": "Lifelong Learner", "focus": "Personal growth, variety, community"},
        ],
        "trend_keywords": [
            "edtech trends", "online learning growth", "AI education",
            "corporate training", "micro-credentials", "learning technology",
        ],
    },

    # -----------------------------------------------------------------------
    # 7. Travel & Hospitality
    # -----------------------------------------------------------------------
    "travel_hospitality": {
        "id": "travel_hospitality",
        "name": "Travel & Hospitality",
        "description": (
            "Travel and hospitality industry including hotels, airlines, "
            "OTAs, travel tech, restaurants, and experience platforms."
        ),
        "research_parameters": {
            "search_keywords": [
                "travel technology", "hospitality", "hotel industry",
                "airline industry", "online travel agency", "tourism",
                "travel trends", "vacation rental", "experience economy",
            ],
            "news_categories": ["business", "general"],
            "trends_timeframe": "today 12-m",
            "trends_geo": "",
            "data_refresh_interval_hours": 12,
        },
        "kpis": [
            {"name": "RevPAR", "full_name": "Revenue per Available Room", "unit": "USD", "benchmark_range": "$80-200"},
            {"name": "ADR", "full_name": "Average Daily Rate", "unit": "USD", "benchmark_range": "$100-300"},
            {"name": "Occupancy Rate", "full_name": "Hotel Occupancy Rate", "unit": "%", "benchmark_range": "60-80%"},
            {"name": "CSAT", "full_name": "Customer Satisfaction Score", "unit": "score", "benchmark_range": "80-90%"},
            {"name": "Booking Conversion", "full_name": "Website Booking Conversion Rate", "unit": "%", "benchmark_range": "2-5%"},
            {"name": "RPG", "full_name": "Revenue per Guest", "unit": "USD", "benchmark_range": "varies"},
            {"name": "Load Factor", "full_name": "Airline Load Factor", "unit": "%", "benchmark_range": "80-90%"},
            {"name": "Direct Booking %", "full_name": "Direct vs OTA Booking Ratio", "unit": "%", "benchmark_range": "30-50% direct"},
            {"name": "Review Score", "full_name": "Average Online Review Score", "unit": "score", "benchmark_range": "4.0-4.5/5.0"},
            {"name": "Repeat Guest Rate", "full_name": "Returning Guest Percentage", "unit": "%", "benchmark_range": "30-50%"},
        ],
        "typical_competitors": [
            "Booking.com", "Expedia", "Airbnb", "Marriott", "Hilton",
            "TripAdvisor", "Kayak", "Skyscanner", "Vrbo", "Tripadvisor",
        ],
        "swot_factors": {
            "typical_strengths": [
                "Strong brand recognition and loyalty programs",
                "Global distribution networks",
                "Rich customer data for personalisation",
                "Experiential and emotional product appeal",
                "Diverse revenue streams (rooms, F&B, events)",
            ],
            "typical_weaknesses": [
                "High fixed costs and capital requirements",
                "Seasonal demand fluctuations",
                "Dependency on OTAs for bookings",
                "Labour-intensive operations",
                "Vulnerability to external shocks",
            ],
            "common_opportunities": [
                "Personalised and experiential travel",
                "Sustainable and eco-tourism growth",
                "Technology-driven guest experience",
                "Bleisure (business + leisure) travel trend",
                "Emerging destination markets",
            ],
            "known_threats": [
                "Economic recession reducing travel spend",
                "Pandemic and health crisis risks",
                "Airbnb and alternative accommodation disruption",
                "Climate change and travel restrictions",
                "Geopolitical instability affecting destinations",
            ],
        },
        "pestel_factors": {
            "political": ["Visa and immigration policies", "Tourism promotion budgets", "Geopolitical stability"],
            "economic": ["Consumer discretionary spending", "Fuel price fluctuations", "Currency exchange rates"],
            "social": ["Experience economy growth", "Sustainable travel preferences", "Remote work and digital nomads"],
            "technological": ["Contactless check-in", "AI concierge services", "Dynamic pricing algorithms"],
            "environmental": ["Carbon offset requirements", "Sustainable tourism certifications", "Climate change impact on destinations"],
            "legal": ["Travel insurance regulations", "Consumer protection for bookings", "Health and safety compliance"],
        },
        "persona_templates": [
            {"archetype": "Business Traveller", "focus": "Efficiency, loyalty perks, connectivity"},
            {"archetype": "Leisure Explorer", "focus": "Experiences, value, reviews"},
            {"archetype": "Luxury Traveller", "focus": "Premium service, exclusivity, personalisation"},
            {"archetype": "Budget Backpacker", "focus": "Affordability, flexibility, authenticity"},
        ],
        "trend_keywords": [
            "travel trends", "hospitality technology", "sustainable tourism",
            "hotel industry", "airline trends", "travel recovery",
        ],
    },
}


class DomainProfileManager:
    """
    Manages industry domain profiles for the business analysis module.

    Provides methods to retrieve, list, and customise domain profiles
    that pre-configure research parameters for specific industries.
    """

    def __init__(self, custom_profiles: Optional[dict] = None):
        """
        Args:
            custom_profiles: Optional dict of additional custom domain profiles.
        """
        self._profiles = dict(DOMAIN_PROFILES)
        if custom_profiles:
            self._profiles.update(custom_profiles)

    def list_domains(self) -> list[dict]:
        """
        List all available domain profiles.

        Returns:
            List of dicts with 'id', 'name', and 'description'.
        """
        return [
            {
                "id": profile["id"],
                "name": profile["name"],
                "description": profile["description"],
            }
            for profile in self._profiles.values()
        ]

    def get_profile(self, domain_id: str) -> Optional[dict]:
        """
        Retrieve a specific domain profile by ID.

        Args:
            domain_id: Domain profile identifier (e.g. 'tech_saas').

        Returns:
            Full domain profile dict, or None if not found.
        """
        return self._profiles.get(domain_id)

    def get_profile_by_name(self, name: str) -> Optional[dict]:
        """
        Find a domain profile by name (case-insensitive partial match).

        Args:
            name: Domain name to search for.

        Returns:
            Best matching domain profile, or None.
        """
        name_lower = name.lower()
        for profile in self._profiles.values():
            if name_lower in profile["name"].lower():
                return profile
            if name_lower in profile["id"].lower():
                return profile
        # Fuzzy match on keywords in description
        for profile in self._profiles.values():
            if name_lower in profile["description"].lower():
                return profile
        return None

    def get_research_keywords(self, domain_id: str) -> list[str]:
        """Get search keywords for a domain."""
        profile = self.get_profile(domain_id)
        if not profile:
            return []
        return profile.get("research_parameters", {}).get("search_keywords", [])

    def get_kpis(self, domain_id: str) -> list[dict]:
        """Get relevant KPIs for a domain."""
        profile = self.get_profile(domain_id)
        if not profile:
            return []
        return profile.get("kpis", [])

    def get_typical_competitors(self, domain_id: str) -> list[str]:
        """Get typical competitors for a domain."""
        profile = self.get_profile(domain_id)
        if not profile:
            return []
        return profile.get("typical_competitors", [])

    def get_swot_factors(self, domain_id: str) -> dict:
        """Get industry-specific SWOT factors."""
        profile = self.get_profile(domain_id)
        if not profile:
            return {}
        return profile.get("swot_factors", {})

    def get_pestel_factors(self, domain_id: str) -> dict:
        """Get industry-specific PESTEL factors."""
        profile = self.get_profile(domain_id)
        if not profile:
            return {}
        return profile.get("pestel_factors", {})

    def get_persona_templates(self, domain_id: str) -> list[dict]:
        """Get persona archetype templates for a domain."""
        profile = self.get_profile(domain_id)
        if not profile:
            return []
        return profile.get("persona_templates", [])

    def get_trend_keywords(self, domain_id: str) -> list[str]:
        """Get trend monitoring keywords for a domain."""
        profile = self.get_profile(domain_id)
        if not profile:
            return []
        return profile.get("trend_keywords", [])

    def add_custom_profile(self, domain_id: str, profile: dict) -> None:
        """
        Add or update a custom domain profile.

        Args:
            domain_id: Unique identifier for the domain.
            profile: Full domain profile dict.
        """
        profile["id"] = domain_id
        self._profiles[domain_id] = profile

    def remove_profile(self, domain_id: str) -> bool:
        """
        Remove a domain profile.

        Args:
            domain_id: Domain to remove.

        Returns:
            True if removed, False if not found.
        """
        if domain_id in self._profiles:
            del self._profiles[domain_id]
            return True
        return False

    def get_all_domain_ids(self) -> list[str]:
        """Return all registered domain IDs."""
        return list(self._profiles.keys())
