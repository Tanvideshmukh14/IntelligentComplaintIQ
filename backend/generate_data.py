"""
HVAC Customer Complaint Analysis System — Synthetic Data Generator
Generates 2500+ realistic HVAC customer complaints with patterns for ML analysis.
"""
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from database import engine, init_db, ComplaintDB
from sqlalchemy.orm import Session

random.seed(42)
np.random.seed(42)

# --- Data Templates ---

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
    "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Christopher", "Karen", "Charles", "Lisa", "Daniel", "Nancy",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Carol", "Kevin", "Amanda", "Brian", "Dorothy", "George", "Melissa",
    "Timothy", "Deborah", "Ronald", "Stephanie", "Edward", "Rebecca", "Jason", "Sharon",
    "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
    "Nicholas", "Angela", "Eric", "Shirley", "Jonathan", "Anna", "Stephen", "Brenda",
    "Larry", "Pamela", "Justin", "Emma", "Scott", "Nicole", "Brandon", "Helen",
    "Benjamin", "Samantha", "Samuel", "Katherine", "Raymond", "Christine", "Gregory", "Debra",
    "Frank", "Rachel", "Alexander", "Carolyn", "Patrick", "Janet", "Jack", "Catherine"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
    "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy"
]

PRODUCT_TYPES = [
    "Central Air Conditioner", "Heat Pump", "Furnace", "Ductless Mini-Split",
    "Packaged HVAC Unit", "Smart Thermostat", "Air Handler", "Boiler",
    "Rooftop Unit", "VRF System"
]

EQUIPMENT_MODELS = {
    "Central Air Conditioner": ["CAC-3000X", "CAC-5000Pro", "CAC-2500E", "CAC-4000S", "CAC-6000Ultra"],
    "Heat Pump": ["HP-2200DX", "HP-3500Elite", "HP-1800Eco", "HP-4200Max", "HP-2800Plus"],
    "Furnace": ["FRN-9800HE", "FRN-7500Pro", "FRN-6000S", "FRN-8500Elite", "FRN-5500E"],
    "Ductless Mini-Split": ["DMS-1200Q", "DMS-1800Pro", "DMS-900Eco", "DMS-2400Max", "DMS-1500S"],
    "Packaged HVAC Unit": ["PKG-7000X", "PKG-5500Pro", "PKG-9000Ultra", "PKG-4000S", "PKG-6500E"],
    "Smart Thermostat": ["ST-500AI", "ST-300Pro", "ST-700Ultra", "ST-200Eco", "ST-400Plus"],
    "Air Handler": ["AH-3000X", "AH-4500Pro", "AH-2000S", "AH-5000Elite", "AH-3500E"],
    "Boiler": ["BLR-8000HE", "BLR-6500Pro", "BLR-5000S", "BLR-9500Ultra", "BLR-7000E"],
    "Rooftop Unit": ["RTU-12000X", "RTU-8000Pro", "RTU-15000Ultra", "RTU-6000S", "RTU-10000E"],
    "VRF System": ["VRF-20000X", "VRF-15000Pro", "VRF-25000Ultra", "VRF-10000S", "VRF-18000E"]
}

CITIES_STATES = [
    ("Phoenix", "Arizona"), ("Houston", "Texas"), ("Miami", "Florida"),
    ("Las Vegas", "Nevada"), ("Dallas", "Texas"), ("Atlanta", "Georgia"),
    ("Chicago", "Illinois"), ("Denver", "Colorado"), ("Minneapolis", "Minnesota"),
    ("Detroit", "Michigan"), ("Boston", "Massachusetts"), ("New York", "New York"),
    ("Los Angeles", "California"), ("San Francisco", "California"), ("Seattle", "Washington"),
    ("Portland", "Oregon"), ("Nashville", "Tennessee"), ("Charlotte", "North Carolina"),
    ("Tampa", "Florida"), ("San Antonio", "Texas"), ("Orlando", "Florida"),
    ("Sacramento", "California"), ("Indianapolis", "Indiana"), ("Columbus", "Ohio"),
    ("Kansas City", "Missouri"), ("Milwaukee", "Wisconsin"), ("Raleigh", "North Carolina"),
    ("Salt Lake City", "Utah"), ("Tucson", "Arizona"), ("Memphis", "Tennessee"),
    ("Jacksonville", "Florida"), ("Albuquerque", "New Mexico"), ("Oklahoma City", "Oklahoma"),
    ("Louisville", "Kentucky"), ("Richmond", "Virginia"), ("Buffalo", "New York"),
    ("Pittsburgh", "Pennsylvania"), ("Cincinnati", "Ohio"), ("St. Louis", "Missouri"),
    ("Cleveland", "Ohio")
]

CUSTOMER_SEGMENTS = ["Residential", "Commercial", "Industrial"]
SEGMENT_WEIGHTS = [0.55, 0.30, 0.15]

RESOLUTION_STATUSES = ["Open", "In Progress", "Resolved", "Escalated", "Closed"]
STATUS_WEIGHTS = [0.15, 0.20, 0.40, 0.10, 0.15]

CHANNELS = ["Phone", "Email", "Chat", "Social Media", "Survey", "CRM", "Service Portal"]
CHANNEL_WEIGHTS = [0.30, 0.20, 0.15, 0.10, 0.05, 0.10, 0.10]

WARRANTY_STATUSES = ["Active", "Expired", "Extended", "Void"]
WARRANTY_WEIGHTS = [0.40, 0.35, 0.15, 0.10]

# --- Complaint Templates by Category ---

COMPLAINT_TEMPLATES = {
    "cooling_failure": [
        "My {product} model {model} is not cooling at all. The house temperature is {temp}°F and it won't go below that. We've been suffering in this heat for {days} days now.",
        "The {product} ({model}) stopped providing cold air yesterday. It's blowing warm air instead. Our office is unbearable at {temp}°F.",
        "AC unit {model} has completely stopped cooling. Thermostat shows {temp}°F but the system is running constantly. Very frustrated.",
        "We purchased the {product} {model} {months} months ago and it's already failing to cool. Temperature stuck at {temp}°F. Unacceptable quality.",
        "The cooling capacity of our {model} has dropped significantly. Rooms are at {temp}°F despite running 24/7. Need immediate service.",
        "Our {product} {model} makes a clicking sound and then stops cooling. House temp is at {temp}°F. Children are uncomfortable.",
        "After the technician visited last week, the {model} still isn't cooling properly. This is our {visit_num} service call for the same issue.",
        "Brand new {product} {model} installed {weeks} weeks ago cannot maintain temperature below {temp}°F. Extremely disappointed.",
    ],
    "heating_failure": [
        "Our {product} {model} stopped heating entirely during the coldest week of winter. Indoor temp dropped to {temp}°F. This is a safety concern.",
        "The {model} furnace is blowing cold air instead of warm. It's {temp}°F inside and we have elderly family members at home.",
        "Heating system {model} fails to ignite. We've tried resetting multiple times. Temperature is dangerously low at {temp}°F.",
        "The heat pump {model} is not providing adequate heating. House is at {temp}°F despite thermostat set to 72°F. Very concerned about pipes freezing.",
        "Our {product} {model} heating stopped working mid-winter. We have a newborn baby and the temp is {temp}°F inside. URGENT help needed!",
        "The pilot light on our {model} keeps going out. Furnace won't stay on. House temperature dropping to {temp}°F overnight.",
        "After annual maintenance, our {product} {model} stopped heating. Now at {temp}°F. This was working fine before the tech came.",
        "Heating failure on our commercial {model}. Building occupants complaining about {temp}°F temperatures. Multiple offices affected.",
    ],
    "noise_complaints": [
        "The {product} {model} is making an extremely loud grinding noise that wakes us up at night. It's been going on for {days} days.",
        "Our {model} has developed a loud rattling sound when it cycles on. The noise level is unbearable and affects our daily life.",
        "Loud buzzing/humming noise coming from the outdoor unit {model}. Neighbors have complained about the noise level.",
        "The {product} {model} makes a high-pitched squealing noise during operation. We cannot sleep or work from home because of it.",
        "Banging noises from the ductwork connected to {model} every time the system starts. Sounds like something is loose inside.",
        "Our {model} compressor makes a terrible clicking and vibrating noise. It gets worse at night. Multiple complaints from family.",
        "The indoor unit of our {product} {model} produces a constant whistling noise. Very annoying and disruptive.",
    ],
    "installation_issues": [
        "The {product} {model} was installed incorrectly. Ductwork is leaking air, and the unit was placed in the wrong location.",
        "Installation team left a mess and didn't complete the {model} installation properly. Wires are exposed and the unit vibrates excessively.",
        "Our new {product} {model} installation is terrible. The condensate drain was connected wrong and water is leaking into the ceiling.",
        "The {model} was installed {weeks} weeks ago but the installer used the wrong size ducts. System is extremely inefficient now.",
        "Installer damaged our wall and ceiling during {product} {model} installation. Also, the system is not balanced — one room is freezing while another is hot.",
        "The {model} installation crew was unprofessional and left refrigerant lines exposed. System is now leaking refrigerant.",
        "Post-installation inspection revealed that the {product} {model} was installed without proper drainage. Basement flooding has occurred.",
    ],
    "maintenance_issues": [
        "Scheduled maintenance for {product} {model} was missed twice. No one contacted us to reschedule. Very poor service.",
        "After maintenance on our {model}, the system performance got worse. The technician may have damaged something.",
        "We've been waiting {days} days for a maintenance appointment for our {product} {model}. No callbacks despite multiple requests.",
        "The maintenance technician for our {model} didn't bring the right parts and left the job incomplete. Still waiting for resolution.",
        "Our annual service contract for {product} {model} has not been honored. Three scheduled visits were cancelled without notice.",
        "Maintenance was performed on {model} but the filter was not replaced and the coils were not cleaned. Paid full price for incomplete work.",
        "Preventive maintenance on our {product} {model} was done poorly. Now the system is short-cycling every {minutes} minutes.",
    ],
    "energy_efficiency": [
        "Our electricity bill has increased by {percent}% since installing the {product} {model}. This unit was supposed to be energy efficient.",
        "The {model} is consuming way too much energy. Our utility bill went from ${old_bill} to ${new_bill} per month since installation.",
        "SEER rating of our {product} {model} seems much lower than advertised. Energy consumption is {percent}% higher than expected.",
        "The {model} runs continuously without cycling off, leading to massive energy bills. Something is wrong with the efficiency.",
        "We chose the {product} {model} specifically for its energy star rating but our bills have skyrocketed by {percent}% this quarter.",
        "Our {model} is supposed to be a high-efficiency unit but we're paying more than with our old system. Very misleading marketing.",
    ],
    "thermostat_connectivity": [
        "The {product} {model} smart thermostat keeps disconnecting from WiFi. Cannot control temperature remotely anymore.",
        "Our {model} thermostat app shows 'Device Offline' constantly. Have reset the router and thermostat multiple times.",
        "The smart thermostat {model} is not syncing with the HVAC system. Temperature readings are inaccurate by {degrees}°F.",
        "WiFi connectivity issues with {product} {model} for the past {weeks} weeks. The scheduling feature doesn't work without connectivity.",
        "Our {model} smart thermostat firmware update bricked the device. Screen is blank and we can't control our HVAC system at all.",
        "The {product} {model} thermostat's geofencing feature stopped working. AC runs all day even when nobody is home. Wasting energy.",
        "Integration between {model} and our home automation system broke after the last update. None of the smart features work now.",
    ],
    "warranty_disputes": [
        "My {product} {model} compressor failed after {months} months. Company refusing to honor the {warranty_years}-year warranty claim.",
        "Warranty claim for {model} was denied citing 'improper installation' even though their own certified technician installed it.",
        "The {product} {model} parts warranty should cover this repair but the dealer says it's a labor issue. Total runaround for {weeks} weeks.",
        "Filed a warranty claim for our {model} {months} months ago. No response from the warranty department despite {calls} follow-up calls.",
        "Extended warranty for {product} {model} was supposed to cover all parts and labor. Now they're saying refrigerant isn't covered.",
        "Our {model} failed within the first year and the company is blaming us for the failure. This is clearly a manufacturing defect.",
        "Warranty repair on {product} {model} has been pending for {weeks} weeks. We're without heating/cooling and no loaner was provided.",
    ],
    "refrigerant_leak": [
        "The {product} {model} has a refrigerant leak. We can smell chemicals and the cooling has stopped. This could be a health hazard.",
        "Technician found a refrigerant leak in our {model} for the third time this year. Clearly a manufacturing defect in the coils.",
        "Our {product} {model} is leaking refrigerant. Green residue visible on the outdoor unit. Children play near it — very concerned about safety.",
        "R-410A refrigerant leak detected in {model}. Cooling performance has degraded and we're worried about environmental impact.",
        "The {model} evaporator coil is leaking refrigerant again. This has been repaired twice already. Need a permanent solution.",
        "Our {product} {model} lost all refrigerant. The system is {months} months old. Suspected manufacturing defect in the line set.",
    ],
    "system_failure": [
        "Complete system failure of our {product} {model}. No power, no response, totally dead. Building has no climate control.",
        "The {model} control board has failed. The entire system is non-functional. We have a commercial building full of employees with no AC.",
        "Our {product} {model} had a catastrophic compressor failure. Loud bang followed by complete shutdown. Potential safety hazard.",
        "Electrical failure in {model}. Circuit breaker keeps tripping. Possible fire hazard. Need emergency service immediately.",
        "The {product} {model} main board is fried after a power surge. System completely down for our {size}-floor office building.",
        "Total system failure on our {model}. Fan motor, compressor, and control board all failed simultaneously. Suspecting electrical issue.",
    ],
}

TECHNICIAN_NOTES_TEMPLATES = [
    "Inspected unit on-site. Found {issue}. Replaced {part}. System operational now.",
    "Customer complaint verified. {issue} confirmed. Ordered replacement {part}. Follow-up scheduled in {days} days.",
    "Performed diagnostics on {model}. {issue} detected. Recommended {action}. Customer approved repair.",
    "Emergency service call. Found {issue}. Temporary fix applied. Permanent repair requires {part} — on backorder.",
    "Routine inspection revealed {issue}. Cleaned coils and replaced filters. System performance improved but {part} showing wear.",
    "Multiple issues found: {issue}. Complete overhaul recommended. Estimate provided to customer. Awaiting approval.",
    "Unit is beyond repair. {issue} too severe. Recommended full system replacement with {replacement}.",
    "Warranty repair completed. {issue} was covered. Replaced {part}. System tested and operational.",
    None,  # Some complaints have no technician notes yet
    None,
    None,
]

TECH_ISSUES = [
    "compressor failure", "refrigerant leak in evaporator coil", "clogged condensate drain",
    "faulty capacitor", "burned-out fan motor", "corroded heat exchanger",
    "loose electrical connections", "failed control board", "damaged ductwork",
    "frozen evaporator coil", "thermostat malfunction", "low refrigerant charge",
    "dirty air filter causing restricted airflow", "cracked heat exchanger",
    "faulty reversing valve", "defective expansion valve", "worn compressor bearings",
    "electrical short in wiring harness", "failed ignition system", "blocked condenser coil"
]

TECH_PARTS = [
    "compressor", "capacitor", "fan motor", "control board", "thermostat",
    "evaporator coil", "condenser coil", "expansion valve", "reversing valve",
    "blower motor", "igniter", "flame sensor", "heat exchanger", "contactor",
    "refrigerant line set", "drain pan", "filter drier", "relay switch"
]

TECH_ACTIONS = [
    "full system replacement", "compressor swap", "coil replacement",
    "electrical rewiring", "duct sealing and insulation", "refrigerant recharge",
    "control board replacement", "system recalibration", "warranty claim processing"
]

TECH_REPLACEMENTS = [
    "newer CAC-6000Ultra model", "upgraded HP-4200Max system", "high-efficiency FRN-9800HE",
    "latest VRF-25000Ultra system", "commercial-grade RTU-15000Ultra"
]


def generate_complaint_description(category, product_type, model):
    """Generate a realistic complaint description from templates."""
    templates = COMPLAINT_TEMPLATES[category]
    template = random.choice(templates)

    return template.format(
        product=product_type,
        model=model,
        temp=random.randint(38, 95),
        days=random.randint(1, 30),
        months=random.randint(1, 36),
        weeks=random.randint(1, 12),
        minutes=random.randint(2, 10),
        percent=random.randint(15, 80),
        old_bill=random.randint(80, 200),
        new_bill=random.randint(250, 600),
        degrees=random.randint(3, 12),
        warranty_years=random.choice([5, 10, 15]),
        calls=random.randint(3, 15),
        visit_num=random.choice(["3rd", "4th", "5th"]),
        size=random.choice(["3", "5", "8", "10", "15"]),
    )


def generate_technician_notes(model):
    """Generate technician notes."""
    template = random.choice(TECHNICIAN_NOTES_TEMPLATES)
    if template is None:
        return None
    return template.format(
        model=model,
        issue=random.choice(TECH_ISSUES),
        part=random.choice(TECH_PARTS),
        days=random.randint(2, 14),
        action=random.choice(TECH_ACTIONS),
        replacement=random.choice(TECH_REPLACEMENTS),
    )


def generate_complaints(n=2500):
    """Generate n synthetic HVAC complaints."""
    complaints = []
    categories = list(COMPLAINT_TEMPLATES.keys())
    # Weighted categories - some are more common
    category_weights = [0.18, 0.15, 0.10, 0.12, 0.10, 0.08, 0.09, 0.07, 0.06, 0.05]

    # Date range: 2 years of data
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 12, 31)
    date_range_days = (end_date - start_date).days

    for i in range(n):
        # Select category and generate complaint
        category = random.choices(categories, weights=category_weights, k=1)[0]
        product_type = random.choice(PRODUCT_TYPES)
        model = random.choice(EQUIPMENT_MODELS[product_type])

        description = generate_complaint_description(category, product_type, model)
        technician_notes = generate_technician_notes(model)

        # Generate date with seasonal patterns
        # More complaints in summer (Jun-Aug) and winter (Dec-Feb)
        month_weights = [0.09, 0.08, 0.06, 0.05, 0.06, 0.12, 0.14, 0.13, 0.07, 0.05, 0.06, 0.09]
        month = random.choices(range(1, 13), weights=month_weights, k=1)[0]
        year = random.choice([2024, 2025])
        day = random.randint(1, 28)
        hour = random.randint(6, 22)
        minute = random.randint(0, 59)
        complaint_date = datetime(year, month, day, hour, minute)

        city, state = random.choice(CITIES_STATES)
        segment = random.choices(CUSTOMER_SEGMENTS, weights=SEGMENT_WEIGHTS, k=1)[0]
        status = random.choices(RESOLUTION_STATUSES, weights=STATUS_WEIGHTS, k=1)[0]
        channel = random.choices(CHANNELS, weights=CHANNEL_WEIGHTS, k=1)[0]
        warranty = random.choices(WARRANTY_STATUSES, weights=WARRANTY_WEIGHTS, k=1)[0]

        # Resolution time based on severity
        if category in ["system_failure", "refrigerant_leak", "heating_failure"]:
            resolution_hours = random.uniform(2, 120)
        elif category in ["cooling_failure", "installation_issues"]:
            resolution_hours = random.uniform(4, 168)
        else:
            resolution_hours = random.uniform(8, 336)

        if status in ["Open", "Escalated"]:
            resolution_hours = None

        # CSAT score - lower for severe issues
        if category in ["system_failure", "refrigerant_leak"]:
            csat = round(random.uniform(1.0, 3.0), 1)
        elif category in ["heating_failure", "cooling_failure"]:
            csat = round(random.uniform(1.5, 3.5), 1)
        elif category in ["warranty_disputes"]:
            csat = round(random.uniform(1.0, 2.5), 1)
        else:
            csat = round(random.uniform(2.0, 5.0), 1)

        complaint = {
            "complaint_id": f"HVAC-{year}-{i+1:05d}",
            "customer_name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "date_time": complaint_date,
            "product_type": product_type,
            "equipment_model": model,
            "complaint_description": description,
            "service_location_city": city,
            "service_location_state": state,
            "customer_segment": segment,
            "resolution_status": status,
            "technician_notes": technician_notes,
            "communication_channel": channel,
            "warranty_status": warranty,
            "resolution_time_hours": resolution_hours,
            "csat_score": csat,
        }
        complaints.append(complaint)

    return complaints


def save_to_database(complaints):
    """Save generated complaints to the SQLite database."""
    init_db()
    session = Session(bind=engine)
    try:
        # Clear existing data
        session.query(ComplaintDB).delete()
        session.commit()

        for c in complaints:
            db_complaint = ComplaintDB(**c)
            session.add(db_complaint)

        session.commit()
        print(f"✅ Successfully saved {len(complaints)} complaints to database.")
    except Exception as e:
        session.rollback()
        print(f"❌ Error saving to database: {e}")
        raise
    finally:
        session.close()


def save_to_csv(complaints, filepath="data/complaints_raw.csv"):
    """Save generated complaints to CSV."""
    import os
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df = pd.DataFrame(complaints)
    df.to_csv(filepath, index=False)
    print(f"✅ Saved {len(complaints)} complaints to {filepath}")
    return df


if __name__ == "__main__":
    print("🏭 Generating HVAC Customer Complaints Dataset...")
    print("=" * 60)
    complaints = generate_complaints(2500)
    print(f"📊 Generated {len(complaints)} complaints")

    # Save to CSV
    df = save_to_csv(complaints)

    # Save to database
    save_to_database(complaints)

    # Print summary
    print("\n📈 Dataset Summary:")
    print(f"  Date Range: {df['date_time'].min()} to {df['date_time'].max()}")
    print(f"  Product Types: {df['product_type'].nunique()}")
    print(f"  Locations: {df['service_location_city'].nunique()} cities")
    print(f"  Channels: {df['communication_channel'].nunique()}")
    print(f"\n  Status Distribution:")
    for status, count in df['resolution_status'].value_counts().items():
        print(f"    {status}: {count}")
    print(f"\n  Segment Distribution:")
    for seg, count in df['customer_segment'].value_counts().items():
        print(f"    {seg}: {count}")
    print("\n✅ Data generation complete!")
