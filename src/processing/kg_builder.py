"""Temporal Knowledge Graph construction using NetworkX and Parquet persistence."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import networkx as nx
import pandas as pd

from src.config import settings

logger = logging.getLogger("fin_nexus.kg_builder")


class TemporalKGBuilder:
    """
    Constructs a temporal knowledge graph representing financial entities,
    filing events, disclosures, XBRL metrics, and point-in-time relations.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or settings.PROCESSED_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.graph = nx.MultiDiGraph()

    def build_graph(
        self,
        entity_registry: List[Dict[str, Any]],
        chunks: List[Dict[str, Any]],
        xbrl_facts: Optional[pd.DataFrame] = None,
    ) -> nx.MultiDiGraph:
        """Populate the graph nodes and temporal edges."""
        self.graph.clear()

        # 1. Company Nodes
        for ent in entity_registry:
            node_id = f"company:{ent['ticker']}"
            self.graph.add_node(
                node_id,
                node_type="Company",
                ticker=ent["ticker"],
                cik=ent["cik"],
                name=ent["name"],
                sector=ent.get("sector", ""),
                qid=ent.get("qid", ""),
            )

        # 2. Filing Nodes & Issues Edges
        seen_filings = set()
        for c in chunks:
            filing_id = f"filing:{c['ticker']}:{c['form']}:{c['filing_date']}"
            if filing_id not in seen_filings:
                seen_filings.add(filing_id)
                self.graph.add_node(
                    filing_id,
                    node_type="Filing",
                    ticker=c["ticker"],
                    form=c["form"],
                    filing_date=c["filing_date"],
                    source_url=c.get("source_url", ""),
                )
                company_node = f"company:{c['ticker']}"
                self.graph.add_edge(
                    company_node,
                    filing_id,
                    relation="issues",
                    timestamp=c["filing_date"],
                )

            # Mentions edge if chunk tags other entities
            for ment_ticker in c.get("entities", []):
                if ment_ticker != c["ticker"]:
                    target_company = f"company:{ment_ticker}"
                    if self.graph.has_node(target_company):
                        self.graph.add_edge(
                            filing_id,
                            target_company,
                            relation="mentions",
                            timestamp=c["filing_date"],
                            section=c.get("section", ""),
                        )

        # 3. XBRL Fact Nodes & Reports Edges
        if xbrl_facts is not None and not xbrl_facts.empty:
            for _, row in xbrl_facts.iterrows():
                fact_node = f"fact:{row['ticker']}:{row['fact']}:{row['period_end']}"
                if not self.graph.has_node(fact_node):
                    self.graph.add_node(
                        fact_node,
                        node_type="FinancialFact",
                        ticker=row["ticker"],
                        fact=row["fact"],
                        value=row["value"],
                        unit=row.get("unit", "USD"),
                        period_end=row["period_end"],
                    )
                filing_id = f"filing:{row['ticker']}:{row['form']}:{row['filing_date']}"
                if self.graph.has_node(filing_id):
                    self.graph.add_edge(
                        filing_id,
                        fact_node,
                        relation="reports",
                        timestamp=row["filing_date"],
                    )

        logger.info(
            "Constructed Temporal KG: %d nodes, %d edges.",
            self.graph.number_of_nodes(),
            self.graph.number_of_edges(),
        )
        return self.graph

    def export_parquet(self) -> Tuple[Path, Path]:
        """Export nodes and edges to Parquet files."""
        nodes_data = []
        for node_id, attrs in self.graph.nodes(data=True):
            rec = {"node_id": node_id}
            rec.update(attrs)
            nodes_data.append(rec)
        nodes_df = pd.DataFrame(nodes_data)

        edges_data = []
        for u, v, k, attrs in self.graph.edges(keys=True, data=True):
            rec = {"source": u, "target": v, "key": k}
            rec.update(attrs)
            edges_data.append(rec)
        edges_df = pd.DataFrame(edges_data)

        nodes_path = self.output_dir / "kg_nodes.parquet"
        edges_path = self.output_dir / "kg_edges.parquet"

        nodes_df.to_parquet(nodes_path, index=False)
        edges_df.to_parquet(edges_path, index=False)

        logger.info("Saved KG nodes to %s, edges to %s", nodes_path, edges_path)
        return nodes_path, edges_path

    def get_ticker_timeline(
        self,
        ticker: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Query chronological timeline of events for an entity from the graph."""
        timeline: List[Dict[str, Any]] = []
        company_node = f"company:{ticker.upper()}"

        if not self.graph.has_node(company_node):
            return timeline

        # Find filings issued by company
        for _, filing_node, attrs in self.graph.out_edges(company_node, data=True):
            if attrs.get("relation") == "issues":
                f_data = self.graph.nodes[filing_node]
                f_date = f_data.get("filing_date", "")
                if from_date and f_date < from_date:
                    continue
                if to_date and f_date > to_date:
                    continue

                timeline.append({
                    "date": f_date,
                    "type": f_data.get("form", "Filing"),
                    "title": f"{f_data.get('form')} Filing - {ticker}",
                    "summary": f"{ticker} submitted official {f_data.get('form')} disclosure to the SEC.",
                    "source_url": f_data.get("source_url", ""),
                    "node_id": filing_node,
                })

        timeline.sort(key=lambda x: x["date"], reverse=True)
        return timeline
