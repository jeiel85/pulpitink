"""GUI entry point: ``python -m pulpit_ink.app.main``.

PySide6 is an optional dependency, so we import it inside :func:`main`
and surface a friendly hint when it is missing.
"""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)

    try:
        from PySide6.QtWidgets import QApplication
    except ModuleNotFoundError:
        sys.stderr.write(
            "PySide6가 설치되어 있지 않습니다. 다음 명령으로 설치하세요:\n"
            "    pip install \"pulpit_ink[gui]\"\n"
            "또는\n"
            "    pip install PySide6\n"
        )
        return 1

    from pulpit_ink.app.logging_config import configure_logging
    from pulpit_ink.ui.main_window import MainWindow

    configure_logging()

    app = QApplication(argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
