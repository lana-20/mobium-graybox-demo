"""Hooks from Python: ask the app to raise a toast, and read it back.

    MOBIUM_DEVICE=emulator-5554 python3 examples/hook_toast.py

MobiumApp registers raiseToast with its gray-box library:

    GrayBox.register('raiseToast', message => {
      setToast(message);                                   // the app's own toast
      if (Platform.OS === 'android') ToastAndroid.show(message, ToastAndroid.SHORT);
      return 'shown';
    });

The test calls it by name and gets back what it returned. Hooks are heard
only in a gray-box launch, and only the names the app registered can be
called: anything else is refused, listing the ones it did.
"""
import os

from mobium import InvalidArgumentError, connect

APP = "dev.mobium.mobiumapp"

device = connect(device=os.environ.get("MOBIUM_DEVICE"))
try:
    device.terminate(APP)
    device.launch(APP, gray_box=True)

    print("hook returned:", repr(device.hook("raiseToast", "Toast raised by test script")))
    print("app's toast:  ", repr(device.text("testid=hookToast")))

    try:
        device.hook("raiseTost", "typo")
    except InvalidArgumentError as e:
        print("typo:", type(e).__name__, "-", e)
finally:
    device.terminate(APP)
    device.close()
