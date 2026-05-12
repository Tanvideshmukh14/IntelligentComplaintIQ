"""
HVAC Complaint Analysis — Clustering Engine
TF-IDF vectorization + K-Means clustering with automatic topic labeling.
"""
import re
import numpy as np
from collections import Counter


class ComplaintClusterEngine:
    """Cluster complaints using TF-IDF and K-Means."""

    # HVAC-specific stop words
    HVAC_STOP_WORDS = {
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
        'been', 'much', 'many', 've', 're', 'll', 'don', 'doesn', 'didn',
        'won', 'wouldn', 'couldn', 'shouldn', 'isn', 'aren', 'wasn', 'weren',
    }

    CLUSTER_LABELS = {
        0: "Cooling System Failures",
        1: "Heating System Issues",
        2: "Noise & Vibration Complaints",
        3: "Installation Quality Problems",
        4: "Maintenance Service Delays",
        5: "Energy Efficiency Concerns",
        6: "Smart Thermostat / IoT Issues",
        7: "Warranty & Billing Disputes",
        8: "Refrigerant Leak Hazards",
        9: "Complete System Failures",
    }

    def __init__(self, n_clusters=8):
        self.n_clusters = n_clusters
        self.vocabulary = {}
        self.idf_values = {}
        self.centroids = None
        self.fitted = False

    def _tokenize(self, text):
        """Tokenize and clean text."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', '', text)
        words = text.split()
        return [w for w in words if w not in self.HVAC_STOP_WORDS and len(w) > 2]

    def _build_vocabulary(self, documents):
        """Build vocabulary from documents."""
        word_doc_count = Counter()
        all_words = Counter()

        for doc in documents:
            tokens = self._tokenize(doc)
            unique_tokens = set(tokens)
            for token in unique_tokens:
                word_doc_count[token] += 1
            for token in tokens:
                all_words[token] += 1

        # Keep top words by frequency, filter rare ones
        min_doc_freq = max(2, len(documents) * 0.01)
        max_doc_freq = len(documents) * 0.8

        vocab_words = [
            word for word, count in word_doc_count.items()
            if min_doc_freq <= count <= max_doc_freq
        ]

        # Sort by frequency and take top N
        vocab_words.sort(key=lambda w: all_words[w], reverse=True)
        vocab_words = vocab_words[:500]

        self.vocabulary = {word: idx for idx, word in enumerate(vocab_words)}

        # Calculate IDF
        n_docs = len(documents)
        self.idf_values = {
            word: np.log(n_docs / (1 + word_doc_count[word]))
            for word in self.vocabulary
        }

    def _tfidf_vector(self, text):
        """Convert text to TF-IDF vector."""
        tokens = self._tokenize(text)
        token_counts = Counter(tokens)
        total_tokens = max(len(tokens), 1)

        vector = np.zeros(len(self.vocabulary))
        for word, idx in self.vocabulary.items():
            tf = token_counts.get(word, 0) / total_tokens
            idf = self.idf_values.get(word, 0)
            vector[idx] = tf * idf

        # Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector /= norm

        return vector

    def _kmeans(self, vectors, n_clusters, max_iter=100):
        """Simple K-Means implementation."""
        n_samples = len(vectors)

        # Initialize centroids using K-Means++
        centroids = [vectors[np.random.randint(n_samples)]]
        for _ in range(1, n_clusters):
            distances = np.array([
                min(np.sum((v - c) ** 2) for c in centroids)
                for v in vectors
            ])
            probs = distances / distances.sum()
            cumprobs = np.cumsum(probs)
            r = np.random.random()
            idx = np.searchsorted(cumprobs, r)
            centroids.append(vectors[min(idx, n_samples - 1)])

        centroids = np.array(centroids)
        labels = np.zeros(n_samples, dtype=int)

        for _ in range(max_iter):
            # Assign clusters
            new_labels = np.array([
                np.argmin([np.sum((v - c) ** 2) for c in centroids])
                for v in vectors
            ])

            # Check convergence
            if np.array_equal(labels, new_labels):
                break
            labels = new_labels

            # Update centroids
            for k in range(n_clusters):
                members = vectors[labels == k]
                if len(members) > 0:
                    centroids[k] = members.mean(axis=0)

        return labels, centroids

    def fit_predict(self, texts):
        """Fit clustering model and predict clusters."""
        if not texts:
            return [], {}

        # Build vocabulary and vectorize
        self._build_vocabulary(texts)
        vectors = np.array([self._tfidf_vector(text) for text in texts])

        # Run K-Means
        n_clusters = min(self.n_clusters, len(texts))
        labels, self.centroids = self._kmeans(vectors, n_clusters)
        self.fitted = True

        # Generate cluster info
        cluster_info = self._generate_cluster_info(texts, labels)

        return labels.tolist(), cluster_info

    def _generate_cluster_info(self, texts, labels):
        """Generate descriptive info for each cluster."""
        cluster_info = {}
        unique_labels = sorted(set(labels))

        for cluster_id in unique_labels:
            cluster_texts = [texts[i] for i in range(len(texts)) if labels[i] == cluster_id]
            # Get top keywords
            word_counts = Counter()
            for text in cluster_texts:
                tokens = self._tokenize(text)
                word_counts.update(tokens)

            top_keywords = [word for word, _ in word_counts.most_common(10)]

            # Determine cluster label based on keywords
            label = self._infer_cluster_label(top_keywords, cluster_id)

            cluster_info[int(cluster_id)] = {
                "label": label,
                "size": len(cluster_texts),
                "percentage": round(len(cluster_texts) / len(texts) * 100, 1),
                "top_keywords": top_keywords,
                "sample_complaints": cluster_texts[:3],
            }

        return cluster_info

    def _infer_cluster_label(self, keywords, default_id):
        """Infer a human-readable label from cluster keywords."""
        keyword_set = set(keywords)

        label_keywords = {
            "Cooling System Failures": {'cooling', 'cool', 'cold', 'air', 'temperature', 'hot', 'warm', 'ac'},
            "Heating System Issues": {'heating', 'heat', 'furnace', 'warm', 'winter', 'cold', 'ignite', 'pilot'},
            "Noise & Vibration Complaints": {'noise', 'loud', 'noisy', 'rattling', 'buzzing', 'grinding', 'squealing', 'banging', 'vibrating'},
            "Installation Quality Problems": {'installation', 'installed', 'installer', 'ductwork', 'wiring', 'placed', 'exposed'},
            "Maintenance Service Delays": {'maintenance', 'scheduled', 'appointment', 'waiting', 'cancelled', 'service', 'contract'},
            "Energy Efficiency Concerns": {'energy', 'electricity', 'bill', 'efficient', 'seer', 'consumption', 'bills', 'utility'},
            "Smart Thermostat / IoT Issues": {'thermostat', 'wifi', 'smart', 'app', 'connectivity', 'firmware', 'device', 'geofencing'},
            "Warranty & Billing Disputes": {'warranty', 'claim', 'denied', 'coverage', 'labor', 'parts', 'extended'},
            "Refrigerant Leak Hazards": {'refrigerant', 'leak', 'leaking', 'chemical', 'coil', 'smell', 'residue'},
            "Complete System Failures": {'failure', 'dead', 'shutdown', 'power', 'board', 'catastrophic', 'complete', 'fried'},
        }

        best_label = self.CLUSTER_LABELS.get(default_id, f"Cluster {default_id}")
        best_score = 0

        for label, kws in label_keywords.items():
            score = len(keyword_set & kws)
            if score > best_score:
                best_score = score
                best_label = label

        return best_label

    def get_cluster_trends(self, texts, labels, dates):
        """Get cluster trends over time."""
        import pandas as pd
        df = pd.DataFrame({
            'date': pd.to_datetime(dates),
            'cluster': labels
        })
        df['month'] = df['date'].dt.to_period('M').astype(str)

        trends = df.groupby(['month', 'cluster']).size().reset_index(name='count')
        return trends.to_dict('records')


# Singleton
_engine = None

def get_cluster_engine():
    global _engine
    if _engine is None:
        _engine = ComplaintClusterEngine(n_clusters=8)
    return _engine
