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
from .scene import DEFAULT_STYLE, scene_prompt, scene_style, scene_subject_text

# Sensible steps/guidance/size per model. Turbo/schnell are few-step, low-CFG.
MODEL_DEFAULTS: dict[str, dict] = {
    "stabilityai/sdxl-turbo": {"steps": 4, "guidance": 0.0, "size": 512},
    "stabilityai/sd-turbo": {"steps": 4, "guidance": 0.0, "size": 512},
    "stabilityai/stable-diffusion-xl-base-1.0": {"steps": 30, "guidance": 7.0, "size": 768},
    "black-forest-labs/FLUX.1-schnell": {"steps": 4, "guidance": 0.0, "size": 768},
    "PixArt-alpha/PixArt-Sigma-XL-2-1024-MS": {"steps": 18, "guidance": 4.5, "size": 768},
    "runwayml/stable-diffusion-v1-5": {"steps": 28, "guidance": 7.5, "size": 512},
}

NEGATIVE = ("people, person, human, figure, crowd, text, words, letters, "
            "watermark, signature, ui, frame, blurry, low quality")


def pick_device() -> str:
    import torch

    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def _quiet_libraries() -> None:
    """Silence torch/transformers/diffusers advisory warnings (not errors)."""
    import warnings

    warnings.filterwarnings("ignore")
    try:
        from diffusers.utils import logging as dlog
        from transformers.utils import logging as tlog
        dlog.set_verbosity_error()
        tlog.set_verbosity_error()
    except Exception:
        pass


class DiffusersGenerator:
    """Callable ``(GameData, loc) -> (png_bytes, "image/png")`` backed by diffusers."""

    def __init__(self, model: str = "stabilityai/sdxl-turbo", *, steps: int | None = None,
                 guidance: float | None = None, size: int | None = None,
                 device: str | None = None, style: str = DEFAULT_STYLE):
        d = MODEL_DEFAULTS.get(model, {"steps": 20, "guidance": 5.0, "size": 512})
        self.model = model
        self.steps = steps if steps is not None else d["steps"]
        self.guidance = guidance if guidance is not None else d["guidance"]
        self.size = size if size is not None else d["size"]
        self.device = device or pick_device()
        self.style = style
        self._pipe = None

    def _ensure_pipe(self):
        if self._pipe is not None:
            return
        _quiet_libraries()
        import torch
        from diffusers import AutoPipelineForText2Image

        if self.device == "cpu":
            dtype = torch.float32
        elif "flux" in self.model.lower():
            dtype = torch.bfloat16          # FLUX is numerically happiest in bf16
        else:
            dtype = torch.float16
        try:
            pipe = AutoPipelineForText2Image.from_pretrained(self.model, torch_dtype=dtype)
        except Exception:
            if "pixart" in self.model.lower():
                from diffusers import PixArtSigmaPipeline
                pipe = PixArtSigmaPipeline.from_pretrained(self.model, torch_dtype=dtype)
            else:
                raise
        pipe = pipe.to(self.device)
        pipe.set_progress_bar_config(disable=True)
        self._pipe = pipe

    def __call__(self, data: GameData, loc: int) -> tuple[bytes, str]:
        self._ensure_pipe()
        kwargs = {"num_inference_steps": self.steps, "guidance_scale": self.guidance,
                  "height": self.size, "width": self.size}
        use_negative = bool(self.guidance and self.guidance > 0)

        name = self.model.lower()
        is_sdxl = "sdxl" in name or "stable-diffusion-xl" in name
        if is_sdxl:
            # SDXL has two CLIP encoders (77 tokens each): scene -> encoder 1,
            # style -> encoder 2, so both apply in full without truncation.
            kwargs["prompt"] = scene_subject_text(data, loc)
            kwargs["prompt_2"] = scene_style(data, loc, self.style)
            if use_negative:
                kwargs["negative_prompt"] = NEGATIVE
                kwargs["negative_prompt_2"] = NEGATIVE
        else:
            # T5-based models (FLUX, SD3, PixArt) take the full combined prompt;
            # single-CLIP models truncate it (not recommended for long scenes).
            kwargs["prompt"] = scene_prompt(data, loc, self.style)
            if use_negative:
                kwargs["negative_prompt"] = NEGATIVE

        image = self._pipe(**kwargs).images[0]
        buf = BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue(), "image/png"

    def render(self, prompt: str, negative: str | None = None) -> tuple[bytes, str]:
        """Generate an image from a single prompt (used for object sprites)."""
        self._ensure_pipe()
        kwargs = {"prompt": prompt, "num_inference_steps": self.steps,
                  "guidance_scale": self.guidance, "height": self.size, "width": self.size}
        if self.guidance and self.guidance > 0 and negative:
            kwargs["negative_prompt"] = negative
        image = self._pipe(**kwargs).images[0]
        buf = BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue(), "image/png"
