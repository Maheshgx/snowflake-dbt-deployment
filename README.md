# Snowflake & dbt CI/CD Deployment Repository

This repository demonstrates the automated deployment of Snowflake objects and dbt models using Snowflake Cortex/Snowpark Python API and GitHub Actions.

## Project Structure
- `.github/workflows/`: CI/CD pipelines for DEV, UAT, PROD.
- `configs/`: Environment-specific parameters for Snowflake deployment.
- `cortex_code/`: Snowpark Python scripts that automate infrastructure (DDL/RBAC) and trigger Cortex validation.
- `dbt_project/`: The dbt project for data transformation.

## How it works
1. **Pull Request (DEV)**: Triggered when a PR is raised. Deploys to an ephemeral DEV schema.
2. **Merge to Main (UAT)**: Deploys the code to the UAT environment for integration testing.
3. **Release Tag (PROD)**: Triggers the production deployment.

## Automation Flow
1. **Python API** sets up databases, schemas, and role grants based on configuration.
2. **dbt** builds the data models within the provisioned schema.
3. **Snowflake Cortex** runs anomaly detection on the newly updated models to guarantee data quality.
