import torch
import numpy as np
from basicsr.utils.registry import METRIC_REGISTRY
from basicsr.metrics.metric_util import reorder_image, to_y_channel

_lpips_model = None


def _init_lpips_model():
    global _lpips_model
    if _lpips_model is None:
        import lpips

        _lpips_model = lpips.LPIPS(net="alex").eval()
    return _lpips_model


@METRIC_REGISTRY.register()
def calculate_lpips(
    img, img2, crop_border=0, input_order="HWC", test_y_channel=False, **kwargs
):
    loss_fn = _init_lpips_model()

    assert img.shape == img2.shape, f"画像サイズが異なります: {img.shape}, {img2.shape}"

    if input_order != "HWC":
        img = reorder_image(img, input_order=input_order)
        img2 = reorder_image(img2, input_order=input_order)

    if crop_border != 0:
        img = img[crop_border:-crop_border, crop_border:-crop_border, ...]
        img2 = img2[crop_border:-crop_border, crop_border:-crop_border, ...]

    if test_y_channel:
        raise NotImplementedError("test_y_channel=True is not implemented.")

    img = torch.from_numpy(img).permute(2, 0, 1).unsqueeze(0).float() / 127.5 - 1
    img2 = torch.from_numpy(img2).permute(2, 0, 1).unsqueeze(0).float() / 127.5 - 1

    device = next(loss_fn.parameters()).device
    img = img.to(device)
    img2 = img2.to(device)

    with torch.no_grad():
        lpips_value = loss_fn.forward(img, img2)

    return lpips_value.item()
