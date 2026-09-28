import os
from sqlalchemy import create_engine
from sqlalchemy.engine import URL


def get_engine(with_database=True):
    """Connection settings come from environment variables (see README)."""
    url = URL.create(
        "mysql+pymysql",
        username=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "password"),
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        database=os.getenv("MYSQL_DB", "treasury") if with_database else None,
    )
    return create_engine(url)
