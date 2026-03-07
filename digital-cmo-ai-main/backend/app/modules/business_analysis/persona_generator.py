"""
Buyer Persona Generator

Generates detailed buyer personas using clustering logic on customer
attributes, behavioral data, and demographic patterns. Supports both
data-driven clustering (when customer data is available) and
LLM-powered persona synthesis for market-based generation.
"""

import json
import logging
import math
from collections import Counter
from datetime import datetime
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


PERSONA_GENERATION_TEMPLATE = """You are a senior marketing strategist specialising in buyer persona development.

Generate {num_personas} detailed, realistic buyer personas for:

**Product/Company:** {subject}
**Industry:** {industry}
**Target Market:** {target_market}
**Context:** {context}

{data_context}

{cluster_insights}

{domain_context}

For each persona, provide comprehensive detail. Return your analysis as a JSON object with this EXACT structure:
{{
    "subject": "{subject}",
    "industry": "{industry}",
    "generated_at": "<ISO timestamp>",
    "methodology": "<data-driven|market-research|hybrid>",
    "personas": [
        {{
            "id": "<persona_1>",
            "name": "<realistic fictional name>",
            "title": "<short persona title, e.g. 'The Tech-Savvy Manager'>",
            "photo_description": "<description for AI image generation>",
            "demographics": {{
                "age_range": "<e.g. 28-35>",
                "gender": "<male|female|non-binary|any>",
                "location": "<geographic location>",
                "education": "<education level>",
                "income_range": "<annual income range>",
                "family_status": "<single|married|parent|etc.>"
            }},
            "professional": {{
                "job_title": "<current job title>",
                "company_size": "<startup|SMB|mid-market|enterprise>",
                "industry": "<their industry>",
                "years_experience": "<range>",
                "decision_making_role": "<decision-maker|influencer|end-user|gatekeeper>",
                "reports_to": "<their manager's title>"
            }},
            "psychographics": {{
                "values": ["<value 1>", "<value 2>"],
                "personality_traits": ["<trait 1>", "<trait 2>"],
                "lifestyle": "<brief lifestyle description>",
                "tech_savviness": "high|medium|low"
            }},
            "goals_and_motivations": [
                {{
                    "goal": "<specific goal>",
                    "motivation": "<why this matters to them>",
                    "priority": "high|medium|low"
                }}
            ],
            "pain_points": [
                {{
                    "pain_point": "<specific challenge>",
                    "severity": "high|medium|low",
                    "current_solution": "<how they currently address this>"
                }}
            ],
            "buying_behavior": {{
                "research_channels": ["<channel 1>", "<channel 2>"],
                "decision_factors": ["<factor 1>", "<factor 2>"],
                "objections": ["<common objection 1>"],
                "budget_authority": "full|partial|none",
                "buying_cycle_length": "<typical duration>",
                "preferred_content_types": ["<type 1>", "<type 2>"]
            }},
            "communication_preferences": {{
                "preferred_channels": ["<email|phone|social|chat|in-person>"],
                "best_time_to_reach": "<time/day preference>",
                "communication_style": "<formal|casual|technical|visual>",
                "social_media_platforms": ["<platform 1>", "<platform 2>"]
            }},
            "brand_affinities": ["<brands they trust/use>"],
            "day_in_the_life": "<brief narrative of a typical day>",
            "quote": "<a characteristic quote from this persona>",
            "marketing_message": "<ideal marketing message for this persona>",
            "content_topics": ["<topic they'd engage with>"],
            "cluster_id": <cluster number if data-driven, else null>
        }}
    ],
    "persona_comparison": {{
        "key_differences": ["<difference 1>", "<difference 2>"],
        "common_threads": ["<commonality 1>", "<commonality 2>"],
        "coverage_gaps": ["<segment not covered>"]
    }},
    "targeting_recommendations": [
        {{
            "persona_id": "<persona_1>",
            "channel": "<best marketing channel>",
            "message_theme": "<key message theme>",
            "content_format": "<blog|video|webinar|case-study|etc.>"
        }}
    ]
}}

Make personas distinct, realistic, and actionable. Return ONLY valid JSON.
"""


class PersonaGenerator:
    """
    Buyer persona generator with data-driven clustering and
    LLM-powered persona synthesis.
    """

    def __init__(
        self,
        llm_client=None,
        trends_client=None,
        news_client=None,
    ):
        self.llm = llm_client
        self.trends_client = trends_client
        self.news_client = news_client

    async def generate_personas(
        self,
        subject: str,
        industry: str = "",
        target_market: str = "",
        num_personas: int = 3,
        customer_data: Optional[list[dict]] = None,
        context: Optional[dict] = None,
        domain_profile: Optional[dict] = None,
    ) -> dict:
        """
        Generate buyer personas, optionally using customer data clustering.

        Args:
            subject: Product or company name.
            industry: Industry context.
            target_market: Target market description.
            num_personas: Number of personas to generate (1-6).
            customer_data: Optional list of customer attribute dicts for clustering.
            context: Additional context.
            domain_profile: Domain profile with persona templates.

        Returns:
            Structured persona generation result.
        """
        context = context or {}
        num_personas = max(1, min(num_personas, 6))

        cluster_insights = ""
        data_context = ""
        domain_context = ""

        # Data-driven clustering if customer data is provided
        if customer_data and len(customer_data) >= num_personas:
            cluster_result = self._cluster_customers(customer_data, num_personas)
            cluster_insights = self._format_cluster_insights(cluster_result)

        # Gather market data context
        data_context = await self._gather_market_context(subject, industry)

        # Domain-specific persona guidance
        if domain_profile:
            persona_templates = domain_profile.get("persona_templates", [])
            if persona_templates:
                templates_text = json.dumps(persona_templates, indent=2)
                domain_context = (
                    f"Industry-typical persona archetypes for reference:\n{templates_text}"
                )

        prompt = PERSONA_GENERATION_TEMPLATE.format(
            num_personas=num_personas,
            subject=subject,
            industry=industry or "General",
            target_market=target_market or "General market",
            context=json.dumps(context, default=str),
            data_context=data_context,
            cluster_insights=cluster_insights,
            domain_context=domain_context,
        )

        raw_response = await self._call_llm(prompt)
        result = self._parse_json_response(raw_response)

        if not result:
            result = self._build_fallback_personas(subject, industry, num_personas)

        result["metadata"] = {
            "subject": subject,
            "industry": industry,
            "num_personas_requested": num_personas,
            "data_driven": bool(customer_data),
            "customer_data_points": len(customer_data) if customer_data else 0,
            "generated_at": datetime.utcnow().isoformat(),
        }

        return {
            "personas": result,
            "type": "persona_generation",
            "insights": self._extract_persona_insights(result),
        }

    async def refine_persona(
        self,
        persona: dict,
        feedback: str,
    ) -> dict:
        """
        Refine an existing persona based on user feedback.

        Args:
            persona: Existing persona dict to refine.
            feedback: User feedback for refinement.

        Returns:
            Refined persona dict.
        """
        prompt = (
            f"Refine this buyer persona based on the following feedback.\n\n"
            f"Current persona:\n{json.dumps(persona, indent=2)}\n\n"
            f"Feedback: {feedback}\n\n"
            f"Return the refined persona as a JSON object with the same structure. "
            f"Return ONLY valid JSON."
        )

        raw_response = await self._call_llm(prompt)
        refined = self._parse_json_response(raw_response)

        return refined if refined else persona

    # ------------------------------------------------------------------
    # Clustering logic
    # ------------------------------------------------------------------

    def _cluster_customers(
        self,
        customer_data: list[dict],
        n_clusters: int,
    ) -> dict:
        """
        Cluster customer data using a simplified K-means approach.

        Supports numeric and categorical features. Categorical features
        are one-hot encoded before clustering.

        Args:
            customer_data: List of customer attribute dicts.
            n_clusters: Number of clusters to create.

        Returns:
            Dict with cluster assignments, centroids, and statistics.
        """
        if not customer_data:
            return {"clusters": [], "n_clusters": 0}

        # Extract and encode features
        features, feature_names = self._encode_features(customer_data)

        if features.shape[0] < n_clusters:
            n_clusters = features.shape[0]

        # Simple K-means clustering
        labels, centroids = self._kmeans(features, n_clusters, max_iter=100)

        # Build cluster summaries
        clusters = []
        for i in range(n_clusters):
            mask = labels == i
            cluster_indices = np.where(mask)[0]
            cluster_customers = [customer_data[idx] for idx in cluster_indices]

            cluster_summary = {
                "cluster_id": i,
                "size": int(mask.sum()),
                "percentage": round(float(mask.sum()) / len(customer_data) * 100, 1),
                "dominant_attributes": self._get_dominant_attributes(cluster_customers),
                "centroid": {
                    feature_names[j]: round(float(centroids[i][j]), 2)
                    for j in range(len(feature_names))
                    if j < len(centroids[i])
                },
            }
            clusters.append(cluster_summary)

        return {
            "clusters": clusters,
            "n_clusters": n_clusters,
            "total_customers": len(customer_data),
            "feature_names": feature_names,
        }

    def _encode_features(self, data: list[dict]) -> tuple:
        """
        Encode customer data into a numeric feature matrix.

        Numeric fields are normalised; categorical fields are one-hot encoded.
        """
        if not data:
            return np.array([]), []

        # Identify all keys and their types
        all_keys = set()
        for record in data:
            all_keys.update(record.keys())

        numeric_keys = []
        categorical_keys = []

        for key in sorted(all_keys):
            sample_values = [
                r[key] for r in data if key in r and r[key] is not None
            ]
            if not sample_values:
                continue
            if all(isinstance(v, (int, float)) for v in sample_values):
                numeric_keys.append(key)
            else:
                categorical_keys.append(key)

        # Build feature matrix
        feature_names = []
        feature_columns = []

        # Numeric features (normalised)
        for key in numeric_keys:
            values = [float(r.get(key, 0)) for r in data]
            arr = np.array(values, dtype=float)
            std = arr.std()
            if std > 0:
                arr = (arr - arr.mean()) / std
            feature_names.append(key)
            feature_columns.append(arr)

        # Categorical features (one-hot)
        for key in categorical_keys:
            unique_values = sorted(
                set(str(r.get(key, "unknown")) for r in data)
            )
            if len(unique_values) > 10:
                unique_values = unique_values[:10]
            for val in unique_values:
                col = np.array(
                    [1.0 if str(r.get(key, "unknown")) == val else 0.0 for r in data]
                )
                feature_names.append(f"{key}_{val}")
                feature_columns.append(col)

        if not feature_columns:
            return np.zeros((len(data), 1)), ["_placeholder"]

        return np.column_stack(feature_columns), feature_names

    @staticmethod
    def _kmeans(
        X: np.ndarray,
        k: int,
        max_iter: int = 100,
        seed: int = 42,
    ) -> tuple:
        """
        Simple K-means clustering implementation.

        Args:
            X: Feature matrix (n_samples, n_features).
            k: Number of clusters.
            max_iter: Maximum iterations.
            seed: Random seed.

        Returns:
            Tuple of (labels array, centroids array).
        """
        rng = np.random.RandomState(seed)
        n_samples = X.shape[0]

        if n_samples == 0 or k <= 0:
            return np.array([]), np.array([])

        k = min(k, n_samples)

        # Initialise centroids using K-means++
        centroids = np.empty((k, X.shape[1]))
        idx = rng.randint(n_samples)
        centroids[0] = X[idx]

        for c in range(1, k):
            distances = np.min(
                [np.sum((X - centroids[j]) ** 2, axis=1) for j in range(c)],
                axis=0,
            )
            total = distances.sum()
            if total == 0:
                centroids[c] = X[rng.randint(n_samples)]
            else:
                probs = distances / total
                idx = rng.choice(n_samples, p=probs)
                centroids[c] = X[idx]

        labels = np.zeros(n_samples, dtype=int)

        for _ in range(max_iter):
            # Assign clusters
            distances = np.array([
                np.sum((X - centroids[j]) ** 2, axis=1) for j in range(k)
            ])
            new_labels = np.argmin(distances, axis=0)

            if np.array_equal(labels, new_labels):
                break
            labels = new_labels

            # Update centroids
            for j in range(k):
                mask = labels == j
                if mask.sum() > 0:
                    centroids[j] = X[mask].mean(axis=0)

        return labels, centroids

    @staticmethod
    def _get_dominant_attributes(customers: list[dict]) -> dict:
        """Find the most common attribute values in a cluster."""
        if not customers:
            return {}

        all_keys = set()
        for c in customers:
            all_keys.update(c.keys())

        dominant = {}
        for key in sorted(all_keys):
            values = [c[key] for c in customers if key in c and c[key] is not None]
            if not values:
                continue
            if all(isinstance(v, (int, float)) for v in values):
                dominant[key] = {
                    "mean": round(sum(values) / len(values), 2),
                    "min": min(values),
                    "max": max(values),
                }
            else:
                counter = Counter(str(v) for v in values)
                most_common = counter.most_common(3)
                dominant[key] = {
                    "top_values": [
                        {"value": v, "count": c, "percentage": round(c / len(values) * 100, 1)}
                        for v, c in most_common
                    ]
                }

        return dominant

    def _format_cluster_insights(self, cluster_result: dict) -> str:
        """Format cluster analysis results for the LLM prompt."""
        if not cluster_result.get("clusters"):
            return ""

        lines = [
            "Customer data clustering analysis results:",
            f"Total customers analysed: {cluster_result['total_customers']}",
            f"Number of clusters identified: {cluster_result['n_clusters']}",
            "",
        ]

        for cluster in cluster_result["clusters"]:
            lines.append(
                f"Cluster {cluster['cluster_id']} "
                f"({cluster['size']} customers, {cluster['percentage']}%):"
            )
            dominant = cluster.get("dominant_attributes", {})
            for attr, info in list(dominant.items())[:5]:
                if "mean" in info:
                    lines.append(f"  - {attr}: avg={info['mean']}")
                elif "top_values" in info:
                    top = info["top_values"][0] if info["top_values"] else {}
                    lines.append(
                        f"  - {attr}: most common = {top.get('value', 'N/A')} "
                        f"({top.get('percentage', 0)}%)"
                    )
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Data gathering
    # ------------------------------------------------------------------

    async def _gather_market_context(self, subject: str, industry: str) -> str:
        """Gather market context for persona generation."""
        parts = []

        if self.trends_client:
            try:
                queries = await self.trends_client.get_related_queries(subject)
                top = queries.get("top", [])[:5]
                if top:
                    terms = [q.get("query", "") for q in top if q.get("query")]
                    parts.append(f"Related search queries: {', '.join(terms)}")
            except Exception:
                pass

        if self.news_client and self.news_client.is_configured:
            try:
                news = await self.news_client.search_news(
                    f"{subject} customers users", days_back=14, page_size=3
                )
                if news:
                    headlines = [a["title"] for a in news if a.get("title")]
                    parts.append(
                        f"Recent market news: {'; '.join(headlines[:3])}"
                    )
            except Exception:
                pass

        if parts:
            return "Market context data:\n" + "\n".join(parts)
        return ""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _call_llm(self, prompt: str) -> str:
        if self.llm:
            try:
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are a senior marketing strategist specialising in "
                            "buyer persona development. Always return valid JSON. "
                            "No markdown code fences."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ]
                return await self.llm.generate(messages)
            except Exception as exc:
                logger.error("LLM call failed: %s", exc)
                return ""
        return ""

    @staticmethod
    def _parse_json_response(text: str) -> Optional[dict]:
        if not text:
            return None
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            return None

    @staticmethod
    def _build_fallback_personas(subject: str, industry: str, num: int) -> dict:
        personas = []
        archetypes = [
            ("Alex", "The Decision Maker", "35-45"),
            ("Jordan", "The Technical Evaluator", "28-38"),
            ("Sam", "The Budget-Conscious Buyer", "30-40"),
            ("Morgan", "The Innovation Seeker", "25-35"),
            ("Taylor", "The Enterprise Champion", "40-50"),
            ("Casey", "The Practical Implementer", "32-42"),
        ]
        for i in range(min(num, len(archetypes))):
            name, title, age = archetypes[i]
            personas.append({
                "id": f"persona_{i + 1}",
                "name": name,
                "title": title,
                "demographics": {"age_range": age, "gender": "any"},
                "professional": {"job_title": "[Configure LLM for details]"},
                "goals_and_motivations": [{"goal": "[Configure LLM]", "priority": "high"}],
                "pain_points": [{"pain_point": "[Configure LLM]", "severity": "high"}],
                "buying_behavior": {"research_channels": [], "decision_factors": []},
                "cluster_id": None,
            })
        return {
            "subject": subject,
            "industry": industry,
            "methodology": "demo",
            "personas": personas,
            "persona_comparison": {"key_differences": [], "common_threads": [], "coverage_gaps": []},
            "targeting_recommendations": [],
        }

    @staticmethod
    def _extract_persona_insights(result: dict) -> list[dict]:
        insights = []
        personas = result.get("personas", [])
        if isinstance(personas, list):
            insights.append({
                "type": "personas_generated",
                "count": len(personas),
                "titles": [
                    p.get("title", p.get("name", ""))
                    for p in personas
                    if isinstance(p, dict)
                ],
            })
        comparison = result.get("persona_comparison", {})
        if comparison.get("coverage_gaps"):
            insights.append({
                "type": "coverage_gaps",
                "gaps": comparison["coverage_gaps"],
            })
        return insights
