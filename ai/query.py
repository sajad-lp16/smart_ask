from ai.components.router import Router


async def query_controller(user_input: str) -> list[str]:
    router = Router

    query_destination = await router.index_path(user_input)
    response = await query_destination

    if not isinstance(response, list):
        return [response]
    return response
