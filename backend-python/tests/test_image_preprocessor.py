"""
图片预处理器测试，覆盖 ImagePreprocessor 全部函数和分支。
"""
import pytest
from io import BytesIO
from PIL import Image, ImageChops
from app.parsers.image_preprocessor import ImagePreprocessor


def _create_test_image(mode: str = "RGB", size: tuple = (200, 100), color: tuple = (200, 200, 200)) -> Image.Image:
    """创建测试用 PIL Image"""
    return Image.new(mode, size, color)


class TestImagePreprocessor:
    """ImagePreprocessor 全面测试"""

    def test_preprocess_default(self):
        """测试默认预处理参数"""
        img = _create_test_image()
        result = ImagePreprocessor.preprocess(img)
        assert result.mode == "L"  # 默认灰度化
        assert result.size == (200, 100)

    def test_preprocess_no_grayscale(self):
        """测试关闭灰度化"""
        img = _create_test_image()
        result = ImagePreprocessor.preprocess(img, apply_grayscale=False)
        assert result.mode == "RGB"

    def test_preprocess_with_binarization(self):
        """测试二值化"""
        img = _create_test_image(mode="L", color=150)
        result = ImagePreprocessor.preprocess(
            img,
            apply_grayscale=False,
            apply_binarization=True,
            apply_denoise=False,
            apply_contrast=False,
        )
        assert result.mode == "L"

    def test_preprocess_with_denoise(self):
        """测试降噪"""
        img = _create_test_image()
        result = ImagePreprocessor.preprocess(
            img,
            apply_grayscale=True,
            apply_binarization=False,
            apply_denoise=True,
            apply_contrast=False,
        )
        assert result.mode == "L"

    def test_preprocess_with_contrast(self):
        """测试对比度增强"""
        img = _create_test_image(mode="L", color=128)
        result = ImagePreprocessor.preprocess(
            img,
            apply_grayscale=False,
            apply_binarization=False,
            apply_denoise=False,
            apply_contrast=True,
        )
        assert result.mode == "L"

    def test_preprocess_with_deskew(self):
        """测试倾斜校正（目前为占位，返回原图）"""
        img = _create_test_image()
        result = ImagePreprocessor.preprocess(
            img,
            apply_grayscale=False,
            apply_binarization=False,
            apply_denoise=False,
            apply_contrast=False,
            apply_deskew=True,
        )
        # 倾斜校正目前是占位，返回原图
        assert result.size == (200, 100)

    def test_preprocess_rgba_image(self):
        """测试 RGBA 模式图片"""
        img = _create_test_image(mode="RGBA", color=(200, 200, 200, 255))
        result = ImagePreprocessor.preprocess(img)
        assert result.mode == "L"

    def test_preprocess_large_image_resize(self):
        """测试超大图片自动缩放"""
        img = _create_test_image(size=(5000, 3000))
        result = ImagePreprocessor.preprocess(img)
        # 应该被缩放到 MAX_WIDTH=4096 以内
        assert result.size[0] <= ImagePreprocessor.MAX_WIDTH
        assert result.size[1] <= ImagePreprocessor.MAX_HEIGHT

    def test_preprocess_very_large_image(self):
        """测试极大图片缩放"""
        img = _create_test_image(size=(8000, 6000))
        result = ImagePreprocessor.preprocess(img)
        assert result.size[0] <= ImagePreprocessor.MAX_WIDTH
        assert result.size[1] <= ImagePreprocessor.MAX_HEIGHT

    def test_preprocess_small_image_no_resize(self):
        """测试小图片不缩放"""
        img = _create_test_image(size=(100, 50))
        result = ImagePreprocessor.preprocess(img)
        assert result.size == (100, 50)

    def test_binarize_dark_image(self):
        """测试暗色图片二值化"""
        img = _create_test_image(mode="L", color=50)
        result = ImagePreprocessor.preprocess(
            img,
            apply_grayscale=False,
            apply_binarization=True,
            apply_denoise=False,
            apply_contrast=False,
        )
        assert result.mode == "L"

    def test_binarize_bright_image(self):
        """测试亮色图片二值化"""
        img = _create_test_image(mode="L", color=200)
        result = ImagePreprocessor.preprocess(
            img,
            apply_grayscale=False,
            apply_binarization=True,
            apply_denoise=False,
            apply_contrast=False,
        )
        assert result.mode == "L"

    def test_get_preprocessing_steps_all(self):
        """测试 get_preprocessing_steps 全部开启"""
        steps = ImagePreprocessor.get_preprocessing_steps({
            "apply_grayscale": True,
            "apply_binarization": True,
            "apply_denoise": True,
            "apply_contrast": True,
            "apply_deskew": True,
        })
        assert "grayscale" in steps
        assert "binarization" in steps
        assert "denoise" in steps
        assert "contrast_enhancement" in steps
        assert "deskew" in steps

    def test_get_preprocessing_steps_none(self):
        """测试 get_preprocessing_steps 全部关闭"""
        steps = ImagePreprocessor.get_preprocessing_steps({
            "apply_grayscale": False,
            "apply_binarization": False,
            "apply_denoise": False,
            "apply_contrast": False,
            "apply_deskew": False,
        })
        assert steps == []

    def test_get_preprocessing_steps_partial(self):
        """测试 get_preprocessing_steps 部分开启"""
        steps = ImagePreprocessor.get_preprocessing_steps({
            "apply_grayscale": True,
            "apply_binarization": False,
            "apply_denoise": True,
            "apply_contrast": False,
            "apply_deskew": False,
        })
        assert steps == ["grayscale", "denoise"]

    def test_preprocess_preserves_aspect_ratio(self):
        """测试缩放保持宽高比"""
        img = _create_test_image(size=(8000, 4000))
        result = ImagePreprocessor.preprocess(img)
        # 宽高比应保持 2:1
        assert abs(result.size[0] / result.size[1] - 2.0) < 0.01
