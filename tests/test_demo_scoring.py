"""Exercise browser-style uploads, demo boundaries, and preserved engine output."""

import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from app import create_app
from config.settings import BASE_DIR, Config
from services.demo_scoring_service import apply_demo_score, match_demo_source


class TestDemoScoring(unittest.TestCase):
    def test_boundaries_and_preserved_evidence(self):
        for raw in (0, 15, 25, 26, 49, 50, 100):
            for source in ("fake", "original", "other"):
                with self.subTest(raw=raw, source=source):
                    original = {"risk_score": raw, "evidence": {"example": "unchanged"}}
                    result = apply_demo_score(original, source)
                    if source == "fake":
                        self.assertGreater(result["risk_score"], 25)
                    else:
                        self.assertLessEqual(result["risk_score"], 15)
                    self.assertEqual(result["computed_analysis"], original)
                    self.assertEqual(original["risk_score"], raw)
                    self.assertEqual(result["risk_level"], result["risk_tier"])
                    self.assertIn("DEMO RESULT", result["recommendation"])
        raw = {"risk_score": 85}
        self.assertIs(apply_demo_score(raw, None), raw)

    def test_missing_dataset_is_not_silently_classified_low(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                match_demo_source("unused.png", directory)

    def test_new_images_moves_and_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "fake").mkdir()
            (root / "original").mkdir()
            uploaded = root / "upload.png"
            Image.new("RGB", (4, 4), "red").save(uploaded)
            self.assertEqual(match_demo_source(uploaded, root), "other")
            original = root / "original" / "same.png"
            original.write_bytes(uploaded.read_bytes())
            self.assertEqual(match_demo_source(uploaded, root), "original")
            fake = root / "fake" / "same.png"
            original.rename(fake)
            self.assertEqual(match_demo_source(uploaded, root), "fake")
            original.write_bytes(uploaded.read_bytes())
            self.assertEqual(match_demo_source(uploaded, root), "fake")


class TestDemoUploadRoute(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app = create_app(Config)
        self.app.config.update(TESTING=True, UPLOAD_FOLDER=self.temp.name, DEMO_FOLDER_SCORING=True)
        self.client = self.app.test_client()
        for target, value in (
            ("routes.scan_routes.check_tesseract_available", False),
            ("services.analysis_orchestrator.check_tesseract_available", False),
            ("services.analysis_orchestrator.ImageQualityAssessmentService.evaluate_image", None),
            ("routes.scan_routes.db_repository.save_scan_audit", None),
        ):
            mocked = patch(target, return_value=value)
            handle = mocked.start()
            self.addCleanup(mocked.stop)
            if target.endswith("save_scan_audit"):
                self.audit = handle

    def upload(self, content, filename="renamed.png", **fields):
        response = self.client.post("/api/scan", data={
            "label_image": (io.BytesIO(content), filename), **fields,
        }, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200, response.get_json())
        return response.get_json()

    def test_all_project_images_with_browser_basenames(self):
        for source in ("fake", "original"):
            images = list((BASE_DIR / "ft_project_images" / source).glob("*"))
            self.assertTrue(images)
            for path in images:
                with self.subTest(image=path.name, source=source):
                    result = self.upload(path.read_bytes(), "renamed" + path.suffix)
                    risk = result["counterfeit_risk"]
                    self.assertEqual(risk["demo_source"], source)
                    if source == "fake":
                        self.assertGreater(risk["risk_score"], 25)
                    else:
                        self.assertLessEqual(risk["risk_score"], 15)
                    report = result["unified_report"]["counterfeit_analysis"]
                    self.assertEqual(report["risk_score"], risk["risk_score"])
                    self.assertEqual(report["computed_analysis"], risk["computed_analysis"])
                    saved = self.audit.call_args.args[0]
                    self.assertEqual(saved["report"], result["unified_report"])

    def test_unknown_file_and_spoofed_folder_are_low_demo_only(self):
        image = io.BytesIO()
        Image.new("RGB", (8, 8), "purple").save(image, format="PNG")
        result = self.upload(image.getvalue(), r"C:\fakepath\fake\photo.png", image_source_type="fake")
        self.assertEqual(result["counterfeit_risk"]["demo_source"], "other")
        self.assertLessEqual(result["counterfeit_risk"]["risk_score"], 15)

    def test_disabled_demo_preserves_engine_result(self):
        path = next((BASE_DIR / "ft_project_images" / "original").glob("*.jpg"))
        self.app.config["DEMO_FOLDER_SCORING"] = False
        engine_result = {
            "risk_score": 80.0, "risk_level": "HIGH", "risk_tier": "HIGH",
            "identified_product": {"brand": None}, "recommendation": "Engine finding",
        }
        with patch("services.analysis_orchestrator.FoodCounterfeitRiskEngine.evaluate_risk", return_value=engine_result):
            result = self.upload(path.read_bytes(), path.name)
        self.assertEqual(result["counterfeit_risk"], engine_result)

    def test_manual_text_and_presets_do_not_use_demo_scoring(self):
        for data in ({"manual_text": "Example food label"}, {"sample_id": "compliant"}):
            response = self.client.post("/api/scan", data=data)
            self.assertEqual(response.status_code, 200)
            self.assertNotIn("scoring_mode", response.get_json()["counterfeit_risk"])


if __name__ == "__main__":
    unittest.main()
