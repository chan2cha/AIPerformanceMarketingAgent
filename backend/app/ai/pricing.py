import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True, slots=True)
class UnitPrice:
    input_per_million_usd: Decimal
    cached_input_per_million_usd: Decimal
    output_per_million_usd: Decimal


class PricingCatalog:
    def __init__(self, path: Path | None = None) -> None:
        catalog_path = path or Path(__file__).with_name("pricing.json")
        self._data = json.loads(catalog_path.read_text(encoding="utf-8"))

    def get(self, provider: str, model: str) -> UnitPrice:
        provider_prices = self._data[provider]
        configured_model = next(
            (
                candidate
                for candidate in sorted(provider_prices, key=len, reverse=True)
                if model == candidate or model.startswith(f"{candidate}-")
            ),
            None,
        )
        if configured_model is None:
            raise KeyError(f"Pricing is not configured for {provider}/{model}")
        values = provider_prices[configured_model]
        return UnitPrice(
            input_per_million_usd=Decimal(values["input_per_million_usd"]),
            cached_input_per_million_usd=Decimal(
                values["cached_input_per_million_usd"]
            ),
            output_per_million_usd=Decimal(values["output_per_million_usd"]),
        )

    def estimate(
        self,
        provider: str,
        model: str,
        input_units: int,
        output_units: int,
        cached_input_units: int = 0,
    ) -> Decimal:
        if cached_input_units < 0 or cached_input_units > input_units:
            raise ValueError("cached input units must be between zero and input units")
        price = self.get(provider, model)
        million = Decimal(1_000_000)
        uncached_input_units = input_units - cached_input_units
        return (
            Decimal(uncached_input_units) * price.input_per_million_usd
            + Decimal(cached_input_units) * price.cached_input_per_million_usd
            + Decimal(output_units) * price.output_per_million_usd
        ) / million
