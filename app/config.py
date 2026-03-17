from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Active Directory (can be overridden via UI)
    ad_server: str = ""
    ad_user: str = ""
    ad_password: str = ""
    ad_base_dn: str = ""
    ad_batts_group_cn: str = "batts"
    ad_unixusers_group_cn: str = "unixusers"

    # vCenter (can be overridden via UI)
    vcenter_host: str = ""
    vcenter_user: str = ""
    vcenter_password: str = ""
    vcenter_disable_ssl: bool = True

    # Jira (can be overridden via UI)
    jira_url: str = ""
    jira_user: str = ""
    jira_password: str = ""

    # Confluence (can be overridden via UI)
    confluence_url: str = ""
    confluence_user: str = ""
    confluence_password: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
