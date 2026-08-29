# Security Policy

## Scope

Rivet is a beta robotics runtime (1.2.0). The current repository contains an in-process simulator and development HMAC signer; it is not a production security boundary.

## Reporting

Do not disclose exploitable details in a public issue. Use the repository's private security reporting feature once an owner has configured it. If private reporting is unavailable, contact the project maintainers through the repository's verified contact channel and include only the minimum reproduction information.

## Safety boundaries

- Never treat a passport as an actuator authority token.
- Keep emergency stop and lease enforcement independent from AI or mission code.
- Do not place real signing keys, tokens, wiring credentials, or device identifiers in source or recordings.
- Validate all protocol frames before dispatch.
- Keep Pi-specific imports optional so unsupported hosts fail safely.

## Supported versions

Only the latest `1.2.x` beta line currently receives security fixes. Physical deployments must add their own hardware interlocks, identity management, and operational review.
