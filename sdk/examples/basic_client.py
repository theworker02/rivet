from rivet.cli import build_runtime
from sdk.python.client import LocalRobotClient


client = LocalRobotClient(build_runtime())
print(client.capabilities())
print(client.tree())
