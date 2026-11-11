"""Regression tests for dsl_check finite JSON, depth, regular-file, and unhashable guards."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import dsl_check
import dsl_io
import dsl_primitives


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

    def test_in_repo_symlink_manifest_artifact_help_and_findings_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="dsl-inrepo-symlink-") as tmp:
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

            inrepo_manifest_link = root / "alias-manifest.json"
            inrepo_manifest_link.symlink_to(manifest_path)
            rep_direct, val_direct = dsl_check.validate_manifest(
                inrepo_manifest_link, root
            )
            self.assertIsNone(val_direct)
            self.assertTrue(rep_direct.has_code("DSL-PATH-001"))

            nested_pkg = root / "packages" / "linked"
            nested_pkg.mkdir(parents=True)
            (nested_pkg / dsl_check.MANIFEST_NAME).symlink_to(manifest_path)
            rep_discover, _ = dsl_check.load_targets(["."], root)
            self.assertTrue(rep_discover.has_code("DSL-PATH-001"))
            (nested_pkg / dsl_check.MANIFEST_NAME).unlink()

            cmd_page = root / "docs" / "DOCUMENT.md"
            backup = root / "docs" / "DOCUMENT.orig"
            cmd_page.rename(backup)
            cmd_page.symlink_to("VERSION.md")
            rep_help, _ = dsl_check.validate_manifest(manifest_path, root)
            self.assertTrue(rep_help.has_code("DSL-PATH-001"))
            cmd_page.unlink()
            backup.rename(cmd_page)

            _, valid_manifest = dsl_check.validate_manifest(manifest_path, root)
            self.assertIsNotNone(valid_manifest)
            assert valid_manifest is not None

            real_reports = root / "real_reports"
            real_reports.mkdir()
            findings_file = real_reports / "findings.json"
            findings_file.write_text("{}\n", encoding="utf-8")
            linked_reports = root / "reports_link"
            linked_reports.symlink_to(real_reports)
            rep_findings, binding = dsl_check.validate_findings_report(
                linked_reports / "findings.json",
                root,
                {dsl_check.MANIFEST_NAME: valid_manifest},
                "a" * 40,
            )
            self.assertIsNone(binding)
            self.assertTrue(rep_findings.has_code("DSL-FINDINGS-001"))

    def test_safe_relative_uri_regex_anchors_and_inode_swap_guards(self) -> None:
        report = dsl_check.Report()
        for bad_rel in (
            "./CONTRIBUTING.md",
            "docs//DOCUMENT.md",
            "docs/./DOCUMENT.md",
            "docs/",
            "docs/DOCUMENT\x7f.md",
        ):
            self.assertIsNone(
                dsl_check.safe_relative(
                    bad_rel, "path", report, Path("dsl-manifest.json")
                )
            )

        for bad_uri in (
            "http:///missing-host",
            "schema:///missing-host",
            "https://example.test/../escape",
            "urn:example:../escape",
            "https://example.test/del\x7f",
        ):
            self.assertFalse(dsl_check.uri_is_valid(bad_uri), bad_uri)
        self.assertTrue(dsl_check.uri_is_valid("urn:ietf:rfc:3986"))
        self.assertIsNone(dsl_check.REVISION.match("a" * 40 + "\n"))
        self.assertIsNone(dsl_check.SEMVER.match("1.0.0\n"))

        with self.assertRaises(TypeError):
            dsl_primitives._enforce_json_depth({1: "bad"})
        with self.assertRaises(ValueError):
            dsl_primitives._enforce_json_depth({"x": float("inf")})

        with tempfile.TemporaryDirectory(prefix="dsl-inode-") as tmp:
            sample = Path(tmp) / "sample.txt"
            sample.write_text("ok\n", encoding="utf-8")
            real_fstat = os.fstat

            def swapped_fstat(fd: int) -> os.stat_result:
                st = real_fstat(fd)
                return os.stat_result(
                    (
                        st.st_mode,
                        st.st_ino + 1,
                        st.st_dev,
                        st.st_nlink,
                        st.st_uid,
                        st.st_gid,
                        st.st_size,
                        st.st_atime,
                        st.st_mtime,
                        st.st_ctime,
                    )
                )

            with (
                mock.patch.object(dsl_io.os, "fstat", side_effect=swapped_fstat),
                self.assertRaises(OSError),
            ):
                dsl_primitives.read_regular_bytes(sample)

    def test_json_int_overflow_surrogates_and_is_string_guards(self) -> None:
        for bad_json in (
            '{"x": ' + "9" * 500 + "}",
            '{"x": -' + "9" * 500 + "}",
            '{"x": ' + "9" * 5000 + "}",
            r'{"x": "\ud800"}',
            r'{"\udfff": 1}',
            '{"x": "\ud800"}',
        ):
            with self.subTest(payload=bad_json[:24]), self.assertRaises(ValueError):
                dsl_check.strict_json_loads(bad_json)

        for bad_obj in (
            {"x": 10**400},
            {"x": -(10**400)},
            {"x": "\ud800"},
            {"\ud800": "v"},
            ["\udfff"],
            "\ud800",
        ):
            with self.assertRaises(ValueError):
                dsl_primitives._enforce_json_depth(bad_obj)

        self.assertFalse(dsl_check.is_string("\ud800"))
        self.assertTrue(dsl_check.is_string("valid-utf8"))

    def test_ancestor_symlinks_max_bytes_bounds_and_uri_segments(self) -> None:
        for bad_uri in (
            "https://[::1",
            "https://./escape",
            "https://../escape",
            "https://example.test/./dot",
            "urn:example:",
            "urn:example::v1",
            "urn:example:.:v1",
            "https://example.test/\ud800",
        ):
            self.assertFalse(dsl_check.uri_is_valid(bad_uri), bad_uri)

        for pattern, valid_sample in (
            (dsl_check.STABLE_ID, "example.id"),
            (dsl_check.DIGEST, "sha256:" + "a" * 64),
            (dsl_check.REVISION, "a" * 40),
            (dsl_primitives.URI_SCHEME, "https"),
        ):
            self.assertIsNotNone(pattern.fullmatch(valid_sample))
            self.assertIsNone(pattern.match("\n" + valid_sample))
            self.assertIsNone(pattern.match(valid_sample + "\n"))

        with tempfile.TemporaryDirectory(prefix="dsl-anc-sym-") as tmp:
            base = Path(tmp)
            real_dir = base / "real" / "nested"
            real_dir.mkdir(parents=True)
            sample = real_dir / "payload.json"
            sample.write_bytes(b"x" * 200)

            for bad_limit in (0, -5, True, False):
                with self.assertRaises(ValueError):
                    dsl_primitives.read_regular_bytes(sample, max_bytes=bad_limit)  # type: ignore[arg-type]

            sym_dir = base / "sym_dir"
            sym_dir.symlink_to(base / "real")
            deep_sym = sym_dir / "nested" / "payload.json"
            with self.assertRaises(OSError):
                dsl_primitives.read_regular_bytes(deep_sym)
            with self.assertRaises(OSError):
                dsl_check.sha256(deep_sym)

            prev_cwd = Path.cwd()
            sibling = base / "sibling"
            sibling.mkdir()
            try:
                os.chdir(base)
                for rel_sym in (
                    Path("sym_dir/nested/payload.json"),
                    Path("sym_dir/../real/nested/payload.json"),
                ):
                    with self.assertRaises(OSError):
                        dsl_primitives.read_regular_bytes(rel_sym)
                os.chdir(sibling)
                with self.assertRaises(OSError):
                    dsl_primitives.read_regular_bytes(
                        Path("../sym_dir/nested/payload.json")
                    )
            finally:
                os.chdir(prev_cwd)

            unnorm_abs = Path(f"{base}/sym_dir/../real/nested/payload.json")
            with self.assertRaises(OSError):
                dsl_primitives.read_regular_bytes(unnorm_abs)

            read_sizes: list[int] = []
            real_read = os.read

            def spy_read(fd: int, length: int) -> bytes:
                read_sizes.append(length)
                return real_read(fd, length)

            small = real_dir / "small.txt"
            small.write_bytes(b"hello")
            with mock.patch.object(dsl_io.os, "read", side_effect=spy_read):
                self.assertEqual(
                    dsl_primitives.read_regular_bytes(small, max_bytes=32), b"hello"
                )
            self.assertTrue(all(size <= 33 for size in read_sizes))

    def test_control_chars_single_line_fields_int_digits_and_module_budget(
        self,
    ) -> None:
        for bad_int in ('{"x": ' + "9" * 401 + "}", '{"x": -' + "1" + "0" * 400 + "}"):
            with self.assertRaises(ValueError):
                dsl_check.strict_json_loads(bad_int)
        self.assertEqual(dsl_io._parse_bounded_int("9" * 400), 10**400 - 1)
        for ctrl in ("\x00", "\x1b", "\r", "\x7f"):
            self.assertFalse(dsl_check.is_string(f"bad{ctrl}text"))
        self.assertTrue(dsl_check.is_string("multi\nline\ttext"))
        for single_bad in ("line1\nline2", "col1\tcol2", "   ", "bad\x7f"):
            self.assertFalse(dsl_primitives.is_single_line_string(single_bad))

        with tempfile.TemporaryDirectory(prefix="dsl-ctrl-") as tmp:
            root = Path(tmp)
            source = root / "CONTRIBUTING.md"
            source.write_text(
                "```dsl\nDOCUMENT EXAMPLE\nVERSION 1\n```\n", encoding="utf-8"
            )
            digests = dsl_check.write_example_help_pages(root)
            doc = dsl_check.valid_example_document(dsl_check.sha256(source), digests)
            doc["owners"][0]["id"] = "owner\ninjected"
            doc["source"]["repository"] = "https://example.test/repo\nextra"
            doc["source"]["declaredVersion"] = "1\t2"
            doc["conformance"]["commands"] = ["python3 check.py\necho bad"]
            doc["mappings"] = [
                {"standard": "std\nbad", "version": "1.0.0\x7f", "relation": "maps-to"}
            ]
            manifest_path = root / dsl_check.MANIFEST_NAME
            manifest_path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
            rep, _ = dsl_check.validate_manifest(manifest_path, root)
            self.assertGreaterEqual(
                sum(item.code == "DSL-MANIFEST-001" for item in rep.findings), 5
            )

        for folder in (SRC, ROOT / "tests"):
            for py_file in sorted(folder.glob("*.py")):
                lines = len(py_file.read_text(encoding="utf-8").splitlines())
                self.assertLess(lines, 500, f"{py_file} has {lines} lines")


if __name__ == "__main__":
    unittest.main()
