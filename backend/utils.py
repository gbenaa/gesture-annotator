# backend/utils.py

from PIL import Image as PILImage
import os
import uuid

def save_crop(original_path, rect, dest_folder):
    """
    Crops the region from original_path based on rect, saves to dest_folder.
    rect: {x, y, width, height} in 600x400 UI coordinates.
    Returns the saved filename.
    """
    img = PILImage.open(original_path)
    ow, oh = img.size

    # Convert UI (600x400) coordinates to image coordinates
    sx, sy = rect["x"] / 600, rect["y"] / 400
    sw, sh = rect["width"] / 600, rect["height"] / 400

    # Handle negative drags
    if sw < 0:
        sx += sw
        sw = -sw
    if sh < 0:
        sy += sh
        sh = -sh

    box = (
        int(sx * ow),
        int(sy * oh),
        int((sx + sw) * ow),
        int((sy + sh) * oh),
    )

    crop = img.crop(box)
    filename = f"{uuid.uuid4().hex}.jpg"
    dest_path = os.path.join(dest_folder, filename)
    crop.save(dest_path, quality=90)
    return filename
