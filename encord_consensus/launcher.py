import site
import sys

from streamlit.web import cli as stcli


def launch():
    site_packages = site.getsitepackages().pop()
    sys.argv = ["streamlit", "run", f"{site_packages}/encord_consensus/app.py"]
    sys.exit(stcli.main())
