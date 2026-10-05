from pathlib import Path

APP_JS = Path(__file__).parent.parent / "app" / "static" / "js" / "app.js"


def _read_app_js():
    return APP_JS.read_text()


class TestClipboardPaste:
    def test_paste_listener_registered(self):
        content = _read_app_js()
        assert "addEventListener('paste', handleImagePaste)" in content

    def test_paste_handler_reuses_existing_pipeline(self):
        content = _read_app_js()
        assert "new DataTransfer()" in content
        assert "imageInput.files = dataTransfer.files" in content
        assert "previewImage(imageInput)" in content

    def test_paste_handler_only_accepts_image_data(self):
        content = _read_app_js()
        assert "getClipboardImageFile" in content
        assert "indexOf('image/') === 0" in content

    def test_paste_handler_ignores_missing_image(self):
        content = _read_app_js()
        assert "if (!file) return;" in content

    def test_paste_handler_requires_report_form(self):
        content = _read_app_js()
        assert "document.getElementById('imageInput')" in content
        assert "document.getElementById('filePreview')" in content

    def test_pasted_file_gets_usable_extension(self):
        content = _read_app_js()
        assert "normalizePastedFile" in content
        assert "PASTED_IMAGE_EXTENSIONS" in content
