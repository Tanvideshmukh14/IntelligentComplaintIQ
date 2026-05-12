"""
HVAC Complaint Intelligence System — Duplicate Detection Engine
Detects exact and semantic duplicates using text hashing and cosine similarity.
"""
import re
import hashlib
import math
from collections import Counter


class DuplicateDetector:
    """Detect exact and semantic duplicate complaints."""

    def __init__(self, similarity_threshold=0.85):
        self.similarity_threshold = similarity_threshold
        self._hash_index = {}      # hash -> complaint_ids
        self._tfidf_vectors = {}   # complaint_id -> vector
        self._vocabulary = {}
        self._idf = {}
        self._groups = {}          # group_id -> [complaint_ids]

    STOP_WORDS = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'shall', 'can', 'to', 'of', 'in', 'for',
        'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
        'and', 'but', 'or', 'nor', 'not', 'so', 'yet', 'both', 'either',
        'neither', 'each', 'every', 'all', 'any', 'few', 'more', 'most',
        'other', 'some', 'such', 'no', 'only', 'own', 'same', 'than', 'too',
        'very', 'just', 'if', 'my', 'our', 'we', 'us', 'i', 'me', 'he',
        'she', 'they', 'them', 'it', 'its', 'this', 'that', 'these', 'those',
    }

    def _normalize_text(self, text):
        """Normalize text for comparison."""
        if not text:
            return ""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text

    def _get_text_hash(self, text):
        """Get hash for exact duplicate detection."""
        normalized = self._normalize_text(text)
        return hashlib.md5(normalized.encode()).hexdigest()

    def _tokenize(self, text):
        """Tokenize text for similarity computation."""
        normalized = self._normalize_text(text)
        words = normalized.split()
        return [w for w in words if w not in self.STOP_WORDS and len(w) > 2]

    def _cosine_similarity(self, vec1, vec2):
        """Compute cosine similarity between two word-frequency vectors."""
        if not vec1 or not vec2:
            return 0.0

        # Get all words
        all_words = set(vec1.keys()) | set(vec2.keys())

        dot_product = sum(vec1.get(w, 0) * vec2.get(w, 0) for w in all_words)
        norm1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        norm2 = math.sqrt(sum(v ** 2 for v in vec2.values()))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _get_word_vector(self, text):
        """Get word frequency vector for a text."""
        tokens = self._tokenize(text)
        total = max(len(tokens), 1)
        freq = Counter(tokens)
        return {word: count / total for word, count in freq.items()}

    def detect_duplicates(self, complaints):
        """
        Detect duplicates in a list of complaints.
        
        Args:
            complaints: list of dicts with 'id' and 'text' keys
            
        Returns:
            dict with duplicate_groups, duplicate_scores, and statistics
        """
        if not complaints:
            return {"duplicate_groups": [], "statistics": {"total": 0, "duplicates": 0}}

        # Phase 1: Exact duplicate detection via hashing
        hash_groups = {}
        for complaint in complaints:
            text_hash = self._get_text_hash(complaint.get('text', ''))
            if text_hash not in hash_groups:
                hash_groups[text_hash] = []
            hash_groups[text_hash].append(complaint['id'])

        exact_duplicates = {h: ids for h, ids in hash_groups.items() if len(ids) > 1}

        # Phase 2: Semantic duplicate detection via cosine similarity
        vectors = {}
        for complaint in complaints:
            vectors[complaint['id']] = self._get_word_vector(complaint.get('text', ''))

        semantic_pairs = []
        complaint_ids = list(vectors.keys())

        # Compare each pair (with optimization: skip already exact-matched)
        exact_ids = set()
        for ids in exact_duplicates.values():
            exact_ids.update(ids)

        for i in range(len(complaint_ids)):
            for j in range(i + 1, min(i + 200, len(complaint_ids))):  # Limit comparisons
                id1, id2 = complaint_ids[i], complaint_ids[j]
                if id1 in exact_ids and id2 in exact_ids:
                    continue

                sim = self._cosine_similarity(vectors[id1], vectors[id2])
                if sim >= self.similarity_threshold:
                    semantic_pairs.append({
                        "complaint_1": id1,
                        "complaint_2": id2,
                        "similarity": round(sim, 4),
                        "type": "semantic"
                    })

        # Build duplicate groups
        duplicate_groups = []
        group_id = 0

        # Exact duplicate groups
        for hash_val, ids in exact_duplicates.items():
            duplicate_groups.append({
                "group_id": group_id,
                "type": "exact",
                "complaint_ids": ids,
                "similarity": 1.0,
                "merge_recommendation": True,
            })
            group_id += 1

        # Semantic duplicate groups (merge connected pairs)
        visited = set()
        for pair in semantic_pairs:
            id1, id2 = pair["complaint_1"], pair["complaint_2"]
            if id1 not in visited and id2 not in visited:
                duplicate_groups.append({
                    "group_id": group_id,
                    "type": "semantic",
                    "complaint_ids": [id1, id2],
                    "similarity": pair["similarity"],
                    "merge_recommendation": pair["similarity"] > 0.92,
                })
                visited.add(id1)
                visited.add(id2)
                group_id += 1

        # Compute per-complaint scores
        duplicate_scores = {}
        for complaint in complaints:
            cid = complaint['id']
            max_sim = 0.0
            is_dup = False
            group_id_found = None

            for group in duplicate_groups:
                if cid in group["complaint_ids"]:
                    max_sim = group["similarity"]
                    is_dup = True
                    group_id_found = group["group_id"]
                    break

            duplicate_scores[cid] = {
                "duplicate_score": max_sim,
                "is_duplicate": is_dup,
                "duplicate_group_id": group_id_found,
            }

        total_duplicates = sum(1 for v in duplicate_scores.values() if v["is_duplicate"])

        return {
            "duplicate_groups": duplicate_groups,
            "duplicate_scores": duplicate_scores,
            "statistics": {
                "total_complaints": len(complaints),
                "total_duplicates": total_duplicates,
                "duplicate_rate": round(total_duplicates / max(len(complaints), 1) * 100, 2),
                "exact_duplicate_groups": len(exact_duplicates),
                "semantic_duplicate_pairs": len(semantic_pairs),
            }
        }

    def check_single(self, text, existing_complaints):
        """
        Check if a single complaint is a duplicate of any existing complaint.
        
        Args:
            text: New complaint text
            existing_complaints: list of dicts with 'id' and 'text'
            
        Returns:
            dict with duplicate_score, similar_complaints, is_duplicate
        """
        if not text or not existing_complaints:
            return {"duplicate_score": 0.0, "similar_complaints": [], "is_duplicate": False}

        new_vector = self._get_word_vector(text)
        new_hash = self._get_text_hash(text)

        similar = []
        for comp in existing_complaints:
            comp_hash = self._get_text_hash(comp.get('text', ''))
            if comp_hash == new_hash:
                similar.append({
                    "complaint_id": comp['id'],
                    "similarity": 1.0,
                    "type": "exact"
                })
                continue

            comp_vector = self._get_word_vector(comp.get('text', ''))
            sim = self._cosine_similarity(new_vector, comp_vector)
            if sim >= self.similarity_threshold * 0.8:  # Lower threshold for single check
                similar.append({
                    "complaint_id": comp['id'],
                    "similarity": round(sim, 4),
                    "type": "semantic"
                })

        similar.sort(key=lambda x: x['similarity'], reverse=True)
        max_score = similar[0]['similarity'] if similar else 0.0

        return {
            "duplicate_score": max_score,
            "similar_complaints": similar[:10],
            "is_duplicate": max_score >= self.similarity_threshold,
            "merge_recommendation": max_score >= 0.92,
        }


# Singleton
_detector = None

def get_duplicate_detector():
    global _detector
    if _detector is None:
        from config import DUPLICATE_THRESHOLD
        _detector = DuplicateDetector(similarity_threshold=DUPLICATE_THRESHOLD)
    return _detector
