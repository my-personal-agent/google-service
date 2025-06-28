from typing import List, Union

from config.settings_config import get_settings
from db.prisma.generated.models import ClientAuth


def deep_merge(base: dict, override: dict) -> dict:
    """
    Recursively merges two dictionaries.

    Values from the override dictionary will overwrite those in the base dictionary.
    If both values are dictionaries, the merge is performed recursively.

    Args:
        base (dict): The base dictionary to merge into.
        override (dict): The dictionary with override values.

    Returns:
        dict: The merged dictionary.
    """
    for key, value in override.items():
        # If both base and override have a dict at this key, merge them recursively
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            base[key] = deep_merge(base[key], value)
        else:
            # Otherwise, override the base value
            base[key] = value
    return base


Jsonable = Union[str, dict]
InputType = Union[str, List[Jsonable]]


def to_string(x: InputType) -> str:
    if isinstance(x, str):
        return x
    elif isinstance(x, list):
        parts = []
        for item in x:
            if isinstance(item, dict):
                # serialize dict to JSON-like string
                parts.append(str(item))
            else:  # item is str
                parts.append(item)
        return " ".join(parts)
    else:
        raise TypeError(f"Unexpected type: {type(x)}")


def get_google_client_config(client_auth: ClientAuth):
    return {
        "web": {
            "client_id": client_auth.googleClientId,
            "client_secret": client_auth.googleClientSecret,
            "auth_uri": str(get_settings().google_auth_uri),
            "token_uri": str(get_settings().google_token_uri),
        }
    }
