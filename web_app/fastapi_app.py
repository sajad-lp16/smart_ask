from fastapi import FastAPI, HTTPException, Depends, Query, Security
from fastapi.security import APIKeyQuery
from pydantic import BaseModel, field_validator
from typing import List, Optional, Union, Annotated
from pydantic_core import PydanticCustomError

app = FastAPI()

api_key_query = APIKeyQuery(name="api_key", auto_error=False)

VALID_API_KEYS = {
    "supportbottokeniamnotabaduserletmeindearapi": "support-bot",
    "admintokenwithfullaccess": "admin"
}


async def get_api_client(
        api_key: str = Security(api_key_query)
):
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key is required",
            headers={"WWW-Authenticate": "API-Key"}
        )

    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "API-Key"}
        )

    return VALID_API_KEYS[api_key]


class TicketRequest(BaseModel):
    ticket_id: Optional[Union[int, str]] = None
    ticket_ids: Optional[List[Union[int, str]]] = None

    @field_validator('ticket_id', 'ticket_ids', mode='before')
    @classmethod
    def validate_ids(cls, v, info):
        field_name = info.field_name

        if field_name == 'ticket_id' and v is not None:
            if isinstance(v, str):
                if not v.isdigit():
                    raise PydanticCustomError(
                        "invalid_ticket_id",
                        "Ticket ID must be a numeric string",
                        {"field": field_name}
                    )
                return int(v)
            return v

        elif field_name == 'ticket_ids' and v is not None:
            validated_ids = []
            for item in v:
                if isinstance(item, str):
                    if not item.isdigit():
                        raise PydanticCustomError(
                            "invalid_ticket_id",
                            "All ticket IDs must be numeric strings",
                            {"field": field_name}
                        )
                    validated_ids.append(int(item))
                else:
                    validated_ids.append(item)
            return validated_ids

        return v


@app.post("/zammad-update/")
async def update_tickets(
        request: TicketRequest,
        client: str = Security(get_api_client)
):
    ids = []

    if request.ticket_id is not None:
        ids.append(int(request.ticket_id))

    if request.ticket_ids is not None:
        ids.extend([int(tid) for tid in request.ticket_ids])

    if not ids:
        raise HTTPException(status_code=400, detail="At least one ticket ID required")

    return {
        "status": "success",
        "processed_ids": ids,
        "message": "Tickets are scheduled for update.",
    }