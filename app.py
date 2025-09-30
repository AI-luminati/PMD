from flask import Flask, request, jsonify
import subprocess
import tempfile
import os
import json
import urllib.request
import zipfile

app = Flask(__name__)

PMD_VERSION = "7.17.0"
PMD_ZIP_URL = f"https://github.com/pmd/pmd/releases/download/pmd_releases/{PMD_VERSION}/pmd-dist-{PMD_VERSION}-bin.zip"

# NOTE: Extracted folder name is "pmd-bin-<version>", not "pmd-dist"
PMD_DIR = f"/tmp/pmd-bin-{PMD_VERSION}"
PMD_CMD = f"{PMD_DIR}/bin/run.sh"
RULESET = f"{PMD_DIR}/rulesets/apex/quickstart.xml"


def ensure_pmd():
    """Download & extract PMD only if not already available"""
    if not os.path.exists(PMD_DIR):
        try:
            os.makedirs("/tmp", exist_ok=True)
            zip_path = f"/tmp/pmd-{PMD_VERSION}.zip"

            print(f"[PMD] Downloading {PMD_ZIP_URL} ...")
            urllib.request.urlretrieve(PMD_ZIP_URL, zip_path)

            print("[PMD] Extracting...")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall("/tmp")

            os.remove(zip_path)
            os.chmod(PMD_CMD, 0o755)
            print(f"[PMD] Ready at {PMD_CMD}")

        except Exception as e:
            print(f"[PMD ERROR] {e}")
            raise


@app.route("/")
def home():
    return "✅ Flask is running! Use POST /run to analyze classes."


@app.route("/run", methods=["POST"])
def run_pmd():
    try:
        ensure_pmd()  # Lazy load PMD when first needed
    except Exception as e:
        return jsonify({"status": "error", "message": f"PMD setup failed: {e}"}), 500

    data = request.get_json(force=True, silent=True) or {}
    classes = data.get("classes", [])

    combined_violations = []
    warnings_list = []

    for cls in classes:
        name = cls.get("name", "UnknownClass")
        source_code = cls.get("source", "")

        # Write class to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".cls", mode="w", encoding="utf-8") as tmp:
            tmp.write(source_code)
            tmp_path = tmp.name

        try:
            result = subprocess.run(
                ["bash", PMD_CMD, "check", "-d", tmp_path, "-R", RULESET, "-f", "json"],
                capture_output=True,
                text=True,
                check=True
            )

            parsed_output = json.loads(result.stdout) if result.stdout else {}
            files = parsed_output.get("files", [])
            for f in files:
                for v in f.get("violations", []):
                    v["className"] = name
                    combined_violations.append(v)

            if result.stderr:
                warnings_list.append(f"Class {name}: {result.stderr.strip()}")

        except subprocess.CalledProcessError as e:
            warnings_list.append(f"PMD failed for {name}: {e.stderr.strip() if e.stderr else str(e)}")
        except Exception as e:
            combined_violations.append({"parseError": str(e), "className": name})
        finally:
            os.remove(tmp_path)

    return jsonify({
        "violations": combined_violations,
        "warnings": warnings_list
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
