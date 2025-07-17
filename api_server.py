from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import json
import csv
from io import StringIO
from main import main
from csvtojson import csv_to_json  # If it has logic you want to reuse

app = FastAPI()

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        filename = file.filename.lower()
        contents = await file.read()

        # Parse logs from file
        if filename.endswith(".json"):
            logs = json.loads(contents.decode("utf-8"))
            if isinstance(logs, dict):
                logs = [logs]

        elif filename.endswith(".csv"):
            # Option 1: Use built-in CSV logic
            decoded = contents.decode("utf-8")
            reader = csv.DictReader(StringIO(decoded))
            logs = list(reader)

            # Option 2: If you already use csv_to_json, uncomment this:
            # with open("/tmp/upload.csv", "wb") as f:
            #     f.write(contents)
            # logs = csv_to_json("/tmp/upload.csv")

        else:
            return JSONResponse(status_code=400, content={"error": "Only .json or .csv files are accepted."})

        if not logs:
            return JSONResponse(status_code=400, content={"error": "No logs found in the file."})

        # Run your pipeline directly
        final_state = main(logs=logs)

        return {
            "message": f"File '{file.filename}' processed successfully.",
            "total_logs": len(logs),
            "incidents_detected": len(final_state.get("logs", [])),
            "sample": final_state.get("logs", [])[:3]
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
