"""
HVAC Complaint Intelligence System — Data Ingestion Engine
Handles CSV, Excel, JSON, SQL data import with auto schema detection and column mapping.
"""
import os
import re
import json
import pandas as pd
import numpy as np
from datetime import datetime


class DataIngestionEngine:
    """Enterprise data ingestion with auto-schema detection and column mapping."""

    # Standard schema fields
    STANDARD_FIELDS = {
        'complaint_id': {'aliases': ['complaint id', 'ticket id', 'id', 'case id', 'ticket_id', 'case_id', 'complaint_id', 'ref', 'reference'], 'type': 'string'},
        'complaint_text': {'aliases': ['complaint text', 'description', 'complaint description', 'complaint_description', 'complaint_text', 'text', 'details', 'issue', 'issue_description', 'comment', 'feedback_text', 'message'], 'type': 'text'},
        'product_type': {'aliases': ['product type', 'product_type', 'product', 'equipment', 'equipment_type', 'system type', 'system_type', 'unit type', 'unit_type', 'hvac type', 'hvac_type'], 'type': 'category'},
        'equipment_model': {'aliases': ['hvac model', 'model', 'equipment_model', 'equipment model', 'model_number', 'model number', 'unit model', 'unit_model'], 'type': 'string'},
        'complaint_category': {'aliases': ['complaint category', 'category', 'complaint_category', 'issue_type', 'issue type', 'problem_type', 'problem type', 'classification'], 'type': 'category'},
        'customer_name': {'aliases': ['customer name', 'customer_name', 'name', 'customer', 'client', 'client_name'], 'type': 'string'},
        'customer_feedback': {'aliases': ['customer feedback', 'customer_feedback', 'feedback', 'review', 'customer_review'], 'type': 'text'},
        'resolution_status': {'aliases': ['resolution status', 'resolution_status', 'status', 'ticket_status', 'case_status', 'state'], 'type': 'category'},
        'department': {'aliases': ['department', 'dept', 'team', 'assigned_team', 'assigned_department', 'routing', 'business_unit'], 'type': 'category'},
        'severity': {'aliases': ['severity', 'severity_level', 'priority', 'priority_level', 'urgency', 'risk_level'], 'type': 'category'},
        'date_time': {'aliases': ['timestamp', 'date', 'datetime', 'date_time', 'created_at', 'created_date', 'submission_date', 'reported_date', 'complaint_date'], 'type': 'datetime'},
        'technician_notes': {'aliases': ['technician notes', 'technician_notes', 'tech notes', 'tech_notes', 'service_notes', 'resolution_notes', 'notes'], 'type': 'text'},
        'service_region': {'aliases': ['service region', 'service_region', 'region', 'location', 'area', 'zone', 'territory', 'service_location', 'city', 'state'], 'type': 'string'},
        'warranty_status': {'aliases': ['warranty status', 'warranty_status', 'warranty', 'coverage', 'warranty_type'], 'type': 'category'},
        'customer_channel': {'aliases': ['customer channel', 'customer_channel', 'channel', 'communication_channel', 'source', 'contact_method', 'submission_channel'], 'type': 'category'},
        'resolution_time': {'aliases': ['resolution time', 'resolution_time', 'resolution_time_hours', 'time_to_resolve', 'ttl', 'turnaround_time', 'tat'], 'type': 'numeric'},
        'customer_segment': {'aliases': ['customer segment', 'customer_segment', 'segment', 'customer_type', 'account_type'], 'type': 'category'},
        'csat_score': {'aliases': ['csat', 'csat_score', 'satisfaction', 'satisfaction_score', 'rating', 'customer_rating'], 'type': 'numeric'},
    }

    SUPPORTED_FORMATS = ['csv', 'xlsx', 'xls', 'json']

    def __init__(self):
        self._last_schema = None
        self._last_mapping = None

    def detect_format(self, filename):
        """Detect file format from extension."""
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext in self.SUPPORTED_FORMATS:
            return ext
        return None

    def read_file(self, filepath, file_format=None):
        """
        Read data file into DataFrame.
        
        Supports: CSV, Excel, JSON
        """
        if not file_format:
            file_format = self.detect_format(filepath)

        if file_format == 'csv':
            # Try different encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    df = pd.read_csv(filepath, encoding=encoding)
                    break
                except (UnicodeDecodeError, Exception):
                    continue
            else:
                raise ValueError("Could not read CSV file with any supported encoding")
        elif file_format in ('xlsx', 'xls'):
            df = pd.read_excel(filepath)
        elif file_format == 'json':
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                if 'data' in data:
                    df = pd.DataFrame(data['data'])
                elif 'complaints' in data:
                    df = pd.DataFrame(data['complaints'])
                elif 'records' in data:
                    df = pd.DataFrame(data['records'])
                else:
                    df = pd.DataFrame([data])
            else:
                raise ValueError("Unsupported JSON structure")
        else:
            raise ValueError(f"Unsupported format: {file_format}")

        return df

    def detect_schema(self, df):
        """
        Auto-detect dataset schema and suggest column mappings.
        
        Returns:
            dict with detected_columns, suggested_mapping, data_types, statistics
        """
        columns = list(df.columns)
        detected = {}
        suggested_mapping = {}
        unmapped = []

        for col in columns:
            col_lower = col.lower().strip().replace(' ', '_')
            col_display = col.lower().strip()
            matched = False

            for standard_field, config in self.STANDARD_FIELDS.items():
                for alias in config['aliases']:
                    alias_normalized = alias.lower().strip().replace(' ', '_')
                    if col_lower == alias_normalized or col_display == alias:
                        suggested_mapping[col] = standard_field
                        detected[col] = {
                            "mapped_to": standard_field,
                            "expected_type": config['type'],
                            "actual_type": str(df[col].dtype),
                            "non_null_count": int(df[col].notna().sum()),
                            "null_count": int(df[col].isna().sum()),
                            "unique_values": int(df[col].nunique()),
                            "sample_values": [str(v) for v in df[col].dropna().head(5).tolist()],
                        }
                        matched = True
                        break
                if matched:
                    break

            if not matched:
                unmapped.append(col)
                detected[col] = {
                    "mapped_to": None,
                    "expected_type": "unknown",
                    "actual_type": str(df[col].dtype),
                    "non_null_count": int(df[col].notna().sum()),
                    "null_count": int(df[col].isna().sum()),
                    "unique_values": int(df[col].nunique()),
                    "sample_values": [str(v) for v in df[col].dropna().head(5).tolist()],
                }

        self._last_schema = detected
        self._last_mapping = suggested_mapping

        return {
            "total_columns": len(columns),
            "total_rows": len(df),
            "detected_columns": detected,
            "suggested_mapping": suggested_mapping,
            "unmapped_columns": unmapped,
            "mapped_count": len(suggested_mapping),
            "mapping_confidence": round(len(suggested_mapping) / max(len(columns), 1) * 100, 1),
            "available_standard_fields": list(self.STANDARD_FIELDS.keys()),
        }

    def apply_mapping(self, df, column_mapping):
        """
        Apply column mapping to DataFrame.
        
        Args:
            df: Source DataFrame
            column_mapping: dict of {source_column: standard_field}
            
        Returns:
            DataFrame with standardized column names
        """
        rename_map = {}
        for source_col, target_field in column_mapping.items():
            if source_col in df.columns:
                rename_map[source_col] = target_field

        df_mapped = df.rename(columns=rename_map)
        return df_mapped

    def preprocess_dataframe(self, df):
        """
        Apply comprehensive preprocessing to the DataFrame.
        
        Handles: missing values, duplicates, type conversion, normalization.
        """
        stats = {
            "original_rows": len(df),
            "original_columns": len(df.columns),
            "actions_performed": [],
        }

        # 1. Remove exact duplicate rows
        before = len(df)
        df = df.drop_duplicates()
        removed = before - len(df)
        if removed > 0:
            stats["actions_performed"].append(f"Removed {removed} exact duplicate rows")

        # 2. Handle missing values in text columns
        text_cols = ['complaint_text', 'complaint_description', 'customer_feedback', 'technician_notes']
        for col in text_cols:
            if col in df.columns:
                null_count = df[col].isna().sum()
                df[col] = df[col].fillna('')
                if null_count > 0:
                    stats["actions_performed"].append(f"Filled {null_count} missing values in {col}")

        # 3. Handle missing categorical values
        cat_cols = ['product_type', 'resolution_status', 'severity', 'department',
                    'warranty_status', 'customer_channel', 'customer_segment',
                    'complaint_category']
        for col in cat_cols:
            if col in df.columns:
                null_count = df[col].isna().sum()
                df[col] = df[col].fillna('Unknown')
                if null_count > 0:
                    stats["actions_performed"].append(f"Filled {null_count} missing {col} with 'Unknown'")

        # 4. Handle missing numeric values
        numeric_cols = ['resolution_time', 'csat_score', 'resolution_time_hours']
        for col in numeric_cols:
            if col in df.columns:
                null_count = df[col].isna().sum()
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val if not pd.isna(median_val) else 0)
                if null_count > 0:
                    stats["actions_performed"].append(f"Filled {null_count} missing {col} with median ({median_val:.1f})")

        # 5. Parse dates
        date_cols = ['date_time', 'timestamp', 'created_at', 'complaint_date']
        for col in date_cols:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    stats["actions_performed"].append(f"Parsed {col} as datetime")
                except Exception:
                    pass

        # 6. Clean text fields
        text_fields = ['complaint_text', 'complaint_description', 'customer_feedback']
        for col in text_fields:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: self._clean_text(x) if isinstance(x, str) else x)
                stats["actions_performed"].append(f"Cleaned noise from {col}")

        # 7. Standardize categorical values
        for col in cat_cols:
            if col in df.columns:
                df[col] = df[col].str.strip().str.title()

        # 8. Generate complaint IDs if missing
        if 'complaint_id' not in df.columns:
            df['complaint_id'] = [f'HVAC-{i+1:06d}' for i in range(len(df))]
            stats["actions_performed"].append("Generated complaint IDs")

        # 9. Generate customer names if missing
        if 'customer_name' not in df.columns:
            df['customer_name'] = [f'Customer-{i+1:04d}' for i in range(len(df))]
            stats["actions_performed"].append("Generated customer names")

        stats["final_rows"] = len(df)
        stats["final_columns"] = len(df.columns)
        stats["rows_removed"] = stats["original_rows"] - stats["final_rows"]

        return df, stats

    def _clean_text(self, text):
        """Clean individual text field."""
        if not text or not isinstance(text, str):
            return text
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        return text

    def ingest_to_database(self, df, session, ComplaintDB, column_mapping=None):
        """
        Ingest preprocessed DataFrame into database.
        
        Args:
            df: Preprocessed DataFrame
            session: SQLAlchemy session
            ComplaintDB: The complaint model class
            column_mapping: Optional column mapping (auto-detected if not provided)
            
        Returns:
            dict with ingestion statistics
        """
        ingested = 0
        skipped = 0
        errors = 0

        # Determine which columns map to which DB fields
        col_map = column_mapping or self._last_mapping or {}

        # Build reverse mapping
        field_to_col = {}
        for col, field in col_map.items():
            if col in df.columns:
                field_to_col[field] = col

        # Also check direct column name matches
        db_fields = [
            'complaint_id', 'customer_name', 'date_time', 'product_type',
            'equipment_model', 'complaint_description', 'complaint_category',
            'service_location_city', 'service_location_state', 'customer_segment',
            'resolution_status', 'technician_notes', 'communication_channel',
            'warranty_status', 'resolution_time_hours', 'csat_score',
        ]

        for field in db_fields:
            if field not in field_to_col and field in df.columns:
                field_to_col[field] = field

        # Handle text field mapping
        if 'complaint_description' not in field_to_col:
            for alt in ['complaint_text', 'description', 'text', 'details', 'issue']:
                if alt in df.columns:
                    field_to_col['complaint_description'] = alt
                    break

        for _, row in df.iterrows():
            try:
                complaint = ComplaintDB()

                for db_field, df_col in field_to_col.items():
                    if hasattr(complaint, db_field) and df_col in row.index:
                        val = row[df_col]
                        if pd.isna(val):
                            val = None
                        elif isinstance(val, (np.integer,)):
                            val = int(val)
                        elif isinstance(val, (np.floating,)):
                            val = float(val)
                        elif isinstance(val, pd.Timestamp):
                            val = val.isoformat()
                        setattr(complaint, db_field, val)

                session.add(complaint)
                ingested += 1

            except Exception as e:
                errors += 1
                if errors < 5:
                    print(f"[WARN] Row ingestion error: {e}")

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise ValueError(f"Database commit failed: {e}")

        return {
            "ingested": ingested,
            "skipped": skipped,
            "errors": errors,
            "total_processed": ingested + skipped + errors,
        }


# Singleton
_engine = None

def get_ingestion_engine():
    global _engine
    if _engine is None:
        _engine = DataIngestionEngine()
    return _engine
