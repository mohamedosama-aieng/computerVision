from __future__ import annotations

import keyring


SERVICE_NAME = "HikvisionSecureViewer"


def credential_key(host: str, username: str) -> str:
    return f"{username}@{host}"


def save_password(host: str, username: str, password: str) -> None:
    keyring.set_password(SERVICE_NAME, credential_key(host, username), password)


def load_password(host: str, username: str) -> str | None:
    return keyring.get_password(SERVICE_NAME, credential_key(host, username))
