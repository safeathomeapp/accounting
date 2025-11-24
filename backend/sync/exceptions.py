"""Custom exceptions for sync engine."""


class SyncException(Exception):
    """Base exception for sync engine."""

    pass


class SyncFetchError(SyncException):
    """Error fetching data from accounting platform."""

    def __init__(self, platform: str, entity_type: str, message: str):
        self.platform = platform
        self.entity_type = entity_type
        super().__init__(
            f"Failed to fetch {entity_type} from {platform}: {message}"
        )


class SyncDatabaseError(SyncException):
    """Error writing data to database."""

    def __init__(self, entity_type: str, message: str):
        self.entity_type = entity_type
        super().__init__(f"Failed to sync {entity_type} to database: {message}")


class SyncValidationError(SyncException):
    """Error validating synced data."""

    def __init__(self, entity_type: str, details: str):
        self.entity_type = entity_type
        super().__init__(f"Validation error for {entity_type}: {details}")
