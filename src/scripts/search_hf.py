from huggingface_hub import HfApi
api = HfApi()
models = api.list_models(search="nllb-200-distilled-600M-ct2")
for model in models:
    print(model.modelId)
