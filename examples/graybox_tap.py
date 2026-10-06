"""The gray box from Python: the same two taps, launched normally and then
with the gray box, on MobiumApp's Busy Demo.

    MOBIUM_DEVICE=emulator-5554 python3 examples/graybox_tap.py

Launched normally, Row B is usually tapped while the old rows are still up,
and says "stale". With the gray box, the tap waits for the app to say it is
done, and says "current". The app grades each tap, not this script.
"""
import os
import time

from mobium import connect

APP = "dev.mobium.mobiumapp"


def busy_demo(device, gray_box):
    """Launch MobiumApp, normally or with the gray box, and open the Busy Demo."""
    device.terminate(APP)
    device.launch(APP, gray_box=gray_box)
    device.scroll_to("label=Busy Demo", direction="down")
    device.tap("label=Busy Demo")


def quiet_refresh_then_row_b(device):
    """Refresh quietly, tap Row B at once, and return what the row said."""
    time.sleep(2)  # any earlier refresh is over, so each try starts clean
    device.tap("testid=busyQuiet")
    device.tap("testid=busyRowB")
    # The row writes its verdict as it handles the tap: wait for the line to
    # name a row before reading it. A read straight after the tap can come
    # back "nothing tapped yet" — the gray box waits for the app's declared
    # work, not for the screen to redraw after a tap.
    device.wait_for("testid=busyOutcome", condition="text", text="row B")
    return device.text("testid=busyOutcome")


device = connect(device=os.environ.get("MOBIUM_DEVICE"))
try:
    busy_demo(device, gray_box=False)
    print("launched normally:  ", quiet_refresh_then_row_b(device))

    busy_demo(device, gray_box=True)
    print("with the gray box:  ", quiet_refresh_then_row_b(device))
finally:
    device.terminate(APP)
    device.close()
