import os
import subprocess
import tempfile
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

PMD_VERSION = "7.17.0"
PMD_ZIP_URL = f"https://github.com/pmd/pmd/releases/download/pmd_releases/{PMD_VERSION}/pmd-dist-{PMD_VERSION}-bin.zip"

# Correct extracted folder name
PMD_DIR = f"/tmp/pmd-dist-{PMD_VERSION}"
PMD_CMD = f"{PMD_DIR}/bin/run.sh"
RULESET = f"{PMD_DIR}/rulesets/apex/quickstart.xml"


def setup_pmd():
    """Download and unzip PMD if not already installed"""
    if not os.path.exists(PMD_CMD):
        try:
            subprocess.run(
                [
                    "curl", "-L", "-o", "/tmp/pmd.zip", PMD_ZIP_URL
                ],
                check=True
            )
            subprocess.run(
                ["unzip", "-o", "/tmp/pmd.zip", "-d", "/tmp/"],
                check=True
            )
            os.remove("/tmp/pmd.zip")
        except Exception as e:
            return str(e)
    return None


@app.route("/analyze", methods=["POST"])
def analyze_apex_classes():
    error = setup_pmd()
    if error:
        return jsonify({"status": "error", "message": f"PMD setup failed: {error}"}), 500

    try:
        data = request.get_json() or {}
        classes = data.get("classes", [])

        results = []
        for cls in classes:
            name = cls.get("name", "UnknownClass")
            source_code = cls.get("source", "")

            with tempfile.NamedTemporaryFile(mode="w+", suffix=".cls", delete=False) as tmp:
                tmp.write(source_code)
                tmp.flush()
                tmp_path = tmp.name

            try:
                result = subprocess.run(
                    [
                        PMD_CMD,
                        "check",
                        "-d", tmp_path,
                        "-R", RULESET,
                        "-f", "json"
                    ],
                    capture_output=True,
                    text=True,
                    check=True
                )
                output = json.loads(result.stdout) if result.stdout else {}
                results.append({"class": name, "violations": output.get("files", [])})
            except subprocess.CalledProcessError as e:
                results.append({
                    "class": name,
                    "error": e.stderr or "PMD execution failed"
                })
            finally:
                os.unlink(tmp_path)

        return jsonify({"status": "success", "results": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
