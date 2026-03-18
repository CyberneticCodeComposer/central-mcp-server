from pycentral import NewCentralBase
from config import (
    CENTRAL_BASE_URL,
    CENTRAL_CLIENT_ID,
    CENTRAL_CLIENT_SECRET,
    validate_credentials,
)


def get_central_connection() -> NewCentralBase:
    """
    Get a Central connection instance.
    This function can be used as a dependency in FastAPI routes.
    Validates that credentials are configured before creating connection.
    """
    # Validate credentials are set
    validate_credentials()

    return NewCentralBase(
        token_info={
            "new_central": {
                "base_url": CENTRAL_BASE_URL,
                "client_id": CENTRAL_CLIENT_ID,
                "client_secret": CENTRAL_CLIENT_SECRET,
            }
        },
    )


# Create a singleton instance for reuse
# Note: This will be created when first imported, so credentials must be set before any tools are used
central_conn = None


def get_conn():
    """
    Get or create the central connection singleton.
    This lazy initialization allows credentials to be set before connection is created.
    """
    global central_conn
    if central_conn is None:
        central_conn = get_central_connection()
    return central_conn
