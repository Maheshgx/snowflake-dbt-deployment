# Automated Snowflake & dbt CI/CD Deployment Framework

This repository provides a production-ready, enterprise-grade Continuous Integration and Continuous Deployment (CI/CD) framework for Snowflake and dbt. It leverages **Snowflake's Python API (Snowpark)** for infrastructure management, **dbt** for data transformation, **Snowflake Cortex** for AI-powered validation, and **GitHub Actions** for automated orchestration across DEV, UAT, and PROD environments.

## 1. Project Overview

**What this repo does:** It fully automates the lifecycle of your data warehouse. From provisioning databases and applying Role-Based Access Control (RBAC) to running incremental data models and validating data quality using Machine Learning—all triggered via Git events.
**Why it exists:** To eliminate manual `CREATE TABLE` deployments, prevent environment drift, and ensure your data warehouse follows strict software engineering practices (version control, isolation, and automated testing).

### Key Technologies
* **Snowflake (Data Cloud)**: The core computing and storage engine.
* **dbt Core**: Executes SQL transformations (`.sql` files) and schema testing.
* **Snowpark Python API**: Provisions DDLs (Databases, Schemas) and handles RBAC.
* **Snowflake Cortex**: Runs `DETECT_ANOMALIES` ML functions to validate data semantic quality post-deployment.
* **GitHub Actions**: The orchestrator pipeline running the CI/CD scripts.

---

## 2. Architecture Overview

```text
  [GitHub Repo]
       │
       ├─ (Pull Request) ─────────> [ GitHub Actions: deploy_dev.yml ] ───> Creates PR-specific Ephemeral DB (DEV)
       │
       ├─ (Merge to main) ────────> [ GitHub Actions: deploy_uat.yml ] ───> Deploys to Persistent DB (UAT)
       │
       └─ (Create tag v1.0) ──────> [ GitHub Actions: deploy_prod.yml] ───> Deploys to Locked-down DB (PROD)
                                              │
                                              v
                            +-----------------------------------+
                            | 1. Snowpark Python (DDL & RBAC)   |
                            | 2. dbt Core (Transform & Test)    |
                            | 3. Cortex ML (Anomaly Detection)  |
                            +-----------------------------------+
```

---

## 3. Repository Structure

Here is how the codebase is organized to support this decoupled architecture:

* **`.github/workflows/`**: The CI/CD pipelines.
  * `deploy_dev.yml`: Runs on Pull Requests. Uses dbt Slim CI (`state:modified+`) to only build changed code.
  * `deploy_uat.yml`: Runs on merge to `main`. Deploys to the UAT environment.
  * `deploy_prod.yml`: Runs on GitHub Release tags. Deploys to PROD.
  * `teardown_dev.yml`: Runs when a PR is closed to automatically `DROP` the ephemeral Snowflake DB.
* **`configs/`**: Environment configurations.
  * `env_dev.json`, `env_uat.json`, `env_prod.json`: JSON files defining target databases, schemas, virtual warehouses, and RBAC roles for each environment.
* **`cortex_code/`**: Python orchestration scripts.
  * `deploy_infrastructure.py`: Creates databases/schemas idempotently and grants permissions.
  * `teardown_infrastructure.py`: Safely cleans up ephemeral PR databases.
  * `validate_deployment.py`: Triggers Snowflake Cortex `DETECT_ANOMALIES` on the newly deployed data.
* **`dbt_project/`**: The dbt workspace.
  * `profiles.yml`: Environment-agnostic profile that uses runtime injected `env_var()` settings.
  * `models/`: The actual SQL transformation logic (e.g., `fct_revenue.sql`).

---

## 4. Prerequisites

Before you can use this repository, you must have:
1. **Snowflake Account**: With `ACCOUNTADMIN` or `SYSADMIN` privileges to create databases and service users.
2. **GitHub Repository**: You must clone this repo to your own GitHub account.
3. **dbt CLI**: Installed locally (`pip install dbt-snowflake`).
4. **Python 3.8+**: For running the Snowpark scripts locally.

---

## 5. Setup Instructions (Step-by-Step)

### Step 1: Clone the repository
```bash
git clone https://github.com/Maheshgx/snowflake-dbt-deployment.git
cd snowflake-dbt-deployment
```

### Step 2: Setup Snowflake Service Accounts
Create dedicated Snowflake service users for GitHub Actions using Key-Pair Authentication. Run this in Snowflake:
```sql
-- Example for DEV
CREATE ROLE DEV_PIPELINE_ROLE;
CREATE USER GITHUB_ACTIONS_DEV RSA_PUBLIC_KEY='<YOUR_PUBLIC_KEY>';
GRANT ROLE DEV_PIPELINE_ROLE TO USER GITHUB_ACTIONS_DEV;
-- Repeat for UAT and PROD
```

### Step 3: Configure GitHub Secrets
Go to your GitHub Repository -> **Settings** -> **Secrets and variables** -> **Actions**. Add the following secrets:

* `SNOWFLAKE_ACCOUNT`: Your account locator (e.g., `xy12345.us-east-1`)
* `SF_DEV_USER`, `SF_UAT_USER`, `SF_PROD_USER`: The service account usernames.
* `SF_DEV_PRIVATE_KEY`, `SF_UAT_PRIVATE_KEY`, `SF_PROD_PRIVATE_KEY`: The raw `.p8` RSA private keys for authentication.

---

## 6. Running Locally

You can test the dbt models on your local machine before pushing code. 

1. Install dependencies:
```bash
pip install -r cortex_code/requirements.txt
pip install dbt-snowflake
```
2. Export your personal local environment variables (which mimic what GitHub Actions does):
```bash
export SNOWFLAKE_ACCOUNT="your_account"
export SNOWFLAKE_USER="your_username"
export SNOWFLAKE_PASSWORD="your_password"
export SNOWFLAKE_ROLE="SYSADMIN"
export SNOWFLAKE_DATABASE="SHOPSTREAM_LOCAL_DEV"
export SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
export SNOWFLAKE_SCHEMA="ANALYTICS"
export DBT_TARGET_ENV="dev"
```
3. Run the Python setup script to build your local DB:
```bash
python cortex_code/deploy_infrastructure.py dev
```
4. Run dbt:
```bash
cd dbt_project
dbt build
```

---

## 7. CI/CD Workflow Explanation

1. **Infrastructure as Code**: The pipelines first execute `cortex_code/deploy_infrastructure.py`. This ensures that the destination database exists and the correct RBAC roles have `USAGE` access. It reads the target state from `configs/env_*.json`.
2. **dbt Slim CI**: Instead of running `dbt build` on the entire project, `deploy_dev.yml` uses `--select state:modified+`. This means the pipeline isolates only the `.sql` files you modified in your PR, saving immense compute cost.
3. **Automated Teardown**: To prevent Snowflake from filling up with hundreds of abandoned `DEV_PR_42` databases, `teardown_dev.yml` listens for the PR `closed` event and automatically executes `DROP DATABASE`.

---

## 8. Deployment Flow

1. **Develop Feature:** You check out a new branch (`feature/new-model`). You modify a dbt model and push.
2. **DEV Validation:** You open a Pull Request. `deploy_dev.yml` runs. An ephemeral database (`SHOPSTREAM_DEV_PR_#`) is built. dbt runs tests. Snowflake Cortex validates data quality.
3. **Merge to UAT:** A reviewer approves the PR. You merge it. `deploy_uat.yml` deploys the exact code to `SHOPSTREAM_UAT`.
4. **Promote to PROD:** You create a GitHub Release Tag (e.g., `v1.2.0`). `deploy_prod.yml` promotes the finalized code to `SHOPSTREAM_PROD`.

---

## 9. Environment Configuration

Configs are completely decoupled from code.
If you need to change the virtual warehouse used in Production, you do not touch the Python scripts. You simply update `configs/env_prod.json`:
```json
{
    "environment": "PROD",
    "database": "SHOPSTREAM_PROD",
    "warehouse": "PROD_HEAVY_TRANSFORM_WH",
    ...
}
```

---

## 10. Best Practices

* **Never use Passwords in CI/CD:** This framework natively supports RSA Key-Pair authentication. Refer to `get_connection_params()` in `deploy_infrastructure.py`.
* **Zero Hardcoded Secrets in dbt:** Notice that `profiles.yml` is entirely populated by `{{ env_var(...) }}`. Never commit credentials to Git.
* **Keep `main` Protected:** In GitHub, configure Branch Protection Rules to prevent direct pushes to the `main` branch. Require Pull Request reviews and passing status checks (from `deploy_dev.yml`).

---

## 11. Troubleshooting

* **Pipeline fails on Snowflake Authentication:** Ensure your RSA Private Key GitHub Secret is formatted correctly. It must include `-----BEGIN PRIVATE KEY-----` and `-----END PRIVATE KEY-----` with proper line breaks.
* **Cortex Validation fails:** If `validate_deployment.py` throws an anomaly error in a DEV environment, it is likely because your DEV database lacks enough historical data points for the ML model to train on. You can catch this exception or mock it for non-PROD environments.
* **Database doesn't drop on PR close:** Check the GitHub Actions logs for `teardown_dev.yml`. Ensure the `DEV_PIPELINE_ROLE` has `OWNERSHIP` or `DROP` privileges on databases it creates.

---

## 12. Future Enhancements

* **Blue/Green Deployments:** Utilize Snowflake's Zero-Copy Cloning to clone PROD, run dbt on the clone, and swap schemas for zero-downtime deployments.
* **dbt Docs Hosting:** Add a step in `deploy_prod.yml` to generate `dbt docs` and deploy them to AWS S3 or GitHub Pages.
