# Deployment

For development, install the core package and run the simulator. For Raspberry Pi deployments, install only the needed `pi` and device extras, run preflight before motion, and keep the guard boundary separate from high-level perception when productionizing.

No cloud service is required. The runtime should remain usable offline. Store secrets outside configuration files and do not use the development HMAC signer for fleet identity.
