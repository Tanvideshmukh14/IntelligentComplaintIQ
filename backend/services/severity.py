"""
HVAC Complaint Analysis — Severity Prediction Engine
Rule-based + ML hybrid severity scoring for HVAC complaints.
"""
import re
from collections import Counter


class SeverityPredictor:
    """Predict complaint severity using keyword analysis and contextual rules."""

    SEVERITY_LEVELS = ["Low", "Medium", "High", "Critical"]

    # Keywords and their severity weights
    CRITICAL_KEYWORDS = {
        'fire': 5.0, 'explosion': 5.0, 'carbon monoxide': 5.0, 'co leak': 5.0,
        'gas leak': 5.0, 'smoke': 4.5, 'burning smell': 4.5, 'electrocution': 5.0,
        'electrical fire': 5.0, 'health hazard': 4.5, 'safety hazard': 4.5,
        'life threatening': 5.0, 'hospitalized': 5.0, 'injured': 4.5,
        'toxic': 4.5, 'fumes': 4.0, 'poisoning': 5.0, 'death': 5.0,
        'newborn': 4.0, 'infant': 4.0, 'baby': 3.5, 'elderly': 3.5,
        'disabled': 3.5, 'medical condition': 4.0, 'oxygen': 4.5,
        'catastrophic': 4.5, 'explosion risk': 5.0, 'gas smell': 4.5,
    }

    HIGH_KEYWORDS = {
        'complete failure': 3.5, 'system failure': 3.5, 'total failure': 3.5,
        'no power': 3.0, 'dead': 3.0, 'non-functional': 3.0,
        'refrigerant leak': 3.5, 'leaking refrigerant': 3.5,
        'freezing': 3.0, 'pipes freezing': 3.5, 'flooding': 3.0,
        'no heating': 3.0, 'no cooling': 3.0, 'winter': 2.5,
        'commercial': 2.5, 'multiple offices': 3.0, 'building': 2.5,
        'cracked heat exchanger': 4.0, 'compressor failure': 3.0,
        'electrical short': 3.5, 'circuit breaker': 3.0, 'tripping': 2.5,
        'repeated': 2.5, 'multiple times': 2.5, 'third time': 3.0,
        'emergency': 3.5, 'urgent': 3.0, 'immediately': 2.5, 'asap': 2.5,
    }

    MEDIUM_KEYWORDS = {
        'noise': 1.5, 'loud': 1.5, 'rattling': 1.5, 'grinding': 2.0,
        'vibrating': 1.5, 'inefficient': 1.5, 'high bills': 2.0,
        'installation': 1.5, 'incorrect': 1.5, 'wrong': 1.5,
        'warranty': 2.0, 'denied': 2.0, 'delayed': 1.5, 'waiting': 1.5,
        'incomplete': 1.5, 'poor service': 2.0, 'unprofessional': 1.5,
        'scheduling': 1.0, 'cancelled': 1.5, 'missed': 1.5,
        'thermostat': 1.5, 'wifi': 1.0, 'connectivity': 1.0,
        'short cycling': 2.0, 'temperature fluctuation': 1.5,
    }

    LOW_KEYWORDS = {
        'question': 0.5, 'inquiry': 0.5, 'information': 0.5,
        'minor': 0.5, 'small': 0.5, 'slight': 0.5,
        'cosmetic': 0.5, 'aesthetic': 0.5, 'appearance': 0.5,
        'filter': 0.5, 'replacement filter': 0.5, 'cleaning': 0.5,
        'routine': 0.5, 'regular': 0.5, 'annual': 0.5,
        'app update': 0.5, 'display': 0.5, 'interface': 0.5,
    }

    def __init__(self):
        pass

    def predict_severity(self, complaint_text, context=None):
        """
        Predict severity level and score for a complaint.

        Args:
            complaint_text: The complaint description
            context: Optional dict with additional context (warranty_status, customer_segment, etc.)

        Returns:
            dict with severity_level, severity_score, risk_factors, priority_rank
        """
        if not complaint_text:
            return {
                "severity_level": "Low",
                "severity_score": 0.1,
                "risk_factors": [],
                "priority_rank": 4,
                "recommendations": ["Review complaint details"]
            }

        text_lower = complaint_text.lower()
        score = 0.0
        risk_factors = []

        # Check critical keywords
        for keyword, weight in self.CRITICAL_KEYWORDS.items():
            if keyword in text_lower:
                score += weight
                risk_factors.append(f"Critical: {keyword}")

        # Check high keywords
        for keyword, weight in self.HIGH_KEYWORDS.items():
            if keyword in text_lower:
                score += weight
                risk_factors.append(f"High Risk: {keyword}")

        # Check medium keywords
        for keyword, weight in self.MEDIUM_KEYWORDS.items():
            if keyword in text_lower:
                score += weight

        # Check low keywords
        for keyword, weight in self.LOW_KEYWORDS.items():
            if keyword in text_lower:
                score += weight

        # Context-based adjustments
        if context:
            # Commercial/Industrial customers get higher priority
            segment = context.get('customer_segment', '')
            if segment == 'Commercial':
                score *= 1.3
                risk_factors.append("Commercial customer impact")
            elif segment == 'Industrial':
                score *= 1.5
                risk_factors.append("Industrial customer - high impact")

            # Warranty disputes increase severity
            warranty = context.get('warranty_status', '')
            if warranty == 'Active':
                score *= 1.1

            # Escalated status
            status = context.get('resolution_status', '')
            if status == 'Escalated':
                score *= 1.4
                risk_factors.append("Previously escalated")

            # Repeat complaints
            if context.get('is_repeat', False):
                score *= 1.3
                risk_factors.append("Repeat complaint")

        # Sentiment-based adjustment
        exclamation_count = complaint_text.count('!')
        caps_words = sum(1 for word in complaint_text.split() if word.isupper() and len(word) > 1)
        score += exclamation_count * 0.3
        score += caps_words * 0.2

        # Normalize score to 0-1
        normalized_score = min(score / 15.0, 1.0)

        # Determine severity level
        if normalized_score >= 0.7:
            level = "Critical"
            priority = 1
        elif normalized_score >= 0.45:
            level = "High"
            priority = 2
        elif normalized_score >= 0.25:
            level = "Medium"
            priority = 3
        else:
            level = "Low"
            priority = 4

        # Generate recommendations
        recommendations = self._generate_recommendations(level, risk_factors)

        return {
            "severity_level": level,
            "severity_score": round(normalized_score, 4),
            "risk_factors": risk_factors[:5],  # Top 5 factors
            "priority_rank": priority,
            "recommendations": recommendations
        }

    def _generate_recommendations(self, severity_level, risk_factors):
        """Generate action recommendations based on severity."""
        recommendations = []

        if severity_level == "Critical":
            recommendations.extend([
                "Dispatch emergency service team immediately",
                "Notify safety department and management",
                "Contact customer within 1 hour",
                "Document all safety-related details",
                "Consider temporary replacement unit"
            ])
        elif severity_level == "High":
            recommendations.extend([
                "Schedule priority service within 24 hours",
                "Assign experienced senior technician",
                "Proactive customer communication",
                "Prepare required replacement parts"
            ])
        elif severity_level == "Medium":
            recommendations.extend([
                "Schedule service within 48-72 hours",
                "Standard technician assignment",
                "Send acknowledgment to customer"
            ])
        else:
            recommendations.extend([
                "Schedule at next available slot",
                "Standard service protocol"
            ])

        # Risk-specific recommendations
        risk_text = ' '.join(risk_factors).lower()
        if 'refrigerant' in risk_text:
            recommendations.append("EPA-certified technician required for refrigerant handling")
        if 'commercial' in risk_text or 'industrial' in risk_text:
            recommendations.append("Assign commercial service team")
        if 'repeat' in risk_text:
            recommendations.append("Review previous service history before dispatch")
        if 'warranty' in risk_text:
            recommendations.append("Verify warranty status and coverage details")

        return recommendations[:5]

    def batch_predict(self, texts, contexts=None):
        """Predict severity for a batch of complaints."""
        if contexts is None:
            contexts = [None] * len(texts)
        return [self.predict_severity(text, ctx) for text, ctx in zip(texts, contexts)]


# Singleton
_predictor = None

def get_severity_predictor():
    global _predictor
    if _predictor is None:
        _predictor = SeverityPredictor()
    return _predictor
