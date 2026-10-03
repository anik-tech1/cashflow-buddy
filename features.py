import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def generate_collection_email(
    client_name: str,
    client_email: str,
    invoice_id: str,
    amount: float,
    days_overdue: int,
    project_name: str = "the project",
) -> str:
    if days_overdue < 0:
        logger.warning(f"Invalid days_overdue ({days_overdue}) for email, using 0")
        days_overdue = 0

    subject = f"Payment Reminder: Invoice {invoice_id} ({days_overdue} days overdue)"

    body = f"""Dear {client_name},

I hope this email finds you well. I'm writing to follow up on an outstanding invoice from our recent work together.

Invoice Details:
  • Invoice ID: {invoice_id}
  • Amount Due: USD {amount:,.2f}
  • Project: {project_name}
  • Days Overdue: {days_overdue}

This invoice was due on {(datetime.now() - timedelta(days=days_overdue)).strftime('%B %d, %Y')}. 
I'd appreciate if you could prioritize this payment at your earliest convenience.

If you've already sent payment, please disregard this message. If you have any questions or need an invoice copy, 
feel free to reach out.

Thank you for your prompt attention to this matter.

Best regards,
Your Name"""

    return f"**Subject:** {subject}\n\n{body}\n\n**To:** {client_email}"


def generate_email_templates(df: pd.DataFrame) -> List[Dict[str, str]]:
    overdue = df[df["status"] == "overdue"].sort_values(by="days_overdue", ascending=False)

    templates = []
    for _, row in overdue.iterrows():
        try:
            email = generate_collection_email(
                client_name=str(row.get("client_name", "Valued Client")).strip(),
                client_email=str(row.get("contact_email", "")).strip(),
                invoice_id=str(row.get("invoice_id", "")).strip(),
                amount=float(row.get("amount", 0)),
                days_overdue=int(row.get("days_overdue", 0)),
                project_name=str(row.get("project_name", "the project")).strip(),
            )
            templates.append(
                {
                    "invoice_id": str(row.get("invoice_id", "")),
                    "client_name": str(row.get("client_name", "")),
                    "email": email,
                }
            )
        except Exception as e:
            logger.error(f"Failed to generate email for row: {e}")
            continue

    return templates


def forecast_multi_month(
    historical_df: pd.DataFrame, months_ahead: int = 3
) -> List[Dict[str, float]]:
    if months_ahead < 1 or months_ahead > 12:
        raise ValueError("months_ahead must be between 1 and 12")

    if len(historical_df) < 2:
        raise ValueError("Need at least 2 months of historical data")

    required_cols = ["expenses", "invoiced"]
    missing_cols = [col for col in required_cols if col not in historical_df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}")

    avg_expenses = float(historical_df["expenses"].mean())
    avg_invoiced = float(historical_df["invoiced"].mean())
    std_expenses = float(historical_df["expenses"].std())
    std_invoiced = float(historical_df["invoiced"].std())

    forecasts = []
    for month in range(1, months_ahead + 1):
        noise_exp = np.random.normal(0, std_expenses * 0.1) if std_expenses > 0 else 0
        noise_inv = np.random.normal(0, std_invoiced * 0.1) if std_invoiced > 0 else 0

        forecast = {
            "month_ahead": month,
            "projected_expenses": max(0, avg_expenses + noise_exp),
            "projected_invoiced": max(0, avg_invoiced + noise_inv),
            "projected_balance": (avg_invoiced + noise_inv) - (avg_expenses + noise_exp),
        }
        forecasts.append(forecast)

    return forecasts


def export_to_csv(
    forecast_list: List[Dict[str, float]], filename: str = "forecast_export.csv"
) -> str:
    try:
        df = pd.DataFrame(forecast_list)
        df.to_csv(filename, index=False)
        logger.info(f"Exported forecast to {filename}")
        return filename
    except Exception as e:
        logger.error(f"Failed to export CSV: {e}")
        raise


def generate_summary_report(
    tabpfn_summary: str,
    redacted_ledger: str,
    llm_output: str,
    multi_month_forecast: List[Dict[str, float]],
) -> str:
    report = f"""
# CashflowBuddy Financial Summary Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

{tabpfn_summary}

## Current Overdue Ledger

{redacted_ledger}

## AI-Generated Action Plan

{llm_output}

## Multi-Month Forecast

| Month Ahead | Projected Expenses | Projected Invoiced | Projected Balance |
|---|---|---|---|
"""

    for forecast in multi_month_forecast:
        month = forecast["month_ahead"]
        exp = forecast["projected_expenses"]
        inv = forecast["projected_invoiced"]
        bal = forecast["projected_balance"]
        report += f"| {month} | USD {exp:,.2f} | USD {inv:,.2f} | USD {bal:,.2f} |\n"

    report += f"""

## Report Metadata
- TabPFN/RandomForest: Local CPU Analysis
- PII Status: All client names anonymized during transmission
- Forecast Horizon: 3 months
- Data Freshness: {datetime.now().isoformat()}
"""
    return report
