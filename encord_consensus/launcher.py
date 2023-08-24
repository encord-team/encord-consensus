import sys
from pathlib import Path

from streamlit.web import cli as stcli


def launch():
    streamlit_page = (Path(__file__).parent / "app.py").expanduser().resolve()
    sys.argv = ["streamlit", "run", streamlit_page.as_posix()]

    sys.exit(stcli.main())


if __name__ == "__main__":
    launch()
