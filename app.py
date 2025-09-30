from flask import Flask, request, jsonify
import subprocess
import tempfile
import os
import json

app = Flask(__name__)

# PMD command (run.sh is in PATH via Dockerfile)
PMD_CMD = "run.sh"
RULESET = "rulesets/apex/quickstart.xml"

@app.route("/run", methods=["POST"])
def run_pmd():
    data = request.get_json()
    classes = data.get("classes", [])

    combined_violations = []
    warnings_list = []

    for cls in classes:
        name = cls.get("name", "UnknownClass")
        source_code = cls.get("source", "")

        # Write class to temp file (UTF-8)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".cls", mode="w", encoding="utf-8") as tmp:
            tmp.write(source_code)
            tmp_path = tmp.name

        try:
            result = subprocess.run([
                PMD_CMD,
                "check",
                "-d", tmp_path,
                "-R", RULESET,
                "-f", "json"
            ], capture_output=True, text=True, check=True)

            parsed_output = json.loads(result.stdout) if result.stdout else {}
            for f in parsed_output.get("files", []):
                for v in f.get("violations", []):
                    v["className"] = name
                    combined_violations.append(v)

            if result.stderr:
                warnings_list.append(f"Class {name}: {result.stderr.strip()}")

        except subprocess.CalledProcessError as e:
            warnings_list.append(f"PMD execution failed for class {name}: {e.stderr.strip() if e.stderr else str(e)}")
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
