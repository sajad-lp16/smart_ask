import json

from openai import APITimeoutError, BadRequestError

from ai.clients import CustomAsyncOpenAI, AIClient


async def fetch_ai_client(prompt: str, client: CustomAsyncOpenAI = None) -> dict | None:
    async def _fetch(_client):
        print("fetching AI ...")
        completion = await _client.chat.completions.create(
            **client.get_template(prompt)
        )
        json_response = completion.choices[0].message.content.strip('```json')
        r =  json.loads(json_response)
        print("returning OK")
        return r

    for _ in range(3):
        try:
            if client is None:
                async with AIClient() as new_client:
                    return await _fetch(new_client)
            return await _fetch(client)

        except APITimeoutError:
            continue
        except BadRequestError as err:
            raise err
        except TypeError as err:
            raise err
