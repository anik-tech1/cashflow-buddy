import pandas as pd


def generate_datasets():
    # 1. Historical monthly cashflow dataset for TabPFN tabular foundation model
    history_data = [
        {"month": "2025-06", "expenses": 2750, "invoiced": 4600, "late_ratio": 0.08, "had_cash_crunch": 0},
        {"month": "2025-07", "expenses": 3200, "invoiced": 3300, "late_ratio": 0.44, "had_cash_crunch": 1},
        {"month": "2025-08", "expenses": 2900, "invoiced": 4900, "late_ratio": 0.12, "had_cash_crunch": 0},
        {"month": "2025-09", "expenses": 3450, "invoiced": 3500, "late_ratio": 0.48, "had_cash_crunch": 1},
        {"month": "2025-10", "expenses": 2800, "invoiced": 4500, "late_ratio": 0.10, "had_cash_crunch": 0},
        {"month": "2025-11", "expenses": 3100, "invoiced": 3200, "late_ratio": 0.45, "had_cash_crunch": 1},
        {"month": "2025-12", "expenses": 3400, "invoiced": 5200, "late_ratio": 0.15, "had_cash_crunch": 0},
        {"month": "2026-01", "expenses": 2900, "invoiced": 2800, "late_ratio": 0.50, "had_cash_crunch": 1},
        {"month": "2026-02", "expenses": 2700, "invoiced": 4800, "late_ratio": 0.05, "had_cash_crunch": 0},
        {"month": "2026-03", "expenses": 3200, "invoiced": 3500, "late_ratio": 0.40, "had_cash_crunch": 1},
        {"month": "2026-04", "expenses": 2850, "invoiced": 4900, "late_ratio": 0.12, "had_cash_crunch": 0},
        {"month": "2026-05", "expenses": 3300, "invoiced": 3600, "late_ratio": 0.38, "had_cash_crunch": 1},
        {"month": "2026-06", "expenses": 2950, "invoiced": 5100, "late_ratio": 0.08, "had_cash_crunch": 0},
        {"month": "2026-07", "expenses": 3100, "invoiced": 4700, "late_ratio": 0.14, "had_cash_crunch": 0},
        {"month": "2026-08", "expenses": 3500, "invoiced": 3700, "late_ratio": 0.42, "had_cash_crunch": 1},
        {"month": "2026-09", "expenses": 3000, "invoiced": 4600, "late_ratio": 0.18, "had_cash_crunch": 0},
    ]
    pd.DataFrame(history_data).to_csv("monthly_history.csv", index=False)

    # 2. Private client invoice tracker (PII stays strictly on your local disk)
    invoice_data = [
        {
            "invoice_id": "INV-101",
            "client_name": "Apex Robotics (Strict NDA)",
            "contact_email": "billing@apexrobotics.io",
            "project_name": "Q3 Design System",
            "amount": 1800,
            "days_overdue": 28,
            "status": "overdue",
        },
        {
            "invoice_id": "INV-102",
            "client_name": "Northstar Gaming Studio",
            "contact_email": "accounts@northstargames.com",
            "project_name": "Shader Optimization Pass",
            "amount": 950,
            "days_overdue": 12,
            "status": "overdue",
        },
        {
            "invoice_id": "INV-103",
            "client_name": "Vertex Cloud Labs",
            "contact_email": "finance@vertexcloud.dev",
            "project_name": "Landing Page Revamp",
            "amount": 2200,
            "days_overdue": 0,
            "status": "paid",
        },
        {
            "invoice_id": "INV-104",
            "client_name": "BlueWave Health Media",
            "contact_email": "ap@bluewavehealth.org",
            "project_name": "Dashboard UI Prototype",
            "amount": 1450,
            "days_overdue": 39,
            "status": "overdue",
        },
    ]
    pd.DataFrame(invoice_data).to_csv("invoices.csv", index=False)
    print("Created monthly_history.csv and invoices.csv locally!")


if __name__ == "__main__":
    generate_datasets()