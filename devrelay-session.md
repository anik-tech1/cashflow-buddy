---
title: "Building CashflowBuddy: Privacy-First Financial AI with Split-Brain Architecture"
description: "AI-assisted development of a split-brain financial assistant that keeps client data private"
tags: ["hacktoberfest", "ai", "privacy", "architecture", "openai"]
---

# Building CashflowBuddy: Privacy-First Financial AI with Split-Brain Architecture

## Overview

This session documents the development of CashflowBuddy, a privacy-first financial assistant for freelancers that uses a split-brain architecture to keep sensitive client data on the user's laptop while leveraging a free Colab GPU for AI inference.

## The Problem

Freelancers need AI help predicting cashflow and prioritizing invoice collections, but their NDAs forbid uploading client names to ChatGPT or similar services.

## The Solution: Split-Brain Architecture

**Local (Your Laptop):**
1. TabPFN ML model predicts cash crunch risk (CPU-based)
2. PII Redactor strips client names/emails
3. PII Rehydrator restores real names after AI processes response

**Remote (Colab GPU):**
3. Gemma LLM generates strategy without seeing client names

**Network Boundary:** Cloudflare Tunnel with TLS 1.3 encryption. Zero client PII crosses it.

## What Was Built

### 1. Core Architecture
- `agent.py` (210 lines): TabPFN inference, PII redaction/rehydration, LangGraph orchestration
- `app.py` (220 lines): Streamlit dashboard with 4 tabs
- `features.py` (150 lines): Email templates, multi-month forecasts, CSV export

### 2. Error Handling & Resilience
- Retry logic with exponential backoff for Colab timeouts (3 attempts: 2s → 4s → 8s)
- Graceful fallback from TabPFN to RandomForest if unavailable
- Input validation (negative amounts, malformed CSVs)
- Comprehensive error logging

### 3. Features
- **Email Templates**: Auto-generate polite payment reminders ranked by urgency
- **Multi-Month Forecasts**: 3-month projections with statistical analysis
- **CSV Export**: Download forecasts for accounting software
- **Privacy Inspector**: Audit exactly what leaves your PC (redacted vs. real data)

### 4. Testing
- 330+ lines of comprehensive unit tests
- Coverage: TabPFN fallback, PII redaction/rehydration edge cases, CSV parsing, email generation, forecasting

### 5. Documentation
- README.md: Getting started + feature overview
- ARCHITECTURE.md: Deep dive on the 4-node workflow, data flows, security model
- CONTRIBUTING.md: Dev setup, code style, testing guidelines
- BACKEND_ARCHITECTURE.md: Explanation of monolithic vs. API design choices

## Key Decisions

1. **Why Split-Brain?** Keeps PII local while leveraging free cloud GPU
2. **Why TabPFN?** Fast tabular ML (0.5s) on CPU; doesn't need internet
3. **Why Gemma?** Open-weight model on free Colab; no API costs
4. **Why LangGraph?** Clean orchestration of 4-step workflow
5. **Why Streamlit?** Fast dashboard development; no frontend build step

## AI Assistance Disclosure

This project was built with **Kiro AI (OpenCode)** for:
- App scaffolding and error handling
- Feature implementation (email templates, forecasts, export)
- Test suite generation (330+ lines)
- Documentation (README, guides)

**Per MLH's Hacktoberfest rules:** *"Teams may use AI to assist them while coding... Teams should be honest and transparent about the AI code tools they used."*

All code was reviewed, tested, validated, and integrated into a cohesive system with real privacy architecture.

## Hacktoberfest 2026 Submission

**Repository:** https://github.com/anik-tech1/cashflow-buddy

**Why This Matters:**
- Solves a real constraint (NDA compliance for freelancers)
- Novel architecture (split-brain pattern rarely seen in hackathons)
- Open-source stack (TabPFN + Gemma + LangGraph + Streamlit; no paid APIs)
- Production-ready (error handling, retry logic, comprehensive tests, full documentation)
- Privacy-by-design (security is architectural, not bolted on)

**Status:** Submission-ready. GitHub repo pushed, tests passing, fully documented.
