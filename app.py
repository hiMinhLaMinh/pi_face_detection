import argparse
import logging
from flask import Flask, Response, jsonify, render_template, request
from hardware import LABS
from service import FaceService
from config import PORT

def create_app(service):
    app = Flask(__name__)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/status")
    def status():
        return jsonify(service.snapshot())

    @app.post("/api/lab")
    def select_lab():
        data = request.get_json(silent=True)
        lab = data.get("lab") if isinstance(data, dict) else None
        if not isinstance(lab, str) or lab not in LABS:
            return jsonify(error="Lab phải là lab1 hoặc lab2"), 400
        try:
            service.select_lab(lab)
        except Exception:
            logging.exception("Cannot select lab")
            return jsonify(error="Không khởi tạo được GPIO; kiểm tra terminal và dây nối"), 503
        return jsonify(service.snapshot())

    @app.get("/video_feed")
    def video_feed():
        if not service.snapshot()["running"]:
            return "Camera chưa sẵn sàng; xem /api/status", 503
        return Response(service.stream(),
                        mimetype="multipart/x-mixed-replace; boundary=frame")
    return app

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true", help="Mô phỏng, không cần Pi")
    parser.add_argument("--lab", choices=list(LABS), default="lab1")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    service = FaceService(mock=args.mock, lab=args.lab)
    try:
        service.start()
        # Không dùng reloader: tránh mở camera / GPIO hai lần.
        create_app(service).run(host="0.0.0.0", port=PORT,
                                threaded=True, debug=False, use_reloader=False)
    finally:
        service.close()
