"""Maintainer-only verification of the actual prebuilt package in isolated storage.

No native plugin registration, network, account login, model calls, or real-user
data is used. Captured business bodies stay in memory; evidence contains only
bounded statuses and size/time measurements. Never run on an existing workspace.
"""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

try:
    from scripts import work_distribution_runtime as runtime
except ModuleNotFoundError:
    import work_distribution_runtime as runtime

ACCOUNT = "1" * 64
OTHER_ACCOUNT = "2" * 64
SCOPE = "test:distribution-verification"
TEXT_VALUES = "SYNTHETIC_PRIVATE_VALUES：合成验收资料，重视诚实与自主。"
TEXT_FRIENDS = "SYNTHETIC_PRIVATE_FRIENDS：合成验收资料，偏好共同阅读与安静交流。"
TEXT_CORRECTED = "SYNTHETIC_PRIVATE_CORRECTION：本人修正的合成偏好，喜欢一起参观展览。"


class VerificationError(ValueError):
    """Fixed diagnostic code only, never a captured child-process body."""


def require(condition, code):
    if not condition:
        raise VerificationError(code)


def clean_environment():
    require(
        os.name == "nt" and platform.machine().lower() in {"amd64", "x86_64"},
        "supported_windows_x64_required",
    )
    names = (
        "SystemRoot",
        "WINDIR",
        "TEMP",
        "TMP",
        "USERPROFILE",
        "LOCALAPPDATA",
        "APPDATA",
        "HOMEDRIVE",
        "HOMEPATH",
        "COMSPEC",
        "PATHEXT",
        "NUMBER_OF_PROCESSORS",
        "PROCESSOR_ARCHITECTURE",
        "PROGRAMDATA",
    )
    environment = {name: os.environ[name] for name in names if name in os.environ}
    system = Path(environment["SystemRoot"])
    environment["PATH"] = os.pathsep.join(str(path) for path in (system / "System32", system))
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    for binary in ("python.exe", "python3.exe", "git.exe", "node.exe", "npm.cmd"):
        require(
            shutil.which(binary, path=environment["PATH"]) is None,
            "developer_tool_present_on_restricted_path",
        )
    return environment


class Recorder:
    def __init__(self, home, environment):
        self.home = home
        self.environment = environment
        self.steps = []
        self.last_step = None

    def call(self, label, executable, arguments, body=None, expected_error=None):
        require(re.fullmatch(r"[a-z_]{1,60}", label) is not None, "invalid_step_label")
        self.last_step = label
        raw = runtime.encoded(body) if body is not None else b""
        start = time.perf_counter()
        completed = subprocess.run(
            [str(executable), *map(str, arguments)],
            input=raw,
            capture_output=True,
            env=self.environment,
            cwd=self.home.parent,
            timeout=60,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        duration = round((time.perf_counter() - start) * 1000, 3)
        # No child stdout/stderr is logged; even an invalid body stays private.
        require(
            len(completed.stdout) <= 2_000_000 and len(completed.stderr) <= 100_000,
            "captured_output_limit",
        )
        try:
            text = completed.stdout.decode("utf-8", errors="strict")
            result = runtime._json(text)
        except (ValueError, UnicodeError):
            raise VerificationError("invalid_child_result") from None
        passed = (
            completed.returncode == 0 and result.get("ok") is True
            if expected_error is None
            else completed.returncode != 0
            and result.get("ok") is False
            and result.get("error", {}).get("code") == expected_error
        )
        self.steps.append(
            {
                "step": label,
                "passed": passed,
                "elapsed_ms": duration,
                "input_utf8_bytes": len(raw),
                "output_utf8_bytes": len(completed.stdout),
                "output_unicode_characters": len(text),
                "stderr_utf8_bytes": len(completed.stderr),
                "expected_refusal": expected_error is not None,
            }
        )
        require(passed, "unexpected_child_result")
        return result

    def business(
        self,
        label,
        executable,
        slot,
        operation,
        body,
        *,
        account=ACCOUNT,
        scope=SCOPE,
        expected_error=None,
    ):
        return self.call(
            label,
            executable,
            [
                "run",
                "--home",
                self.home,
                "--slot",
                slot,
                "--account-key",
                account,
                "--scope",
                scope,
                operation,
                "--input-json",
                "-",
            ],
            body,
            expected_error,
        )


def installed_executable(home):
    pointer = runtime._json(runtime.read_bytes(home / "active.json", 4096))
    require(
        re.fullmatch(runtime.RELEASE, pointer.get("release", "")) is not None,
        "invalid_installed_pointer",
    )
    executable = runtime.check_path(home / "releases" / pointer["release"] / runtime.EXECUTABLE)
    require(executable.is_file(), "installed_executable_missing")
    return executable


def private_claim(topic, text, claim_id=None):
    value = {
        "topic": topic,
        "text": text,
        "source": {"source_type": "self_report", "reference": "synthetic-package-verification"},
        "confirmation": "corrected" if claim_id else "confirmed",
        "uncertainty": "Synthetic local verification; no claim about a real person.",
    }
    if claim_id:
        value["id"] = claim_id
    return {"action": "upsert", "claim": value}


def synthetic_peer_summary():
    return {
        "schema_version": "2.0",
        "mode": "dating",
        "summary_id": "a" * 32,
        "version": 1,
        "expires_at": (datetime.now(UTC) + timedelta(days=2)).replace(microsecond=0).isoformat(),
        "alias": "Synthetic Cedar",
        "age_band": "25-34",
        "city": "Toronto",
        "areas": ["Toronto"],
        "relationship_goal": "long_term",
        "accepted_goals": ["long_term"],
        "accepted_age_bands": ["25-34"],
        "values": ["honesty"],
        "life_directions": ["still_exploring"],
        "communication_preferences": ["reflective"],
        "interests": ["reading"],
        "preferences": ["honesty"],
        "visibility": "participants",
        "discoverable": True,
    }


def profile_fingerprint(location):
    """Compare only the verifier's own synthetic profile files; never export hashes."""
    path = runtime.private_location(location / "profile")
    require(path.is_dir(), "synthetic_profile_missing")
    return {
        file.relative_to(path).as_posix(): runtime.digest(runtime.read_bytes(file, 2_000_000))
        for file in path.rglob("*")
        if file.is_file()
    }


def verify_interrupted_install(package, workspace, recorder):
    """Terminate only this owned installer while its reserved staging is visible."""
    root = runtime.mkdir(workspace / "interruption-check")
    home = root / "portable"
    retained = runtime.mkdir(root / "accounts") / "synthetic-retention-marker.txt"
    marker = b"SYNTHETIC_INTERRUPTION_RETENTION_ONLY"
    retained.write_bytes(marker)
    executable = package / runtime.EXECUTABLE
    start = time.perf_counter()
    process = subprocess.Popen(
        [str(executable), "install", "--home", str(home), "--package", str(package)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=recorder.environment,
        cwd=root,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    observed = False
    terminated = False
    deadline = time.monotonic() + 15
    try:
        while process.poll() is None and time.monotonic() < deadline:
            releases = home / "releases"
            if releases.exists() and not (home / "active.json").exists():
                staging = [
                    path
                    for path in releases.iterdir()
                    if re.fullmatch(r"\.staging-[a-f0-9]{32}", path.name)
                ]
                # Detect actual file copy, not a synthetic marker or completed install.
                if any(path.is_dir() and any(path.iterdir()) for path in staging):
                    observed = True
                    if process.poll() is None:
                        process.terminate()
                        terminated = True
                    break
            time.sleep(0.02)
        output, errors = process.communicate(timeout=45)
    except subprocess.TimeoutExpired:
        # Still terminate only this exact owned Popen process; this path is not
        # credited as an observed mid-copy interruption.
        process.terminate()
        output, errors = process.communicate(timeout=10)
        terminated = False
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
    require(len(output) <= 2_000_000 and len(errors) <= 100_000, "captured_output_limit")
    interrupted = (
        observed and terminated and process.returncode != 0 and not (home / "active.json").exists()
    )
    recorder.steps.append(
        {
            "step": "actual_install_interruption",
            "passed": interrupted,
            "elapsed_ms": round((time.perf_counter() - start) * 1000, 3),
            "input_utf8_bytes": 0,
            "output_utf8_bytes": len(output),
            "output_unicode_characters": len(output.decode("utf-8", errors="replace")),
            "stderr_utf8_bytes": len(errors),
            "expected_refusal": True,
            "owned_process_terminated_during_observed_copy": interrupted,
        }
    )
    if not interrupted:
        return "not_checked_mid_copy_window_not_observed"
    recorder.call(
        "interrupted_install_retry",
        executable,
        [
            "install",
            "--home",
            home,
            "--package",
            package,
        ],
    )
    installed = installed_executable(home)
    recorder.call("interrupted_retry_doctor", installed, ["doctor", "--home", home])
    require(retained.read_bytes() == marker, "interrupted_retry_changed_synthetic_data")
    require(not list((home / "releases").glob(".staging-*")), "interrupted_staging_not_cleaned")
    recorder.call("interrupted_retry_uninstall", executable, ["uninstall", "--home", home])
    require(retained.read_bytes() == marker, "interrupted_cleanup_changed_synthetic_data")
    return "passed_owned_process_terminated_during_actual_copy_then_retry"


def verify(package, workspace=None):
    environment = clean_environment()
    package = runtime.check_path(package, directory=True).resolve(strict=True)
    release, checksum = runtime.manifest(package)
    workspace = runtime.private_location(
        workspace
        or (Path(environment["LOCALAPPDATA"]) / runtime.PRODUCT / "verification" / uuid4().hex)
    )
    require(
        not workspace.exists() or not any(workspace.iterdir()),
        "new_empty_verification_workspace_required",
    )
    workspace = runtime.mkdir(workspace)
    home = workspace / "portable"
    recorder = Recorder(home, environment)
    executable = package / runtime.EXECUTABLE
    checks = {}
    report = {
        "schema_version": 1,
        "product": runtime.PRODUCT,
        "version": release["version"],
        "channel": "controlled-preview",
        "scope": "isolated_local_synthetic_only",
        "manifest_sha256": checksum,
        "source_commit": release["source_commit"],
        "source_dirty": release["source_dirty"],
        "developer_tools_on_child_path": False,
        "model_calls": 0,
        "native_chatgpt": "not_checked",
        "remote_authentication": "not_checked",
        "two_independent_accounts": "not_checked",
        "real_upgrade_atomic_rollback": "unit_tests_only",
        "checks": checks,
        "steps": recorder.steps,
    }
    try:
        first = recorder.call(
            "first_install",
            executable,
            [
                "install",
                "--home",
                home,
                "--package",
                package,
                "--expected-manifest-sha256",
                checksum,
            ],
        )
        require(first.get("status") == "installed", "first_install_status_mismatch")
        installed = installed_executable(home)
        require(installed.parent.parent == home.resolve() / "releases", "installed_path_mismatch")
        repeated = recorder.call(
            "repeat_install",
            executable,
            [
                "install",
                "--home",
                home,
                "--package",
                package,
            ],
        )
        require(repeated.get("status") == "already_installed", "repeat_install_status_mismatch")
        checks["first_and_repeat_install"] = "passed_actual_package"
        recorder.call("doctor", installed, ["doctor", "--home", home])
        created = recorder.call(
            "synthetic_slot",
            installed,
            [
                "slot-create",
                "--home",
                home,
                "--account-key",
                ACCOUNT,
                "--scope",
                SCOPE,
                "--confirmed",
            ],
        )
        slot = created.get("slot", "")
        require(re.fullmatch(runtime.SLOT, slot) is not None, "invalid_synthetic_slot")
        recorder.call(
            "owner_doctor",
            installed,
            [
                "doctor",
                "--home",
                home,
                "--slot",
                slot,
                "--account-key",
                ACCOUNT,
                "--scope",
                SCOPE,
            ],
        )
        baseline = recorder.business("empty_profile", installed, slot, "profile-index", {})[
            "result"
        ]
        require(
            baseline["revision"] == 0 and baseline["claim_count"] == 0, "nonempty_synthetic_profile"
        )
        request = {
            "expected_revision": 0,
            "confirmed": True,
            "changes": [
                private_claim("values", TEXT_VALUES),
                private_claim("friend_needs", TEXT_FRIENDS),
            ],
        }
        saved = recorder.business(
            "profile_update_full", installed, slot, "profile-update", request
        )["result"]
        require(saved["revision"] == 1 and len(saved["claims"]) == 2, "profile_update_mismatch")
        index = recorder.business("profile_index", installed, slot, "profile-index", {})["result"]
        require(
            index["revision"] == 1
            and index["claim_count"] == 2
            and index["includes_private_text"] is False,
            "profile_index_mismatch",
        )
        require("SYNTHETIC_PRIVATE" not in json.dumps(index), "index_private_text_leak")
        complete = recorder.business("profile_read_full", installed, slot, "profile-read", {})[
            "result"
        ]
        require(
            {claim["text"] for claim in complete["claims"]} == {TEXT_VALUES, TEXT_FRIENDS},
            "profile_persistence_mismatch",
        )
        targeted = recorder.business(
            "profile_read_targeted", installed, slot, "profile-read", {"topics": ["values"]}
        )["result"]
        require(
            len(targeted["claims"]) == 1
            and targeted["claims"][0]["text"] == TEXT_VALUES
            and targeted["selection"]["complete"] is False,
            "targeted_profile_mismatch",
        )
        require(
            TEXT_FRIENDS not in json.dumps(targeted, ensure_ascii=False),
            "unrelated_targeted_text_leak",
        )
        friend = next(claim for claim in saved["claims"] if claim["topic"] == "friend_needs")
        changed = recorder.business(
            "profile_update_incremental",
            installed,
            slot,
            "profile-update",
            {
                "expected_revision": 1,
                "confirmed": True,
                "response": "changes",
                "changes": [private_claim("friend_needs", TEXT_CORRECTED, friend["id"])],
            },
        )["result"]
        require(
            changed["revision"] == 2
            and len(changed["claims"]) == 1
            and changed["claims"][0]["text"] == TEXT_CORRECTED
            and changed["selection"]["changed_only"] is True,
            "incremental_profile_mismatch",
        )
        require(
            TEXT_VALUES not in json.dumps(changed, ensure_ascii=False),
            "unrelated_incremental_text_leak",
        )
        checks["profile_persistence_selection_correction"] = "passed_actual_package"
        prepared = recorder.business(
            "assessment_prepare",
            installed,
            slot,
            "assessment-prepare",
            {
                "expected_revision": 2,
                "peer_summary": synthetic_peer_summary(),
            },
        )["result"]
        context = prepared["context"]
        assessment = recorder.business(
            "assessment_save",
            installed,
            slot,
            "assessment-save",
            {
                "confirmed": True,
                "context_id": context["context_id"],
                "own_revision": 2,
                "peer_summary_digest": context["peer_summary_digest"],
                "possible_alignment": [
                    {
                        "text": "SYNTHETIC_PRIVATE_ASSESSMENT: tentative shared value.",
                        "own_claim_ids": [saved["claims"][0]["id"]],
                        "peer_fields": ["values"],
                        "uncertainty": "Synthetic self-report cannot establish actual behavior.",
                    }
                ],
                "questions_and_tensions": [],
                "unknowns": ["Their full profile is unavailable."],
                "respectful_questions": ["How do you prefer to discuss a disagreement?"],
                "caveats": ["Fixed synthetic storage test; no model generated this assessment."],
            },
        )["result"]
        assessment_id = assessment["assessment_id"]
        reread = recorder.business(
            "assessment_read", installed, slot, "assessment-read", {"id": assessment_id}
        )["result"]
        require(reread == assessment, "assessment_persistence_mismatch")
        checks["private_assessment_storage"] = "passed_fixed_synthetic_content_no_generation"
        probe = recorder.business("local_probe", installed, slot, "local-probe", {})
        require(probe.get("local_read_write") == "passed_synthetic_only", "local_probe_mismatch")
        checks["synthetic_local_probe"] = "passed_actual_package"
        recorder.business(
            "wrong_account_refused",
            installed,
            slot,
            "profile-read",
            {},
            account=OTHER_ACCOUNT,
            expected_error="owner_binding_mismatch",
        )
        recorder.business(
            "wrong_scope_refused",
            installed,
            slot,
            "profile-read",
            {},
            scope="production",
            expected_error="owner_binding_mismatch",
        )
        checks["explicit_local_binding_refusals"] = "passed_local_assertions_not_authentication"
        location = workspace / "accounts" / slot / "work"
        require(
            not list((location / "outbound").iterdir())
            and not list((location / "publications").iterdir()),
            "unexpected_shared_artifact",
        )
        before = profile_fingerprint(location)
        # Deliberately damage only a harmless guide in this new isolated install.
        guide = runtime.check_path(installed.parent / "INSTALL_WITH_CHATGPT.md", directory=False)
        require(guide.is_file() and guide.parent == installed.parent, "repair_target_mismatch")
        guide.write_bytes(
            b"Synthetic interrupted guide replacement for package repair verification.\n"
        )
        recorder.call(
            "corruption_detected",
            executable,
            ["doctor", "--home", home],
            expected_error="component_integrity_failed",
        )
        recorder.call("repair", executable, ["repair", "--home", home, "--package", package])
        installed = installed_executable(home)
        recorder.call("repaired_doctor", installed, ["doctor", "--home", home])
        require(profile_fingerprint(location) == before, "repair_changed_synthetic_profile")
        checks["repair"] = "passed_controlled_guide_corruption"
        removed = recorder.call("uninstall", executable, ["uninstall", "--home", home])
        require(removed.get("status") == "runtime_uninstalled", "uninstall_status_mismatch")
        require(
            profile_fingerprint(location) == before and not (home / "active.json").exists(),
            "uninstall_preservation_mismatch",
        )
        recorder.call(
            "reinstall_retained_data",
            executable,
            [
                "install",
                "--home",
                home,
                "--package",
                package,
            ],
        )
        installed = installed_executable(home)
        retained = recorder.business("read_retained_data", installed, slot, "profile-read", {})[
            "result"
        ]
        require(
            retained["revision"] == 2
            and {claim["text"] for claim in retained["claims"]} == {TEXT_VALUES, TEXT_CORRECTED},
            "retained_profile_unreadable",
        )
        retained_assessment = recorder.business(
            "assessment_after_reinstall", installed, slot, "assessment-read", {"id": assessment_id}
        )["result"]
        require(retained_assessment == assessment, "retained_assessment_unreadable")
        recorder.call("final_uninstall", executable, ["uninstall", "--home", home])
        require(profile_fingerprint(location) == before, "final_data_preservation_mismatch")
        checks["uninstall_reinstall_data_preservation"] = "passed_actual_package"
        checks["actual_interrupted_install_retry"] = verify_interrupted_install(
            package,
            workspace,
            recorder,
        )
        report["ok"] = True
    except Exception as error:
        report["ok"] = False
        report["error"] = {
            "code": str(error) if isinstance(error, VerificationError) else "verification_failed",
            "step": recorder.last_step,
        }
    report["metrics"] = {
        "executable_calls": len(recorder.steps),
        "elapsed_ms": round(sum(step["elapsed_ms"] for step in recorder.steps), 3),
        "input_utf8_bytes": sum(step["input_utf8_bytes"] for step in recorder.steps),
        "output_utf8_bytes": sum(step["output_utf8_bytes"] for step in recorder.steps),
        "output_unicode_characters": sum(
            step["output_unicode_characters"] for step in recorder.steps
        ),
        "true_model_tokens": "unavailable_not_inferred_from_text_or_subscription_usage",
        "private_explanation_generation": "not_measured_no_model_session",
        "measurement_scope": "local_executable_only_not_chatgpt_guidance",
    }
    report["synthetic_data"] = "retained_in_isolated_verification_workspace"
    runtime.atomic(workspace / "verification-result.json", report)
    return report


def main(argv=None):
    parser = runtime.Parser(description="Verify actual Windows Work package in isolation")
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--workspace", type=Path)
    try:
        args = parser.parse_args(argv)
        result = verify(args.package, args.workspace)
    except Exception as error:
        result = {
            "ok": False,
            "error": {
                "code": str(error)
                if isinstance(error, VerificationError)
                else "verification_precondition_failed"
            },
            "model_calls": 0,
        }
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
