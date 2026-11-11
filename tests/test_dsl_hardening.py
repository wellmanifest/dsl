"""Regression tests for dsl_check finite JSON, depth, regular-file, and unhashable guards."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import dsl_check


class DslHardeningTest(unittest.TestCase):
    def test_strict_json_loads_rejects_nan_infinity_overflow_and_deep_nesting(
        self,
    ) -> None:
        for invalid in (
            '{"x": NaN}',
            '{"x": Infinity}',
            '{"x": -Infinity}',
            '{"x": 1e999}',
            "[" * 80 + "1" + "]" * 80,
        ):
            with self.subTest(payload=invalid[:32]), self.assertRaises(ValueError):
                dsl_check.strict_json_loads(invalid)

    def test_unique_and_check_object_handle_nan_and_non_string_keys(self) -> None:
        self.assertFalse(dsl_check.unique([float("nan"), 1]))
        report = dsl_check.Report()
        self.assertIsNone(
            dsl_check.check_object(
                {1: "bad"},
                {"schema"},
                {"schema"},
                "manifest",
                report,
                Path("dsl-manifest.json"),
            )
        )
        self.assertTrue(report.has_code("DSL-MANIFEST-001"))

    def test_unhashable_enums_and_malformed_levels_record_findings_without_type_error(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="dsl-hardening-") as tmp:
            root = Path(tmp)
            source = root / "CONTRIBUTING.md"
            source.write_text(
                "```dsl\nDOCUMENT EXAMPLE\nVERSION 1\n```\n", encoding="utf-8"
            )
            doc_digests = dsl_check.write_example_help_pages(root)
            doc = dsl_check.valid_example_document(
                dsl_check.sha256(source), doc_digests
            )
            doc["status"] = ["unhashable"]
            doc["owners"][0]["kind"] = {"bad": 1}
            doc["source"]["canonical"] = ["bad"]
            doc["artifacts"][0]["role"] = ["bad"]
            doc["projections"] = [
                {
                    "name": "p",
                    "mediaType": "text/plain",
                    "direction": ["bad"],
                    "lossless": True,
                }
            ]
            doc["lifecycle"]["stability"] = {"bad": 1}
            doc["semantics"]["effectModel"] = ["bad"]
            doc["semantics"]["unknownPolicy"] = {"bad": 1}
            doc["llm"]["mode"] = ["bad"]
            doc["llm"]["naturalLanguage"] = ["bad"]
            doc["llm"]["decisionProtocol"] = {"bad": 1}
            doc["documentation"]["vocabularyKind"] = ["bad"]
            doc["publicationPolicy"]["declaredTier"] = {"bad": 1}
            doc["conformance"]["levels"] = 123
            doc["mappings"] = [
                {"standard": "s", "version": "1.0.0", "relation": ["bad"]}
            ]

            manifest_path = root / dsl_check.MANIFEST_NAME
            manifest_path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
            report, _ = dsl_check.validate_manifest(manifest_path, root)
            self.assertTrue(report.failed)
            self.assertTrue(report.has_code("DSL-MANIFEST-001"))
            self.assertTrue(report.has_code("DSL-LLM-001"))
            self.assertTrue(report.has_code("DSL-PUBLICATION-001"))

    def test_findings_gate_handles_unhashable_fields_and_non_dict_resolution(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="dsl-findings-hardening-") as tmp:
            root = Path(tmp)
            source = root / "CONTRIBUTING.md"
            source.write_text(
                "```dsl\nDOCUMENT EXAMPLE\nVERSION 1\n```\n", encoding="utf-8"
            )
            doc_digests = dsl_check.write_example_help_pages(root)
            doc = dsl_check.valid_example_document(
                dsl_check.sha256(source), doc_digests
            )
            manifest_path = root / dsl_check.MANIFEST_NAME
            manifest_path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
            _, manifest = dsl_check.validate_manifest(manifest_path, root)
            self.assertIsNotNone(manifest)
            assert manifest is not None

            revision = "b" * 40
            findings_path = root / "findings.json"
            findings_doc = {
                "schema": dsl_check.FINDINGS_SCHEMA,
                "producer": {
                    "id": "subactor.twin-probes",
                    "version": "1.0.0",
                    "adapter": "wellmanifest-twin-probes/v1",
                },
                "subject": {
                    "repository": "https://example.test/repository",
                    "revision": revision,
                    "manifest": dsl_check.MANIFEST_NAME,
                },
                "evaluable": True,
                "failureReason": None,
                "findings": [
                    {
                        "id": "security.example.002",
                        "code": "SECURITY-001",
                        "severity": ["unhashable"],
                        "security": True,
                        "path": "CONTRIBUTING.md",
                        "helpPath": "docs/CRITICAL/SECURITY-001.md",
                        "message": "Malformed finding with non-dict resolution",
                        "resolution": "not-an-object",
                        "evidence": [
                            {
                                "kind": {"bad": 1},
                                "path": "CONTRIBUTING.md",
                                "digest": dsl_check.sha256(source),
                            }
                        ],
                    }
                ],
            }
            findings_path.write_text(
                json.dumps(findings_doc, indent=2) + "\n", encoding="utf-8"
            )
            gate_report = dsl_check.gate_findings(
                root, [manifest], [findings_path], revision
            )
            self.assertTrue(gate_report.has_code("DSL-FINDINGS-001"))
            self.assertTrue(gate_report.has_code("DSL-CRITICAL-001"))

    def test_fifo_manifest_and_sha256_fail_fast_without_blocking(self) -> None:
        if not hasattr(os, "mkfifo"):
            return
        with tempfile.TemporaryDirectory(prefix="dsl-fifo-") as tmp:
            root = Path(tmp)
            fifo_path = root / dsl_check.MANIFEST_NAME
            os.mkfifo(fifo_path)
            report, validated = dsl_check.validate_manifest(fifo_path, root)
            self.assertIsNone(validated)
            self.assertTrue(report.has_code("DSL-MANIFEST-001"))
            with self.assertRaises(OSError):
                dsl_check.sha256(fifo_path)


if __name__ == "__main__":
    unittest.main()
