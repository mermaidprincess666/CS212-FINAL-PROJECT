"""Load and cache image files used by the game."""

import pygame

from settings import ASSETS_DIR


class AssetLoader:
    """Load each image once per requested size and hand back the cached copy."""

    def __init__(self):
        self._images = {}

    def load_image(self, filename, size=None, subdirectory="MENU/BG"):
        """Return an image, optionally scaled to ``size``.

        By default, images load from ``ASSET/MENU/BG``; set ``subdirectory``
        for another folder under ``ASSET``. The cache key includes ``size``, so
        the same file requested at two sizes is decoded twice. Missing files
        raise an error naming the path that was tried.
        """
        key = (subdirectory, filename, size)
        if key in self._images:
            return self._images[key]

        image_path = ASSETS_DIR / subdirectory / filename
        if not image_path.is_file():
            raise FileNotFoundError(
                f"Missing image asset '{filename}'. Expected it at: {image_path}"
            )

        image = pygame.image.load(str(image_path)).convert_alpha()
        if size is not None and image.get_size() != size:
            image = pygame.transform.smoothscale(image, size)

        self._images[key] = image
        return image