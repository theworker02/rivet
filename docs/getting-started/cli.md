# CLI

Common commands:

```text
rivet init [PATH]                 create a JSON robot configuration
rivet version                    print package version
rivet doctor --verbose           inspect runtime and safety readiness
rivet discover                  list capability contracts
rivet devices                   list devices and capabilities
rivet tree                      show the device tree
rivet run --simulate             run the simulator
rivet demo --record run.rivet   exercise commands and replay
rivet role evaluate search-rescue
rivet skill explain construction.drilling
rivet mission explain "search sector B"
rivet team organize
```

JSON output is the stable automation surface. Human-oriented formatting should be added only as an explicit format option with tests.
