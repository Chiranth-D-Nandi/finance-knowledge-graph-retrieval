"""Entity Registry Builder: creates canonical entity mastering table with aliases and metadata."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from pydantic import BaseModel, Field

from src.config import settings

logger = logging.getLogger("fin_nexus.entity_registry")


class EntityRecord(BaseModel):
    ticker: str = Field(..., description="Canonical stock ticker symbol")
    cik: str = Field(..., description="10-digit zero-padded SEC Central Index Key")
    name: str = Field(..., description="Canonical legal corporate name")
    aliases: List[str] = Field(default_factory=list, description="Common corporate aliases and colloquial names")
    sector: str = Field(..., description="GICS Sector")
    isin: Optional[str] = Field(default=None, description="International Securities Identification Number")
    qid: Optional[str] = Field(default=None, description="Wikidata item ID")
    description: str = Field(default="", description="Business profile description")


# Curated high-precision alias map for S&P 50 universe
CURATED_ENTITY_METADATA: Dict[str, Dict[str, Any]] = {
    "AAPL": {
        "aliases": ["Apple", "Apple Inc.", "Apple Computer", "Cupertino"],
        "qid": "Q312",
        "description": "Designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and services.",
    },
    "MSFT": {
        "aliases": ["Microsoft", "Microsoft Corporation", "Microsoft Corp", "Redmond"],
        "qid": "Q2283",
        "description": "Develops software, services, devices and solutions, including Windows, Azure cloud, Office 365, and AI.",
    },
    "GOOGL": {
        "aliases": ["Google", "Alphabet", "Alphabet Inc.", "Google LLC", "Mountain View"],
        "qid": "Q95",
        "description": "Global technology company specializing in online search, cloud computing, software, and hardware.",
    },
    "AMZN": {
        "aliases": ["Amazon", "Amazon.com", "Amazon.com Inc.", "AWS", "Seattle"],
        "qid": "Q3884",
        "description": "E-commerce retailer, cloud computing provider through AWS, digital streaming, and artificial intelligence.",
    },
    "NVDA": {
        "aliases": ["Nvidia", "NVIDIA Corporation", "Nvidia Corp", "Santa Clara"],
        "qid": "Q182477",
        "description": "Pioneered accelerated computing, designing GPUs for gaming, datacenter AI acceleration, and autonomous vehicles.",
    },
    "BRK.B": {
        "aliases": ["Berkshire", "Berkshire Hathaway", "Berkshire Hathaway Inc.", "Omaha"],
        "qid": "Q478214",
        "description": "Conglomerate holding company engaged in insurance, freight rail transportation, utility and energy, manufacturing.",
    },
    "META": {
        "aliases": ["Meta", "Meta Platforms", "Facebook", "Facebook Inc.", "Menlo Park"],
        "qid": "Q380",
        "description": "Builds technologies that help people connect, find communities, and grow businesses across Instagram, WhatsApp, VR.",
    },
    "TSLA": {
        "aliases": ["Tesla", "Tesla Inc.", "Tesla Motors", "Austin"],
        "qid": "Q478214",
        "description": "Designs, develops, manufactures, sells, and leases fully electric vehicles, energy generation and storage systems.",
    },
    "JPM": {
        "aliases": ["JPMorgan", "JP Morgan", "JPMorgan Chase", "JPMorgan Chase & Co.", "Chase", "Morgan Guaranty"],
        "qid": "Q334303",
        "description": "Global financial services firm and banking institution offering investment banking, commercial banking, and asset management.",
    },
    "JNJ": {
        "aliases": ["Johnson & Johnson", "J&J", "Johnson and Johnson"],
        "qid": "Q333215",
        "description": "Healthcare products company researching, developing, and manufacturing pharmaceuticals and medical technologies.",
    },
    "V": {
        "aliases": ["Visa", "Visa Inc."],
        "qid": "Q185871",
        "description": "Digital payments network facilitating transactions between consumers, merchants, financial institutions, and government entities.",
    },
    "UNH": {
        "aliases": ["UnitedHealth", "UnitedHealth Group", "UnitedHealthcare", "Optum"],
        "qid": "Q2092505",
        "description": "Diversified healthcare company providing medical benefits through UnitedHealthcare and information/technology-enabled services through Optum.",
    },
    "XOM": {
        "aliases": ["Exxon", "ExxonMobil", "Exxon Mobil", "Exxon Mobil Corp", "Standard Oil"],
        "qid": "Q156238",
        "description": "International energy company exploring and producing crude oil and natural gas, manufacturing petroleum products and petrochemicals.",
    },
    "WMT": {
        "aliases": ["Walmart", "Wal-Mart", "Walmart Inc.", "Wal-Mart Stores"],
        "qid": "Q483551",
        "description": "Operates retail and wholesale stores, discount departmental stores, supercenters, and eCommerce platforms worldwide.",
    },
    "MA": {
        "aliases": ["Mastercard", "Mastercard Inc.", "MasterCard Incorporated"],
        "qid": "Q144799",
        "description": "Global payments technology company connecting consumers, financial institutions, merchants, and governments.",
    },
    "PG": {
        "aliases": ["Procter & Gamble", "P&G", "Procter and Gamble"],
        "qid": "Q157790",
        "description": "Manufactures and markets branded consumer packaged goods across beauty, grooming, health care, fabric and home care.",
    },
    "HD": {
        "aliases": ["Home Depot", "The Home Depot", "Home Depot Inc."],
        "qid": "Q864407",
        "description": "Home improvement retailer selling building materials, home improvement products, lawn and garden products, and decor.",
    },
    "CVX": {
        "aliases": ["Chevron", "Chevron Corporation", "Chevron Corp", "Texaco"],
        "qid": "Q319642",
        "description": "Integrated energy operations managing exploration and production, refining, marketing, and chemical manufacturing.",
    },
    "BAC": {
        "aliases": ["Bank of America", "BofA", "BofA Securities", "Merrill Lynch", "Countrywide"],
        "qid": "Q487907",
        "description": "Financial institution providing banking, investing, asset management and other financial and risk-management products.",
    },
    "ABBV": {
        "aliases": ["AbbVie", "AbbVie Inc."],
        "qid": "Q2820982",
        "description": "Research-based biopharmaceutical company developing immunology, oncology, neuroscience, and eye care therapies.",
    },
    "PFE": {
        "aliases": ["Pfizer", "Pfizer Inc."],
        "qid": "Q206921",
        "description": "Discovers, develops, manufactures, marketing, sales and distributes biopharmaceutical products and vaccines.",
    },
    "AVGO": {
        "aliases": ["Broadcom", "Broadcom Inc.", "Avago Technologies"],
        "qid": "Q2925586",
        "description": "Designs, develops, and supplies semiconductor devices and enterprise software infrastructure solutions.",
    },
    "KO": {
        "aliases": ["Coca-Cola", "Coca Cola", "The Coca-Cola Company", "Coke"],
        "qid": "Q3295867",
        "description": "Non-alcoholic beverage company manufacturing, marketing, and selling sparkling soft drinks, water, juices, and coffee.",
    },
    "COST": {
        "aliases": ["Costco", "Costco Wholesale", "Costco Wholesale Corp"],
        "qid": "Q715583",
        "description": "Operates membership warehouses offering low prices on a limited selection of branded and private-label products.",
    },
    "MRK": {
        "aliases": ["Merck", "Merck & Co.", "Merck Sharp & Dohme", "MSD"],
        "qid": "Q1417318",
        "description": "Global healthcare company delivering innovative health solutions through prescription medicines, vaccines, and animal health products.",
    },
    "PEP": {
        "aliases": ["PepsiCo", "Pepsi", "PepsiCo Inc.", "Frito-Lay"],
        "qid": "Q334800",
        "description": "Food and beverage company manufacturing and marketing snacks, carbonated beverages, grain-based foods, and juices.",
    },
    "ADBE": {
        "aliases": ["Adobe", "Adobe Systems", "Adobe Inc."],
        "qid": "Q11463",
        "description": "Diversified software company offering creative cloud tools, digital marketing, and document management solutions.",
    },
    "DHR": {
        "aliases": ["Danaher", "Danaher Corporation", "Danaher Corp"],
        "qid": "Q1159239",
        "description": "Global science and technology innovator designing medical diagnostics, life sciences, and biotechnology equipment.",
    },
    "CRM": {
        "aliases": ["Salesforce", "Salesforce.com", "Salesforce Inc."],
        "qid": "Q34484",
        "description": "Customer relationship management technology provider offering cloud applications for sales, service, marketing, and analytics.",
    },
    "NFLX": {
        "aliases": ["Netflix", "Netflix Inc."],
        "qid": "Q907311",
        "description": "Entertainment service with paid memberships in over 190 countries streaming TV series, documentaries, feature films, and games.",
    },
    "WFC": {
        "aliases": ["Wells Fargo", "Wells Fargo & Company", "Wells Fargo Bank"],
        "qid": "Q744149",
        "description": "Diversified financial services company providing banking, investment and mortgage products and services.",
    },
    "AMD": {
        "aliases": ["Advanced Micro Devices", "AMD", "AMD Inc."],
        "qid": "Q128896",
        "description": "Semiconductor company developing computer processors and related technologies for business and consumer markets.",
    },
}


class EntityRegistryBuilder:
    def __init__(self, entities_csv_path: Optional[Path] = None, output_json_path: Optional[Path] = None):
        self.csv_path = entities_csv_path or (settings.ENTITIES_RAW_DIR / "sp500_constituents_20230101.csv")
        self.output_path = output_json_path or (settings.ENTITIES_RAW_DIR / "entity_registry.json")

    def build(self) -> List[Dict[str, Any]]:
        """Construct the canonical entity registry from constituents CSV and curated metadata."""
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Constituents CSV not found: {self.csv_path}")

        df = pd.read_csv(self.csv_path)
        records: List[Dict[str, Any]] = []

        for _, row in df.iterrows():
            ticker = str(row["ticker"]).strip().upper()
            cik = str(row["cik"]).strip().zfill(10)
            name = str(row["name"]).strip()
            sector = str(row["sector"]).strip()

            curated = CURATED_ENTITY_METADATA.get(ticker, {})
            aliases = set(curated.get("aliases", []))
            aliases.add(name)
            aliases.add(ticker)
            aliases.add(ticker.replace(".", " "))

            qid = curated.get("qid", None)
            desc = curated.get("description", f"{name} is an S&P 500 company operating in the {sector} sector.")

            record = EntityRecord(
                ticker=ticker,
                cik=cik,
                name=name,
                aliases=sorted(list(aliases)),
                sector=sector,
                isin=f"US{cik[:10]}",
                qid=qid,
                description=desc,
            )
            records.append(record.model_dump())

        # Write to JSON
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)

        logger.info("Constructed entity registry with %d entities at %s", len(records), self.output_path)
        return records


def load_entity_registry(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load canonical entity registry records from disk."""
    p = path or (settings.ENTITIES_RAW_DIR / "entity_registry.json")
    if not p.exists():
        builder = EntityRegistryBuilder(output_json_path=p)
        return builder.build()
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)
