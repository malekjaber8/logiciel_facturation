import sys
import os
import traceback

if getattr(sys, "frozen", False):
    _dossier_app = os.path.dirname(sys.executable)
    _log_path = os.path.join(_dossier_app, "erreur.log")
    if sys.stdout is None or sys.stderr is None:
        _log = open(_log_path, "a", encoding="utf-8", buffering=1)
        sys.stdout = _log
        sys.stderr = _log

import db
from ui_app import App

if __name__ == "__main__":
    try:
        db.init_db()
        app = App()
        app.mainloop()
    except Exception:
        traceback.print_exc()
        raise
