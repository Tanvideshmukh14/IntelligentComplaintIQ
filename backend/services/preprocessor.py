"""
HVAC Complaint Intelligence System — Text Preprocessing Engine
Enterprise-grade NLP preprocessing for complaint text data.
Handles: noise removal, spelling correction, stopwords, tokenization, lemmatization.
"""
import re
import string
from collections import Counter


class TextPreprocessor:
    """Comprehensive text preprocessing for HVAC complaint data."""

    # Common HVAC misspellings and corrections
    SPELLING_CORRECTIONS = {
        'airconditioner': 'air conditioner', 'airconditioning': 'air conditioning',
        'ac': 'air conditioner', 'a/c': 'air conditioner',
        'hvac': 'hvac system', 'thermastat': 'thermostat', 'thermstat': 'thermostat',
        'compresser': 'compressor', 'compressor': 'compressor', 'compresser': 'compressor',
        'refridgerant': 'refrigerant', 'refrigerent': 'refrigerant', 'freon': 'refrigerant',
        'furnance': 'furnace', 'furnice': 'furnace', 'furnase': 'furnace',
        'condensar': 'condenser', 'condensser': 'condenser',
        'evaporater': 'evaporator', 'evaporater': 'evaporator',
        'ductwork': 'duct work', 'ducting': 'duct work',
        'maintenace': 'maintenance', 'maintanence': 'maintenance', 'maintainance': 'maintenance',
        'waranty': 'warranty', 'warrantee': 'warranty', 'warrenty': 'warranty',
        'instalation': 'installation', 'installtion': 'installation',
        'techician': 'technician', 'technision': 'technician', 'technicain': 'technician',
        'temperture': 'temperature', 'temprature': 'temperature', 'tempature': 'temperature',
        'humidty': 'humidity', 'humditiy': 'humidity',
        'electrial': 'electrical', 'eletrical': 'electrical',
        'circut': 'circuit', 'circit': 'circuit',
        'calender': 'calendar', 'schedual': 'schedule', 'scedule': 'schedule',
        'recieved': 'received', 'recived': 'received',
        'reapir': 'repair', 'repiar': 'repair',
        'leaaking': 'leaking', 'leking': 'leaking',
        'noisey': 'noisy', 'nosey': 'noisy',
    }

    # Extended stop words for HVAC domain
    STOP_WORDS = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'shall', 'can', 'need', 'dare', 'ought',
        'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
        'as', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
        'between', 'out', 'off', 'over', 'under', 'again', 'further', 'then',
        'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each',
        'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
        'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
        'just', 'because', 'but', 'and', 'or', 'if', 'while', 'that', 'this',
        'these', 'those', 'am', 'it', 'its', 'my', 'our', 'we', 'us', 'i',
        'me', 'he', 'she', 'they', 'them', 'his', 'her', 'their', 'what',
        'which', 'who', 'whom', 'up', 'about', 'also', 'get', 'got', 'going',
        'much', 'many', 've', 're', 'll', 'don', 'doesn', 'didn',
        'won', 'wouldn', 'couldn', 'shouldn', 'isn', 'aren', 'wasn', 'weren',
        'please', 'thank', 'thanks', 'hi', 'hello', 'dear', 'sir', 'madam',
        'regards', 'sincerely', 'yours', 'truly',
    }

    # Simple lemmatization rules (suffix-based)
    LEMMA_RULES = [
        (r'ies$', 'y'), (r'ves$', 'f'), (r'ses$', 's'), (r'zes$', 'z'),
        (r'ches$', 'ch'), (r'shes$', 'sh'), (r'xes$', 'x'),
        (r'ing$', ''), (r'tion$', 'te'), (r'sion$', 'se'),
        (r'ment$', ''), (r'ness$', ''), (r'ful$', ''),
        (r'less$', ''), (r'able$', ''), (r'ible$', ''),
        (r'ated$', 'ate'), (r'ized$', 'ize'), (r'ised$', 'ise'),
        (r'ed$', ''), (r'ly$', ''), (r'er$', ''), (r'est$', ''),
        (r's$', ''),
    ]

    def __init__(self):
        self._word_freq = Counter()

    def preprocess(self, text, options=None):
        """
        Full preprocessing pipeline.
        
        Args:
            text: Raw complaint text
            options: dict with preprocessing toggles
            
        Returns:
            dict with original, cleaned, tokens, and metadata
        """
        if not text or not isinstance(text, str):
            return {
                "original": str(text) if text else "",
                "cleaned": "",
                "tokens": [],
                "word_count": 0,
                "char_count": 0,
            }

        options = options or {}
        original = text
        
        # Step 1: Basic cleaning
        text = self._clean_noise(text)
        
        # Step 2: Spelling correction
        if options.get('spelling_correction', True):
            text = self._correct_spelling(text)
        
        # Step 3: Normalize
        text = self._normalize(text)
        
        # Step 4: Tokenize
        tokens = self._tokenize(text)
        
        # Step 5: Remove stopwords
        if options.get('remove_stopwords', True):
            tokens = [t for t in tokens if t not in self.STOP_WORDS]
        
        # Step 6: Lemmatize
        if options.get('lemmatize', True):
            tokens = [self._lemmatize(t) for t in tokens]
        
        # Filter empty tokens and short words
        tokens = [t for t in tokens if len(t) > 1]
        
        cleaned = ' '.join(tokens)
        
        return {
            "original": original,
            "cleaned": cleaned,
            "tokens": tokens,
            "word_count": len(tokens),
            "char_count": len(cleaned),
        }

    def _clean_noise(self, text):
        """Remove noise: URLs, emails, phone numbers, special chars."""
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        # Remove emails
        text = re.sub(r'\S+@\S+\.\S+', '', text)
        # Remove phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '', text)
        # Remove ticket/reference numbers
        text = re.sub(r'\b[A-Z]{2,4}[-]?\d{4,}\b', '', text)
        # Remove excessive punctuation
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        text = re.sub(r'[.]{3,}', '.', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\'-.,!?°]', ' ', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _correct_spelling(self, text):
        """Apply HVAC-specific spelling corrections."""
        words = text.lower().split()
        corrected = []
        for word in words:
            clean_word = word.strip(string.punctuation)
            if clean_word in self.SPELLING_CORRECTIONS:
                corrected.append(self.SPELLING_CORRECTIONS[clean_word])
            else:
                corrected.append(word)
        return ' '.join(corrected)

    def _normalize(self, text):
        """Normalize text: lowercase, fix spacing."""
        text = text.lower()
        text = re.sub(r'[^\w\s\'-]', ' ', text)
        text = re.sub(r'\d+', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _tokenize(self, text):
        """Simple whitespace tokenizer with cleaning."""
        return [w.strip("'-") for w in text.split() if w.strip("'-")]

    def _lemmatize(self, word):
        """Simple rule-based lemmatization."""
        if len(word) <= 3:
            return word
        for pattern, replacement in self.LEMMA_RULES:
            result = re.sub(pattern, replacement, word)
            if result != word and len(result) > 2:
                return result
        return word

    def batch_preprocess(self, texts, options=None):
        """Preprocess a batch of texts."""
        return [self.preprocess(text, options) for text in texts]

    def get_vocabulary_stats(self, texts):
        """Get vocabulary statistics from a corpus."""
        all_tokens = []
        for text in texts:
            result = self.preprocess(text)
            all_tokens.extend(result['tokens'])
        
        freq = Counter(all_tokens)
        return {
            "total_tokens": len(all_tokens),
            "unique_tokens": len(freq),
            "top_50_words": freq.most_common(50),
            "avg_tokens_per_doc": round(len(all_tokens) / max(len(texts), 1), 1),
        }


# Singleton
_preprocessor = None

def get_preprocessor():
    global _preprocessor
    if _preprocessor is None:
        _preprocessor = TextPreprocessor()
    return _preprocessor
