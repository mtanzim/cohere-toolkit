import logging
from typing import Any, Dict, List

from fastapi.security import OAuth2PasswordBearer

from backend.tools.base import BaseTool
from backend.crud import tool_auth as tool_auth_crud
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


class GoogleDrive(BaseTool):
    """
    Tool that searches Google Drive with an oauth token
    """

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
    

    @classmethod
    def is_available(cls) -> bool:
        return True

    @classmethod
    def is_available(cls) -> bool:
        return True

    def call(self, parameters: dict, **kwargs: Any) -> List[Dict[str, Any]]:
        query = parameters.get("query", "")
        # TODO this should call google drive with the oauth token stored in the DB
        # If it is expired it should refresh the token 
        
        auth = tool_auth_crud.get_tool_auth(kwargs.get("session"), "Google_Drive", "user_id")
        creds = Credentials(auth.encrypted_access_token.decode())
        print(auth.encrypted_access_token.decode())
        service = build("drive", "v3", credentials=creds)
        results = (
            service.files()
            .list(pageSize=10, fields="nextPageToken, files(id, name)")
            .execute()
        )
        print(items)
        items = results.get("files", [])
        return items