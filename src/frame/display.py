from inky import Inky_Impressions_7

from frame.flow.settings import FlowSettingsStore
from frame.layout import PairingLayout
from frame.ui import render

_store = FlowSettingsStore()
layout = PairingLayout(_store.current)


def debug():
    render(layout, width=800, height=480).show()


def display():
    output = Inky_Impressions_7()
    output.set_border(output.WHITE)
    output.set_image(render(layout, width=output.width, height=output.height))
    output.show()
