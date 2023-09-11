from encord_consensus.app.common.constants import (
    CHOOSE_PROJECT_PAGE_NAME,
    EXPORT_PAGE_NAME,
    INSPECT_FILES_PAGE_NAME,
)


class Settings:
    API_URL: str = "http://localhost:8501"

    # ---------- INTERNAL URLS ----------
    CHOOSE_PROJECT_PAGE_URL: str = API_URL + "/" + CHOOSE_PROJECT_PAGE_NAME.replace(" ", "_")
    EXPORT_PAGE_URL: str = API_URL + "/" + EXPORT_PAGE_NAME.replace(" ", "_")
    HOME_PAGE_URL: str = API_URL + "/"
    INSPECT_FILES_PAGE_URL: str = API_URL + "/" + INSPECT_FILES_PAGE_NAME.replace(" ", "_")
