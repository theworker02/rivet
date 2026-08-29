# CLI

Rivet 1.2 commands are executable and covered by integration or end-to-end tests:

```text
rivet version --verbose                 version, Python, platform, schema, protocol, driver API
rivet verify                            installation health and 18 simulator scenarios
rivet check-release                     strict release gate
rivet init [PATH]                      create schema-v2 JSON configuration
rivet config validate PATH              validate configuration
rivet config migrate PATH               migrate v1 configuration
rivet drivers                          driver metadata and qualification evidence
rivet hardware certify DRIVER           hardware conformance report
rivet doctor --verbose                  runtime and safety diagnostics
rivet preflight                         readiness before motion
rivet pulse                             component health/heartbeat snapshot
rivet record start PATH                 create a deterministic flight recording
rivet replay PATH --summary             inspect a recording
rivet timeline PATH                    inspect ordered runtime events
rivet mission run GOAL --dry-run        plan without hardware commands
rivet compatibility                     platform support matrix
rivet resource-test                    nano/core/full resource checks
rivet benchmark runtime                performance budget checks
rivet crash inspect latest              inspect sanitized crash evidence
rivet support bundle PATH               create a sanitized diagnostics archive
rivet capsule install PATH              validate/install a portable bundle
```

JSON is the stable automation surface where `--json` is offered. Human reports are intended for operators; a nonzero exit code always means the requested gate or check did not pass.
