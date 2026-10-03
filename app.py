import os
import requests
import streamlit as st
import pandas as pd
from seed_data import generate_datasets
from agent import (
    build_cashflow_graph,
    compute_tabpfn_probabilities,
    get_redacted_invoice_payload,
)
from features import (
    generate_email_templates,
    forecast_multi_month,
    generate_summary_report,
    export_to_csv,
)

st.set_page_config(page_title="CashflowBuddy | Gemma + TabPFN", layout="wide")

if not os.path.exists("invoices.csv") or not os.path.exists("monthly_history.csv"):
    generate_datasets()

st.title("CashflowBuddy: Split-Brain Open-Source Runway Agent")
st.caption(
    "Hacktoberfest 2026 | Local CPU: Prior Labs TabPFN + PII Redaction Shield  "
    "⇄  Remote GPU: Google Gemma on Colab T4 via Cloudflare Tunnel"
)

with st.sidebar:
    st.header("1. Remote Colab GPU Config")
    colab_url = st.text_input(
        "Colab Cloudflare Tunnel URL",
        value=os.getenv("COLAB_TUNNEL_URL", ""),
        placeholder="https://random-words.trycloudflare.com",
    )

    model_name = st.selectbox(
        "Gemma Model on Colab T4",
        ["gemma3:4b", "gemma4:e4b", "gemma2:9b"],
    )

    if st.button("Ping Remote Ollama Tunnel"):
        if not colab_url:
            st.warning("Paste your trycloudflare.com URL from Cell 2 first.")
        else:
            try:
                resp = requests.get(f"{colab_url.rstrip('/')}/api/tags", timeout=8)
                if resp.status_code == 200:
                    models = [m["name"] for m in resp.json().get("models", [])]
                    st.success(f"Connected! Models on T4 GPU: {', '.join(models) or 'None pulled yet'}")
                else:
                    st.error(f"Tunnel returned HTTP {resp.status_code}")
            except Exception as e:
                st.error(f"Could not reach tunnel: {e}")

    st.divider()
    st.header("2. Next Month Projections")
    expenses = st.number_input("Upcoming Monthly Expenses ($)", value=3350, step=100)
    invoiced = st.number_input("Expected New Invoices ($)", value=3600, step=100)

tab1, tab2, tab3, tab4 = st.tabs([
    "Agent Dashboard",
    "Zero-Trust Privacy Inspector",
    "Email Templates",
    "Multi-Month Forecast"
])

with tab1:
    col1, col2 = st.columns([1.05, 1.25])

    with col1:
        st.subheader("Local Private Vault (Never Leaves PC)")
        st.dataframe(pd.read_csv("invoices.csv"), use_container_width=True)

        stats = compute_tabpfn_probabilities(expenses, invoiced)
        m1, m2 = st.columns(2)
        m1.metric(
            "TabPFN Baseline Crunch Risk",
            f"{stats['prob_baseline']:.1%}",
            delta="High Deficit Risk" if stats["prob_baseline"] > 0.5 else "Manageable",
            delta_color="inverse",
        )
        m2.metric(
            "Risk After Collecting INV-104",
            f"{stats['prob_recovered']:.1%}",
            delta=f"-{(stats['prob_baseline'] - stats['prob_recovered']):.1%} risk reduction",
            delta_color="normal",
        )

    with col2:
        st.subheader("Gemma + LangGraph Action Plan")
        if st.button("Run Open-Source Agent Graph", type="primary", use_container_width=True):
            if not colab_url:
                st.error("Please paste your Colab Cloudflare Tunnel URL in the left sidebar first!")
            else:
                with st.spinner(f"Running local TabPFN → Redacting PII → Querying {model_name} on Colab T4..."):
                    try:
                        graph = build_cashflow_graph()
                        result = graph.invoke(
                            {
                                "upcoming_expenses": float(expenses),
                                "expected_invoiced": float(invoiced),
                                "colab_url": colab_url,
                                "model_name": model_name,
                            }
                        )
                        st.success("Analysis complete! Client PII rehydrated locally on your PC.")
                        st.markdown(result["final_rehydrated_output"])

                        with st.expander("View Raw Redacted Text Received from Remote Gemma"):
                            st.code(result["raw_llm_output"], language="markdown")
                    except Exception as e:
                        st.error(f"Agent execution error: {e}")

with tab2:
    st.subheader("Split-Brain Privacy Verification")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**1. Raw Local CSV on Disk (Contains NDA Client Names & Emails)**")
        st.dataframe(
            pd.read_csv("invoices.csv")[["invoice_id", "client_name", "contact_email", "amount", "days_overdue"]]
        )
    with c2:
        st.markdown("**2. Exact Redacted String Sent Over Cloudflare Tunnel to Colab**")
        st.code(get_redacted_invoice_payload(), language="text")

with tab3:
    st.subheader("Ready-to-Send Payment Reminder Emails")
    try:
        invoices_df = pd.read_csv("invoices.csv")
        email_templates = generate_email_templates(invoices_df)
        
        if not email_templates:
            st.info("No overdue invoices. All clients are current!")
        else:
            selected_email = st.selectbox(
                "Select an email to preview:",
                options=[f"{e['invoice_id']} — {e['client_name']}" for e in email_templates],
            )
            
            if selected_email:
                idx = [f"{e['invoice_id']} — {e['client_name']}" for e in email_templates].index(selected_email)
                email_content = email_templates[idx]["email"]
                st.markdown(email_content)
                
                st.download_button(
                    label="📥 Download as Text",
                    data=email_content,
                    file_name=f"email_{email_templates[idx]['invoice_id']}.txt",
                    mime="text/plain"
                )
    except Exception as e:
        st.error(f"Failed to generate email templates: {e}")

with tab4:
    st.subheader("3-Month Cashflow Forecast")
    try:
        history_df = pd.read_csv("monthly_history.csv")
        forecasts = forecast_multi_month(history_df, months_ahead=3)
        
        forecast_data = {
            "Month Ahead": [f["month_ahead"] for f in forecasts],
            "Projected Expenses": [f["projected_expenses"] for f in forecasts],
            "Projected Invoiced": [f["projected_invoiced"] for f in forecasts],
            "Projected Balance": [f["projected_balance"] for f in forecasts],
        }
        
        forecast_df = pd.DataFrame(forecast_data)
        st.dataframe(forecast_df, use_container_width=True)
        
        col_exp, col_inv, col_bal = st.columns(3)
        with col_exp:
            avg_exp = forecast_df["Projected Expenses"].mean()
            st.metric("Avg Projected Expenses", f"USD {avg_exp:,.2f}")
        with col_inv:
            avg_inv = forecast_df["Projected Invoiced"].mean()
            st.metric("Avg Projected Invoiced", f"USD {avg_inv:,.2f}")
        with col_bal:
            avg_bal = forecast_df["Projected Balance"].mean()
            delta_color = "normal" if avg_bal > 0 else "inverse"
            st.metric("Avg Projected Balance", f"USD {avg_bal:,.2f}", delta_color=delta_color)
        
        csv_buffer = forecast_df.to_csv(index=False)
        st.download_button(
            label="📊 Download Forecast as CSV",
            data=csv_buffer,
            file_name="cashflow_forecast.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"Failed to generate forecast: {e}")