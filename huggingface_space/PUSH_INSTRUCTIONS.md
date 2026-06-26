# Push Instructions

This directory is the Hugging Face Space bundle for the Cree1865 Tinker
inference app.

## One-Time Setup

Create the Space if it does not already exist:

```powershell
hf repos create HarleyCooper/Cree1865-Tinker-Inference --type space --space-sdk gradio --exist-ok
```

Set the `TINKER_API_KEY` Space secret in the Hugging Face UI or with
`huggingface_hub.HfApi.add_space_secret`.

## Upload

From `C:\Users\chris\Cree1865`:

```powershell
@'
from huggingface_hub import HfApi
api = HfApi()
api.upload_folder(
    repo_id="HarleyCooper/Cree1865-Tinker-Inference",
    repo_type="space",
    folder_path=r"C:\Users\chris\Cree1865\huggingface_space",
    path_in_repo=".",
    ignore_patterns=["**/__pycache__/**", "*.pyc"],
    commit_message="Update Cree1865 Tinker inference Space",
)
'@ | python -
```

Do not commit API keys. The app reads `TINKER_API_KEY` only from environment
variables or Hugging Face Space secrets.
