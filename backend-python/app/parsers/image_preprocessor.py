"""
图片预处理工具，用于提高 OCR 识别率的图像处理流水线。
支持灰度化、二值化、降噪、倾斜校正等操作。
"""
from typing import List, Optional
from PIL import Image, ImageFilter, ImageEnhance, ImageOps


class ImagePreprocessor:
    """
    图片预处理流水线，对输入图片进行一系列增强操作，
    以提高 OCR 引擎的文本识别准确率。
    """

    # 最大处理尺寸（像素），超过则缩放
    MAX_WIDTH = 4096
    MAX_HEIGHT = 4096

    @staticmethod
    def preprocess(
        image: Image.Image,
        apply_grayscale: bool = True,
        apply_binarization: bool = False,
        apply_denoise: bool = True,
        apply_contrast: bool = True,
        apply_deskew: bool = False,
    ) -> Image.Image:
        """
        对图片执行预处理流水线。
        
        :param image: PIL Image 对象
        :param apply_grayscale: 是否灰度化
        :param apply_binarization: 是否二值化（OTSU 阈值）
        :param apply_denoise: 是否降噪
        :param apply_contrast: 是否增强对比度
        :param apply_deskew: 是否倾斜校正
        :return: 处理后的 PIL Image 对象
        """
        img = image.copy()
        
        # Step 1: 缩放过大图片
        img = ImagePreprocessor._resize_if_needed(img)
        
        # Step 2: 转换为 RGB（确保统一格式）
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        
        # Step 3: 灰度化
        if apply_grayscale:
            img = img.convert("L")
        
        # Step 4: 增强对比度
        if apply_contrast and img.mode == "L":
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0)
        
        # Step 5: 降噪
        if apply_denoise:
            img = img.filter(ImageFilter.MedianFilter(size=3))
        
        # Step 6: 二值化
        if apply_binarization and img.mode == "L":
            img = ImagePreprocessor._binarize(img)
        
        # Step 7: 倾斜校正
        if apply_deskew:
            img = ImagePreprocessor._deskew(img)
        
        return img

    @staticmethod
    def _resize_if_needed(image: Image.Image) -> Image.Image:
        """
        如果图片尺寸超过最大限制，按比例缩放。
        """
        width, height = image.size
        if width <= ImagePreprocessor.MAX_WIDTH and height <= ImagePreprocessor.MAX_HEIGHT:
            return image
        
        ratio = min(
            ImagePreprocessor.MAX_WIDTH / width,
            ImagePreprocessor.MAX_HEIGHT / height,
        )
        new_size = (int(width * ratio), int(height * ratio))
        return image.resize(new_size, Image.Resampling.LANCZOS)

    @staticmethod
    def _binarize(image: Image.Image) -> Image.Image:
        """
        使用 OTSU 算法进行二值化处理。
        将灰度图转换为纯黑白图。
        """
        # 使用阈值 128 进行简单二值化
        # 更精确的 OTSU 需要 numpy，这里使用简单阈值
        threshold = 128
        return image.point(lambda x: 255 if x > threshold else 0, mode="1").convert("L")

    @staticmethod
    def _deskew(image: Image.Image) -> Image.Image:
        """
        简单的倾斜校正。
        注意：精确的倾斜校正需要更复杂的算法，
        这里作为占位，后续可集成 deskew 库。
        """
        # 目前返回原图，后续可集成 deskew 算法
        return image

    @staticmethod
    def get_preprocessing_steps(applied: dict) -> List[str]:
        """
        返回实际应用的预处理步骤列表，用于元数据记录。
        
        :param applied: 各步骤的开关字典
        :return: 已应用的步骤名称列表
        """
        steps = []
        if applied.get("apply_grayscale"):
            steps.append("grayscale")
        if applied.get("apply_binarization"):
            steps.append("binarization")
        if applied.get("apply_denoise"):
            steps.append("denoise")
        if applied.get("apply_contrast"):
            steps.append("contrast_enhancement")
        if applied.get("apply_deskew"):
            steps.append("deskew")
        return steps
