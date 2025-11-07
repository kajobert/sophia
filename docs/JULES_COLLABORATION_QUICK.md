# SOPHIA ↔ JULES Collaboration Guide

**Date:** 2025-11-07  
**Purpose:** Define when Sophia should use Jules vs handle tasks herself

---

## 🎯 Core Principles

### SOPHIA = Autonomous System Manager
- **Has:** Full access to running system, local LLM (Ollama), cloud LLM (OpenRouter)
- **Can:** Modify code, run tests, deploy changes, manage databases
- **Should:** Make autonomous decisions, use self-reflection to delegate wisely

### JULES = External Contractor/Consultant  
- **Has:** Access to **production GitHub repo** (master branch, no gitignore files)
- **Can:** Read code, analyze patterns, research web, write proposals, implement isolated features
- **Cannot:** Run Sophia, access local LLM, test runtime behavior, access local databases

---

## ✅ WHEN SOPHIA SHOULD USE JULES

### 1. Deep Web Research
### 2. Codebase Analysis (Read-Only)
### 3. Documentation Writing
### 4. Implementation Proposals
### 5. Specialized Branch Development

## ❌ WHEN SOPHIA SHOULD HANDLE HERSELF

### 1. Runtime Testing → **cognitive_dashboard_testing**
### 2. Live System Debugging
### 3. Local LLM Operations
### 4. Database Operations
### 5. Quick Fixes

---

**See full guide:** `docs/en/SOPHIA_JULES_COLLABORATION.md`
