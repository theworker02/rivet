from __future__ import annotations

import time
import uuid
from typing import Callable

from .errors import AuthorityError, LeaseError
from .models import AuthorityGrant, Lease


class AuthorityManager:
    def __init__(self, clock: Callable[[], float] | None = None) -> None:
        self._clock = clock or time.monotonic
        self._active: dict[str, AuthorityGrant] = {}

    def acquire(self, domain: str, owner: str, priority: int, ttl_s: float) -> AuthorityGrant:
        self.expire()
        current = self._active.get(domain)
        if current and current.owner != owner and priority <= current.priority:
            raise AuthorityError(
                f"authority denied for {domain}: {current.owner} has priority {current.priority}"
            )
        grant = AuthorityGrant(domain, owner, priority, uuid.uuid4().hex, self._clock() + ttl_s)
        self._active[domain] = grant
        return grant

    def validate(self, domain: str, owner: str, token: str) -> AuthorityGrant:
        self.expire()
        grant = self._active.get(domain)
        if not grant or grant.token != token or grant.owner != owner:
            raise AuthorityError(f"no valid authority for {domain} owned by {owner}")
        return grant

    def renew(self, token: str, ttl_s: float) -> AuthorityGrant:
        self.expire()
        for domain, grant in self._active.items():
            if grant.token == token:
                renewed = AuthorityGrant(grant.domain, grant.owner, grant.priority, grant.token, self._clock() + ttl_s)
                self._active[domain] = renewed
                return renewed
        raise AuthorityError("authority token is not active")

    def expire(self, now: float | None = None) -> list[AuthorityGrant]:
        now = self._clock() if now is None else now
        expired = [grant for grant in self._active.values() if grant.expires_at <= now]
        for grant in expired:
            self._active.pop(grant.domain, None)
        return expired

    def active(self) -> list[AuthorityGrant]:
        self.expire()
        return list(self._active.values())

    def revoke_all(self) -> list[AuthorityGrant]:
        revoked = list(self._active.values())
        self._active.clear()
        return revoked


class LeaseManager:
    def __init__(self, clock: Callable[[], float] | None = None) -> None:
        self._clock = clock or time.monotonic
        self._active: dict[str, Lease] = {}

    def acquire(self, target: str, owner: str, ttl_s: float) -> Lease:
        self.expire()
        current = self._active.get(target)
        if current and current.owner != owner:
            raise LeaseError(f"lease denied for {target}: owned by {current.owner}")
        lease = Lease(target, owner, uuid.uuid4().hex, self._clock() + ttl_s)
        self._active[target] = lease
        return lease

    def validate(self, target: str, owner: str, token: str) -> Lease:
        self.expire()
        lease = self._active.get(target)
        if not lease or lease.token != token or lease.owner != owner:
            raise LeaseError(f"no valid lease for {target} owned by {owner}")
        return lease

    def renew(self, token: str, ttl_s: float) -> Lease:
        self.expire()
        for target, lease in self._active.items():
            if lease.token == token:
                renewed = Lease(lease.target, lease.owner, lease.token, self._clock() + ttl_s)
                self._active[target] = renewed
                return renewed
        raise LeaseError("lease token is not active")

    def expire(self, now: float | None = None) -> list[Lease]:
        now = self._clock() if now is None else now
        expired = [lease for lease in self._active.values() if lease.expires_at <= now]
        for lease in expired:
            self._active.pop(lease.target, None)
        return expired

    def active(self) -> list[Lease]:
        self.expire()
        return list(self._active.values())

    def revoke_all(self) -> list[Lease]:
        revoked = list(self._active.values())
        self._active.clear()
        return revoked
