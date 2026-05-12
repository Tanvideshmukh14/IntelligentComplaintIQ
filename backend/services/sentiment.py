"""
HVAC Complaint Analysis — Sentiment Analysis Service
Uses VADER + custom HVAC-specific lexicon for sentiment and emotion detection.
"""
import re
import math
from collections import Counter


class SentimentAnalyzer:
    """Sentiment and emotion analyzer for HVAC customer complaints."""

    def __init__(self):
        # VADER-inspired sentiment lexicon tuned for HVAC complaints
        self.positive_words = {
            'good': 0.5, 'great': 0.7, 'excellent': 0.9, 'wonderful': 0.8,
            'satisfied': 0.6, 'happy': 0.7, 'pleased': 0.6, 'thank': 0.4,
            'thanks': 0.4, 'perfect': 0.9, 'impressive': 0.7, 'resolved': 0.5,
            'fixed': 0.4, 'working': 0.3, 'helpful': 0.6, 'professional': 0.5,
            'efficient': 0.5, 'quick': 0.4, 'reliable': 0.5, 'comfortable': 0.5,
            'improved': 0.5, 'appreciate': 0.6, 'recommend': 0.5, 'love': 0.7,
            'best': 0.7, 'amazing': 0.8, 'fantastic': 0.8, 'outstanding': 0.9,
            'smooth': 0.4, 'quiet': 0.4, 'cool': 0.3, 'warm': 0.3,
            'operational': 0.3, 'functional': 0.3, 'responsive': 0.5,
        }

        self.negative_words = {
            'bad': -0.5, 'terrible': -0.9, 'horrible': -0.9, 'awful': -0.8,
            'poor': -0.6, 'worst': -0.9, 'unacceptable': -0.8, 'frustrated': -0.7,
            'frustrating': -0.7, 'angry': -0.8, 'furious': -0.9, 'disappointed': -0.7,
            'disappointing': -0.6, 'failure': -0.7, 'failed': -0.7, 'broken': -0.6,
            'broke': -0.6, 'damaged': -0.6, 'dangerous': -0.8, 'hazard': -0.8,
            'hazardous': -0.9, 'leak': -0.6, 'leaking': -0.6, 'noise': -0.4,
            'noisy': -0.5, 'loud': -0.5, 'unbearable': -0.8, 'suffering': -0.7,
            'uncomfortable': -0.5, 'dead': -0.7, 'stopped': -0.5, 'runaround': -0.7,
            'ignored': -0.7, 'neglected': -0.7, 'complaint': -0.3, 'problem': -0.4,
            'issue': -0.3, 'defect': -0.6, 'defective': -0.7, 'faulty': -0.6,
            'wrong': -0.5, 'incorrect': -0.5, 'error': -0.5, 'mess': -0.6,
            'unprofessional': -0.7, 'incompetent': -0.8, 'useless': -0.8,
            'waste': -0.6, 'wasting': -0.5, 'overcharged': -0.6, 'scam': -0.9,
            'urgent': -0.5, 'emergency': -0.6, 'critical': -0.6, 'immediate': -0.4,
            'denied': -0.6, 'refused': -0.6, 'refusing': -0.6, 'cancelled': -0.5,
            'missed': -0.5, 'incomplete': -0.5, 'pending': -0.3, 'waiting': -0.4,
            'delayed': -0.5, 'slow': -0.4, 'never': -0.5, 'nothing': -0.4,
            'unsafe': -0.8, 'risk': -0.5, 'fire': -0.8, 'flooding': -0.7,
            'mold': -0.6, 'health': -0.4, 'sick': -0.6, 'allergies': -0.4,
            'freezing': -0.6, 'cold': -0.3, 'hot': -0.3, 'sweltering': -0.6,
            'skyrocketed': -0.6, 'expensive': -0.5, 'overpriced': -0.6,
            'nightmare': -0.9, 'disaster': -0.9, 'catastrophic': -0.9,
            'malfunction': -0.6, 'nonfunctional': -0.7, 'inoperative': -0.7,
        }

        # Intensifiers
        self.intensifiers = {
            'very': 1.3, 'extremely': 1.5, 'incredibly': 1.4, 'absolutely': 1.4,
            'totally': 1.3, 'completely': 1.3, 'highly': 1.2, 'really': 1.2,
            'so': 1.2, 'too': 1.2, 'quite': 1.1, 'rather': 1.1,
            'terribly': 1.4, 'horribly': 1.5, 'ridiculously': 1.4,
        }

        # Negation words
        self.negations = {'not', 'no', 'never', 'neither', 'nobody', 'nothing',
                          'nowhere', 'nor', "don't", "doesn't", "didn't", "won't",
                          "wouldn't", "couldn't", "shouldn't", "isn't", "aren't",
                          "wasn't", "weren't", "hasn't", "haven't", "hadn't", "can't", "cannot"}

        # Emotion keywords
        self.emotion_keywords = {
            'frustration': ['frustrated', 'frustrating', 'annoyed', 'annoying', 'aggravated',
                           'irritated', 'tired', 'fed up', 'sick of', 'enough'],
            'anger': ['angry', 'furious', 'outraged', 'livid', 'infuriated', 'enraged',
                     'mad', 'irate', 'unacceptable', 'ridiculous', 'absurd'],
            'confusion': ['confused', 'confusing', 'unclear', 'understand', "don't know",
                         'lost', 'complicated', 'mixed signals', 'contradictory'],
            'urgency': ['urgent', 'emergency', 'immediate', 'asap', 'right away',
                       'critical', 'desperately', 'need help', 'cannot wait', 'time-sensitive'],
            'satisfaction': ['satisfied', 'happy', 'pleased', 'grateful', 'thankful',
                           'appreciate', 'excellent', 'wonderful', 'great job'],
            'fear': ['afraid', 'scared', 'worried', 'concerned', 'fear', 'anxious',
                    'safety', 'hazard', 'dangerous', 'risk', 'health'],
        }

    def preprocess_text(self, text):
        """Clean and preprocess complaint text."""
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r'[^\w\s\'-]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def analyze_sentiment(self, text):
        """
        Analyze sentiment of complaint text.
        Returns: dict with sentiment_score, sentiment_label, emotion, escalation_probability
        """
        if not text:
            return {
                "sentiment_score": 0.0,
                "sentiment_label": "Neutral",
                "emotion": "None",
                "escalation_probability": 0.0,
                "emotion_scores": {}
            }

        processed = self.preprocess_text(text)
        words = processed.split()
        scores = []
        negation_active = False

        for i, word in enumerate(words):
            # Check for negation
            if word in self.negations:
                negation_active = True
                continue

            # Check for intensifier
            intensity = 1.0
            if i > 0 and words[i - 1] in self.intensifiers:
                intensity = self.intensifiers[words[i - 1]]

            # Score the word
            score = 0.0
            if word in self.positive_words:
                score = self.positive_words[word] * intensity
            elif word in self.negative_words:
                score = self.negative_words[word] * intensity

            # Apply negation
            if negation_active and score != 0:
                score *= -0.75
                negation_active = False

            if score != 0:
                scores.append(score)

            # Reset negation after 3 words
            if negation_active and i > 0:
                words_since = True
                negation_active = False

        # Calculate compound score
        if scores:
            sum_scores = sum(scores)
            # Normalize to [-1, 1] using a modified tanh
            compound = sum_scores / math.sqrt(sum_scores ** 2 + 15)
        else:
            compound = -0.1  # Default slightly negative for complaints

        # Determine label
        if compound >= 0.3:
            label = "Positive"
        elif compound >= -0.1:
            label = "Neutral"
        elif compound >= -0.5:
            label = "Negative"
        else:
            label = "Highly Negative"

        # Detect emotions
        emotion_scores = self._detect_emotions(processed)
        primary_emotion = max(emotion_scores, key=emotion_scores.get) if emotion_scores else "None"
        if emotion_scores.get(primary_emotion, 0) < 0.1:
            primary_emotion = "Frustration" if compound < -0.2 else "None"

        # Calculate escalation probability
        escalation_prob = self._calculate_escalation_probability(compound, emotion_scores, text)

        return {
            "sentiment_score": round(compound, 4),
            "sentiment_label": label,
            "emotion": primary_emotion.title(),
            "escalation_probability": round(escalation_prob, 4),
            "emotion_scores": {k: round(v, 4) for k, v in emotion_scores.items()}
        }

    def _detect_emotions(self, text):
        """Detect emotion intensities from text."""
        emotion_scores = {}
        words = text.split()

        for emotion, keywords in self.emotion_keywords.items():
            score = 0.0
            for keyword in keywords:
                if ' ' in keyword:
                    if keyword in text:
                        score += 0.3
                else:
                    count = words.count(keyword)
                    score += count * 0.2
            emotion_scores[emotion] = min(score, 1.0)

        return emotion_scores

    def _calculate_escalation_probability(self, sentiment_score, emotion_scores, text):
        """Calculate probability that complaint will escalate."""
        prob = 0.0

        # Negative sentiment increases escalation
        if sentiment_score < -0.5:
            prob += 0.3
        elif sentiment_score < -0.3:
            prob += 0.2
        elif sentiment_score < 0:
            prob += 0.1

        # Anger and urgency increase escalation
        prob += emotion_scores.get('anger', 0) * 0.25
        prob += emotion_scores.get('urgency', 0) * 0.2
        prob += emotion_scores.get('fear', 0) * 0.15

        # Keywords that indicate escalation
        escalation_keywords = ['lawyer', 'attorney', 'legal', 'sue', 'lawsuit',
                              'bbb', 'better business bureau', 'consumer protection',
                              'manager', 'supervisor', 'escalate', 'unacceptable',
                              'media', 'news', 'report', 'review']
        text_lower = text.lower()
        for kw in escalation_keywords:
            if kw in text_lower:
                prob += 0.15

        # Caps usage (shouting) indicates escalation
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        if caps_ratio > 0.3:
            prob += 0.1

        # Exclamation marks
        excl_count = text.count('!')
        prob += min(excl_count * 0.03, 0.15)

        return min(prob, 0.99)

    def batch_analyze(self, texts):
        """Analyze sentiment for a list of texts."""
        return [self.analyze_sentiment(text) for text in texts]


# Singleton instance
_analyzer = None

def get_analyzer():
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentAnalyzer()
    return _analyzer
