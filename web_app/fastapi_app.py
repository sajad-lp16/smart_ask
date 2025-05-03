from typing import List, Optional, Union

import uvicorn
from fastapi import FastAPI, HTTPException, Security, Request
from fastapi.security import APIKeyQuery
from pydantic import BaseModel, field_validator
from pydantic_core import PydanticCustomError

from core.log_config import api_logger as logger
from core.config import AVICENNA_TOKEN
from ai.query import query_controller
from core.redis_service import redis_gateway

app = FastAPI()

api_key_query = APIKeyQuery(name="api_key", auto_error=False)

VALID_API_KEYS = {
    AVICENNA_TOKEN: "support-bot",
}


async def get_api_client(
        api_key: str = Security(api_key_query)
):
    if not api_key:
        logger.warning("API key is missing")
        raise HTTPException(
            status_code=401,
            detail="API key is required",
            headers={"WWW-Authenticate": "API-Key"}
        )

    if api_key not in VALID_API_KEYS:
        logger.warning(f"Invalid API key attempted: {api_key[:5]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "API-Key"}
        )

    return VALID_API_KEYS[api_key]


class TicketRequest(BaseModel):
    ticket_ids: Optional[List[Union[int, str]]] = None

    @field_validator("ticket_ids", mode="before")
    @classmethod
    def validate_ids(cls, v, info):
        field_name = info.field_name
        if field_name == "ticket_ids" and v is not None:
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
    logger.info(f"Received update request from client: {client}")
    ids = []

    if request.ticket_ids is not None:
        ids.extend([int(tid) for tid in request.ticket_ids])

    if not ids:
        raise HTTPException(status_code=400, detail="At least one ticket ID required")

    await redis_gateway.queue_items("zammad", ids)
    logger.info(f"Successfully processed ticket update request for IDs: {ids}")
    return {
        "status": "success",
        "processed_ids": ids,
        "message": "Tickets are scheduled for update.",
    }


@app.post("/forum-update/")
async def forum_update(request: Request):
    try:
        payload = await request.json()
        event_type = request.headers.get("x-discourse-event-type")
        logger.info(f"Received Discourse webhook event: {event_type}")

        if event_type == "post":
            topic_id = payload["post"]["topic_id"]

        elif event_type == "topic":
            topic_id = payload["topic"]["id"]

        else:
            logger.info(f"Unhandled event type: {event_type}")
            raise HTTPException(status_code=400, detail=f"Unhandled event type: {event_type}")

        await redis_gateway.queue_items("forum", [topic_id])
        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/query")
async def query_endpoint(message: str, client: str = Security(get_api_client)):
    logger.info(f"Received query request from client: {client}")
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    responses = await query_controller(message)
    return {"responses": responses}


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8089,
        loop="asyncio",
        workers=4,
    )
