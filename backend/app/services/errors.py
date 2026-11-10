"""Service-level errors translated to HTTP responses by the API layer."""


class ResourceNotFoundError(Exception):
    """Raised when a requested resource or required parent does not exist."""


class ResourceConflictError(Exception):
    """Raised when a valid operation is disallowed by a resource's current state."""


class InvalidRelationshipError(Exception):
    """Raised when two existing records cannot be related consistently."""


