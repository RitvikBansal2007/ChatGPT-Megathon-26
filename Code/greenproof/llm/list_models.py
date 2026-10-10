from greenproof.llm.client import get_client

client = get_client()
for model in client.models.list():
    print(model.name)
