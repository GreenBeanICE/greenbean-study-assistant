"""
图片 OCR 解析器测试文件，用于验证 OCR 图片解析逻辑。
由于 OCR 需要 Tesseract 引擎，测试使用 mock 模拟。
"""
import pytest
from unittest.mock import MagicMock, patch, mock_open
from io import BytesIO
from PIL import Image

from app.parsers.image_ocr_parser import ImageOCRParser


def _create_test_image(format: str = "PNG", size: tuple = (100, 50)) -> bytes:
    """
    创建一个简单的测试图片字节流。
    """
    img = Image.new("RGB", size, color="white")
    buf = BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


@pytest.mark.us25
def test_ocr_parser_png():
    """
    测试 ImageOCRParser 解析 PNG 图片。
    """
    parser = ImageOCRParser()
    image_bytes = _create_test_image("PNG")
    
    # 模拟 pytesseract.image_to_string
    with patch("pytesseract.image_to_string", return_value="Hello Greenbean\n这是中文\nBonjour le monde"):
        result = parser.parse(image_bytes)
        
        assert len(result) == 1
        assert result[0]["page_number"] == 1
        assert "Hello Greenbean" in result[0]["content"]
        assert "这是中文" in result[0]["content"]
        assert "Bonjour le monde" in result[0]["content"]
        assert result[0]["metadata"]["source_type"] == "image"
        assert result[0]["metadata"]["image_format"] == "PNG"
        assert result[0]["metadata"]["ocr_engine"] == "tesseract"
        assert result[0]["metadata"]["ocr_lang"] == "chi_sim+eng+fra"


@pytest.mark.us25
def test_ocr_parser_jpg():
    """
    测试 ImageOCRParser 解析 JPG 图片。
    """
    parser = ImageOCRParser()
    image_bytes = _create_test_image("JPEG")
    
    with patch("pytesseract.image_to_string", return_value="JPG test content"):
        result = parser.parse(image_bytes)
        
        assert len(result) == 1
        assert result[0]["metadata"]["image_format"] == "JPEG"
        assert "JPG test content" in result[0]["content"]


@pytest.mark.us25
def test_ocr_parser_webp():
    """
    测试 ImageOCRParser 解析 WEBP 图片。
    """
    parser = ImageOCRParser()
    image_bytes = _create_test_image("WEBP")
    
    with patch("pytesseract.image_to_string", return_value="WEBP test content"):
        result = parser.parse(image_bytes)
        
        assert len(result) == 1
        assert result[0]["metadata"]["image_format"] == "WEBP"
        assert "WEBP test content" in result[0]["content"]


@pytest.mark.us25
def test_ocr_parser_image_metadata():
    """
    测试 ImageOCRParser 返回的图片元数据是否正确。
    """
    parser = ImageOCRParser()
    image_bytes = _create_test_image("PNG", size=(1920, 1080))
    
    with patch("pytesseract.image_to_string", return_value="Test"):
        result = parser.parse(image_bytes)
        
        metadata = result[0]["metadata"]
        assert metadata["image_width"] == 1920
        assert metadata["image_height"] == 1080
        assert "grayscale" in metadata["preprocessing_applied"]
        assert "denoise" in metadata["preprocessing_applied"]
        assert "contrast_enhancement" in metadata["preprocessing_applied"]


@pytest.mark.us25
def test_ocr_parser_ocr_failure():
    """
    测试 OCR 失败时的降级处理。
    """
    parser = ImageOCRParser()
    image_bytes = _create_test_image("PNG")
    
    with patch("pytesseract.image_to_string", side_effect=Exception("Tesseract not found")):
        result = parser.parse(image_bytes)
        
        assert len(result) == 1
        assert result[0]["content"] == ""  # OCR 失败返回空文本
        assert "ocr_error" in result[0]["metadata"]
        assert "Tesseract not found" in result[0]["metadata"]["ocr_error"]


@pytest.mark.us25
def test_ocr_parser_invalid_image():
    """
    测试传入无效图片数据时的错误处理。
    """
    parser = ImageOCRParser()
    
    with pytest.raises(ValueError, match="无法解析图片文件"):
        parser.parse(b"this is not an image file")


@pytest.mark.us25
def test_ocr_parser_custom_tesseract_path():
    """
    测试自定义 Tesseract 路径配置。
    """
    parser = ImageOCRParser(tesseract_cmd=r"C:\custom\tesseract.exe")
    image_bytes = _create_test_image("PNG")
    
    with patch("pytesseract.image_to_string", return_value="Custom path test"):
        with patch("pytesseract.pytesseract.tesseract_cmd", new_callable=MagicMock):
            result = parser.parse(image_bytes)
            # 验证路径被设置
            assert parser._tesseract_cmd == r"C:\custom\tesseract.exe"
            assert result[0]["char_count"] > 0


@pytest.mark.us25
def test_ocr_parser_get_tesseract_cache():
    """
    测试 _get_tesseract 的缓存分支（第 46 行）。
    第二次调用应直接返回缓存的 pytesseract 实例。
    """
    parser = ImageOCRParser()
    # 第一次调用会导入并缓存
    with patch("pytesseract.image_to_string", return_value="first call"):
        parser.parse(_create_test_image("PNG"))
    
    # 第二次调用应走缓存分支（self._pytesseract is not None）
    with patch("pytesseract.image_to_string", return_value="second call"):
        result = parser.parse(_create_test_image("PNG"))
        assert "second call" in result[0]["content"]
