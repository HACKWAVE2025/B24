from flask import Blueprint, jsonify, current_app, request

from utils.auth import token_required


def create_threat_intel_blueprint(threat_intel_service):
    bp = Blueprint("threat_intel", __name__)

    def _service():
        # Allow lazy fallback to app config in case blueprint is reused
        service = threat_intel_service
        if service is None:
            service = current_app.config.get("THREAT_INTEL_SERVICE")
        return service

    def _serialize_datetime(value):
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return value

    def _serialize_snapshot(snapshot):
        if not snapshot:
            return {}
        processed = snapshot.copy()
        processed["last_seen"] = _serialize_datetime(processed.get("last_seen"))
        return processed

    def _serialize_history(history):
        serialized = []
        for entry in history:
            serialized.append(
                {
                    "timestamp": _serialize_datetime(entry.get("timestamp")),
                    "agent_outputs": entry.get("agent_outputs", []),
                    "transaction": entry.get("transaction", {}),
                }
            )
        return serialized

    @bp.route("/api/threat-intel/receiver/<receiver_id>", methods=["GET"])
    @token_required
    def get_receiver_intel(receiver_id):
        service = _service()
        if service is None:
            return jsonify({"error": "Threat intel service unavailable"}), 503

        snapshot = _serialize_snapshot(service.get_receiver_snapshot(receiver_id))
        history = _serialize_history(service.get_receiver_history(receiver_id))
        return jsonify(
            {
                "receiver": receiver_id,
                "threatScore": snapshot.get("threat_score", 0),
                "snapshot": snapshot,
                "history": history,
            }
        ), 200

    @bp.route("/api/threat-intel/global", methods=["GET"])
    @token_required
    def get_global_threats():
        service = _service()
        if service is None:
            return jsonify({"error": "Threat intel service unavailable"}), 503

        trending = [
            {
                **item,
                "last_seen": _serialize_datetime(item.get("last_seen")),
            }
            for item in service.get_trending_threats(limit=5)
        ]
        clusters = [
            {
                **cluster,
                "updatedAt": _serialize_datetime(cluster.get("updatedAt")),
            }
            for cluster in service.get_clusters(limit=5)
        ]
        return jsonify(
            {
                "trending": trending,
                "clusters": clusters,
            }
        ), 200

    def _cluster_response(include_inactive: bool = False):
        service = _service()
        if service is None:
            return jsonify({"error": "Threat intel service unavailable"}), 503

        clusters = [
            {
                **cluster,
                "updatedAt": _serialize_datetime(cluster.get("updatedAt")),
            }
            for cluster in service.get_clusters(include_inactive=include_inactive, limit=5)
        ]
        return jsonify({"clusters": clusters}), 200

    @bp.route("/api/threat-intel/clusters", methods=["GET"])
    @token_required
    def get_cluster_details():
        return _cluster_response(include_inactive=False)

    @bp.route("/api/intel/dynamic-clusters", methods=["GET"])
    @token_required
    def get_dynamic_clusters():
        include_inactive = bool(request.args.get("include_inactive"))
        return _cluster_response(include_inactive=include_inactive)

    return bp

