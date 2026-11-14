from .client import FLOW_CLIENT

FLOW_CLIENT.register(
  "ping",
  lambda _: FLOW_CLIENT.send_json({"type": "pong"}),
)
