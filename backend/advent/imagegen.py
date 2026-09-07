# Copyright (c) 2026 Athena Decisions Systems SAS.
"""Local open-weights image generation for scene art (optional).

This is the pluggable generator for :class:`advent.scene.SceneStore`.  It needs
heavy, optional dependencies (``torch`` + ``diffusers``) that are *not* in the
backend's requirements -- install the ``imagegen`` extra to use it, and run it
where there is a GPU/MPS (your Mac), typically via ``advent.pregen`` to fill the
scene cache offline.  Import stays cheap: torch/diffusers load lazily.
"""
from __future__ import annotations

from io import BytesIO

from .data import GameData
from .scene import scene_prompt

# Sensible steps/guidance/size per model. Turbo/schnell are few-step, low-CFG.
MODEL_DEFAULTS: dict[str, dict] = {
    "stabilityai/sdxl-turbo": {"steps": 2, "guidance": 0.0, "size": 512},
    "stabilityai/sd-turbo": {"steps": 2, "guidance": 0.0, "size": 512},
    "stabilityai/stable-diffusion-xl-base-1.0": {"steps": 30, "guidance": 7.0, "size": 768},
    "black-forest-labs/FLUX.1-schnell": {"steps": 4, "guidance": 0.0, "size": 1024},
    "runwayml/stable-diffusion-v1-5": {"steps": 28, "guidance": 7.5, "size": 512},
}

NEGATIVE = "text, words, letters, watermark, signature, ui, frame, blurry, low quality"


def pick_device() -> str:
    import torch

    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


class DiffusersGenerator:
    """Callable ``(GameData, loc) -> (png_bytes, "image/png")`` backed by diffusers."""

    def __init__(self, model: str = "stabilityai/sdxl-turbo", *, steps: int | None = None,
                 guidance: float | None = None, size: int | None = None,
                 device: str | None = None):
        d = MODEL_DEFAULTS.get(model, {"steps": 20, "guidance": 5.0, "size": 512})
        self.model = model
        self.steps = steps if steps is not None else d["steps"]
        self.guidance = guidance if guidance is not None else d["guidance"]
        self.size = size if size is not None else d["size"]
        self.device = device or pick_device()
        self._pipe = None

    def _ensure_pipe(self):
        if self._pipe is not None:
            return
        import torch
        from diffusers import AutoPipelineForText2Image

        dtype = torch.float32 if self.device == "cpu" else torch.float16
        pipe = AutoPipelineForText2Image.from_pretrained(self.model, torch_dtype=dtype)
        pipe = pipe.to(self.device)
        pipe.set_progress_bar_config(disable=True)
        self._pipe = pipe

    def __call__(self, data: GameData, loc: int) -> tuple[bytes, str]:
        self._ensure_pipe()
        prompt = scene_prompt(data, loc)
        kwargs = {"prompt": prompt, "num_inference_steps": self.steps,
                  "guidance_scale": self.guidance, "height": self.size, "width": self.size}
        # Turbo/schnell pipelines reject a negative prompt at guidance 0.
        if self.guidance and self.guidance > 0:
            kwargs["negative_prompt"] = NEGATIVE
        image = self._pipe(**kwargs).images[0]
        buf = BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue(), "image/png"
