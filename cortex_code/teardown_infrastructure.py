import os
import sys
from snowflake.snowpark import Session
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import dsa
from cryptography.hazmat.primitives import serialization

def get_connection_params():
    """Builds connection parameters supporting both Password and Key-Pair Auth"""
    params = {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "role": os.getenv("SNOWFLAKE_ROLE"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE")
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

def teardown_infrastructure():
    db_name = os.getenv("SNOWFLAKE_DATABASE")
    
    if not db_name or "PR_" not in db_name:
        print(f"Safety check failed. Will not drop database: {db_name}")
        sys.exit(1)
        
    print(f"Tearing down ephemeral PR database: {db_name}")
    
    params = get_connection_params()
    session = Session.builder.configs(params).create()
    
    try:
        session.sql(f"DROP DATABASE IF EXISTS {db_name}").collect()
        print(f"Successfully dropped database: {db_name}")
    except Exception as e:
        print(f"Failed to drop database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    teardown_infrastructure()
