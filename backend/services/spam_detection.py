"""
HVAC Complaint Intelligence System — Spam & Fake Complaint Detection
Detects spam, fake warranty claims, bot-generated, toxic, and irrelevant complaints.
"""
import re
import math
from collections import Counter


class SpamDetector:
    """Detect spam, fake, toxic, and irrelevant complaints."""

    # Spam indicators
    SPAM_KEYWORDS = [
        'buy now', 'click here', 'free offer', 'limited time', 'act now',
        'congratulations', 'winner', 'prize', 'lottery', 'bitcoin',
        'cryptocurrency', 'investment', 'earn money', 'work from home',
        'lose weight', 'miracle cure', 'viagra', 'casino', 'gambling',
        'subscribe', 'unsubscribe', 'opt out', 'marketing', 'promotion',
    ]

    # Toxic/abusive language indicators
    TOXIC_PATTERNS = [
        r'\b(idiot|stupid|dumb|moron|fool)\b',
        r'\b(hate|kill|die|destroy|murder)\b',
        r'\b(damn|hell|crap)\b',
        r'\b(worst\s+company|terrible\s+company|scam\s+company)\b',
        r'\b(never\s+buy|boycott|sue\s+you)\b',
        r'\b(incompetent|useless|pathetic|disgrace)\b',
        r'[!]{3,}',  # Excessive exclamation marks
        r'[A-Z]{10,}',  # Long ALL CAPS sequences
    ]

    # Fake complaint indicators
    FAKE_INDICATORS = [
        'test', 'testing', 'asdf', 'qwerty', 'lorem ipsum', 'xxx',
        'fake', 'dummy', 'sample', 'example complaint', 'placeholder',
        'n/a', 'none', 'null', 'undefined', 'blank',
    ]

    # Irrelevant to HVAC indicators
    IRRELEVANT_KEYWORDS = [
        'car', 'automobile', 'vehicle', 'phone', 'mobile', 'laptop',
        'computer', 'software', 'internet', 'cable tv', 'streaming',
        'restaurant', 'food', 'delivery', 'shipping', 'package',
        'clothing', 'fashion', 'shoes', 'furniture', 'appliance',
    ]

    # Bot-generated patterns
    BOT_PATTERNS = [
        r'(.{20,})\1{2,}',  # Repeated long text blocks
        r'^[a-z]{100,}$',  # No spaces in very long text
        r'[^\x00-\x7F]{10,}',  # Excessive non-ASCII characters
    ]

    # HVAC-relevant keywords (presence increases legitimacy)
    HVAC_KEYWORDS = [
        'hvac', 'air conditioning', 'heating', 'cooling', 'furnace', 'boiler',
        'thermostat', 'compressor', 'refrigerant', 'ductwork', 'ventilation',
        'air handler', 'heat pump', 'condenser', 'evaporator', 'filter',
        'temperature', 'maintenance', 'repair', 'installation', 'technician',
        'warranty', 'service', 'unit', 'system', 'coil', 'fan', 'motor',
        'blower', 'vents', 'insulation', 'energy', 'efficiency', 'seer',
        'noise', 'leak', 'drain', 'humidity', 'comfort', 'zone',
    ]

    def __init__(self, spam_threshold=0.6):
        self.spam_threshold = spam_threshold

    def detect(self, complaint_text, metadata=None):
        """
        Analyze complaint for spam, fake, toxic, and irrelevant content.
        
        Args:
            complaint_text: The complaint text
            metadata: Optional dict with additional fields (timestamp, ip, channel, etc.)
            
        Returns:
            dict with spam_probability, fraud_risk, toxicity_score, classification
        """
        if not complaint_text:
            return self._empty_result()

        text_lower = complaint_text.lower()
        metadata = metadata or {}

        # 1. Spam probability
        spam_score = self._compute_spam_score(text_lower, complaint_text)

        # 2. Fake complaint detection
        fake_score = self._compute_fake_score(text_lower, complaint_text)

        # 3. Toxicity detection
        toxicity_score = self._compute_toxicity_score(text_lower, complaint_text)

        # 4. Bot detection
        bot_score = self._compute_bot_score(text_lower, complaint_text)

        # 5. Relevance check
        relevance_score = self._compute_relevance_score(text_lower)

        # 6. Fraud risk (warranty-specific)
        fraud_score = self._compute_fraud_risk(text_lower, metadata)

        # Composite spam probability
        composite_spam = (
            spam_score * 0.25 +
            fake_score * 0.20 +
            bot_score * 0.15 +
            (1 - relevance_score) * 0.20 +
            fraud_score * 0.10 +
            toxicity_score * 0.10
        )

        # Determine classification
        flags = []
        if spam_score > 0.6:
            flags.append("spam")
        if fake_score > 0.5:
            flags.append("fake")
        if toxicity_score > 0.5:
            flags.append("toxic")
        if bot_score > 0.5:
            flags.append("bot-generated")
        if relevance_score < 0.3:
            flags.append("irrelevant")
        if fraud_score > 0.5:
            flags.append("fraud-risk")

        is_spam = composite_spam >= self.spam_threshold

        return {
            "spam_probability": round(composite_spam, 4),
            "is_spam": is_spam,
            "fraud_risk_score": round(fraud_score, 4),
            "toxicity_score": round(toxicity_score, 4),
            "bot_probability": round(bot_score, 4),
            "relevance_score": round(relevance_score, 4),
            "fake_probability": round(fake_score, 4),
            "flags": flags,
            "auto_flag": len(flags) > 0,
            "classification": "spam" if is_spam else "legitimate",
            "details": {
                "spam_indicators": self._get_spam_indicators(text_lower),
                "toxic_phrases": self._get_toxic_phrases(text_lower),
            }
        }

    def _compute_spam_score(self, text_lower, original):
        """Compute spam probability."""
        score = 0.0
        indicators = 0

        # Check spam keywords
        for keyword in self.SPAM_KEYWORDS:
            if keyword in text_lower:
                score += 0.15
                indicators += 1

        # URL count
        url_count = len(re.findall(r'https?://\S+|www\.\S+', original))
        score += min(url_count * 0.1, 0.3)

        # Email count
        email_count = len(re.findall(r'\S+@\S+\.\S+', original))
        score += min(email_count * 0.1, 0.2)

        # Phone numbers
        phone_count = len(re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', original))
        if phone_count > 2:
            score += 0.1

        # Very short text (likely not genuine)
        if len(text_lower.split()) < 3:
            score += 0.2

        # Excessive capitalization
        caps_ratio = sum(1 for c in original if c.isupper()) / max(len(original), 1)
        if caps_ratio > 0.5:
            score += 0.1

        return min(score, 1.0)

    def _compute_fake_score(self, text_lower, original):
        """Compute fake complaint probability."""
        score = 0.0

        # Check fake indicators
        for indicator in self.FAKE_INDICATORS:
            if indicator in text_lower:
                score += 0.15

        # Very short text
        word_count = len(text_lower.split())
        if word_count < 3:
            score += 0.3
        elif word_count < 5:
            score += 0.15

        # Gibberish detection (low unique character ratio)
        if len(original) > 10:
            unique_chars = len(set(original.lower()))
            char_ratio = unique_chars / len(original)
            if char_ratio < 0.1:
                score += 0.3

        # Repetitive text
        words = text_lower.split()
        if words:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3:
                score += 0.25

        return min(score, 1.0)

    def _compute_toxicity_score(self, text_lower, original):
        """Compute toxicity score."""
        score = 0.0
        matches = 0

        for pattern in self.TOXIC_PATTERNS:
            found = re.findall(pattern, text_lower)
            matches += len(found)
            score += len(found) * 0.1

        # Aggressive punctuation
        excl_count = original.count('!')
        score += min(excl_count * 0.02, 0.15)

        # All caps words
        caps_words = sum(1 for w in original.split() if w.isupper() and len(w) > 2)
        score += min(caps_words * 0.03, 0.2)

        return min(score, 1.0)

    def _compute_bot_score(self, text_lower, original):
        """Compute bot-generated probability."""
        score = 0.0

        for pattern in self.BOT_PATTERNS:
            if re.search(pattern, original):
                score += 0.3

        # Check for unnaturally uniform sentence length
        sentences = re.split(r'[.!?]+', original)
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) > 3:
            lengths = [len(s.split()) for s in sentences]
            avg_len = sum(lengths) / len(lengths)
            variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
            if variance < 1.0 and avg_len > 5:
                score += 0.2  # Unusually uniform

        # Check for timestamp patterns (bot submissions at exact intervals)
        # This would use metadata in production

        return min(score, 1.0)

    def _compute_relevance_score(self, text_lower):
        """Compute HVAC relevance score."""
        hvac_matches = sum(1 for kw in self.HVAC_KEYWORDS if kw in text_lower)
        irrelevant_matches = sum(1 for kw in self.IRRELEVANT_KEYWORDS if kw in text_lower)

        if hvac_matches == 0 and irrelevant_matches == 0:
            return 0.5  # Neutral

        relevance = hvac_matches / max(hvac_matches + irrelevant_matches, 1)
        return round(relevance, 4)

    def _compute_fraud_risk(self, text_lower, metadata):
        """Compute warranty fraud risk."""
        score = 0.0

        # Fraud-related keywords
        fraud_keywords = [
            'warranty just expired', 'extend my warranty', 'should be covered',
            'previous owner', 'bought used', 'not registered', 'lost receipt',
            'no proof of purchase', 'self installed', 'unauthorized dealer',
        ]

        for kw in fraud_keywords:
            if kw in text_lower:
                score += 0.15

        # Multiple warranty claims (from metadata)
        if metadata.get('warranty_claims_count', 0) > 3:
            score += 0.2

        return min(score, 1.0)

    def _get_spam_indicators(self, text_lower):
        """Get list of spam indicators found."""
        return [kw for kw in self.SPAM_KEYWORDS if kw in text_lower]

    def _get_toxic_phrases(self, text_lower):
        """Get list of toxic phrases found."""
        phrases = []
        for pattern in self.TOXIC_PATTERNS:
            matches = re.findall(pattern, text_lower)
            phrases.extend(matches)
        return phrases[:10]

    def _empty_result(self):
        return {
            "spam_probability": 0.0, "is_spam": False,
            "fraud_risk_score": 0.0, "toxicity_score": 0.0,
            "bot_probability": 0.0, "relevance_score": 1.0,
            "fake_probability": 0.0, "flags": [],
            "auto_flag": False, "classification": "legitimate",
            "details": {"spam_indicators": [], "toxic_phrases": []}
        }

    def batch_detect(self, texts, metadata_list=None):
        """Detect spam for a batch of texts."""
        if metadata_list is None:
            metadata_list = [None] * len(texts)
        return [self.detect(text, meta) for text, meta in zip(texts, metadata_list)]


# Singleton
_detector = None

def get_spam_detector():
    global _detector
    if _detector is None:
        from config import SPAM_THRESHOLD
        _detector = SpamDetector(spam_threshold=SPAM_THRESHOLD)
    return _detector
