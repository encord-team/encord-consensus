import sys
from pathlib import Path

from streamlit.web import cli as stcli

from encord_consensus.app.common.constants import HOME_PAGE_TITLE


def launch():
    streamlit_page = (Path(__file__).parent / f"app/{HOME_PAGE_TITLE}.py").expanduser().resolve()
    sys.argv = ["streamlit", "run", streamlit_page.as_posix()]

    sys.exit(stcli.main())


if __name__ == "__main__":
    launch()
