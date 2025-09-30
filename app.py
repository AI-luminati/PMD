from flask import Flask, request, jsonify
import subprocess
import tempfile
import os
import json
import zipfile

app = Flask(__name__)

# PMD version and URLs
PMD_VERSION = "7.17.0"
PMD_ZIP = f"pmd-bin-{PMD_VERSION}.zip"
PMD_DIR = f"/tmp/pmd-bin-{PMD_VERSION}"   # unzipped folder
PMD_PATH = f"{PMD_DIR}/bin/run.sh"
PMD_URL = f"https://github.com/pmd/pmd/releases/download/pmd_releases/{PMD_VERSION}/{PMD_ZIP}"
RULESET = f"{PMD_DIR}/rulesets/apex/quickstart.xml"


def setup_pmd():
    """Download and unzip PMD if not already present"""
    if not os.path.exists(PMD_PATH):
        try:
            # Download PMD ZIP
            subprocess.run(["curl", "-L", "-o", PMD_ZIP, PMD_URL], check=True)

            # Check file size (basic validation)
            if os.path.getsize(PMD_ZIP) < 1024:
                return {"status": "error", "message": "Downloaded PMD ZIP is too small, likely invalid."}

            # Unzip using Python's zipfile
            with zipfile.ZipFile(PMD_ZIP, 'r') as zip_ref:
                zip_ref.extractall("/tmp/")
            os.remove(PMD_ZIP)

            # Make run.sh executable
            subprocess.run(["chmod", "+x", PMD_PATH], check=True)

        except Exception as e:
            return {"status": "error", "message": f"PMD setup failed: {str(e)}"}

    return {"status": "ok"}


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "PMD Flask API is running. Use POST /analyze to analyze Apex classes."
    })


@app.route("/analyze", methods=["POST"])
def analyze_apex_classes():
    # Ensure PMD is installed
    setup_status = setup_pmd()
    if setup_status["status"] == "error":
        return jsonify(setup_status), 500

    data = request.get_json() or {}
    classes = data.get("classes", [])

    combined_violations = []
    warnings_list = []

    for cls in classes:
        name = cls.get("name", "UnknownClass")
        source_code = cls.get("source", "")

        # Write source to temporary .cls file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".cls", mode="w", encoding="utf-8") as tmp:
            tmp.write(source_code)
            tmp_path = tmp.name

        # Run PMD analysis
        try:
            result = subprocess.run([
                PMD_PATH,
                "check",
                "-d", tmp_path,
                "-R", RULESET,
                "-f", "json"
            ], capture_output=True, text=True)

            os.remove(tmp_path)

            # Parse JSON output
            parsed_output = json.loads(result.stdout) if result.stdout else {}
            files = parsed_output.get("files", [])
            for f in files:
                for v in f.get("violations", []):
                    v["className"] = name
                    combined_violations.append(v)

            if result.stderr:
                warnings_list.append(f"Class {name}: {result.stderr.strip()}")

        except Exception as e:
            combined_violations.append({"parseError": str(e), "className": name})

    return jsonify({
        "violations": combined_violations,
        "warnings": warnings_list
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
