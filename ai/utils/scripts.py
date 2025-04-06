def get_chunks(conversation: str, lvl: int = 1) -> list[str]:
    if lvl > 1:
        l_c = len(conversation)
        offset = l_c // lvl
        prev = 0
        conversations = []
        while prev <= l_c:
            conversations.append(conversation[prev:offset + prev])
            prev += offset
        conversations = list(filter(lambda c: len(c) > 5, conversations))
    else:
        conversations = [conversation]
    return conversations

# llm = Ollama(
#     base_url="http://127.0.0.1:11434",
#     model="mistral",
#     temperature=0.1
# )
# embed_model = OllamaEmbedding(
#     model_name="nomic-embed-text:latest",
#     base_url="http://127.0.0.1:11434",
# )
# Settings.embed_model = embed_model


# import json
# from apps.sales.models import Person
#
# m = {}
#
# for p in Person.objects.values("id", "email_main", "email_1", "email_2", "email_3"):
#     if p.get("email_main"):
#         m[p.get("email_main")] = p["id"]
#     if p.get("email_1"):
#         m[p.get("email_1")] = p["id"]
#     if p.get("email_2"):
#         m[p.get("email_2")] = p["id"]
#     if p.get("email_3"):
#         m[p.get("email_3")] = p["id"]
#
# with open("email_person_mapper.json", "w") as file:
#     json.dump(m, file, indent=4, ensure_ascii=False)
#
#
# import json
# from apps.sales.models import ZammadTicket
#
# m = {}
#
# for z in ZammadTicket.objects.filter(deal__isnull=False).values("ticket_id", "deal_id"):
#     m[z["ticket_id"]] = z["deal_id"]
#
# with open("ticket_deal_mapper.json", "w") as file:
#     json.dump(m, file, indent=4, ensure_ascii=False

# import json
# with open("email_person_mapper.json") as email, open("ticket_deal_mapper.json") as deal:
#     email_map = json.load(email)
#     deal_map = json.load(deal)
#     for filename in os.listdir("step_4_tickets_OK"):
#         with open(f"step_4_tickets_OK/{filename}") as change:
#             c_f = json.load(change)
#         c_f["person_ids"] = []
#         c_f["deal_ids"] = []
#         for e in c_f["emails"]:
#             person_id = email_map.get(e)
#             if person_id:
#                 c_f["person_ids"].append(person_id)
#         deal_id = deal_map.get(filename.split(".")[0])
#         if deal_id:
#             print(filename)
#             c_f["deal_ids"].append(deal_id)
#         with open(f"ready/{filename}", "w") as ready_file:
#             json.dump(c_f, ready_file, indent=4, ensure_ascii=False)
