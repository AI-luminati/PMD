from flask import Flask, request, jsonify
import subprocess
import tempfile
import os
import json
import zipfile
import urllib.request

app = Flask(__name__)

# PMD version and URLs
PMD_VERSION = "7.17.0"
PMD_ZIP = f"pmd-dist-{PMD_VERSION}-bin.zip"
PMD_DIR = f"/tmp/pmd-bin-{PMD_VERSION}"  # unzipped folder
PMD_PATH = f"{PMD_DIR}/bin/pmd"  # PMD executable
PMD_URL = f"https://github.com/pmd/pmd/releases/download/pmd_releases%2F{PMD_VERSION}/{PMD_ZIP}"
RULESET = f"{PMD_DIR}/rulesets/apex/quickstart.xml"


def setup_pmd():
    """Download and unzip PMD if not already present"""
    if not os.path.exists(PMD_PATH):
        try:
            zip_tmp_path = f"/tmp/{PMD_ZIP}"
            # Download PMD ZIP if missing
            if not os.path.exists(zip_tmp_path):
                print("Downloading PMD ZIP...")
                urllib.request.urlretrieve(PMD_URL, zip_tmp_path)

            # Unzip
            with zipfile.ZipFile(zip_tmp_path, 'r') as zip_ref:
                zip_ref.extractall("/tmp/")
            os.remove(zip_tmp_path)

            # Make PMD executable
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

        try:
            # Run PMD check
            result = subprocess.run([
                PMD_PATH,
                "check",
                "-d", tmp_path,
                "-R", RULESET,
                "-f", "json"
            ], capture_output=True, text=True)

            os.remove(tmp_path)

            if result.stderr:
                warnings_list.append(f"Class {name}: {result.stderr.strip()}")

            # Parse JSON output
            parsed_output = json.loads(result.stdout) if result.stdout else {}
            files = parsed_output.get("files", [])
            for f in files:
                for v in f.get("violations", []):
                    v["className"] = name
                    combined_violations.append(v)

        except Exception as e:
            combined_violations.append({"parseError": str(e), "className": name})

    return jsonify({
        "violations": combined_violations,
        "warnings": warnings_list
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
