"""
HVAC Complaint Intelligence System — Resolution Time Prediction
Predicts expected resolution duration and SLA breach probability.
"""
import re
import math


class ResolutionPredictor:
    """Predict complaint resolution time and SLA compliance."""

    # Base resolution times by category (in hours)
    CATEGORY_BASE_TIMES = {
        "Cooling Failure": 36, "Heating Failure": 30, "Gas Leakage": 8,
        "Installation Problem": 48, "Maintenance Issue": 24,
        "Warranty Complaint": 72, "Thermostat Connectivity": 18,
        "High Energy Consumption": 48, "Noise Issue": 24,
        "Water Leakage": 20, "Customer Service Issue": 12,
        "Electrical Failure": 28, "Compressor Failure": 42,
        "Refrigerant Leak": 30,
    }

    # SLA targets by severity
    SLA_TARGETS = {
        "Critical": 12, "High": 24, "Medium": 48, "Low": 72,
    }

    # Adjustment factors
    SEVERITY_MULTIPLIERS = {
        "Critical": 0.5,  # Faster resolution for critical
        "High": 0.7,
        "Medium": 1.0,
        "Low": 1.3,
    }

    SEGMENT_MULTIPLIERS = {
        "Industrial": 0.6,
        "Commercial": 0.7,
        "Residential Premium": 0.8,
        "Residential": 1.0,
        "Government": 0.75,
    }

    WARRANTY_MULTIPLIERS = {
        "Active": 0.85,
        "Extended": 0.9,
        "Expired": 1.2,
        "None": 1.3,
    }

    def __init__(self):
        pass

    def predict(self, complaint_text, context=None):
        """
        Predict resolution time for a complaint.
        
        Args:
            complaint_text: Complaint text
            context: dict with severity_level, category, customer_segment,
                     warranty_status, department, etc.
                     
        Returns:
            dict with predicted_hours, sla_target, breach_probability, delay_risks
        """
        context = context or {}
        
        # Get base time from category
        category = context.get('predicted_category', context.get('category', ''))
        base_hours = self.CATEGORY_BASE_TIMES.get(category, 36)

        # Apply severity multiplier
        severity = context.get('severity_level', 'Medium')
        severity_mult = self.SEVERITY_MULTIPLIERS.get(severity, 1.0)
        predicted = base_hours * severity_mult

        # Apply segment multiplier
        segment = context.get('customer_segment', 'Residential')
        segment_mult = self.SEGMENT_MULTIPLIERS.get(segment, 1.0)
        predicted *= segment_mult

        # Apply warranty multiplier
        warranty = context.get('warranty_status', 'None')
        warranty_mult = self.WARRANTY_MULTIPLIERS.get(warranty, 1.0)
        predicted *= warranty_mult

        # Text complexity adjustment
        if complaint_text:
            text_lower = complaint_text.lower()
            
            # Multiple issues increase time
            issue_keywords = ['also', 'additionally', 'another', 'plus', 'besides', 'furthermore']
            multi_issues = sum(1 for kw in issue_keywords if kw in text_lower)
            predicted *= (1 + multi_issues * 0.1)

            # Parts-related keywords increase time
            parts_keywords = ['parts', 'replacement', 'order', 'backorder', 'discontinued', 'special order']
            parts_factor = sum(1 for kw in parts_keywords if kw in text_lower)
            predicted *= (1 + parts_factor * 0.15)

            # Escalation history increases time
            escalation_keywords = ['escalated', 'multiple times', 'third time', 'again', 'still not']
            esc_factor = sum(1 for kw in escalation_keywords if kw in text_lower)
            predicted *= (1 + esc_factor * 0.12)

            # Weekend/holiday factor (simplified)
            # In production, this would check actual calendar

        # Get SLA target
        sla_target = self.SLA_TARGETS.get(severity, 48)

        # Calculate breach probability
        breach_prob = self._calculate_breach_probability(predicted, sla_target)

        # Identify delay risk factors
        delay_risks = self._identify_delay_risks(complaint_text, context)

        # Confidence based on available context
        confidence = 0.5
        if category:
            confidence += 0.15
        if severity != 'Medium':
            confidence += 0.1
        if segment != 'Residential':
            confidence += 0.05
        if warranty != 'None':
            confidence += 0.05

        return {
            "predicted_resolution_hours": round(predicted, 1),
            "predicted_resolution_days": round(predicted / 24, 1),
            "sla_target_hours": sla_target,
            "sla_breach_probability": round(breach_prob, 4),
            "delay_risks": delay_risks,
            "confidence": round(min(confidence, 0.95), 4),
            "urgency_classification": self._classify_urgency(predicted, sla_target),
        }

    def _calculate_breach_probability(self, predicted_hours, sla_target):
        """Calculate probability of SLA breach."""
        if sla_target <= 0:
            return 0.5
        
        ratio = predicted_hours / sla_target
        
        if ratio <= 0.5:
            return 0.05
        elif ratio <= 0.75:
            return 0.15
        elif ratio <= 0.9:
            return 0.35
        elif ratio <= 1.0:
            return 0.55
        elif ratio <= 1.2:
            return 0.75
        elif ratio <= 1.5:
            return 0.88
        else:
            return 0.95

    def _identify_delay_risks(self, text, context):
        """Identify factors that may delay resolution."""
        risks = []
        
        if text:
            text_lower = text.lower()
            
            if any(kw in text_lower for kw in ['parts', 'replacement', 'backorder']):
                risks.append({
                    "factor": "Parts Availability",
                    "impact": "high",
                    "description": "Replacement parts may need to be ordered"
                })
            
            if any(kw in text_lower for kw in ['multiple', 'several', 'various', 'many issues']):
                risks.append({
                    "factor": "Multiple Issues",
                    "impact": "medium",
                    "description": "Multiple issues require extended diagnostic time"
                })
            
            if any(kw in text_lower for kw in ['commercial', 'industrial', 'building', 'office']):
                risks.append({
                    "factor": "Commercial Complexity",
                    "impact": "medium",
                    "description": "Commercial systems require specialized teams"
                })
            
            if any(kw in text_lower for kw in ['remote', 'rural', 'far', 'distant']):
                risks.append({
                    "factor": "Location Access",
                    "impact": "medium",
                    "description": "Remote location may delay technician dispatch"
                })

        severity = context.get('severity_level', '')
        if severity == 'Critical':
            risks.append({
                "factor": "Critical Priority",
                "impact": "low",
                "description": "Critical issues receive immediate dispatch priority"
            })

        warranty = context.get('warranty_status', '')
        if warranty == 'Expired':
            risks.append({
                "factor": "Warranty Expired",
                "impact": "medium",
                "description": "Out-of-warranty repairs require customer approval for costs"
            })

        return risks[:5]

    def _classify_urgency(self, predicted_hours, sla_target):
        """Classify urgency based on predicted vs SLA."""
        ratio = predicted_hours / max(sla_target, 1)
        
        if ratio <= 0.5:
            return "On Track"
        elif ratio <= 0.8:
            return "Monitor"
        elif ratio <= 1.0:
            return "At Risk"
        else:
            return "SLA Breach Risk"

    def batch_predict(self, texts, contexts=None):
        """Predict resolution times for a batch."""
        if contexts is None:
            contexts = [{}] * len(texts)
        return [self.predict(text, ctx) for text, ctx in zip(texts, contexts)]


# Singleton
_predictor = None

def get_resolution_predictor():
    global _predictor
    if _predictor is None:
        _predictor = ResolutionPredictor()
    return _predictor
