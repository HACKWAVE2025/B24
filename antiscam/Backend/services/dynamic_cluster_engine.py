"""
Dynamic Threat Clustering Engine

Responsible for:
- Building feature vectors from agent evidence, pattern keywords, and transaction context
- Running Agglomerative clustering to discover organic scam clusters
- Deriving human-readable cluster names and lifecycle metadata
"""
from __future__ import annotations

import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple
from uuid import uuid4

import numpy as np
from numpy.typing import NDArray
from FlagEmbedding import FlagModel
from sklearn.cluster import AgglomerativeClustering
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


PATTERN_KEYWORD_BUCKETS = 128
AGENT_SCORE_VECTOR_SIZE = 8  # Allows future agents without reshaping vectors
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"


@dataclass
class ClusterSample:
    receiver: str
    message: str
    pattern_flags: List[str]
    agent_scores: List[float]
    threat_score: float
    timestamp: datetime
    vector: NDArray[np.float64]


class DynamicClusterEngine:
    """
    Self-learning clustering engine powered by embeddings + agent telemetry.
    """

    def __init__(
        self,
        min_cluster_size: int = 3,
        similarity_threshold: float = 0.85,
        distance_threshold: float = 4.0,
    ) -> None:
        self.min_cluster_size = min_cluster_size
        self.similarity_threshold = similarity_threshold
        self.distance_threshold = distance_threshold
        self.embedding_model = FlagModel(
            EMBEDDING_MODEL_NAME,
            use_fp16=False,
        )

    # ------------------------------------------------------------------ #
    # Feature engineering
    # ------------------------------------------------------------------ #
    def generate_feature_vector(
        self,
        message: str,
        pattern_flags: Sequence[str],
        agent_scores: Sequence[float],
    ) -> NDArray[np.float64]:
        """
        Embed message text, encode pattern keywords, and append agent scores.
        Produces a dense vector of roughly ~520 dims.
        """
        text = message or ""
        embedding = self._encode_text(text)

        keyword_vector = np.zeros(PATTERN_KEYWORD_BUCKETS, dtype=np.float64)
        for flag in pattern_flags or []:
            if not flag:
                continue
            bucket = hash(flag.lower()) % PATTERN_KEYWORD_BUCKETS
            keyword_vector[bucket] = 1.0

        score_vector = np.zeros(AGENT_SCORE_VECTOR_SIZE, dtype=np.float64)
        for idx, score in enumerate(agent_scores[:AGENT_SCORE_VECTOR_SIZE]):
            try:
                score_vector[idx] = float(score) / 100.0
            except (TypeError, ValueError):
                score_vector[idx] = 0.0

        return np.concatenate([embedding, keyword_vector, score_vector])

    # ------------------------------------------------------------------ #
    # Clustering & naming helpers
    # ------------------------------------------------------------------ #
    def cluster_vectors_with_agglomerative(
        self,
        feature_vectors: NDArray[np.float64],
    ) -> Tuple[NDArray[np.int32], Dict[int, NDArray[np.float64]]]:
        """
        Run Agglomerative Clustering with a distance threshold and return cluster labels + centroids.
        """
        sample_count = len(feature_vectors)
        if sample_count < self.min_cluster_size:
            return np.full(sample_count, -1, dtype=np.int32), {}

        clusterer = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=self.distance_threshold,
            metric="euclidean",
            linkage="ward",
        )
        labels = clusterer.fit_predict(feature_vectors)

        centers: Dict[int, NDArray[np.float64]] = {}
        processed_labels = labels.astype(np.int32)
        label_counts = Counter(processed_labels.tolist())

        for label, count in label_counts.items():
            if count < self.min_cluster_size:
                processed_labels[processed_labels == label] = -1

        for label in sorted(set(processed_labels.tolist())):
            if label == -1:
                continue
            members = feature_vectors[processed_labels == label]
            if len(members) == 0:
                continue
            centers[label] = members.mean(axis=0)

        return processed_labels, centers

    def derive_cluster_name(
        self,
        members: Sequence[ClusterSample],
        fallback_index: int,
    ) -> Tuple[str, List[str]]:
        """
        Use TF-IDF to extract salient keywords for the cluster name.
        """
        corpus = []
        for sample in members:
            tokens = " ".join(sample.pattern_flags or [])
            corpus.append(f"{sample.message} {tokens}".strip())

        valid_docs = [doc for doc in corpus if doc]
        if not valid_docs:
            return (f"Emerging Scam Cluster #{fallback_index}", [])

        vectorizer = TfidfVectorizer(max_features=12, stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(valid_docs)
        scores = np.asarray(tfidf_matrix.sum(axis=0)).ravel()
        feature_names = vectorizer.get_feature_names_out()
        top_indices = scores.argsort()[::-1][:3]
        top_keywords = [feature_names[i] for i in top_indices if scores[i] > 0]

        if not top_keywords:
            return (f"Emerging Scam Cluster #{fallback_index}", [])

        readable_name = " / ".join(keyword.title() for keyword in top_keywords)
        return readable_name, top_keywords

    # ------------------------------------------------------------------ #
    # Lifecycle policies
    # ------------------------------------------------------------------ #
    def merge_similar_clusters(
        self,
        clusters: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Merge clusters within the same batch that have similar keywords or centroids.
        This prevents duplicate clusters like "Urgent / Loan / Upi" and "Loan / Urgent / Emi".
        """
        if len(clusters) <= 1:
            return clusters
        
        merged: List[Dict[str, Any]] = []
        used_indices: set[int] = set()
        
        # Debug: print cluster count (can be removed in production)
        # print(f"[DEBUG] merge_similar_clusters: Processing {len(clusters)} clusters")
        
        # Sort clusters by size (descending) to merge larger into smaller, preserving larger cluster names
        sorted_clusters = sorted(clusters, key=lambda c: c.get("size", 0), reverse=True)
        
        # First pass: merge clusters with identical keywords (most aggressive)
        for i, cluster_a in enumerate(sorted_clusters):
            if i in used_indices:
                continue
            
            keywords_a = set(kw.lower().strip() for kw in cluster_a.get("top_keywords", []))
            if not keywords_a:
                continue
            
            # Normalize payment keywords for first pass comparison too
            payment_keywords = {"upi", "emi", "paytm", "pay", "payment"}
            keywords_a_normalized = set()
            for kw in keywords_a:
                if kw in payment_keywords:
                    keywords_a_normalized.add("payment")
                else:
                    keywords_a_normalized.add(kw)
                
            # Try to merge with other clusters that have identical keywords (after normalization)
            merged_cluster = cluster_a.copy()
            for j, cluster_b in enumerate(sorted_clusters[i + 1:], start=i + 1):
                if j in used_indices:
                    continue
                
                keywords_b = set(kw.lower().strip() for kw in cluster_b.get("top_keywords", []))
                # Normalize keywords_b too
                keywords_b_normalized = set()
                for kw in keywords_b:
                    if kw in payment_keywords:
                        keywords_b_normalized.add("payment")
                    else:
                        keywords_b_normalized.add(kw)
                
                # Merge if normalized keywords are identical (treats UPI/EMI as same)
                if keywords_a_normalized == keywords_b_normalized:
                    merged_cluster = self._merge_cluster_payloads(merged_cluster, cluster_b)
                    used_indices.add(j)
            
            # Add cluster (merged or not) to results
            merged.append(merged_cluster)
            used_indices.add(i)
        
        # Second pass: merge remaining clusters with similar keywords/centroids (only unmerged ones)
        for i, cluster_a in enumerate(sorted_clusters):
            if i in used_indices:
                continue
            
            # Try to merge with other clusters
            merged_cluster = cluster_a.copy()
            for j, cluster_b in enumerate(sorted_clusters[i + 1:], start=i + 1):
                if j in used_indices:
                    continue
                
                # Check keyword overlap (Jaccard similarity)
                # Use merged_cluster's keywords (which may have been updated from previous merges)
                keywords_a = set(kw.lower().strip() for kw in merged_cluster.get("top_keywords", []))
                keywords_b = set(kw.lower().strip() for kw in cluster_b.get("top_keywords", []))
                
                # Normalize payment-related keywords (upi, emi, paytm, etc. are equivalent in scam context)
                payment_keywords = {"upi", "emi", "paytm", "pay", "payment"}
                
                # Normalize keywords for comparison: replace payment keywords with generic "payment"
                keywords_a_normalized = set()
                keywords_b_normalized = set()
                
                for kw in keywords_a:
                    if kw in payment_keywords:
                        keywords_a_normalized.add("payment")
                    else:
                        keywords_a_normalized.add(kw)
                
                for kw in keywords_b:
                    if kw in payment_keywords:
                        keywords_b_normalized.add("payment")
                    else:
                        keywords_b_normalized.add(kw)
                
                # Check if both have payment keywords (for special handling)
                has_payment_a = bool(keywords_a & payment_keywords)
                has_payment_b = bool(keywords_b & payment_keywords)
                
                if keywords_a_normalized and keywords_b_normalized:
                    intersection = keywords_a_normalized & keywords_b_normalized
                    union = keywords_a_normalized | keywords_b_normalized
                    keyword_similarity = len(intersection) / len(union) if union else 0.0
                    
                    # Also calculate original intersection for fallback checks
                    original_intersection = keywords_a & keywords_b
                else:
                    keyword_similarity = 0.0
                    original_intersection = set()
                
                # Check centroid similarity
                centroid_a = merged_cluster.get("centroid")
                centroid_b = cluster_b.get("centroid")
                centroid_similarity = 0.0
                
                if centroid_a and centroid_b:
                    try:
                        vec_a = np.array(centroid_a, dtype=np.float64)
                        vec_b = np.array(centroid_b, dtype=np.float64)
                        centroid_similarity = float(cosine_similarity([vec_a], [vec_b])[0][0])
                    except Exception:
                        pass
                
                # Merge if:
                # 1. Keywords are identical (100% overlap) - merge immediately
                # 2. High keyword overlap (>= 40% - lowered for better merging) OR high centroid similarity (>= 0.70)
                # 3. If 2+ keywords match (even if similarity < 40%), merge if they're clearly the same scam type
                # 4. If cluster names are very similar (for cases where keywords might differ slightly)
                should_merge = False
                
                # Check name similarity as a fallback
                name_a = merged_cluster.get("name", "").lower()
                name_b = cluster_b.get("name", "").lower()
                name_words_a = set(name_a.split(" / "))
                name_words_b = set(name_b.split(" / "))
                name_overlap = len(name_words_a & name_words_b) / max(len(name_words_a | name_words_b), 1)
                
                if keyword_similarity >= 1.0:  # Identical keywords - ALWAYS merge
                    should_merge = True
                elif keyword_similarity >= 0.4 or centroid_similarity >= 0.70:
                    should_merge = True
                elif len(intersection) >= 2:  # At least 2 keywords match - likely same scam type
                    should_merge = True
                elif len(original_intersection) >= 2:  # At least 2 original keywords match
                    # Additional check: if they share core scam keywords, merge them
                    core_scam_keywords = {"loan", "otp", "job", "invest", "crypto", "urgent", "verify", "kyc", "work", "hiring"}
                    shared_core = original_intersection & core_scam_keywords
                    # If both have payment keywords, count as shared (they're equivalent)
                    if has_payment_a and has_payment_b:
                        shared_core = shared_core | {"payment"}
                    
                    if len(shared_core) >= 2:  # Share at least 2 core scam keywords
                        should_merge = True
                    # Special case: if they share "loan" and "urgent" (core loan scam pattern), merge even if payment term differs
                    elif "loan" in original_intersection and "urgent" in original_intersection:
                        should_merge = True
                elif name_overlap >= 0.67 and len(intersection) >= 1:  # 2/3 name words match and at least 1 keyword
                    should_merge = True
                
                if should_merge:
                    merged_cluster = self._merge_cluster_payloads(merged_cluster, cluster_b)
                    used_indices.add(j)
            
            merged.append(merged_cluster)
            used_indices.add(i)
        
        # Debug: print merge result (can be removed in production)
        # print(f"[DEBUG] merge_similar_clusters: Reduced {len(clusters)} clusters to {len(merged)} clusters")
        return merged
    
    def merge_with_existing(
        self,
        new_clusters: List[Dict[str, Any]],
        existing_clusters: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Match new clusters to existing ones via centroid cosine similarity in order
        to preserve stable cluster IDs and histories.
        """
        if not existing_clusters:
            return new_clusters

        existing_vectors = []
        existing_ids = []
        for cluster in existing_clusters:
            centroid = cluster.get("centroid")
            if centroid is None:
                continue
            existing_vectors.append(np.array(centroid, dtype=np.float64))
            existing_ids.append(cluster["cluster_id"])

        if not existing_vectors:
            return new_clusters

        existing_matrix = np.vstack(existing_vectors)

        merged_results: List[Dict[str, Any]] = []
        matched_existing: set[str] = set()

        for new_cluster in new_clusters:
            centroid = np.array(new_cluster["centroid"], dtype=np.float64)
            similarities = cosine_similarity([centroid], existing_matrix)[0]
            best_idx = int(np.argmax(similarities))
            best_score = similarities[best_idx]

            if best_score >= self.similarity_threshold:
                matched_id = existing_ids[best_idx]
                matched_existing.add(matched_id)
                merged_cluster = self._merge_cluster_payloads(
                    existing_clusters[best_idx],
                    new_cluster,
                )
                merged_results.append(merged_cluster)
            else:
                merged_results.append(new_cluster)

        # Carry forward unmatched historical clusters with lifecycle updates
        for cluster in existing_clusters:
            if cluster["cluster_id"] in matched_existing:
                continue
            merged_results.append(cluster)

        return merged_results

    def apply_lifecycle_rules(
        self,
        clusters: List[Dict[str, Any]],
        now: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        - Mark clusters inactive if size < 3 or no updates in 30 days
        - Promote large emerging groups automatically
        """
        now = now or datetime.now(timezone.utc)
        cutoff = now - timedelta(days=30)

        for cluster in clusters:
            updated_at: datetime = cluster.get("updated_at", now)
            # Ensure both datetimes are timezone-aware for comparison
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=timezone.utc)
            if cutoff.tzinfo is None:
                cutoff = cutoff.replace(tzinfo=timezone.utc)
            
            size = cluster.get("size", 0)
            if size < 3 or (updated_at < cutoff):
                cluster["active"] = False
            else:
                cluster["active"] = True
        return clusters

    def detect_emerging_clusters(
        self,
        noise_samples: Sequence[ClusterSample],
    ) -> List[Dict[str, Any]]:
        """
        Identify large homogeneous groups among HDBSCAN noise points.
        """
        groups: Dict[str, List[ClusterSample]] = defaultdict(list)
        for sample in noise_samples:
            signature_tokens = tuple(sorted(flag.lower() for flag in sample.pattern_flags)[:3])
            key = "|".join(signature_tokens) or sample.message.lower()[:32]
            groups[key].append(sample)

        emerging_clusters = []
        for _, samples in groups.items():
            if len(samples) < 15:
                continue
            avg_score = statistics.mean(sample.threat_score for sample in samples)
            if avg_score < 60:
                continue
            centroid = np.vstack([sample.vector for sample in samples]).mean(axis=0)
            name = f"Emerging Scam Cluster #{len(emerging_clusters) + 1}"
            top_keywords = self._top_keywords_from_samples(samples)
            emerging_clusters.append(
                {
                    "cluster_id": str(uuid4()),
                    "name": name,
                    "members": [sample.receiver for sample in samples],
                    "size": len(samples),
                    "avg_score": round(avg_score, 1),
                    "top_keywords": top_keywords,
                    "centroid": centroid.tolist(),
                    "updated_at": datetime.now(timezone.utc),
                    "active": True,
                }
            )
        return emerging_clusters

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _merge_cluster_payloads(
        self,
        existing: Dict[str, Any],
        new: Dict[str, Any],
    ) -> Dict[str, Any]:
        merged_members = sorted(set(existing.get("members", []) + new.get("members", [])))
        merged_keywords = self._merge_keywords(
            existing.get("top_keywords", []),
            new.get("top_keywords", []),
        )
        merged_size = len(merged_members)
        avg_score = round(
            statistics.mean(
                [existing.get("avg_score", 0), new.get("avg_score", 0)]
            ),
            1,
        )
        centroid = np.mean(
            np.vstack(
                [
                    np.array(existing.get("centroid"), dtype=np.float64),
                    np.array(new.get("centroid"), dtype=np.float64),
                ]
            ),
            axis=0,
        )
        return {
            **existing,
            "members": merged_members,
            "size": merged_size,
            "avg_score": avg_score,
            "top_keywords": merged_keywords,
            "centroid": centroid.tolist(),
            "updated_at": datetime.now(timezone.utc),
            "active": True,
        }

    def _merge_keywords(self, lhs: Sequence[str], rhs: Sequence[str]) -> List[str]:
        merged = Counter({kw: 1 for kw in lhs})
        merged.update({kw: 1 for kw in rhs})
        return [kw for kw, _ in merged.most_common(5)]

    def _top_keywords_from_samples(
        self,
        samples: Sequence[ClusterSample],
    ) -> List[str]:
        words = Counter()
        for sample in samples:
            for flag in sample.pattern_flags:
                words[flag.lower()] += 1
        return [word for word, _ in words.most_common(5)]

    def _encode_text(self, text: str) -> NDArray[np.float64]:
        embedding = self.embedding_model.encode([text])[0]
        norm = np.linalg.norm(embedding)
        if norm != 0:
            embedding = embedding / norm
        return np.array(embedding, dtype=np.float64)


__all__ = ["DynamicClusterEngine", "ClusterSample"]

