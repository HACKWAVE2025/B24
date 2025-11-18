"""
Threat Intelligence Service (CTIH)
Aggregates agent outputs, maintains threat scores per receiver,
and exposes helper methods for downstream consumers.
"""
from datetime import datetime, timezone
from statistics import mean
from typing import List, Dict, Any, Optional, Sequence
from uuid import uuid4

import numpy as np

from database.db import get_db
from services.dynamic_cluster_engine import (
    ClusterSample,
    DynamicClusterEngine,
)


class ThreatIntelService:
    """
    Central Threat Intelligence Hub (CTIH)
    """

    def __init__(self):
        self.collection_name = "threat_intel"
        self.history_collection_name = "threat_intel_events"
        self.cluster_collection_name = "dynamic_clusters"
        self._pending_reports = 0
        self.cluster_refresh_threshold = 10
        self.cluster_engine = DynamicClusterEngine()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def update_and_get_score(
        self,
        receiver: str,
        agent_outputs: List[Dict[str, Any]],
        transaction: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Upsert threat intel document for receiver based on latest agent outputs
        and return the updated snapshot.
        """
        if not receiver:
            return None

        collection = self._get_collection(self.collection_name)
        if collection is None:
            return None

        metrics = self._derive_metrics(agent_outputs, transaction)
        now = datetime.now(timezone.utc)

        update_doc = {
            "$set": {
                "receiver": receiver,
                "threat_score": metrics["threat_score"],
                "avg_agent_risk": metrics["avg_agent_risk"],
                "behavior_anomalies": metrics["behavior_anomalies"],
                "pattern_flags": metrics["pattern_flags"],
                "velocity_score": metrics["velocity_score"],
                "geo_anomalies": metrics["geo_anomalies"],
                "last_seen": now,
            },
            "$inc": {"total_reports": metrics["report_increment"]},
        }

        # Avoid inserting zero increments
        if metrics["report_increment"] == 0:
            update_doc.pop("$inc")

        collection.update_one({"receiver": receiver}, update_doc, upsert=True)
        snapshot = collection.find_one({"receiver": receiver}) or {}

        return snapshot

    def get_receiver_threat_score(self, receiver: str) -> float:
        """Return cached threat score for receiver (0-100)."""
        collection = self._get_collection(self.collection_name)
        if collection is None or not receiver:
            return 0.0
        doc = collection.find_one({"receiver": receiver})
        return float(doc.get("threat_score", 0)) if doc else 0.0

    def record_agent_outputs(
        self,
        transaction: Dict[str, Any],
        agent_outputs: List[Dict[str, Any]],
    ) -> None:
        """Persist raw agent outputs for historical analysis."""
        history_collection = self._get_collection(self.history_collection_name)
        if history_collection is None:
            return
        receiver = transaction.get("receiver")
        history_collection.insert_one(
            {
                "receiver": receiver,
                "agent_outputs": agent_outputs,
                "transaction": {
                    "amount": transaction.get("amount"),
                    "reason": transaction.get("reason"),
                    "user_id": transaction.get("user_id"),
                },
                "timestamp": datetime.now(timezone.utc),
            }
        )
        self._pending_reports += 1
        if self._pending_reports >= self.cluster_refresh_threshold:
            self.refresh_dynamic_clusters()
            self._pending_reports = 0

    def get_trending_threats(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Return top receivers by threat score, only if they have at least 5 reports."""
        collection = self._get_collection(self.collection_name)
        if collection is None:
            return []
        cursor = (
            collection.find({"total_reports": {"$gte": 5}})
            .sort("threat_score", -1)
            .limit(limit)
        )
        return [self._serialize_doc(doc) for doc in cursor]

    def refresh_dynamic_clusters(self, force: bool = False) -> None:
        """
        Rebuild dynamic scam clusters using the latest threat intel events.
        """
        if not force and self._pending_reports < self.cluster_refresh_threshold:
            return
        self._pending_reports = 0

        history_collection = self._get_collection(self.history_collection_name)
        snapshot_collection = self._get_collection(self.collection_name)
        cluster_collection = self._get_collection(self.cluster_collection_name)

        if history_collection is None or snapshot_collection is None or cluster_collection is None:
            return

        recent_reports = list(
            history_collection.find({}).sort("timestamp", -1).limit(600)
        )
        if not recent_reports:
            return

        receiver_ids = {report.get("receiver") for report in recent_reports if report.get("receiver")}
        snapshots = {
            doc.get("receiver"): doc
            for doc in snapshot_collection.find({"receiver": {"$in": list(receiver_ids)}})
        }

        samples: List[ClusterSample] = []
        vectors: List[np.ndarray] = []

        for report in recent_reports:
            receiver = report.get("receiver")
            if not receiver:
                continue
            transaction = report.get("transaction", {})
            message = (transaction.get("reason") or "").strip()
            pattern_flags = self._extract_pattern_flags(report.get("agent_outputs", []))
            agent_scores = self._collect_agent_scores(report.get("agent_outputs", []))
            snapshot = snapshots.get(receiver, {})
            threat_score = float(snapshot.get("threat_score", 0))
            vector = self.cluster_engine.generate_feature_vector(
                f"{message} {receiver}".strip(),
                pattern_flags,
                agent_scores,
            )
            sample = ClusterSample(
                receiver=receiver,
                message=message,
                pattern_flags=pattern_flags,
                agent_scores=agent_scores,
                threat_score=threat_score,
                timestamp=report.get("timestamp", datetime.now(timezone.utc)),
                vector=vector,
            )
            samples.append(sample)
            vectors.append(vector)

        if not vectors:
            return

        feature_matrix = np.vstack(vectors)
        labels, centers = self.cluster_engine.cluster_vectors_with_agglomerative(feature_matrix)

        grouped: Dict[int, List[ClusterSample]] = {}
        noise_samples: List[ClusterSample] = []
        for idx, label in enumerate(labels):
            sample = samples[idx]
            if label == -1:
                noise_samples.append(sample)
                continue
            grouped.setdefault(int(label), []).append(sample)

        now = datetime.now(timezone.utc)
        new_clusters: List[Dict[str, Any]] = []
        cluster_index = 1
        for label, members in grouped.items():
            centroid = centers.get(label)
            if centroid is None:
                continue
            name, top_keywords = self.cluster_engine.derive_cluster_name(members, cluster_index)
            members_set = sorted({member.receiver for member in members})
            avg_score = round(mean(member.threat_score for member in members), 1) if members else 0.0
            new_clusters.append(
                {
                    "cluster_id": str(uuid4()),
                    "name": name,
                    "members": members_set,
                    "size": len(members_set),
                    "avg_score": avg_score,
                    "top_keywords": top_keywords,
                    "centroid": centroid.tolist(),
                    "updated_at": now,
                    "active": True,
                }
            )
            cluster_index += 1

        emerging_clusters = self.cluster_engine.detect_emerging_clusters(noise_samples)
        if emerging_clusters:
            new_clusters.extend(emerging_clusters)

        # Merge similar clusters within the same batch first
        new_clusters = self.cluster_engine.merge_similar_clusters(new_clusters)

        existing_clusters = list(cluster_collection.find({}))
        # Also merge any duplicate clusters in existing data before merging with new
        if existing_clusters:
            existing_clusters = self.cluster_engine.merge_similar_clusters(existing_clusters)
        
        merged_clusters = self.cluster_engine.merge_with_existing(new_clusters, existing_clusters)
        # Final pass: merge any remaining similar clusters in the final merged set
        # This catches cases where clusters from different batches weren't compared
        merged_clusters = self.cluster_engine.merge_similar_clusters(merged_clusters)
        lifecycle_clusters = self.cluster_engine.apply_lifecycle_rules(merged_clusters, now=now)

        cluster_collection.delete_many({})
        if lifecycle_clusters:
            cluster_collection.insert_many(lifecycle_clusters)

    # ------------------------------------------------------------------
    # Endpoint helpers
    # ------------------------------------------------------------------
    def get_receiver_snapshot(self, receiver: str) -> Dict[str, Any]:
        collection = self._get_collection(self.collection_name)
        if collection is None or not receiver:
            return {}
        doc = collection.find_one({"receiver": receiver})
        return self._serialize_doc(doc) if doc else {}

    def get_receiver_history(self, receiver: str, limit: int = 25) -> List[Dict[str, Any]]:
        history_collection = self._get_collection(self.history_collection_name)
        if history_collection is None or not receiver:
            return []
        cursor = (
            history_collection.find({"receiver": receiver})
            .sort("timestamp", -1)
            .limit(limit)
        )
        history = []
        for entry in cursor:
            history.append(
                {
                    "timestamp": entry.get("timestamp"),
                    "agent_outputs": entry.get("agent_outputs", []),
                    "transaction": entry.get("transaction", {}),
                }
            )
        return self._serialize_history(history)

    def get_clusters(self, include_inactive: bool = False, limit: int = 5) -> List[Dict[str, Any]]:
        """Return top clusters sorted by average score, limited to top N."""
        cluster_collection = self._get_collection(self.cluster_collection_name)
        if cluster_collection is None:
            return []
        query = {} if include_inactive else {"active": True}
        cursor = cluster_collection.find(query).sort("avg_score", -1).limit(limit)
        return [
            {
                "clusterId": doc.get("cluster_id"),
                "name": doc.get("name"),
                "members": doc.get("members", []),
                "avgScore": doc.get("avg_score", 0),
                "count": doc.get("size", 0),
                "topKeywords": doc.get("top_keywords", []),
                "active": doc.get("active", True),
                "updatedAt": doc.get("updated_at"),
            }
            for doc in cursor
        ]

    def check_cluster_match(
        self,
        transaction: Dict[str, Any],
        agent_outputs: List[Dict[str, Any]],
        similarity_threshold: float = 0.70,
    ) -> Optional[Dict[str, Any]]:
        """
        Check if a transaction matches an existing cluster pattern.
        Returns the matched cluster info if similarity >= threshold, None otherwise.
        
        Uses cosine similarity between transaction feature vector and cluster centroids.
        Lower threshold (0.70) allows detection of similar but not identical patterns.
        """
        cluster_collection = self._get_collection(self.cluster_collection_name)
        if cluster_collection is None:
            return None

        # Get active clusters with centroids
        active_clusters = list(cluster_collection.find({"active": True}))
        if not active_clusters:
            return None

        # Generate feature vector for this transaction
        message = (transaction.get("reason") or "").strip()
        pattern_flags = self._extract_pattern_flags(agent_outputs)
        agent_scores = self._collect_agent_scores(agent_outputs)
        
        transaction_vector = self.cluster_engine.generate_feature_vector(
            f"{message} {transaction.get('receiver', '')}".strip(),
            pattern_flags,
            agent_scores,
        )

        # Compare with each cluster centroid
        best_match = None
        best_similarity = 0.0

        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np

        # Normalize payment keywords for keyword matching
        payment_keywords = {"upi", "emi", "paytm", "pay", "payment"}
        pattern_flags_normalized = set()
        for flag in pattern_flags:
            if flag.lower() in payment_keywords:
                pattern_flags_normalized.add("payment")
            else:
                pattern_flags_normalized.add(flag.lower())

        for cluster in active_clusters:
            centroid = cluster.get("centroid")
            if not centroid:
                continue

            try:
                centroid_vector = np.array(centroid, dtype=np.float64)
                similarity = float(
                    cosine_similarity([transaction_vector], [centroid_vector])[0][0]
                )

                # Also check keyword overlap as fallback
                cluster_keywords = set(kw.lower() for kw in cluster.get("top_keywords", []))
                cluster_keywords_normalized = set()
                for kw in cluster_keywords:
                    if kw in payment_keywords:
                        cluster_keywords_normalized.add("payment")
                    else:
                        cluster_keywords_normalized.add(kw)
                
                keyword_overlap = len(pattern_flags_normalized & cluster_keywords_normalized)
                keyword_union = len(pattern_flags_normalized | cluster_keywords_normalized)
                keyword_similarity = keyword_overlap / keyword_union if keyword_union > 0 else 0.0
                
                # Core scam keywords that indicate strong match even with low overall similarity
                core_scam_keywords = {"loan", "otp", "job", "invest", "crypto", "urgent", "verify", "kyc", "work", "hiring"}
                shared_core = pattern_flags_normalized & cluster_keywords_normalized & core_scam_keywords
                
                # Use combined score: 70% vector similarity + 30% keyword similarity
                combined_similarity = (similarity * 0.7) + (keyword_similarity * 0.3)
                
                # Match if:
                # 1. Vector similarity meets threshold
                # 2. Keyword similarity ≥50% with ≥2 keywords
                # 3. Shared core scam keyword (e.g., "loan") - match even with lower vector similarity
                # 4. Combined similarity meets threshold
                should_match = False
                if similarity >= similarity_threshold:
                    should_match = True
                elif keyword_similarity >= 0.5 and keyword_overlap >= 2:  # At least 2 keywords match
                    should_match = True
                    combined_similarity = max(combined_similarity, keyword_similarity)
                elif len(shared_core) >= 1:  # Core keyword match (e.g., "loan" in both)
                    # If core keyword matches, accept even with lower vector similarity (≥0.30)
                    # This catches cases like "loan" messages that should match loan clusters
                    # Core keywords are strong indicators, so we trust them even with lower vector similarity
                    if similarity >= 0.30:
                        should_match = True
                        # Boost similarity score for core keyword match
                        combined_similarity = max(combined_similarity, 0.70)  # Minimum 70% for core keyword match
                elif combined_similarity >= similarity_threshold:
                    should_match = True

                if should_match and combined_similarity > best_similarity:
                    best_similarity = combined_similarity
                    best_match = {
                        "clusterId": cluster.get("cluster_id"),
                        "name": cluster.get("name"),
                        "avgScore": cluster.get("avg_score", 0),
                        "count": cluster.get("size", 0),
                        "topKeywords": cluster.get("top_keywords", []),
                        "similarity": round(combined_similarity, 3),
                        "vectorSimilarity": round(similarity, 3),
                        "keywordSimilarity": round(keyword_similarity, 3),
                    }
            except Exception as e:
                print(f"⚠️ Error comparing with cluster {cluster.get('name')}: {e}")
                continue

        return best_match

    def check_receiver_in_trending(self, receiver: str) -> Optional[Dict[str, Any]]:
        """Check if receiver is in trending threats list."""
        if not receiver:
            return None
        trending = self.get_trending_threats(limit=10)  # Check top 10 to be safe
        for threat in trending:
            if threat.get("receiver") == receiver:
                return {
                    "receiver": threat.get("receiver"),
                    "threatScore": threat.get("threat_score", 0),
                    "totalReports": threat.get("total_reports", 0),
                    "patternFlags": threat.get("pattern_flags", []),
                }
        return None

    def check_receiver_in_clusters(self, receiver: str) -> Optional[Dict[str, Any]]:
        """Check if receiver is a member of any active cluster."""
        if not receiver:
            return None
        clusters = self.get_clusters(include_inactive=False, limit=20)  # Check top 20 clusters
        for cluster in clusters:
            members = cluster.get("members", [])
            if receiver in members:
                return {
                    "clusterId": cluster.get("clusterId"),
                    "name": cluster.get("name"),
                    "avgScore": cluster.get("avgScore", 0),
                    "count": cluster.get("count", 0),
                    "topKeywords": cluster.get("topKeywords", []),
                }
        return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_collection(self, name: str):
        db = get_db()
        if db is None:
            return None
        return getattr(db, name, None)

    def _derive_metrics(
        self, agent_outputs: List[Dict[str, Any]], transaction: Dict[str, Any]
    ) -> Dict[str, Any]:
        avg_agent_risk = self._compute_avg_risk(agent_outputs)
        behavior_anomalies = self._extract_agent_score(agent_outputs, "Behavior Agent")
        pattern_flags = self._extract_pattern_flags(agent_outputs)
        velocity_score = self._compute_velocity_score(transaction)
        geo_anomalies = self._compute_geo_anomaly(transaction)
        pattern_bonus = min(len(pattern_flags) * 5, 20)

        threat_score = round(
            min(
                100.0,
                (avg_agent_risk * 0.6)
                + (behavior_anomalies * 0.2)
                + (velocity_score * 0.15)
                + (geo_anomalies * 0.05)
                + pattern_bonus,
            ),
            1,
        )

        return {
            "avg_agent_risk": round(avg_agent_risk, 1),
            "behavior_anomalies": round(behavior_anomalies, 1),
            "pattern_flags": pattern_flags,
            "velocity_score": round(velocity_score, 1),
            "geo_anomalies": round(geo_anomalies, 1),
            "threat_score": threat_score,
            "report_increment": 1,
        }

    @staticmethod
    def _compute_avg_risk(agent_outputs: List[Dict[str, Any]]) -> float:
        scores = [float(output.get("risk_score", 0)) for output in agent_outputs]
        return sum(scores) / len(scores) if scores else 0.0

    @staticmethod
    def _extract_agent_score(agent_outputs: List[Dict[str, Any]], agent_name: str) -> float:
        for output in agent_outputs:
            if output.get("agent_name") == agent_name:
                return float(output.get("risk_score", 0))
        return 0.0

    @staticmethod
    def _extract_pattern_flags(agent_outputs: List[Dict[str, Any]]) -> List[str]:
        for output in agent_outputs:
            if output.get("agent_name") == "Pattern Agent":
                evidence = output.get("evidence", [])
                if isinstance(evidence, list):
                    return evidence[:5]
        return []

    @staticmethod
    def _collect_agent_scores(agent_outputs: Sequence[Dict[str, Any]]) -> List[float]:
        scores: List[float] = []
        for output in agent_outputs:
            try:
                scores.append(float(output.get("risk_score", 0)))
            except (TypeError, ValueError):
                scores.append(0.0)
        return scores

    @staticmethod
    def _compute_velocity_score(transaction: Dict[str, Any]) -> float:
        amount = float(transaction.get("amount", 0) or 0)
        velocity = 0.0
        if amount >= 20000:
            velocity += 40
        elif amount >= 10000:
            velocity += 25
        elif amount >= 5000:
            velocity += 15

        # Time-based heuristic: late-night transfers bump the velocity score
        time_str = transaction.get("time", "")
        try:
            hour = int(time_str.split(":")[0])
            if hour >= 22 or hour <= 5:
                velocity += 15
        except Exception:
            pass
        return min(100.0, velocity)

    @staticmethod
    def _compute_geo_anomaly(transaction: Dict[str, Any]) -> float:
        # Placeholder for future geo-signal detection
        return float(transaction.get("geo_anomaly_score", 0) or 0)

    @staticmethod
    def _serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
        if not doc:
            return {}
        serialized = {
            "receiver": doc.get("receiver"),
            "threat_score": doc.get("threat_score", 0),
            "avg_agent_risk": doc.get("avg_agent_risk", 0),
            "behavior_anomalies": doc.get("behavior_anomalies", 0),
            "pattern_flags": doc.get("pattern_flags", []),
            "velocity_score": doc.get("velocity_score", 0),
            "geo_anomalies": doc.get("geo_anomalies", 0),
            "total_reports": doc.get("total_reports", 0),
            "last_seen": doc.get("last_seen"),
        }
        return serialized

    @staticmethod
    def _serialize_history(history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        serialized = []
        for entry in history:
            serialized.append(
                {
                    "timestamp": entry.get("timestamp"),
                    "agent_outputs": entry.get("agent_outputs", []),
                    "transaction": entry.get("transaction", {}),
                }
            )
        return serialized

