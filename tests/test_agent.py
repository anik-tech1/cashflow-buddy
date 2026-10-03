import pytest
import pandas as pd
import numpy as np
from io import StringIO
import tempfile
import os
from agent import (
    compute_tabpfn_probabilities,
    get_redacted_invoice_payload,
    rehydrate_pii_locally,
)
from features import (
    generate_collection_email,
    generate_email_templates,
    forecast_multi_month,
    export_to_csv,
    generate_summary_report,
)


class TestTabPFNForecast:
    def setup_method(self):
        self.valid_history = pd.DataFrame({
            "expenses": [3200, 3350, 3500],
            "invoiced": [3100, 3600, 2900],
            "late_ratio": [0.15, 0.22, 0.35],
            "had_cash_crunch": [0, 0, 1],
        })

    def test_valid_forecast(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            history_path = os.path.join(tmpdir, "monthly_history.csv")
            self.valid_history.to_csv(history_path, index=False)
            os.chdir(tmpdir)

            result = compute_tabpfn_probabilities(3350, 3600)
            assert "engine" in result
            assert "prob_baseline" in result
            assert "prob_recovered" in result
            assert 0 <= result["prob_baseline"] <= 1
            assert 0 <= result["prob_recovered"] <= 1

    def test_negative_expenses_raises_error(self):
        with pytest.raises(ValueError, match="non-negative"):
            compute_tabpfn_probabilities(-100, 3600)

    def test_negative_invoices_raises_error(self):
        with pytest.raises(ValueError, match="non-negative"):
            compute_tabpfn_probabilities(3350, -100)

    def test_missing_csv_raises_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            with pytest.raises(FileNotFoundError):
                compute_tabpfn_probabilities(3350, 3600)

    def test_empty_csv_raises_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_df = pd.DataFrame(columns=["expenses", "invoiced", "late_ratio", "had_cash_crunch"])
            empty_path = os.path.join(tmpdir, "monthly_history.csv")
            empty_df.to_csv(empty_path, index=False)
            os.chdir(tmpdir)

            with pytest.raises(ValueError, match="at least 2 rows"):
                compute_tabpfn_probabilities(3350, 3600)

    def test_missing_columns_raises_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            incomplete_df = pd.DataFrame({"expenses": [3200, 3350]})
            incomplete_path = os.path.join(tmpdir, "monthly_history.csv")
            incomplete_df.to_csv(incomplete_path, index=False)
            os.chdir(tmpdir)

            with pytest.raises(ValueError, match="missing columns"):
                compute_tabpfn_probabilities(3350, 3600)

    def test_nan_values_raises_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            nan_df = pd.DataFrame({
                "expenses": [3200, np.nan],
                "invoiced": [3100, 3600],
                "late_ratio": [0.15, 0.22],
                "had_cash_crunch": [0, 0],
            })
            nan_path = os.path.join(tmpdir, "monthly_history.csv")
            nan_df.to_csv(nan_path, index=False)
            os.chdir(tmpdir)

            with pytest.raises(ValueError, match="NaN"):
                compute_tabpfn_probabilities(3350, 3600)


class TestPIIRedaction:
    def setup_method(self):
        self.valid_invoices = pd.DataFrame({
            "invoice_id": ["INV-104", "INV-101"],
            "client_name": ["BlueWave Health Media", "Acme Corp"],
            "contact_email": ["ap@bluewavehealth.org", "billing@acme.com"],
            "project_name": ["Dashboard Redesign", "Mobile App"],
            "amount": [1450.00, 2100.00],
            "status": ["overdue", "overdue"],
            "days_overdue": [39, 25],
        })

    def test_valid_redaction(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            invoices_path = os.path.join(tmpdir, "invoices.csv")
            self.valid_invoices.to_csv(invoices_path, index=False)
            os.chdir(tmpdir)

            result = get_redacted_invoice_payload()
            assert "[CLIENT_INV-104]" in result
            assert "[CLIENT_INV-101]" in result
            assert "BlueWave Health Media" not in result
            assert "ap@bluewavehealth.org" not in result
            assert "ANONYMIZED OVERDUE LEDGER" in result

    def test_no_overdue_invoices(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            no_overdue = pd.DataFrame({
                "invoice_id": ["INV-105"],
                "client_name": ["Tech Startup"],
                "contact_email": ["finance@techstartup.io"],
                "project_name": ["API Development"],
                "amount": [800.00],
                "status": ["paid"],
                "days_overdue": [0],
            })
            invoices_path = os.path.join(tmpdir, "invoices.csv")
            no_overdue.to_csv(invoices_path, index=False)
            os.chdir(tmpdir)

            result = get_redacted_invoice_payload()
            assert "No overdue invoices" in result

    def test_negative_amount_skipped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            invalid_invoices = pd.DataFrame({
                "invoice_id": ["INV-104", "INV-101"],
                "client_name": ["BlueWave", "Acme"],
                "contact_email": ["a@b.com", "c@d.com"],
                "project_name": ["Project", "Project"],
                "amount": [1450.00, -100.00],
                "status": ["overdue", "overdue"],
                "days_overdue": [39, 25],
            })
            invoices_path = os.path.join(tmpdir, "invoices.csv")
            invalid_invoices.to_csv(invoices_path, index=False)
            os.chdir(tmpdir)

            result = get_redacted_invoice_payload()
            assert "[CLIENT_INV-104]" in result
            assert "[CLIENT_INV-101]" not in result

    def test_missing_csv_raises_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            with pytest.raises(FileNotFoundError):
                get_redacted_invoice_payload()

    def test_missing_columns_raises_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            incomplete = pd.DataFrame({"invoice_id": ["INV-104"]})
            invoices_path = os.path.join(tmpdir, "invoices.csv")
            incomplete.to_csv(invoices_path, index=False)
            os.chdir(tmpdir)

            with pytest.raises(ValueError, match="missing columns"):
                get_redacted_invoice_payload()


class TestPIIRehydration:
    def setup_method(self):
        self.valid_invoices = pd.DataFrame({
            "invoice_id": ["INV-104", "INV-101"],
            "client_name": ["BlueWave Health Media", "Acme Corp"],
            "contact_email": ["ap@bluewavehealth.org", "billing@acme.com"],
            "project_name": ["Dashboard Redesign", "Mobile App"],
            "amount": [1450.00, 2100.00],
            "status": ["overdue", "overdue"],
            "days_overdue": [39, 25],
        })

    def test_valid_rehydration(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            invoices_path = os.path.join(tmpdir, "invoices.csv")
            self.valid_invoices.to_csv(invoices_path, index=False)
            os.chdir(tmpdir)

            anonymized = "Please contact [CLIENT_INV-104] for payment."
            result = rehydrate_pii_locally(anonymized)
            assert "BlueWave Health Media" in result
            assert "ap@bluewavehealth.org" in result
            assert "[CLIENT_INV-104]" not in result

    def test_rehydration_with_special_characters(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            special_invoices = pd.DataFrame({
                "invoice_id": ["INV-104"],
                "client_name": ["A&B Inc. (Ltd.)"],
                "contact_email": ["test@example.com"],
                "project_name": ["Project"],
                "amount": [1450.00],
                "status": ["overdue"],
                "days_overdue": [39],
            })
            invoices_path = os.path.join(tmpdir, "invoices.csv")
            special_invoices.to_csv(invoices_path, index=False)
            os.chdir(tmpdir)

            anonymized = "Contact [CLIENT_INV-104] for payment."
            result = rehydrate_pii_locally(anonymized)
            assert "A&B Inc. (Ltd.)" in result
            assert "[CLIENT_INV-104]" not in result

    def test_missing_csv_handles_gracefully(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            anonymized = "Original text with [CLIENT_INV-104]"
            result = rehydrate_pii_locally(anonymized)
            assert result == anonymized


class TestEmailGeneration:
    def test_valid_email_generation(self):
        email = generate_collection_email(
            client_name="Acme Corp",
            client_email="billing@acme.com",
            invoice_id="INV-101",
            amount=2100.00,
            days_overdue=25,
            project_name="Mobile App",
        )
        assert "Subject: Payment Reminder: Invoice INV-101" in email
        assert "2100.00" in email
        assert "Acme Corp" in email
        assert "billing@acme.com" in email
        assert "Mobile App" in email

    def test_negative_days_overdue_handled(self):
        email = generate_collection_email(
            client_name="Test Client",
            client_email="test@example.com",
            invoice_id="INV-001",
            amount=500.00,
            days_overdue=-5,
            project_name="Project",
        )
        assert "Invoice INV-001" in email
        assert "Test Client" in email

    def test_email_templates_generation(self):
        invoices_df = pd.DataFrame({
            "invoice_id": ["INV-104", "INV-101"],
            "client_name": ["BlueWave", "Acme"],
            "contact_email": ["a@b.com", "c@d.com"],
            "project_name": ["Project1", "Project2"],
            "amount": [1450.00, 2100.00],
            "status": ["overdue", "overdue"],
            "days_overdue": [39, 25],
        })
        templates = generate_email_templates(invoices_df)
        assert len(templates) == 2
        assert templates[0]["invoice_id"] == "INV-104"
        assert "BlueWave" in templates[0]["email"]


class TestMultiMonthForecast:
    def setup_method(self):
        self.valid_history = pd.DataFrame({
            "expenses": [3200, 3350, 3500],
            "invoiced": [3100, 3600, 2900],
        })

    def test_valid_forecast(self):
        forecasts = forecast_multi_month(self.valid_history, months_ahead=3)
        assert len(forecasts) == 3
        for i, forecast in enumerate(forecasts):
            assert forecast["month_ahead"] == i + 1
            assert "projected_expenses" in forecast
            assert "projected_invoiced" in forecast
            assert "projected_balance" in forecast
            assert forecast["projected_expenses"] >= 0
            assert forecast["projected_invoiced"] >= 0

    def test_invalid_months_ahead(self):
        with pytest.raises(ValueError, match="between 1 and 12"):
            forecast_multi_month(self.valid_history, months_ahead=0)

        with pytest.raises(ValueError, match="between 1 and 12"):
            forecast_multi_month(self.valid_history, months_ahead=13)

    def test_insufficient_data(self):
        insufficient = pd.DataFrame({"expenses": [3200], "invoiced": [3100]})
        with pytest.raises(ValueError, match="at least 2 months"):
            forecast_multi_month(insufficient, months_ahead=3)

    def test_missing_columns(self):
        incomplete = pd.DataFrame({"expenses": [3200, 3350]})
        with pytest.raises(ValueError, match="Missing columns"):
            forecast_multi_month(incomplete, months_ahead=3)


class TestCSVExport:
    def test_valid_export(self):
        forecast_data = [
            {"month_ahead": 1, "projected_expenses": 3200, "projected_invoiced": 3100},
            {"month_ahead": 2, "projected_expenses": 3350, "projected_invoiced": 3600},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = os.path.join(tmpdir, "test_export.csv")
            os.chdir(tmpdir)
            result = export_to_csv(forecast_data, filename="test_export.csv")
            assert os.path.exists(result)
            exported_df = pd.read_csv(result)
            assert len(exported_df) == 2
            assert "month_ahead" in exported_df.columns


class TestSummaryReport:
    def test_report_generation(self):
        tabpfn_summary = "Risk: 75%"
        redacted_ledger = "Invoice: INV-104"
        llm_output = "Action plan"
        forecasts = [{"month_ahead": 1, "projected_expenses": 3200, "projected_invoiced": 3100}]

        report = generate_summary_report(tabpfn_summary, redacted_ledger, llm_output, forecasts)
        assert "CashflowBuddy Financial Summary Report" in report
        assert "Risk: 75%" in report
        assert "Invoice: INV-104" in report
        assert "Action plan" in report
        assert "Month Ahead" in report
