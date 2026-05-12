"""
HVAC Complaint Analysis — Department Routing Service
Automatically classifies and routes complaints to the appropriate department.
"""
import re
from collections import Counter


class DepartmentRouter:
    """Route complaints to the appropriate business department."""

    DEPARTMENTS = [
        "Product Manufacturing",
        "Installation Team",
        "Field Service",
        "Maintenance",
        "Customer Support",
        "Warranty Department",
        "Sales Team",
        "Smart HVAC / IoT Division",
        "Supply Chain",
        "Quality Assurance"
    ]

    # Keyword mappings for each department
    DEPARTMENT_KEYWORDS = {
        "Product Manufacturing": {
            'keywords': ['manufacturing', 'defect', 'defective', 'design flaw', 'build quality',
                        'product quality', 'factory', 'production', 'batch', 'recall',
                        'material', 'component failure', 'engineering', 'structural',
                        'cracked', 'corroded', 'rust', 'deterioration', 'premature failure',
                        'manufacturing defect', 'poorly made', 'cheaply made'],
            'weight': 1.0
        },
        "Installation Team": {
            'keywords': ['installation', 'installed', 'installer', 'install', 'setup',
                        'ductwork', 'wiring', 'placement', 'commissioning', 'hookup',
                        'mounted', 'positioned', 'connected wrong', 'incorrect installation',
                        'new system', 'newly installed', 'post-installation', 'exposed wires',
                        'drainage', 'condensate line', 'duct', 'airflow balance'],
            'weight': 1.0
        },
        "Field Service": {
            'keywords': ['repair', 'fix', 'technician', 'service call', 'on-site',
                        'emergency service', 'dispatch', 'field', 'broken', 'stopped working',
                        'not working', 'malfunction', 'breakdown', 'failure', 'failed',
                        'no cooling', 'no heating', 'system down', 'dead', 'non-functional',
                        'refrigerant leak', 'compressor', 'fan motor', 'capacitor',
                        'circuit board', 'control board', 'replace', 'replacement'],
            'weight': 1.0
        },
        "Maintenance": {
            'keywords': ['maintenance', 'preventive', 'scheduled', 'annual', 'routine',
                        'inspection', 'tune-up', 'check-up', 'filter', 'cleaning',
                        'service contract', 'maintenance plan', 'regular service',
                        'coil cleaning', 'belt replacement', 'lubrication',
                        'missed appointment', 'overdue maintenance', 'pm schedule'],
            'weight': 1.0
        },
        "Customer Support": {
            'keywords': ['callback', 'response', 'communication', 'phone', 'email',
                        'hold', 'waiting', 'no response', 'customer service', 'rude',
                        'unprofessional', 'attitude', 'follow up', 'follow-up',
                        'never called back', 'voicemail', 'representative', 'agent',
                        'support', 'help desk', 'call center', 'complaint about service'],
            'weight': 1.0
        },
        "Warranty Department": {
            'keywords': ['warranty', 'claim', 'coverage', 'guarantee', 'extended warranty',
                        'warranty repair', 'warranty replacement', 'denied', 'rejected',
                        'warranty status', 'parts warranty', 'labor warranty', 'void',
                        'expired warranty', 'warranty dispute', 'free repair', 'covered'],
            'weight': 1.2  # Higher weight for explicit warranty mentions
        },
        "Sales Team": {
            'keywords': ['purchase', 'buy', 'pricing', 'quote', 'estimate', 'cost',
                        'upgrade', 'new system', 'replacement unit', 'trade-in',
                        'financing', 'payment plan', 'contract', 'proposal',
                        'recommendation', 'which model', 'comparison', 'options',
                        'misleading', 'promised', 'advertised', 'sales person',
                        'misrepresented', 'false advertising', 'overcharged'],
            'weight': 0.9
        },
        "Smart HVAC / IoT Division": {
            'keywords': ['smart', 'thermostat', 'wifi', 'app', 'connectivity', 'iot',
                        'remote control', 'automation', 'smart home', 'alexa', 'google home',
                        'firmware', 'software', 'update', 'geofencing', 'scheduling',
                        'sensor', 'zone control', 'wireless', 'bluetooth', 'hub',
                        'api', 'integration', 'compatibility', 'device offline',
                        'sync', 'pairing', 'network'],
            'weight': 1.1
        },
        "Supply Chain": {
            'keywords': ['parts', 'backorder', 'out of stock', 'shipping', 'delivery',
                        'delayed parts', 'wrong parts', 'availability', 'lead time',
                        'supplier', 'order', 'inventory', 'waiting for parts',
                        'component shortage', 'discontinued', 'obsolete part'],
            'weight': 0.9
        },
        "Quality Assurance": {
            'keywords': ['quality', 'reliability', 'recurring', 'repeat', 'pattern',
                        'multiple failures', 'design issue', 'systematic', 'batch problem',
                        'quality control', 'testing', 'certification', 'standard',
                        'compliance', 'regulation', 'safety standard', 'inspection failed',
                        'third time', 'same issue', 'same problem', 'again'],
            'weight': 1.0
        }
    }

    def __init__(self):
        pass

    def route_complaint(self, complaint_text, product_type=None, context=None):
        """
        Route a complaint to the most appropriate department.

        Returns:
            dict with predicted_department, confidence, all_scores, routing_reasons
        """
        if not complaint_text:
            return {
                "predicted_department": "Customer Support",
                "confidence": 0.3,
                "all_scores": {dept: 0.0 for dept in self.DEPARTMENTS},
                "routing_reasons": ["Default routing - insufficient information"],
                "secondary_department": None
            }

        text_lower = complaint_text.lower()
        scores = {}
        reasons = {}

        for dept, config in self.DEPARTMENT_KEYWORDS.items():
            dept_score = 0.0
            dept_reasons = []

            for keyword in config['keywords']:
                if keyword in text_lower:
                    # Multi-word keywords get higher scores
                    word_count = len(keyword.split())
                    kw_score = (0.5 + word_count * 0.3) * config['weight']
                    dept_score += kw_score
                    dept_reasons.append(keyword)

            scores[dept] = dept_score
            reasons[dept] = dept_reasons

        # Product type based routing boost
        if product_type:
            pt = product_type.lower()
            if 'thermostat' in pt or 'smart' in pt:
                scores["Smart HVAC / IoT Division"] += 2.0
            elif 'boiler' in pt or 'furnace' in pt:
                scores["Field Service"] += 0.5

        # Normalize scores
        total = sum(scores.values())
        if total > 0:
            normalized = {dept: score / total for dept, score in scores.items()}
        else:
            # Default to Customer Support
            normalized = {dept: (0.3 if dept == "Customer Support" else 0.078) for dept in self.DEPARTMENTS}

        # Get top department
        sorted_depts = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
        best_dept = sorted_depts[0][0]
        best_confidence = sorted_depts[0][1]
        secondary = sorted_depts[1][0] if len(sorted_depts) > 1 else None

        # Get routing reasons for best department
        routing_reasons = reasons.get(best_dept, [])[:5]
        if not routing_reasons:
            routing_reasons = ["General complaint classification"]

        return {
            "predicted_department": best_dept,
            "confidence": round(best_confidence, 4),
            "all_scores": {k: round(v, 4) for k, v in normalized.items()},
            "routing_reasons": routing_reasons,
            "secondary_department": secondary
        }

    def batch_route(self, texts, product_types=None, contexts=None):
        """Route a batch of complaints."""
        if product_types is None:
            product_types = [None] * len(texts)
        if contexts is None:
            contexts = [None] * len(texts)
        return [
            self.route_complaint(text, pt, ctx)
            for text, pt, ctx in zip(texts, product_types, contexts)
        ]


# Singleton
_router = None

def get_router():
    global _router
    if _router is None:
        _router = DepartmentRouter()
    return _router
