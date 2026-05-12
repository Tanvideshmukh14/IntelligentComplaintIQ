"""
Universal Schema Intelligence Engine
Auto-detects column types, semantic meanings, and data profiles for ANY dataset.
"""
import re
import math
from collections import Counter
from difflib import SequenceMatcher
from datetime import datetime


# ─── Semantic Role Definitions ────────────────────────────────────────────────
SEMANTIC_ROLES = {
    "text_primary": {
        "keywords": ["complaint", "description", "text", "message", "feedback", "review",
                      "comment", "issue", "detail", "body", "content", "note", "summary",
                      "query", "question", "concern", "observation", "remark", "ticket_body",
                      "complaint_text", "complaint_description", "issue_description",
                      "customer_feedback", "review_text", "support_message"],
        "weight": 1.0,
    },
    "text_secondary": {
        "keywords": ["technician_notes", "resolution_notes", "agent_notes", "internal_notes",
                      "notes", "response", "reply", "answer", "solution", "follow_up"],
        "weight": 0.8,
    },
    "id_column": {
        "keywords": ["id", "complaint_id", "ticket_id", "case_id", "order_id", "ref",
                      "reference", "number", "serial", "code", "key", "uid", "uuid",
                      "customer_id", "user_id", "tracking", "case_number", "sr_no"],
        "weight": 1.0,
    },
    "date_column": {
        "keywords": ["date", "time", "datetime", "timestamp", "created", "created_at",
                      "updated", "updated_at", "submitted", "reported", "complaint_date",
                      "order_date", "purchase_date", "resolved_date", "closed_date",
                      "due_date", "deadline", "scheduled", "occurred", "received_date"],
        "weight": 1.0,
    },
    "category_column": {
        "keywords": ["category", "type", "class", "group", "department", "product_type",
                      "product_category", "complaint_type", "issue_type", "ticket_type",
                      "service_type", "topic", "classification", "segment", "division",
                      "product_name", "product", "brand", "model", "subcategory"],
        "weight": 0.9,
    },
    "status_column": {
        "keywords": ["status", "resolution_status", "complaint_status", "ticket_status",
                      "case_status", "order_status", "progress", "stage", "phase", "outcome",
                      "result", "disposition", "resolved", "closed", "is_resolved"],
        "weight": 1.0,
    },
    "customer_column": {
        "keywords": ["customer", "customer_name", "client", "user", "name", "full_name",
                      "first_name", "buyer", "account", "contact", "requester", "reporter",
                      "author", "submitter", "caller", "email", "customer_email", "phone"],
        "weight": 0.8,
    },
    "location_column": {
        "keywords": ["city", "state", "country", "region", "location", "address", "zip",
                      "postal", "area", "zone", "branch", "office", "site", "store",
                      "warehouse", "facility", "service_location", "geo", "place"],
        "weight": 0.8,
    },
    "severity_column": {
        "keywords": ["severity", "priority", "urgency", "importance", "impact", "level",
                      "criticality", "risk", "risk_level", "sla", "tier", "grade"],
        "weight": 0.9,
    },
    "rating_column": {
        "keywords": ["rating", "score", "satisfaction", "csat", "nps", "stars", "feedback_rating",
                      "customer_rating", "review_rating", "quality_score", "happiness"],
        "weight": 0.9,
    },
    "channel_column": {
        "keywords": ["channel", "source", "medium", "platform", "origin", "method",
                      "communication_channel", "contact_method", "complaint_source",
                      "device", "device_type", "app_version", "submitted_via"],
        "weight": 0.8,
    },
    "amount_column": {
        "keywords": ["amount", "price", "cost", "total", "revenue", "payment", "refund",
                      "fee", "charge", "value", "budget", "spend", "invoice", "billing"],
        "weight": 0.8,
    },
    "duration_column": {
        "keywords": ["duration", "time_hours", "resolution_time", "response_time", "wait_time",
                      "handle_time", "processing_time", "turnaround", "elapsed", "age",
                      "first_response_time", "resolution_time_hours", "delay", "delay_days"],
        "weight": 0.9,
    },
    "boolean_column": {
        "keywords": ["is_", "has_", "was_", "escalation_required", "refund_requested",
                      "is_duplicate", "is_spam", "is_resolved", "is_escalated", "flag",
                      "active", "enabled", "verified", "confirmed"],
        "weight": 0.7,
    },
}


class SchemaIntelligenceEngine:
    """AI-powered schema detection and semantic mapping."""

    def analyze_schema(self, df):
        """Full schema analysis pipeline."""
        profile = self._profile_columns(df)
        semantic_map = self._semantic_mapping(df, profile)
        dataset_type = self._detect_dataset_type(semantic_map, df)
        applicable = self._determine_applicable_analyses(semantic_map, profile)
        quality = self._assess_data_quality(df, profile)

        return {
            "dataset_type": dataset_type,
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "column_profiles": profile,
            "semantic_mapping": semantic_map,
            "applicable_analyses": applicable,
            "data_quality": quality,
            "summary": self._generate_summary(df, semantic_map, dataset_type, profile),
        }

    def _profile_columns(self, df):
        """Profile each column: type, unique count, null rate, sample values."""
        profiles = {}
        for col in df.columns:
            series = df[col]
            non_null = series.dropna()
            unique_count = non_null.nunique()
            null_pct = round(series.isna().mean() * 100, 1)
            total = len(series)

            # Detect data type
            dtype = self._detect_dtype(series, col)
            samples = non_null.head(5).tolist() if len(non_null) > 0 else []

            profile = {
                "original_dtype": str(series.dtype),
                "detected_type": dtype,
                "null_percentage": null_pct,
                "unique_count": unique_count,
                "unique_ratio": round(unique_count / max(total, 1), 4),
                "sample_values": [str(s)[:100] for s in samples],
            }

            if dtype == "numeric":
                profile["min"] = float(non_null.min()) if len(non_null) > 0 else None
                profile["max"] = float(non_null.max()) if len(non_null) > 0 else None
                profile["mean"] = round(float(non_null.mean()), 2) if len(non_null) > 0 else None
                profile["std"] = round(float(non_null.std()), 2) if len(non_null) > 0 else None

            if dtype == "categorical":
                top = non_null.value_counts().head(10)
                profile["top_values"] = {str(k): int(v) for k, v in top.items()}

            if dtype == "text":
                lengths = non_null.astype(str).str.len()
                profile["avg_length"] = round(float(lengths.mean()), 1) if len(lengths) > 0 else 0
                profile["max_length"] = int(lengths.max()) if len(lengths) > 0 else 0

            profiles[col] = profile
        return profiles

    def _detect_dtype(self, series, col_name):
        """Detect the semantic data type of a column."""
        non_null = series.dropna()
        if len(non_null) == 0:
            return "empty"

        col_lower = col_name.lower().strip()

        # Check for datetime
        if self._is_datetime(series, col_lower):
            return "datetime"

        # Check for boolean
        unique_vals = set(str(v).lower().strip() for v in non_null.unique()[:20])
        bool_vals = {"true", "false", "yes", "no", "1", "0", "y", "n", "t", "f"}
        if len(unique_vals) <= 3 and unique_vals.issubset(bool_vals):
            return "boolean"

        # Check for numeric
        if str(series.dtype).startswith(("int", "float", "Int", "Float")):
            unique_ratio = non_null.nunique() / max(len(non_null), 1)
            if unique_ratio < 0.02 and non_null.nunique() <= 15:
                return "categorical"
            return "numeric"

        # Try to parse as numeric
        try:
            import pandas as pd
            numeric = pd.to_numeric(non_null, errors='coerce')
            if numeric.notna().mean() > 0.8:
                return "numeric"
        except Exception:
            pass

        # Text vs categorical
        str_series = non_null.astype(str)
        avg_len = str_series.str.len().mean()
        unique_ratio = non_null.nunique() / max(len(non_null), 1)

        if avg_len > 50:
            return "text"
        if unique_ratio < 0.05 or non_null.nunique() <= 30:
            return "categorical"
        if avg_len > 20 and unique_ratio > 0.3:
            return "text"
        if unique_ratio > 0.8:
            return "identifier"

        return "categorical"

    def _is_datetime(self, series, col_name):
        """Check if a column contains datetime values."""
        import pandas as pd
        if pd.api.types.is_datetime64_any_dtype(series):
            return True
        date_keywords = ["date", "time", "timestamp", "created", "updated", "at", "on", "when"]
        if any(kw in col_name for kw in date_keywords):
            try:
                sample = series.dropna().head(20)
                parsed = pd.to_datetime(sample, errors='coerce', infer_datetime_format=True)
                if parsed.notna().mean() > 0.7:
                    return True
            except Exception:
                pass
        # Try anyway for string columns that look like dates
        if str(series.dtype) == 'object':
            try:
                sample = series.dropna().head(10)
                date_patterns = [
                    r'\d{4}-\d{2}-\d{2}', r'\d{2}/\d{2}/\d{4}', r'\d{2}-\d{2}-\d{4}',
                    r'\d{2}-\d{2}-\d{2}', r'\d{4}/\d{2}/\d{2}',
                ]
                matches = sum(1 for v in sample if any(re.search(p, str(v)) for p in date_patterns))
                if matches / max(len(sample), 1) > 0.6:
                    return True
            except Exception:
                pass
        return False

    def _semantic_mapping(self, df, profiles):
        """Map columns to semantic roles using fuzzy matching."""
        mapping = {}
        used_roles = {}

        for col in df.columns:
            col_lower = col.lower().strip().replace(" ", "_")
            dtype = profiles[col]["detected_type"]
            best_role = None
            best_score = 0

            for role, config in SEMANTIC_ROLES.items():
                # Skip role-type mismatches
                if role in ("text_primary", "text_secondary") and dtype not in ("text",):
                    continue
                if role == "id_column" and dtype not in ("identifier", "text", "categorical"):
                    continue
                if role == "date_column" and dtype != "datetime":
                    continue
                if role in ("amount_column", "duration_column", "rating_column") and dtype != "numeric":
                    continue
                if role == "boolean_column" and dtype != "boolean":
                    continue

                score = self._match_score(col_lower, config["keywords"], config["weight"])
                if score > best_score and score > 0.35:
                    best_score = score
                    best_role = role

            # Fallback: assign by data type if no semantic match
            if best_role is None:
                if dtype == "text" and profiles[col].get("avg_length", 0) > 40:
                    best_role = "text_primary"
                    best_score = 0.4
                elif dtype == "datetime":
                    best_role = "date_column"
                    best_score = 0.5
                elif dtype == "numeric":
                    best_role = "amount_column"
                    best_score = 0.3
                elif dtype == "identifier":
                    best_role = "id_column"
                    best_score = 0.4
                elif dtype == "boolean":
                    best_role = "boolean_column"
                    best_score = 0.4

            if best_role:
                # If role already taken, keep the better match
                if best_role in used_roles:
                    if best_score > used_roles[best_role]["score"]:
                        # Demote previous assignment
                        prev_col = used_roles[best_role]["column"]
                        mapping[prev_col]["semantic_role"] = self._fallback_role(profiles[prev_col]["detected_type"])
                        used_roles[best_role] = {"column": col, "score": best_score}
                    else:
                        best_role = self._fallback_role(dtype)
                else:
                    used_roles[best_role] = {"column": col, "score": best_score}

            mapping[col] = {
                "semantic_role": best_role or "unknown",
                "confidence": round(best_score, 3),
                "detected_type": dtype,
            }

        return mapping

    def _match_score(self, col_name, keywords, weight):
        """Fuzzy match a column name against keyword list."""
        best = 0
        col_clean = col_name.replace("_", " ").replace("-", " ").lower()

        for kw in keywords:
            kw_clean = kw.replace("_", " ").replace("-", " ").lower()

            # Exact match
            if col_clean == kw_clean:
                return 1.0 * weight

            # Contains match
            if kw_clean in col_clean or col_clean in kw_clean:
                score = 0.85 * weight
                if score > best:
                    best = score
                continue

            # Fuzzy ratio
            ratio = SequenceMatcher(None, col_clean, kw_clean).ratio()
            if ratio > 0.7:
                score = ratio * weight
                if score > best:
                    best = score

            # Word overlap
            col_words = set(col_clean.split())
            kw_words = set(kw_clean.split())
            overlap = col_words & kw_words
            if overlap:
                score = len(overlap) / max(len(col_words | kw_words), 1) * weight
                if score > best:
                    best = score

        return best

    def _fallback_role(self, dtype):
        """Assign a generic role based on data type."""
        return {
            "text": "text_secondary",
            "numeric": "amount_column",
            "categorical": "category_column",
            "datetime": "date_column",
            "identifier": "id_column",
            "boolean": "boolean_column",
        }.get(dtype, "unknown")

    def _detect_dataset_type(self, semantic_map, df):
        """Infer the overall dataset type."""
        roles = [v["semantic_role"] for v in semantic_map.values()]
        col_names = " ".join(df.columns).lower()

        # Check for specific domain keywords
        domain_signals = {
            "HVAC / Maintenance Complaints": ["hvac", "compressor", "cooling", "heating", "refrigerant", "thermostat", "technician"],
            "E-commerce / Orders": ["order", "cart", "shipping", "delivery", "purchase", "refund", "payment", "sku"],
            "Customer Support / Tickets": ["ticket", "support", "helpdesk", "agent", "sla", "escalat", "case"],
            "Product Reviews / Feedback": ["review", "rating", "stars", "recommend", "satisfaction"],
            "Logistics / Supply Chain": ["shipment", "warehouse", "logistics", "tracking", "freight", "carrier"],
            "CRM / Customer Data": ["lead", "opportunity", "pipeline", "account", "deal", "crm"],
            "Healthcare / Clinical": ["patient", "diagnosis", "treatment", "clinical", "medical"],
            "HR / Employee": ["employee", "department", "salary", "leave", "attendance", "hr"],
        }

        best_domain = "General Tabular Dataset"
        best_score = 0
        for domain, keywords in domain_signals.items():
            score = sum(1 for kw in keywords if kw in col_names)
            if score > best_score:
                best_score = score
                best_domain = domain

        has_text = "text_primary" in roles
        has_date = "date_column" in roles
        has_cat = "category_column" in roles or "status_column" in roles

        if has_text and has_cat and best_score < 2:
            best_domain = "Customer Complaints / Feedback"
        elif has_text and not has_cat and best_score < 2:
            best_domain = "Text / Survey Dataset"
        elif not has_text and has_cat and best_score < 2:
            best_domain = "Operational / Transactional Dataset"

        return best_domain

    def _determine_applicable_analyses(self, semantic_map, profiles):
        """Determine which analyses can run based on detected schema."""
        roles = {v["semantic_role"]: k for k, v in semantic_map.items()}
        types = {k: v["detected_type"] for k, v in profiles.items()}

        text_cols = [k for k, v in semantic_map.items() if v["semantic_role"] in ("text_primary", "text_secondary")]
        date_cols = [k for k, v in semantic_map.items() if v["semantic_role"] == "date_column"]
        cat_cols = [k for k, v in semantic_map.items() if v["detected_type"] == "categorical"]
        num_cols = [k for k, v in semantic_map.items() if v["detected_type"] == "numeric"]
        status_cols = [k for k, v in semantic_map.items() if v["semantic_role"] == "status_column"]
        rating_cols = [k for k, v in semantic_map.items() if v["semantic_role"] == "rating_column"]

        analyses = []

        if text_cols:
            analyses.extend([
                {"name": "sentiment_analysis", "label": "Sentiment Analysis", "columns": text_cols, "icon": "💬"},
                {"name": "keyword_extraction", "label": "Keyword Extraction", "columns": text_cols, "icon": "🔑"},
                {"name": "topic_clustering", "label": "Topic Clustering", "columns": text_cols, "icon": "🔬"},
                {"name": "text_statistics", "label": "Text Statistics", "columns": text_cols, "icon": "📝"},
            ])
        if date_cols:
            analyses.append({"name": "trend_analysis", "label": "Trend Analysis", "columns": date_cols, "icon": "📈"})
            if text_cols:
                analyses.append({"name": "temporal_sentiment", "label": "Sentiment Over Time", "columns": date_cols + text_cols, "icon": "📅"})
        if cat_cols:
            analyses.append({"name": "category_distribution", "label": "Category Distribution", "columns": cat_cols, "icon": "📊"})
            if text_cols:
                analyses.append({"name": "category_sentiment", "label": "Sentiment by Category", "columns": cat_cols + text_cols, "icon": "🏷️"})
        if num_cols:
            analyses.append({"name": "numerical_statistics", "label": "Numerical Statistics", "columns": num_cols, "icon": "📐"})
            if len(num_cols) >= 2:
                analyses.append({"name": "correlation_analysis", "label": "Correlation Analysis", "columns": num_cols, "icon": "🔗"})
        if status_cols:
            analyses.append({"name": "status_distribution", "label": "Status Distribution", "columns": status_cols, "icon": "🎯"})
        if rating_cols:
            analyses.append({"name": "rating_analysis", "label": "Rating Analysis", "columns": rating_cols, "icon": "⭐"})

        # Cross-analyses
        if text_cols and cat_cols:
            analyses.append({"name": "recurring_issues", "label": "Recurring Issue Detection", "columns": text_cols + cat_cols, "icon": "🔄"})
        if num_cols and cat_cols:
            analyses.append({"name": "category_metrics", "label": "Metrics by Category", "columns": num_cols + cat_cols, "icon": "📊"})

        # Always add
        analyses.append({"name": "data_quality", "label": "Data Quality Report", "columns": list(profiles.keys()), "icon": "✅"})
        analyses.append({"name": "ai_insights", "label": "AI-Generated Insights", "columns": list(profiles.keys()), "icon": "🧠"})

        return analyses

    def _assess_data_quality(self, df, profiles):
        """Assess overall data quality."""
        total_cells = len(df) * len(df.columns)
        null_cells = df.isna().sum().sum()
        completeness = round((1 - null_cells / max(total_cells, 1)) * 100, 1)

        high_null_cols = [col for col, p in profiles.items() if p["null_percentage"] > 50]
        empty_cols = [col for col, p in profiles.items() if p["detected_type"] == "empty"]
        dup_rows = int(df.duplicated().sum())

        return {
            "completeness_pct": completeness,
            "total_null_cells": int(null_cells),
            "high_null_columns": high_null_cols,
            "empty_columns": empty_cols,
            "duplicate_rows": dup_rows,
            "duplicate_pct": round(dup_rows / max(len(df), 1) * 100, 1),
            "quality_score": min(100, round(completeness - len(high_null_cols) * 5 - len(empty_cols) * 10, 1)),
        }

    def _generate_summary(self, df, semantic_map, dataset_type, profiles):
        """Generate a human-readable summary."""
        text_cols = [k for k, v in semantic_map.items() if "text" in v["semantic_role"]]
        date_cols = [k for k, v in semantic_map.items() if v["semantic_role"] == "date_column"]
        cat_cols = [k for k, v in semantic_map.items() if v["detected_type"] == "categorical"]
        num_cols = [k for k, v in semantic_map.items() if v["detected_type"] == "numeric"]

        parts = [f"Detected as: {dataset_type}"]
        parts.append(f"{len(df)} rows × {len(df.columns)} columns")
        if text_cols:
            parts.append(f"Text fields: {', '.join(text_cols[:3])}")
        if date_cols:
            parts.append(f"Date fields: {', '.join(date_cols[:3])}")
        if cat_cols:
            parts.append(f"Categories: {', '.join(cat_cols[:3])}")
        if num_cols:
            parts.append(f"Numeric fields: {', '.join(num_cols[:3])}")

        return " | ".join(parts)


_engine = None
def get_schema_engine():
    global _engine
    if _engine is None:
        _engine = SchemaIntelligenceEngine()
    return _engine
