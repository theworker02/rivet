from rivet.cli import build_runtime
from sdk.python.client import LocalRobotClient


runtime = build_runtime()
client = LocalRobotClient(runtime)
print("capabilities:", [item["path"] for item in client.capabilities()])
grant = runtime.acquire_control("motion", "example", priority=500)
lease = runtime.acquire_lease("motion.left-wheel", "example", grant.token)
state = runtime.command("motion.left-wheel", "velocity", 0.25, "example", grant.token, lease.token)
print("left wheel:", state.payload)
runtime.tick(lease.expires_at + 1)
print("safe state:", runtime.devices["motion.left-wheel"].telemetry())
