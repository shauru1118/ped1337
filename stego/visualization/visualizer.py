import numpy as np
from typing import Tuple, Dict, List
from ..interfaces.stego import IVisualizer
from ..interfaces.image import IImageAdapter, IBlockMapHandler
from ..config import StegoConfig


class StegoVisualizer(IVisualizer):
    """Visualizer component generating colored overlay maps of channel bit allocations."""

    def __init__(
        self,
        config: StegoConfig,
        image_adapter: IImageAdapter,
        block_map_handler: IBlockMapHandler,
    ):
        self.config = config
        self.image_adapter = image_adapter
        self.block_map_handler = block_map_handler

    def visualize(
        self,
        image_path: str,
        output_path: str,
        colors: Dict[int, List[int]],
        strength: float = 0.5,
    ) -> str:
        block_map = self.block_map_handler.read(image_path, self.config.magic_bytes)
        img = self.image_adapter.load(image_path)
        h, w, _ = img.shape

        result = img.astype(np.float32)
        map_idx = 0
        bs = self.config.block_size

        for y in range(0, h, bs):
            for x in range(0, w, bs):
                if map_idx >= len(block_map):
                    break

                bpc = block_map[map_idx]
                map_idx += 1

                if bpc not in colors:
                    continue

                block = result[y : y + bs, x : x + bs]
                target_color = np.array(colors[bpc], dtype=np.float32)
                block[:] = block * (1 - strength) + target_color * strength

        result = np.clip(result, 0, 255).astype(np.uint8)
        self.image_adapter.save(result, output_path)
        return output_path

    def generate_all_views(self, image_path: str) -> Tuple[str, str, str, str]:
        out_full = f"{image_path}_output.png"
        out_0 = f"{image_path}_output_0.png"
        out_1 = f"{image_path}_output_1.png"
        out_2 = f"{image_path}_output_2.png"

        self.visualize(
            image_path,
            out_full,
            {0: [255, 0, 0], 1: [255, 255, 0], 2: [0, 255, 0], 3: [0, 0, 0]},
            0.5,
        )
        self.visualize(
            image_path,
            out_0,
            {0: [255, 0, 0], 1: [0, 0, 0], 2: [0, 0, 0], 3: [0, 0, 0]},
            0.5,
        )
        self.visualize(
            image_path,
            out_1,
            {0: [0, 0, 0], 1: [255, 255, 0], 2: [0, 0, 0], 3: [0, 0, 0]},
            0.5,
        )
        self.visualize(
            image_path,
            out_2,
            {0: [0, 0, 0], 1: [0, 0, 0], 2: [0, 255, 0], 3: [0, 0, 0]},
            0.5,
        )

        return (out_0, out_1, out_2, out_full)
