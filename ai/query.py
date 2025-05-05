from ai.components.router import router


async def query_controller(user_input: str, user_id: str) -> list[str]:
    query_destination = await router.index_path(user_id, user_input)
    response = await query_destination

    if not isinstance(response, list):
        return [response]
    return response
