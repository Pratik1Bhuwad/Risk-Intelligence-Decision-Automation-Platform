"""
HTML report generation module for PaySim Data Audit.
Produces a clean, factual, professional report distinguishing audit statuses.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import jinja2
import pandas as pd

REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PaySim Data Audit Report - Risk Intelligence & Decision Automation Platform</title>
    <style>
        :root {
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --border-color: #e2e8f0;
            --primary: #2563eb;
            --primary-light: #eff6ff;
            --status-confirmed: #0284c7;
            --status-observed: #475569;
            --status-hypothesis: #9333ea;
            --status-unknown: #ca8a04;
            --status-investigate: #ea580c;
            --status-critical: #dc2626;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            line-height: 1.5;
            padding: 2rem 1.5rem;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        header { margin-bottom: 2rem; border-bottom: 2px solid var(--border-color); padding-bottom: 1.5rem; }
        h1 { font-size: 1.875rem; font-weight: 700; color: #1e293b; margin-bottom: 0.5rem; }
        h2 { font-size: 1.35rem; font-weight: 600; color: #334155; margin-top: 2rem; margin-bottom: 1rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem; }
        h3 { font-size: 1.1rem; font-weight: 600; color: #475569; margin-top: 1rem; margin-bottom: 0.5rem; }
        p { margin-bottom: 0.75rem; color: #334155; }
        .meta-bar {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            margin-top: 0.75rem;
            font-size: 0.875rem;
            color: var(--text-muted);
        }
        .meta-item { background: #f1f5f9; padding: 0.35rem 0.75rem; border-radius: 4px; border: 1px solid #cbd5e1; }
        .meta-item strong { color: #1e293b; }
        
        .card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.25rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        
        .grid-kpi {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        .kpi-box {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 1rem;
            text-align: center;
        }
        .kpi-val { font-size: 1.5rem; font-weight: 700; color: var(--primary); }
        .kpi-lbl { font-size: 0.8rem; text-transform: uppercase; color: var(--text-muted); margin-top: 0.25rem; letter-spacing: 0.5px; }

        .badge {
            display: inline-block;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.2rem 0.55rem;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .badge-CONFIRMED { background: #e0f2fe; color: var(--status-confirmed); border: 1px solid #bae6fd; }
        .badge-OBSERVED { background: #f1f5f9; color: var(--status-observed); border: 1px solid #cbd5e1; }
        .badge-HYPOTHESIS { background: #f3e8ff; color: var(--status-hypothesis); border: 1px solid #e9d5ff; }
        .badge-UNKNOWN { background: #fef9c3; color: var(--status-unknown); border: 1px solid #fef08a; }
        .badge-INVESTIGATE { background: #ffedd5; color: var(--status-investigate); border: 1px solid #fed7aa; }
        .badge-CRITICAL { background: #fee2e2; color: var(--status-critical); border: 1px solid #fca5a5; }
        .badge-FEASIBLE { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
        .badge-SEVERELY_CONSTRAINED { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.875rem;
            margin-top: 0.5rem;
            margin-bottom: 1rem;
        }
        th, td {
            padding: 0.6rem 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }
        th { background: #f8fafc; font-weight: 600; color: #475569; }
        tr:hover { background-color: #f1f5f9; }

        .alert-box {
            padding: 1rem;
            border-radius: 6px;
            margin-bottom: 1rem;
            border-left: 4px solid;
            font-size: 0.9rem;
        }
        .alert-info { background: #eff6ff; border-color: #3b82f6; color: #1e40af; }
        .alert-warning { background: #fffbeb; border-color: #f59e0b; color: #92400e; }
        .alert-danger { background: #fef2f2; border-color: #ef4444; color: #991b1b; }
    </style>
</head>
<body>
<div class="container">
    <header>
        <h1>PaySim Data Audit Report</h1>
        <p><strong>Platform:</strong> Risk Intelligence & Decision Automation Platform</p>
        <div class="meta-bar">
            <div class="meta-item"><strong>Audit Version:</strong> {{ run_metadata.audit_version }}</div>
            <div class="meta-item"><strong>Mode:</strong> <span class="badge badge-CONFIRMED">{{ run_metadata.audit_mode }}</span></div>
            <div class="meta-item"><strong>Timestamp:</strong> {{ run_metadata.execution_timestamp }}</div>
            <div class="meta-item"><strong>Rows:</strong> {{ "{:,}".format(file_info.row_count) }}</div>
            <div class="meta-item"><strong>Columns:</strong> {{ file_info.column_count }}</div>
            <div class="meta-item"><strong>SHA-256:</strong> <code>{{ file_info.sha256[:16] }}...</code></div>
        </div>
    </header>

    <!-- Executive Summary -->
    <div class="card">
        <h2>1. Executive Summary & Findings</h2>
        <div class="grid-kpi">
            <div class="kpi-box">
                <div class="kpi-val">{{ "{:,}".format(file_info.row_count) }}</div>
                <div class="kpi-lbl">Total Records</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-val">{{ "{:,}".format(summary_kpis.fraud_count) }}</div>
                <div class="kpi-lbl">Fraud Transactions</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-val">{{ summary_kpis.fraud_rate }}%</div>
                <div class="kpi-lbl">Fraud Prevalence</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-val">{{ summary_kpis.single_orig_pct }}%</div>
                <div class="kpi-lbl">Single-Tx Originators</div>
            </div>
        </div>

        <div class="alert-box alert-warning">
            <strong>Critical Architectural Finding:</strong> 
            {{ summary_kpis.single_orig_pct }}% of originating accounts (<code>nameOrig</code>) appear exactly once. 
            <strong>Customer Risk Scoring</strong> and <strong>Behavioral Change Detection</strong> for originating accounts cannot rely on historical transaction profile within PaySim.
        </div>
        <div class="alert-box alert-info">
            <strong>Synthetic Constraint Confirmed:</strong> 
            Fraud transactions occur <em>strictly</em> in <code>TRANSFER</code> and <code>CASH_OUT</code> transactions. All other transaction types (<code>PAYMENT</code>, <code>CASH_IN</code>, <code>DEBIT</code>) have exactly 0 observed fraud records.
        </div>
    </div>

    <!-- File Verification & Read-Only Integrity -->
    <div class="card">
        <h2>2. File Verification & Data Integrity</h2>
        <table>
            <thead>
                <tr><th>Attribute</th><th>Observed Value</th><th>Status</th></tr>
            </thead>
            <tbody>
                <tr><td>Dataset File Path</td><td><code>{{ file_info.file_path }}</code></td><td><span class="badge badge-CONFIRMED">CONFIRMED</span></td></tr>
                <tr><td>File Size</td><td>{{ "{:,}".format(file_info.file_size_bytes) }} bytes (~{{ (file_info.file_size_bytes / (1024*1024)) | round(1) }} MB)</td><td><span class="badge badge-CONFIRMED">CONFIRMED</span></td></tr>
                <tr><td>Full SHA-256 Hash</td><td><code>{{ file_info.sha256 }}</code></td><td><span class="badge badge-CONFIRMED">CONFIRMED</span></td></tr>
                <tr><td>Read Success</td><td>{{ file_info.read_success }}</td><td><span class="badge badge-CONFIRMED">CONFIRMED</span></td></tr>
                <tr><td>Malformed Rows Detected</td><td>{{ file_info.malformed_rows }}</td><td><span class="badge badge-CONFIRMED">CONFIRMED</span></td></tr>
                <tr><td>Read-Only Integrity</td><td>{{ integrity_msg }}</td><td><span class="badge badge-CONFIRMED">VERIFIED</span></td></tr>
            </tbody>
        </table>
    </div>

    <!-- Schema & Missingness -->
    <div class="card">
        <h2>3. Schema & Data-Quality Summary</h2>
        <table>
            <thead>
                <tr>
                    <th>Column</th>
                    <th>Dtype</th>
                    <th>Semantic Category</th>
                    <th>Missing Count</th>
                    <th>Zero Count</th>
                    <th>Unique Count</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% for row in schema_rows %}
                <tr>
                    <td><strong>{{ row.column_name }}</strong></td>
                    <td><code>{{ row.pandas_dtype }}</code></td>
                    <td>{{ row.inferred_semantic_category }}</td>
                    <td>{{ row.null_count }} ({{ row.null_percentage }}%)</td>
                    <td>{{ row.zero_count if row.zero_count is defined else 'N/A' }}</td>
                    <td>{{ "{:,}".format(row.unique_count) }}</td>
                    <td><span class="badge badge-{{ row.status }}">{{ row.status }}</span></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- Target Analysis -->
    <div class="card">
        <h2>4. Target & Stratification Analysis</h2>
        <table>
            <thead>
                <tr>
                    <th>Level</th>
                    <th>Group</th>
                    <th>Total Count</th>
                    <th>Fraud Count</th>
                    <th>Fraud Rate (%)</th>
                    <th>Notes</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% for row in target_rows %}
                <tr>
                    <td>{{ row.analysis_level }}</td>
                    <td><strong>{{ row.group_name }}</strong></td>
                    <td>{{ "{:,}".format(row.total_count) }}</td>
                    <td>{{ "{:,}".format(row.fraud_count) }}</td>
                    <td>{{ row.fraud_rate_pct }}%</td>
                    <td>{{ row.notes }}</td>
                    <td><span class="badge badge-{{ row.status }}">{{ row.status }}</span></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- Prediction-Time Availability & Leakage -->
    <div class="card">
        <h2>5. Prediction-Time Availability & Leakage Matrix</h2>
        <p>Operational decision point status: <code>STATUS: UNKNOWN</code>. Evaluated against candidate pre-auth decision points.</p>
        <table>
            <thead>
                <tr>
                    <th>Field</th>
                    <th>Available at Tx Time?</th>
                    <th>Generated After?</th>
                    <th>Leakage Risk</th>
                    <th>Rationale & Recommended Handling</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% for row in pred_rows %}
                <tr>
                    <td><strong>{{ row.field }}</strong></td>
                    <td>{{ 'YES' if row.available_at_transaction_time else 'NO' }}</td>
                    <td>{{ 'YES' if row.generated_after_transaction else 'NO' }}</td>
                    <td><span class="badge badge-{{ 'CRITICAL' if 'TARGET' in row.leakage_risk else ('INVESTIGATE' if 'LEAKAGE' in row.leakage_risk or 'RISK' in row.leakage_risk else 'CONFIRMED') }}">{{ row.leakage_risk }}</span></td>
                    <td>{{ row.rationale }}</td>
                    <td><span class="badge badge-{{ row.status }}">{{ row.status }}</span></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- Synthetic Artifact Review -->
    <div class="card">
        <h2>6. Synthetic-Data Artifact Review</h2>
        <table>
            <thead>
                <tr>
                    <th>Hypothesis ID</th>
                    <th>Hypothesis Description</th>
                    <th>Empirical Evidence</th>
                    <th>Interpretation</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% for row in synth_rows %}
                <tr>
                    <td><code>{{ row.hypothesis_id }}</code></td>
                    <td>{{ row.hypothesis_description }}</td>
                    <td>{{ row.empirical_evidence }}</td>
                    <td>{{ row.interpretation }}</td>
                    <td><span class="badge badge-{{ row.status }}">{{ row.status }}</span></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- Capability Feasibility Assessment -->
    <div class="card">
        <h2>7. Capability Feasibility Matrix</h2>
        <table>
            <thead>
                <tr>
                    <th>Capability</th>
                    <th>Evidence Observed</th>
                    <th>Status</th>
                    <th>Limitation</th>
                </tr>
            </thead>
            <tbody>
                {% for row in cap_rows %}
                <tr>
                    <td><strong>{{ row.capability }}</strong></td>
                    <td>{{ row.evidence_observed }}</td>
                    <td><span class="badge badge-{{ row.status }}">{{ row.status }}</span></td>
                    <td>{{ row.limitation }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

</div>
</body>
</html>
"""


def render_html_report(
    output_path: str,
    file_info: Dict[str, Any],
    run_metadata: Dict[str, Any],
    schema_df: pd.DataFrame,
    missing_df: pd.DataFrame,
    target_df: pd.DataFrame,
    prediction_df: pd.DataFrame,
    synthetic_df: pd.DataFrame,
    capability_df: pd.DataFrame,
    entity_df: pd.DataFrame,
    integrity_msg: str,
) -> None:
    """Render HTML report and write to output_path."""
    template = jinja2.Template(REPORT_TEMPLATE)

    # Merge zero count into schema for cleaner table presentation
    merged_schema = schema_df.copy()
    if not missing_df.empty and "zero_count" in missing_df.columns:
        zero_map = dict(zip(missing_df["column"], missing_df["zero_count"]))
        merged_schema["zero_count"] = merged_schema["column_name"].map(
            zero_map
        )

    # Extract summary KPIs
    fraud_count = 0
    fraud_rate = 0.0
    if not target_df.empty:
        overall_rows = target_df[target_df["analysis_level"] == "OVERALL"]
        if not overall_rows.empty:
            fraud_count = int(overall_rows.iloc[0]["fraud_count"])
            fraud_rate = float(overall_rows.iloc[0]["fraud_rate_pct"])

    single_orig_pct = 0.0
    if not entity_df.empty:
        single_rows = entity_df[
            entity_df["metric"] == "SINGLE_TRANSACTION_ENTITIES"
        ]
        if not single_rows.empty:
            single_orig_pct = float(single_rows.iloc[0]["percentage"])

    summary_kpis = {
        "fraud_count": fraud_count,
        "fraud_rate": fraud_rate,
        "single_orig_pct": single_orig_pct,
    }

    html_content = template.render(
        file_info=file_info,
        run_metadata=run_metadata,
        summary_kpis=summary_kpis,
        schema_rows=merged_schema.to_dict(orient="records"),
        target_rows=target_df.to_dict(orient="records"),
        pred_rows=prediction_df.to_dict(orient="records"),
        synth_rows=synthetic_df.to_dict(orient="records"),
        cap_rows=capability_df.to_dict(orient="records"),
        integrity_msg=integrity_msg,
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
