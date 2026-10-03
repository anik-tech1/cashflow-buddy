import re
import time
import logging
from typing import TypedDict
import numpy as np
import pandas as pd
from tabpfn import TabPFNClassifier
from sklearn.ensemble import RandomForestClassifier
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from requests.exceptions import RequestException, Timeout

logger = logging.getLogger(__name__)


class CashflowState(TypedDict):
    upcoming_expenses: float
    expected_invoiced: float
    colab_url: str
    model_name: str
    tabpfn_summary: str
    redacted_ledger: str
    raw_llm_output: str
    final_rehydrated_output: str


def compute_tabpfn_probabilities(upcoming_expenses: float, expected_invoiced: float) -> dict:
    if upcoming_expenses < 0 or expected_invoiced < 0:
        raise ValueError("Expenses and invoices must be non-negative")

    try:
        df = pd.read_csv("monthly_history.csv")
    except FileNotFoundError:
        raise FileNotFoundError("monthly_history.csv not found. Run seed_data.py first.")
    except pd.errors.ParserError as e:
        raise ValueError(f"Invalid CSV format in monthly_history.csv: {e}")

    if df.empty or len(df) < 2:
        raise ValueError("monthly_history.csv must have at least 2 rows")

    required_cols = ["expenses", "invoiced", "late_ratio", "had_cash_crunch"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"monthly_history.csv missing columns: {missing_cols}")

    X_train = df[["expenses", "invoiced", "late_ratio"]].values
    y_train = df["had_cash_crunch"].values

    if np.any(np.isnan(X_train)) or np.any(np.isnan(y_train)):
        raise ValueError("monthly_history.csv contains NaN values")

    avg_late = float(df["late_ratio"].mean())

    try:
        clf = TabPFNClassifier(device="cpu")
        clf.fit(X_train, y_train)
        engine_used = "TabPFN-v2 (Local CPU)"
        logger.info("TabPFN classifier fitted successfully")
    except ImportError:
        logger.warning("TabPFN not available, falling back to RandomForest")
        clf = RandomForestClassifier(n_estimators=100, random_state=42)
        clf.fit(X_train, y_train)
        engine_used = "Scikit-Learn Fallback (Local CPU)"
    except Exception as e:
        logger.warning(f"TabPFN initialization failed ({e}), using RandomForest")
        clf = RandomForestClassifier(n_estimators=100, random_state=42)
        clf.fit(X_train, y_train)
        engine_used = "Scikit-Learn Fallback (Local CPU)"

    X_baseline = np.array([[upcoming_expenses, expected_invoiced, avg_late]])
    prob_baseline = float(clf.predict_proba(X_baseline)[0][1])

    X_recovered = np.array([[upcoming_expenses, expected_invoiced + 1450.0, 0.12]])
    prob_recovered = float(clf.predict_proba(X_recovered)[0][1])

    return {
        "engine": engine_used,
        "avg_late_ratio": avg_late,
        "prob_baseline": prob_baseline,
        "prob_recovered": prob_recovered,
    }


def get_redacted_invoice_payload() -> str:
    try:
        df = pd.read_csv("invoices.csv")
    except FileNotFoundError:
        raise FileNotFoundError("invoices.csv not found. Run seed_data.py first.")
    except pd.errors.ParserError as e:
        raise ValueError(f"Invalid CSV format in invoices.csv: {e}")

    required_cols = ["invoice_id", "status", "days_overdue", "amount"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"invoices.csv missing columns: {missing_cols}")

    overdue = df[df["status"] == "overdue"].sort_values(by="days_overdue", ascending=False)

    if overdue.empty:
        logger.info("No overdue invoices found")
        return "ANONYMIZED OVERDUE LEDGER: No overdue invoices at this time.\n"

    lines = []
    for _, row in overdue.iterrows():
        inv_id = str(row["invoice_id"]).strip()
        amt = float(row["amount"])
        days = int(row["days_overdue"])

        if amt < 0:
            logger.warning(f"Skipping invoice {inv_id}: negative amount")
            continue
        if days < 0:
            logger.warning(f"Skipping invoice {inv_id}: negative days_overdue")
            continue

        lines.append(
            f"- Invoice ID: {inv_id} | Client Token: [CLIENT_{inv_id}] | "
            f"Amount: USD {amt:,.2f} | Days Overdue: {days}"
        )

    if not lines:
        logger.info("All overdue invoices filtered due to validation")
        return "ANONYMIZED OVERDUE LEDGER: No valid overdue invoices.\n"

    total = overdue[overdue["amount"] >= 0]["amount"].sum()
    count = len(lines)
    return (
        f"ANONYMIZED OVERDUE LEDGER (Total Overdue: USD {total:,.2f} across {count} invoices):\n"
        + "\n".join(lines)
    )


def rehydrate_pii_locally(llm_response_text: str) -> str:
    try:
        df = pd.read_csv("invoices.csv")
    except FileNotFoundError:
        logger.warning("invoices.csv not found for rehydration, returning anonymized text")
        return llm_response_text
    except pd.errors.ParserError as e:
        logger.error(f"Failed to parse invoices.csv for rehydration: {e}")
        return llm_response_text

    if df.empty:
        logger.warning("invoices.csv is empty, skipping rehydration")
        return llm_response_text

    rehydrated = llm_response_text
    rehydration_count = 0

    for _, row in df.iterrows():
        try:
            inv_id = str(row["invoice_id"]).strip()
            c_name = str(row.get("client_name", "Unknown")).strip()
            c_email = str(row.get("contact_email", "Unknown")).strip()
            p_name = str(row.get("project_name", "Unknown")).strip()

            real_label = f"**{c_name}** (`{c_email}` — *{p_name}*)"
            token_pattern = rf"\[?CLIENT_{re.escape(inv_id)}\]?"

            original_len = len(rehydrated)
            rehydrated = re.sub(token_pattern, real_label, rehydrated, flags=re.IGNORECASE)

            if len(rehydrated) > original_len:
                rehydration_count += 1
                logger.debug(f"Rehydrated token CLIENT_{inv_id} → {c_name}")

        except (KeyError, ValueError, AttributeError) as e:
            logger.warning(f"Failed to rehydrate row: {e}, skipping")
            continue

    if rehydration_count == 0:
        logger.warning("No tokens were rehydrated; check token format in LLM output")

    logger.info(f"Successfully rehydrated {rehydration_count} PII tokens")
    return rehydrated


# --- LangGraph Stateful Nodes ---
def node_tabpfn_forecast(state: CashflowState) -> dict:
    try:
        exp = state["upcoming_expenses"]
        inv = state["expected_invoiced"]
        stats = compute_tabpfn_probabilities(exp, inv)
        eng = stats["engine"]
        p_base = stats["prob_baseline"]
        p_rec = stats["prob_recovered"]
        late = stats["avg_late_ratio"]

        summary = (
            f"TabPFN Statistical Forecast ({eng}):\n"
            f"- Upcoming Expenses: USD {exp:,.2f}\n"
            f"- Expected New Invoices: USD {inv:,.2f}\n"
            f"- Baseline Cash Crunch Probability: {p_base:.1%} (Historical late-payment rate: {late:.1%})\n"
            f"- Cash Crunch Probability After Recovering Top Overdue Invoice: {p_rec:.1%}"
        )
        return {"tabpfn_summary": summary}
    except Exception as e:
        logger.error(f"TabPFN forecast failed: {e}")
        raise


def node_pii_redactor(state: CashflowState) -> dict:
    try:
        return {"redacted_ledger": get_redacted_invoice_payload()}
    except Exception as e:
        logger.error(f"PII redaction failed: {e}")
        raise


def node_local_rehydrator(state: CashflowState) -> dict:
    try:
        final_text = rehydrate_pii_locally(state["raw_llm_output"])
        return {"final_rehydrated_output": final_text}
    except Exception as e:
        logger.error(f"PII rehydration failed: {e}")
        raise


def node_local_rehydrator(state: CashflowState) -> dict:
    final_text = rehydrate_pii_locally(state["raw_llm_output"])
    return {"final_rehydrated_output": final_text}


def build_cashflow_graph():
    """Compiles the 4-node LangGraph StateGraph workflow."""
    builder = StateGraph(CashflowState)
    builder.add_node("local_tabpfn_forecast", node_tabpfn_forecast)
    builder.add_node("local_pii_redactor", node_pii_redactor)
    builder.add_node("remote_gemma_inference", node_gemma_reasoning)
    builder.add_node("local_pii_rehydrator", node_local_rehydrator)

    builder.add_edge(START, "local_tabpfn_forecast")
    builder.add_edge("local_tabpfn_forecast", "local_pii_redactor")
    builder.add_edge("local_pii_redactor", "remote_gemma_inference")
    builder.add_edge("remote_gemma_inference", "local_pii_rehydrator")
    builder.add_edge("local_pii_rehydrator", END)

    return builder.compile()