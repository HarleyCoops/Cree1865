# Cree1865 Space Deployment

Space:

`https://huggingface.co/spaces/HarleyCooper/Cree1865-Tinker-Inference`

Runtime:

- SDK: Gradio
- Hardware: CPU Basic
- Backend: remote Tinker sampler
- Endpoint: `tinker://c71aadd1-8e48-51b0-b890-149a2889b4fa:train:0/sampler_weights/final`

Required Hugging Face Space secret:

- `TINKER_API_KEY`

Deploy from the repo root:

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
    commit_message="Deploy Cree1865 Tinker inference Space",
)
'@ | python -
```

The Space does not host the 30B model. It only calls the remote sampler, so GPU
hardware is not required for the interface itself.
