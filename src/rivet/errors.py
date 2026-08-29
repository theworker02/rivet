class RivetError(Exception):
    """Base exception for expected Rivet runtime failures."""


class NotFoundError(RivetError):
    pass


class AuthorityError(RivetError):
    pass


class LeaseError(RivetError):
    pass


class CommandError(RivetError):
    pass
