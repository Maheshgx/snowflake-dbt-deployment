import json
import os
import sys
from snowflake.snowpark import Session
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import dsa
from cryptography.hazmat.primitives import serialization

def load_config(env):
    with open(f"configs/env_{env}.json", "r") as f:
        return json.load(f)

def get_connection_params(config):
    """Builds connection parameters supporting both Password and Key-Pair Auth"""
    params = {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "role": os.getenv("SNOWFLAKE_ROLE"),
        "warehouse": config['warehouse']
    }

    private_key = os.getenv("SNOWFLAKE_PRIVATE_KEY")
    password = os.getenv("SNOWFLAKE_PASSWORD")

    if private_key:
        p_key = serialization.load_pem_private_key(
            private_key.encode('utf-8'),
            password=os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE", "").encode('utf-8') if os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE") else None,
            backend=default_backend()
        )
        pkb = p_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        params["private_key"] = pkb
    elif password:
        params["password"] = password
    else:
        raise ValueError("Must provide either SNOWFLAKE_PRIVATE_KEY or SNOWFLAKE_PASSWORD")

    return params

def deploy_native_objects(session, db_name, raw_schema):
    """Executes pure Snowflake DDLs (Tables, Views, Stages) before dbt runs."""
    objects_dir = "snowflake_objects"
    if not os.path.exists(objects_dir):
        print("No native snowflake objects found to deploy.")
        return

    print("Deploying Native Snowflake Objects...")
    for filename in sorted(os.listdir(objects_dir)):
        if filename.endswith(".sql"):
            file_path = os.path.join(objects_dir, filename)
            print(f" -> Executing {filename}...")
            
            with open(file_path, "r") as f:
                sql_script = f.read()
            
            # Dynamically inject environment context
            sql_script = sql_script.replace("{db_name}", db_name)
            sql_script = sql_script.replace("{raw_schema}", raw_schema)
            
            # Split script by semicolon to run multiple statements
            queries = [q.strip() for q in sql_script.split(';') if q.strip()]
            for query in queries:
                try:
                    session.sql(query).collect()
                except Exception as e:
                    print(f"Error executing query: {query}\n{e}")
                    raise e

def deploy_infrastructure(session, config):
    db_name = os.getenv("SNOWFLAKE_DATABASE", config['database'])
    raw_schema = config['raw_schema']
    
    print(f"Deploying to Environment: {config['environment']} | DB: {db_name}")
    
    # 1. Create Database and Schemas Idempotently
    session.sql(f"CREATE DATABASE IF NOT EXISTS {db_name}").collect()
    session.sql(f"CREATE SCHEMA IF NOT EXISTS {db_name}.{raw_schema}").collect()
    session.sql(f"CREATE SCHEMA IF NOT EXISTS {db_name}.{config['analytics_schema']}").collect()
    
    # 2. Deploy Native Snowflake Objects (Raw Tables, Secure Views, etc.)
    deploy_native_objects(session, db_name, raw_schema)
    
    # 3. Apply RBAC (Role-Based Access Control)
    for role in config['roles']:
        # Note: In a real environment, you'd ensure the roles exist or create them if needed.
        # This assumes the roles have been provisioned by an account admin.
        session.sql(f"GRANT USAGE ON DATABASE {db_name} TO ROLE {role}").collect()
        session.sql(f"GRANT USAGE ON SCHEMA {db_name}.{raw_schema} TO ROLE {role}").collect()
        session.sql(f"GRANT SELECT ON ALL TABLES IN SCHEMA {db_name}.{raw_schema} TO ROLE {role}").collect()
        session.sql(f"GRANT SELECT ON FUTURE TABLES IN SCHEMA {db_name}.{raw_schema} TO ROLE {role}").collect()

    print("Infrastructure deployment completed successfully.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python deploy_infrastructure.py <env>")
        sys.exit(1)
        
    env = sys.argv[1]
    config = load_config(env)
    
    # Connection parameters injected by GitHub Actions
    connection_parameters = get_connection_params(config)
    
    session = Session.builder.configs(connection_parameters).create()
    deploy_infrastructure(session, config)
