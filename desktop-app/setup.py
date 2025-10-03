from setuptools import setup

APP = ["finance_tracker_gui.py"]
DATA_FILES = []
OPTIONS = {
    "argv_emulation": True,
    "plist": {
        "CFBundleName": "Finance Tracker 2.0",
        "CFBundleDisplayName": "Finance Tracker 2.0",
        "CFBundleIdentifier": "com.yourname.financetracker",
        "CFBundleVersion": "2.0.0",
        "CFBundleShortVersionString": "2.0.0",
        "NSHighResolutionCapable": True,
        "LSUIElement": True,
    },
    "includes": ["tkinter", "tkinter.ttk", "tkinter.filedialog", "tkinter.messagebox"],
    "excludes": ["matplotlib", "numpy", "scipy"],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
