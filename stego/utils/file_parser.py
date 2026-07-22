import os
from pathlib import Path


class FileParserError(Exception):
    """Custom exception raised when file parsing fails or dependencies are missing."""
    pass


def extract_text_from_file(file_path: Path) -> str:
    """Extracts text from a given file path supporting txt, docx, and pdf formats.

    Raises FileParserError if the file type is unsupported or parser library is missing.
    """
    if not os.path.exists(file_path):
        raise FileParserError(f"Файл не найден: {file_path}")

    ext = file_path.suffix.lower()

    if ext == ".txt":
        # Try UTF-8 first, fallback to CP1251
        for encoding in ("utf-8", "cp1251", "latin-1"):
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        raise FileParserError("Не удалось прочитать txt файл. Неподдерживаемая кодировка.")

    elif ext == ".docx":
        try:
            import docx
        except ImportError:
            raise FileParserError(
                "Библиотека `python-docx` не установлена.\n"
                "Для извлечения текста из Word файлов установите её:\n"
                "`pip install python-docx`"
            )
        try:
            doc = docx.Document(str(file_path))
            text = [para.text for para in doc.paragraphs]
            return "\n".join(text)
        except Exception as e:
            raise FileParserError(f"Ошибка при чтении Word файла: {e}")

    elif ext == ".pdf":
        try:
            import pypdf
        except ImportError:
            try:
                import PyPDF2 as pypdf
            except ImportError:
                raise FileParserError(
                    "Библиотека `pypdf` не установлена.\n"
                    "Для извлечения текста из PDF файлов установите её:\n"
                    "`pip install pypdf`"
                )
        try:
            reader = pypdf.PdfReader(str(file_path))
            text = []
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text.append(extracted)
            return "\n".join(text)
        except Exception as e:
            raise FileParserError(f"Ошибка при чтении PDF файла: {e}")

    else:
        raise FileParserError(
            f"Неподдерживаемый формат для извлечения текста: {ext}.\n"
            "Доступные форматы: .txt, .pdf, .docx"
        )
