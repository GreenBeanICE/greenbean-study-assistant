"""
图片 OCR 解析器，用于解析 JPG/JPEG/PNG/WEBP 格式图片，
通过 Tesseract OCR 引擎提取文本内容。
支持中、英、法三语混合识别。

输出统一的 PageIndex 结构，与 PDFParser 保持一致。
"""
import io
from typing import List, Dict, Any, Optional
from PIL import Image

from app.parsers.image_preprocessor import ImagePreprocessor
from app.utils.text_utils import clean_text


# Tesseract OCR 引擎路径配置
# 如果 Tesseract 安装在非默认路径，需要在此配置
TESSERACT_CMD = None  # 例如: r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# OCR 语言配置：中英法三语
OCR_LANG = "chi_sim+eng+fra"


class ImageOCRParser:
    """
    图片 OCR 解析器，支持 JPG/JPEG/PNG/WEBP 格式。
    使用 Tesseract OCR 引擎进行文本识别。
    """

    def __init__(self, lang: str = OCR_LANG, tesseract_cmd: Optional[str] = TESSERACT_CMD):
        """
        初始化 OCR 解析器。
        
        :param lang: Tesseract 语言参数，默认中英法三语
        :param tesseract_cmd: Tesseract 可执行文件路径
        """
        self.lang = lang
        self._tesseract_cmd = tesseract_cmd
        self._pytesseract = None  # 延迟导入

    def _get_tesseract(self):
        """
        延迟导入 pytesseract 并配置路径。
        """
        if self._pytesseract is not None:
            return self._pytesseract
        
        import pytesseract
        if self._tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self._tesseract_cmd
        self._pytesseract = pytesseract
        return self._pytesseract

    def parse(self, file_content: bytes) -> List[Dict[str, Any]]:
        """
        解析图片字节流，通过 OCR 提取文本并构建 PageIndex 结构。
        
        单张图片视为 1 个 PageIndex 节点。
        
        :param file_content: 前端上传文件的二进制数据
        :return: 包含文本和元数据的列表（单元素列表）
        :raises ValueError: 图片格式不支持或 OCR 失败
        """
        # Step 1: 打开图片
        try:
            image = Image.open(io.BytesIO(file_content))
            image_format = image.format or "UNKNOWN"
            image_width, image_height = image.size
        except Exception as e:
            raise ValueError(f"无法解析图片文件: {e}")
        
        # Step 2: 图片预处理
        preprocessor = ImagePreprocessor()
        preprocessing_config = {
            "apply_grayscale": True,
            "apply_binarization": False,
            "apply_denoise": True,
            "apply_contrast": True,
            "apply_deskew": False,
        }
        processed_image = preprocessor.preprocess(image, **preprocessing_config)
        
        # Step 3: OCR 识别
        try:
            pytesseract = self._get_tesseract()
            text = pytesseract.image_to_string(
                processed_image,
                lang=self.lang,
                config="--psm 6"  # 假设为统一的文本块
            )
            text = clean_text(text)
        except Exception as e:
            # 如果 OCR 失败，返回空文本但保留元数据
            text = ""
            ocr_error = str(e)
        else:
            ocr_error = None
        
        # Step 4: 构造 PageIndex 节点
        page_node = {
            "page_number": 1,
            "content": text,
            "char_count": len(text),
            "metadata": {
                "source_type": "image",
                "image_format": image_format,
                "image_width": image_width,
                "image_height": image_height,
                "ocr_engine": "tesseract",
                "ocr_lang": self.lang,
                "preprocessing_applied": preprocessor.get_preprocessing_steps(preprocessing_config),
            }
        }
        
        # 如果 OCR 出错，记录错误信息
        if ocr_error:
            page_node["metadata"]["ocr_error"] = ocr_error
        
        return [page_node]
