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

    # Jira Cloud (can be overridden via UI).
    # ``jira_user`` must be the Atlassian account email and ``jira_api_token``
    # must be an API token from
    # https://id.atlassian.com/manage-profile/security/api-tokens.
    jira_url: str = ""
    jira_user: str = ""
    jira_api_token: str = ""

    # Confluence Cloud (can be overridden via UI).
    # ``confluence_user`` must be the Atlassian account email and
    # ``confluence_api_token`` must be an API token from
    # https://id.atlassian.com/manage-profile/security/api-tokens.
    confluence_url: str = ""
    confluence_user: str = ""
    confluence_api_token: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
