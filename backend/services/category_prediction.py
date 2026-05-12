"""
HVAC Complaint Intelligence System — Category Prediction Engine
NLP-based complaint category classification using keyword analysis and TF-IDF scoring.
"""
import re
import math
from collections import Counter


class CategoryPredictor:
    """Predict complaint category using keyword-based NLP classification."""

    CATEGORIES = {
        "Cooling Failure": {
            "keywords": [
                'cooling', 'cool', 'cold', 'ac', 'air conditioning', 'air conditioner',
                'not cooling', 'warm air', 'hot air', 'no cold air', 'insufficient cooling',
                'evaporator', 'condenser', 'refrigerant', 'ice', 'frozen', 'freeze',
                'temperature high', 'too hot', 'overheating', 'sweltering',
            ],
            "weight": 1.0
        },
        "Heating Failure": {
            "keywords": [
                'heating', 'heat', 'furnace', 'boiler', 'not heating', 'no heat',
                'cold air blowing', 'pilot light', 'ignition', 'burner', 'flame',
                'heat pump', 'too cold', 'freezing', 'no warm air', 'insufficient heat',
                'radiator', 'baseboard', 'heat exchanger',
            ],
            "weight": 1.0
        },
        "Gas Leakage": {
            "keywords": [
                'gas leak', 'gas smell', 'gas odor', 'natural gas', 'propane',
                'carbon monoxide', 'co leak', 'co detector', 'fumes', 'toxic',
                'poisoning', 'explosion', 'fire hazard', 'safety hazard',
                'gas line', 'gas valve', 'gas pipe',
            ],
            "weight": 1.5
        },
        "Installation Problem": {
            "keywords": [
                'installation', 'installed', 'installer', 'install', 'setup',
                'new system', 'new unit', 'ductwork', 'wiring', 'placement',
                'commissioning', 'hookup', 'mounted', 'positioned', 'connected wrong',
                'incorrect installation', 'poor installation', 'exposed wires',
                'drainage', 'condensate line', 'duct', 'airflow balance',
            ],
            "weight": 1.0
        },
        "Maintenance Issue": {
            "keywords": [
                'maintenance', 'service', 'tune-up', 'check-up', 'filter',
                'cleaning', 'scheduled', 'appointment', 'routine', 'annual',
                'inspection', 'preventive', 'overdue', 'missed appointment',
                'service contract', 'maintenance plan', 'pm schedule',
            ],
            "weight": 0.9
        },
        "Warranty Complaint": {
            "keywords": [
                'warranty', 'claim', 'coverage', 'guarantee', 'denied',
                'rejected', 'expired', 'void', 'warranty repair', 'parts warranty',
                'labor warranty', 'extended warranty', 'warranty status',
                'covered', 'not covered', 'warranty dispute',
            ],
            "weight": 1.1
        },
        "Thermostat Connectivity": {
            "keywords": [
                'thermostat', 'smart thermostat', 'wifi', 'connectivity', 'app',
                'smart home', 'alexa', 'google home', 'firmware', 'software',
                'geofencing', 'scheduling', 'sensor', 'zone control', 'wireless',
                'bluetooth', 'hub', 'device offline', 'sync', 'pairing', 'network',
                'display', 'touchscreen', 'programming',
            ],
            "weight": 1.0
        },
        "High Energy Consumption": {
            "keywords": [
                'energy', 'electricity', 'bill', 'bills', 'utility', 'power',
                'consumption', 'efficient', 'inefficient', 'seer', 'eer',
                'high bills', 'expensive', 'cost', 'running constantly',
                'short cycling', 'never shuts off', 'always running',
            ],
            "weight": 1.0
        },
        "Noise Issue": {
            "keywords": [
                'noise', 'noisy', 'loud', 'sound', 'rattling', 'banging',
                'buzzing', 'humming', 'grinding', 'squealing', 'clicking',
                'vibrating', 'vibration', 'whistle', 'screech', 'clunking',
                'popping', 'knocking',
            ],
            "weight": 1.0
        },
        "Water Leakage": {
            "keywords": [
                'water leak', 'leaking water', 'dripping', 'condensation',
                'drain', 'overflow', 'flooding', 'water damage', 'moisture',
                'wet', 'puddle', 'mold', 'mildew', 'condensate pump',
                'drain line', 'clogged drain', 'pan overflow',
            ],
            "weight": 1.0
        },
        "Customer Service Issue": {
            "keywords": [
                'customer service', 'rude', 'unprofessional', 'no callback',
                'no response', 'waiting', 'hold', 'communication', 'attitude',
                'incompetent', 'ignored', 'neglected', 'follow up', 'delayed',
                'cancelled', 'representative', 'agent', 'supervisor', 'manager',
            ],
            "weight": 0.9
        },
        "Electrical Failure": {
            "keywords": [
                'electrical', 'electric', 'wiring', 'circuit', 'breaker',
                'tripping', 'short circuit', 'power surge', 'capacitor',
                'control board', 'circuit board', 'fuse', 'transformer',
                'voltage', 'amperage', 'relay', 'contactor',
            ],
            "weight": 1.0
        },
        "Compressor Failure": {
            "keywords": [
                'compressor', 'compressor failure', 'compressor not starting',
                'compressor noise', 'compressor overheating', 'scroll compressor',
                'reciprocating', 'locked rotor', 'hard start', 'compressor seized',
            ],
            "weight": 1.1
        },
        "Refrigerant Leak": {
            "keywords": [
                'refrigerant', 'refrigerant leak', 'r410a', 'r22', 'freon',
                'low charge', 'recharge', 'charge', 'coil leak', 'line set',
                'flare', 'braze', 'leak test', 'dye test', 'nitrogen test',
            ],
            "weight": 1.1
        },
    }

    def __init__(self):
        pass

    def predict_category(self, complaint_text):
        """
        Predict complaint category.
        Returns: dict with predicted_category, confidence, top_categories
        """
        if not complaint_text:
            return {
                "predicted_category": "Customer Service Issue",
                "confidence": 0.1,
                "top_categories": [],
                "category_scores": {}
            }

        text_lower = complaint_text.lower()
        scores = {}

        for category, config in self.CATEGORIES.items():
            score = 0.0
            matched_keywords = []

            for keyword in config['keywords']:
                if keyword in text_lower:
                    word_count = len(keyword.split())
                    kw_score = (0.4 + word_count * 0.3) * config['weight']
                    score += kw_score
                    matched_keywords.append(keyword)

            scores[category] = {
                "score": score,
                "matched_keywords": matched_keywords
            }

        # Normalize scores
        total = sum(s["score"] for s in scores.values())
        if total > 0:
            for cat in scores:
                scores[cat]["normalized"] = round(scores[cat]["score"] / total, 4)
        else:
            for cat in scores:
                scores[cat]["normalized"] = round(1.0 / len(self.CATEGORIES), 4)

        # Sort by score
        sorted_cats = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)
        best = sorted_cats[0]

        top_categories = [
            {"category": cat, "confidence": data["normalized"], "keywords": data["matched_keywords"][:5]}
            for cat, data in sorted_cats[:5]
            if data["score"] > 0
        ]

        return {
            "predicted_category": best[0],
            "confidence": best[1]["normalized"],
            "top_categories": top_categories,
            "category_scores": {cat: data["normalized"] for cat, data in sorted_cats}
        }

    def batch_predict(self, texts):
        """Predict categories for a batch of texts."""
        return [self.predict_category(text) for text in texts]


# Singleton
_predictor = None

def get_category_predictor():
    global _predictor
    if _predictor is None:
        _predictor = CategoryPredictor()
    return _predictor
