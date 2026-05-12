"""
Universal Analytics Engine — Dynamic analysis for ANY dataset.
Runs sentiment, clustering, trends, statistics based on detected schema.
"""
import re
import math
import numpy as np
import pandas as pd
from collections import Counter
from datetime import datetime


class UniversalAnalyticsEngine:
    """Run dynamic analyses based on detected schema."""

    def run_all(self, df, schema_result):
        """Run all applicable analyses and return combined results."""
        sem = schema_result["semantic_mapping"]
        analyses = schema_result["applicable_analyses"]
        results = {"dataset_type": schema_result["dataset_type"], "row_count": len(df),
                    "column_count": len(df.columns), "analyses": {}, "kpis": {},
                    "charts": [], "insights": []}

        analysis_map = {a["name"]: a for a in analyses}

        if "sentiment_analysis" in analysis_map:
            results["analyses"]["sentiment"] = self._sentiment_analysis(df, sem)
        if "keyword_extraction" in analysis_map:
            results["analyses"]["keywords"] = self._keyword_extraction(df, sem)
        if "topic_clustering" in analysis_map:
            results["analyses"]["clusters"] = self._topic_clustering(df, sem)
        if "text_statistics" in analysis_map:
            results["analyses"]["text_stats"] = self._text_statistics(df, sem)
        if "trend_analysis" in analysis_map:
            results["analyses"]["trends"] = self._trend_analysis(df, sem)
        if "category_distribution" in analysis_map:
            results["analyses"]["categories"] = self._category_distribution(df, sem)
        if "status_distribution" in analysis_map:
            results["analyses"]["status"] = self._status_distribution(df, sem)
        if "numerical_statistics" in analysis_map:
            results["analyses"]["numerical"] = self._numerical_statistics(df, sem)
        if "correlation_analysis" in analysis_map:
            results["analyses"]["correlations"] = self._correlation_analysis(df, sem)
        if "rating_analysis" in analysis_map:
            results["analyses"]["ratings"] = self._rating_analysis(df, sem)
        if "category_sentiment" in analysis_map:
            results["analyses"]["cat_sentiment"] = self._category_sentiment(df, sem)
        if "recurring_issues" in analysis_map:
            results["analyses"]["recurring"] = self._recurring_issues(df, sem)
        if "category_metrics" in analysis_map:
            results["analyses"]["cat_metrics"] = self._category_metrics(df, sem)

        results["analyses"]["quality"] = self._data_quality_report(df, schema_result)
        results["kpis"] = self._build_kpis(df, sem, results["analyses"])
        results["charts"] = self._build_charts(results["analyses"], sem)
        results["insights"] = self._generate_insights(df, sem, results["analyses"])
        return results

    def _get_text_col(self, sem):
        for col, info in sem.items():
            if info["semantic_role"] == "text_primary":
                return col
        for col, info in sem.items():
            if "text" in info["semantic_role"]:
                return col
        return None

    def _get_date_col(self, sem):
        for col, info in sem.items():
            if info["semantic_role"] == "date_column":
                return col
        return None

    def _get_cols_by_role(self, sem, role):
        return [c for c, i in sem.items() if i["semantic_role"] == role]

    def _get_cols_by_type(self, sem, dtype):
        return [c for c, i in sem.items() if i["detected_type"] == dtype]

    # ─── Text Analyses ────────────────────────────────────────────────────────
    def _sentiment_analysis(self, df, sem):
        from services.sentiment import get_analyzer
        text_col = self._get_text_col(sem)
        if not text_col:
            return {"error": "No text column found"}
        texts = df[text_col].dropna().astype(str).tolist()
        if not texts:
            return {"error": "No text data"}
        analyzer = get_analyzer()
        results = analyzer.batch_analyze(texts[:5000])
        scores = [r["sentiment_score"] for r in results]
        labels = [r["sentiment_label"] for r in results]
        emotions = [r.get("emotion", "None") for r in results]
        label_dist = dict(Counter(labels))
        emotion_dist = dict(Counter(emotions))
        return {
            "distribution": label_dist,
            "emotion_distribution": emotion_dist,
            "avg_score": round(np.mean(scores), 4),
            "median_score": round(float(np.median(scores)), 4),
            "negative_pct": round(sum(1 for s in scores if s < -0.2) / max(len(scores), 1) * 100, 1),
            "positive_pct": round(sum(1 for s in scores if s > 0.2) / max(len(scores), 1) * 100, 1),
            "neutral_pct": round(sum(1 for s in scores if -0.2 <= s <= 0.2) / max(len(scores), 1) * 100, 1),
            "scores": scores,
            "labels": labels,
            "text_column": text_col,
        }

    def _keyword_extraction(self, df, sem):
        text_col = self._get_text_col(sem)
        if not text_col:
            return {}
        texts = df[text_col].dropna().astype(str).tolist()
        all_text = " ".join(texts).lower()
        words = re.findall(r'\b[a-z]{3,}\b', all_text)
        stopwords = {"the","and","for","that","this","with","are","was","has","have","been",
                     "not","but","from","they","were","will","can","all","had","her","his",
                     "one","our","out","you","had","hot","how","its","may","own","too","use",
                     "way","who","did","get","got","let","say","she","him","old","see","now",
                     "new","also","than","very","when","what","just","into","over","such","any"}
        filtered = [w for w in words if w not in stopwords]
        freq = Counter(filtered)

        # Bigrams
        bigrams = [f"{filtered[i]} {filtered[i+1]}" for i in range(len(filtered)-1)]
        bigram_freq = Counter(bigrams).most_common(20)

        return {
            "top_words": [{"word": w, "count": c} for w, c in freq.most_common(30)],
            "top_bigrams": [{"phrase": w, "count": c} for w, c in bigram_freq],
            "total_words": len(words),
            "unique_words": len(set(words)),
            "text_column": text_col,
        }

    def _topic_clustering(self, df, sem):
        text_col = self._get_text_col(sem)
        if not text_col:
            return {}
        from services.clustering import get_cluster_engine
        texts = df[text_col].dropna().astype(str).tolist()
        if len(texts) < 10:
            return {"error": "Not enough text data for clustering"}
        engine = get_cluster_engine()
        cluster_labels, info = engine.fit_predict(texts)
        # Count from actual labels
        from collections import Counter
        label_counts = Counter(cluster_labels)
        dist = {}
        details = {}
        for cid, cinfo in info.items():
            name = cinfo.get("label", f"Topic {cid}")
            count = label_counts.get(cid, cinfo.get("count", 0))
            dist[name] = count
            details[name] = {"count": count, "keywords": cinfo.get("keywords", [])[:8]}
        return {"cluster_distribution": dist, "cluster_details": details, "text_column": text_col}

    def _text_statistics(self, df, sem):
        text_col = self._get_text_col(sem)
        if not text_col:
            return {}
        texts = df[text_col].dropna().astype(str)
        lengths = texts.str.len()
        word_counts = texts.str.split().str.len()
        return {
            "avg_length": round(float(lengths.mean()), 1),
            "max_length": int(lengths.max()),
            "min_length": int(lengths.min()),
            "avg_words": round(float(word_counts.mean()), 1),
            "total_entries": len(texts),
            "text_column": text_col,
        }

    # ─── Date Analyses ────────────────────────────────────────────────────────
    def _trend_analysis(self, df, sem):
        date_col = self._get_date_col(sem)
        if not date_col:
            return {}
        dfc = df.copy()
        dfc[date_col] = pd.to_datetime(dfc[date_col], errors='coerce')
        dfc = dfc.dropna(subset=[date_col])
        if len(dfc) == 0:
            return {"error": "No valid dates"}
        dfc["_month"] = dfc[date_col].dt.to_period("M").astype(str)
        monthly = dfc.groupby("_month").size()
        trend_data = {str(k): int(v) for k, v in monthly.items()}
        # Day of week distribution
        dow = dfc[date_col].dt.day_name().value_counts()
        dow_dist = {str(k): int(v) for k, v in dow.items()}
        # Hourly if time component exists
        hourly = {}
        if dfc[date_col].dt.hour.nunique() > 1:
            h = dfc[date_col].dt.hour.value_counts().sort_index()
            hourly = {str(k): int(v) for k, v in h.items()}
        return {
            "monthly_trend": trend_data,
            "day_of_week": dow_dist,
            "hourly_distribution": hourly,
            "date_range": {"min": str(dfc[date_col].min()), "max": str(dfc[date_col].max())},
            "date_column": date_col,
        }

    # ─── Category Analyses ────────────────────────────────────────────────────
    def _category_distribution(self, df, sem):
        cat_cols = self._get_cols_by_type(sem, "categorical")
        if not cat_cols:
            return {}
        distributions = {}
        for col in cat_cols[:6]:
            vc = df[col].value_counts().head(20)
            distributions[col] = {str(k): int(v) for k, v in vc.items()}
        return {"distributions": distributions, "columns": cat_cols}

    def _status_distribution(self, df, sem):
        status_cols = self._get_cols_by_role(sem, "status_column")
        if not status_cols:
            return {}
        col = status_cols[0]
        dist = df[col].value_counts()
        return {"column": col, "distribution": {str(k): int(v) for k, v in dist.items()}}

    # ─── Numerical Analyses ───────────────────────────────────────────────────
    def _numerical_statistics(self, df, sem):
        num_cols = self._get_cols_by_type(sem, "numeric")
        if not num_cols:
            return {}
        stats = {}
        for col in num_cols[:10]:
            s = pd.to_numeric(df[col], errors='coerce').dropna()
            if len(s) == 0:
                continue
            q1, q3 = float(s.quantile(0.25)), float(s.quantile(0.75))
            iqr = q3 - q1
            outliers = int(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum())
            stats[col] = {
                "mean": round(float(s.mean()), 2), "median": round(float(s.median()), 2),
                "std": round(float(s.std()), 2), "min": round(float(s.min()), 2),
                "max": round(float(s.max()), 2), "q1": round(q1, 2), "q3": round(q3, 2),
                "outlier_count": outliers,
                "distribution": self._histogram(s),
            }
        return {"statistics": stats, "columns": num_cols}

    def _histogram(self, series, bins=10):
        counts, edges = np.histogram(series.dropna(), bins=bins)
        return [{"range": f"{edges[i]:.1f}-{edges[i+1]:.1f}", "count": int(counts[i])} for i in range(len(counts))]

    def _correlation_analysis(self, df, sem):
        num_cols = self._get_cols_by_type(sem, "numeric")
        if len(num_cols) < 2:
            return {}
        num_df = df[num_cols].apply(pd.to_numeric, errors='coerce')
        corr = num_df.corr()
        pairs = []
        for i, c1 in enumerate(corr.columns):
            for j, c2 in enumerate(corr.columns):
                if i < j:
                    val = corr.iloc[i, j]
                    if not np.isnan(val) and abs(val) > 0.3:
                        pairs.append({"col1": c1, "col2": c2, "correlation": round(float(val), 3),
                                      "strength": "Strong" if abs(val) > 0.7 else "Moderate"})
        pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        return {"significant_correlations": pairs[:20], "columns": num_cols}

    def _rating_analysis(self, df, sem):
        rating_cols = self._get_cols_by_role(sem, "rating_column")
        if not rating_cols:
            return {}
        col = rating_cols[0]
        s = pd.to_numeric(df[col], errors='coerce').dropna()
        if len(s) == 0:
            return {}
        return {
            "column": col, "avg_rating": round(float(s.mean()), 2),
            "median_rating": round(float(s.median()), 2),
            "distribution": {str(k): int(v) for k, v in s.value_counts().sort_index().items()},
            "below_avg_pct": round(float((s < s.mean()).mean() * 100), 1),
        }

    # ─── Cross Analyses ───────────────────────────────────────────────────────
    def _category_sentiment(self, df, sem):
        text_col = self._get_text_col(sem)
        cat_cols = self._get_cols_by_type(sem, "categorical")
        if not text_col or not cat_cols:
            return {}
        sent = self._sentiment_analysis(df, sem)
        if "scores" not in sent:
            return {}
        scores = sent["scores"]
        idx = df[text_col].dropna().index
        result = {}
        for cat_col in cat_cols[:3]:
            cat_sent = {}
            for i, score in enumerate(scores):
                if i < len(idx):
                    cat = str(df.loc[idx[i], cat_col]) if cat_col in df.columns else "Unknown"
                    if cat not in cat_sent:
                        cat_sent[cat] = []
                    cat_sent[cat].append(score)
            result[cat_col] = {k: round(np.mean(v), 4) for k, v in cat_sent.items() if len(v) >= 3}
        return result

    def _recurring_issues(self, df, sem):
        text_col = self._get_text_col(sem)
        if not text_col:
            return {}
        texts = df[text_col].dropna().astype(str).tolist()
        # Find repeated phrases (3-grams)
        all_ngrams = []
        for t in texts:
            words = re.findall(r'\b[a-z]{3,}\b', t.lower())
            for i in range(len(words)-2):
                all_ngrams.append(f"{words[i]} {words[i+1]} {words[i+2]}")
        freq = Counter(all_ngrams)
        recurring = [{"phrase": p, "count": c} for p, c in freq.most_common(15) if c >= 5]
        return {"recurring_phrases": recurring, "text_column": text_col}

    def _category_metrics(self, df, sem):
        cat_cols = self._get_cols_by_type(sem, "categorical")
        num_cols = self._get_cols_by_type(sem, "numeric")
        if not cat_cols or not num_cols:
            return {}
        result = {}
        cat_col = cat_cols[0]
        for num_col in num_cols[:3]:
            s = df.groupby(cat_col)[num_col].apply(lambda x: pd.to_numeric(x, errors='coerce').mean())
            result[f"{num_col}_by_{cat_col}"] = {str(k): round(float(v), 2) for k, v in s.dropna().items()}
        return result

    def _data_quality_report(self, df, schema_result):
        return schema_result.get("data_quality", {})

    # ─── KPI Builder ──────────────────────────────────────────────────────────
    def _build_kpis(self, df, sem, analyses):
        kpis = [
            {"label": "Total Records", "value": str(len(df)), "icon": "📊"},
            {"label": "Columns", "value": str(len(df.columns)), "icon": "📋"},
        ]
        if "sentiment" in analyses and "avg_score" in analyses["sentiment"]:
            s = analyses["sentiment"]
            kpis.append({"label": "Avg Sentiment", "value": str(s["avg_score"]), "icon": "💬",
                         "color": "green" if s["avg_score"] > 0 else "red"})
            kpis.append({"label": "Negative %", "value": f"{s['negative_pct']}%", "icon": "😡", "color": "red"})
            kpis.append({"label": "Positive %", "value": f"{s['positive_pct']}%", "icon": "😊", "color": "green"})
        if "status" in analyses and "distribution" in analyses["status"]:
            for status, count in list(analyses["status"]["distribution"].items())[:3]:
                kpis.append({"label": status, "value": str(count), "icon": "🎯"})
        if "ratings" in analyses and "avg_rating" in analyses["ratings"]:
            kpis.append({"label": "Avg Rating", "value": str(analyses["ratings"]["avg_rating"]), "icon": "⭐"})
        if "trends" in analyses and "date_range" in analyses["trends"]:
            dr = analyses["trends"]["date_range"]
            kpis.append({"label": "Date Range", "value": f"{dr['min'][:10]} to {dr['max'][:10]}", "icon": "📅"})
        return kpis

    # ─── Chart Builder ────────────────────────────────────────────────────────
    def _build_charts(self, analyses, sem):
        charts = []
        if "sentiment" in analyses and "distribution" in analyses["sentiment"]:
            charts.append({"id": "chart-sentiment", "type": "doughnut", "title": "Sentiment Distribution",
                           "data": analyses["sentiment"]["distribution"]})
        if "sentiment" in analyses and "emotion_distribution" in analyses["sentiment"]:
            charts.append({"id": "chart-emotions", "type": "doughnut", "title": "Emotion Distribution",
                           "data": analyses["sentiment"]["emotion_distribution"]})
        if "clusters" in analyses and "cluster_distribution" in analyses["clusters"]:
            charts.append({"id": "chart-clusters", "type": "bar", "title": "Topic Clusters",
                           "data": analyses["clusters"]["cluster_distribution"]})
        if "trends" in analyses and "monthly_trend" in analyses["trends"]:
            charts.append({"id": "chart-trend", "type": "line", "title": "Volume Over Time",
                           "data": analyses["trends"]["monthly_trend"]})
        if "trends" in analyses and "day_of_week" in analyses["trends"]:
            charts.append({"id": "chart-dow", "type": "bar", "title": "Day of Week Distribution",
                           "data": analyses["trends"]["day_of_week"]})
        if "categories" in analyses and "distributions" in analyses["categories"]:
            for col, dist in list(analyses["categories"]["distributions"].items())[:4]:
                charts.append({"id": f"chart-cat-{col[:20]}", "type": "bar",
                               "title": f"{col.replace('_',' ').title()} Distribution", "data": dist})
        if "status" in analyses and "distribution" in analyses["status"]:
            charts.append({"id": "chart-status", "type": "doughnut", "title": "Status Distribution",
                           "data": analyses["status"]["distribution"]})
        if "ratings" in analyses and "distribution" in analyses["ratings"]:
            charts.append({"id": "chart-ratings", "type": "bar", "title": "Rating Distribution",
                           "data": analyses["ratings"]["distribution"]})
        if "keywords" in analyses and "top_words" in analyses["keywords"]:
            top = analyses["keywords"]["top_words"][:15]
            charts.append({"id": "chart-keywords", "type": "bar",
                           "title": "Top Keywords", "data": {w["word"]: w["count"] for w in top}})
        return charts

    # ─── AI Insight Generator ─────────────────────────────────────────────────
    def _generate_insights(self, df, sem, analyses):
        insights = []
        if "sentiment" in analyses:
            s = analyses["sentiment"]
            if s.get("negative_pct", 0) > 40:
                insights.append({"type": "warning", "icon": "⚠️", "title": "High Negative Sentiment",
                    "message": f"{s['negative_pct']}% of entries have negative sentiment. Investigate root causes.",
                    "priority": "high"})
            elif s.get("positive_pct", 0) > 60:
                insights.append({"type": "success", "icon": "✅", "title": "Strong Positive Sentiment",
                    "message": f"{s['positive_pct']}% positive sentiment detected.", "priority": "low"})
            if s.get("avg_score", 0) < -0.3:
                insights.append({"type": "critical", "icon": "🚨", "title": "Critical Sentiment Alert",
                    "message": f"Average sentiment score is {s['avg_score']} — significantly negative.",
                    "priority": "critical"})

        if "clusters" in analyses and "cluster_distribution" in analyses["clusters"]:
            cd = analyses["clusters"]["cluster_distribution"]
            if cd:
                top = max(cd, key=cd.get)
                insights.append({"type": "info", "icon": "🔬", "title": "Dominant Topic",
                    "message": f"'{top}' is the most common topic with {cd[top]} entries.",
                    "priority": "medium"})

        if "trends" in analyses and "monthly_trend" in analyses["trends"]:
            mt = analyses["trends"]["monthly_trend"]
            values = list(mt.values())
            if len(values) >= 3 and values[-1] > values[-2] * 1.3:
                insights.append({"type": "warning", "icon": "📈", "title": "Volume Spike",
                    "message": f"Recent period shows {int((values[-1]/max(values[-2],1)-1)*100)}% increase.",
                    "priority": "high"})

        if "numerical" in analyses and "statistics" in analyses["numerical"]:
            for col, stats in analyses["numerical"]["statistics"].items():
                if stats.get("outlier_count", 0) > len(df) * 0.05:
                    insights.append({"type": "info", "icon": "📐", "title": f"Outliers in {col}",
                        "message": f"{stats['outlier_count']} outliers detected ({col}).",
                        "priority": "medium"})

        if "correlations" in analyses and "significant_correlations" in analyses["correlations"]:
            for corr in analyses["correlations"]["significant_correlations"][:3]:
                if corr["strength"] == "Strong":
                    insights.append({"type": "info", "icon": "🔗", "title": "Strong Correlation",
                        "message": f"{corr['col1']} ↔ {corr['col2']}: {corr['correlation']}",
                        "priority": "medium"})

        if "quality" in analyses:
            q = analyses["quality"]
            if q.get("completeness_pct", 100) < 80:
                insights.append({"type": "warning", "icon": "⚠️", "title": "Data Quality Issue",
                    "message": f"Data completeness is only {q['completeness_pct']}%.",
                    "priority": "high"})
            if q.get("duplicate_pct", 0) > 10:
                insights.append({"type": "info", "icon": "📋", "title": "Duplicate Records",
                    "message": f"{q['duplicate_pct']}% duplicate rows detected.",
                    "priority": "medium"})

        if not insights:
            insights.append({"type": "info", "icon": "✅", "title": "Analysis Complete",
                "message": "No significant anomalies detected.", "priority": "low"})

        insights.sort(key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.get("priority", "low"), 4))
        return insights


_engine = None
def get_universal_analytics():
    global _engine
    if _engine is None:
        _engine = UniversalAnalyticsEngine()
    return _engine
