from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_secret_key: str = "change-me-to-a-random-secret"
    admin_username: str = "admin"
    admin_password: str = "changeme123"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Active Directory
    ad_server: str = ""
    ad_user: str = ""
    ad_password: str = ""
    ad_base_dn: str = ""
    ad_batts_group_cn: str = "batts"
    ad_unixusers_group_cn: str = "unixusers"

    # vCenter
    vcenter_host: str = ""
    vcenter_user: str = ""
    vcenter_password: str = ""
    vcenter_disable_ssl: bool = True

    # Jira
    jira_url: str = ""
    jira_user: str = ""
    jira_api_token: str = ""

    # Confluence
    confluence_url: str = ""
    confluence_user: str = ""
    confluence_api_token: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
