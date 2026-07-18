"""
Entity tracking and fake data replacement.

This module handles:
1. Tracking which real values map to which fake values (entity registry)
2. Generating fake replacements that preserve format
3. Applying replacements to document runs

Design decision: We use a simple dict for the entity registry.
The key is the real value, the value is the fake value.
This is sufficient for a single-document tool.

For faker, we use the faker library to generate realistic-looking
fake data. We seed it for determinism.
"""

import re
from faker import Faker

# Seed for deterministic fake data generation
fake = Faker()
Faker.seed(42)


class EntityRegistry:
    """Maps real PII values to fake replacements.

    Ensures the same real value always maps to the same fake value.
    """

    def __init__(self):
        self._registry: dict[str, str] = {}

    def get_fake(self, real_value: str, pii_type: str) -> str:
        """Get or create a fake replacement for a real value.

        Args:
            real_value: The real PII value.
            pii_type: The type of PII (e.g., "email", "phone", "person").

        Returns:
            The fake replacement value.
        """
        if real_value not in self._registry:
            self._registry[real_value] = self._generate_fake(real_value, pii_type)
        return self._registry[real_value]

    def _generate_fake(self, real_value: str, pii_type: str) -> str:
        """Generate a fake value based on PII type.

        Args:
            real_value: The original value (used as hint for format).
            pii_type: The type of PII.

        Returns:
            A fake value matching the expected format.
        """
        if pii_type == "email":
            return self._generate_fake_email(real_value)
        elif pii_type == "phone":
            return self._generate_fake_phone(real_value)
        elif pii_type == "person":
            return self._generate_fake_name()
        elif pii_type == "company":
            return self._generate_fake_company(real_value)
        elif pii_type == "address":
            return self._generate_fake_address(real_value)
        else:
            return f"[REDACTED {pii_type.upper()}]"

    def _generate_fake_email(self, real_email: str) -> str:
        """Generate a fake email preserving format.

        Preserves: firstname.lastname@domain pattern
        """
        first = fake.first_name().lower()
        last = fake.last_name().lower()
        domain = fake.free_email_domain()
        return f"{first}.{last}@{domain}"

    def _generate_fake_phone(self, real_phone: str) -> str:
        """Generate a fake phone preserving format.

        Preserves: +91 prefix and general structure.
        """
        # Generate a random Indian mobile number
        number = fake.numerify("##########")
        return f"+91 {number}"

    def _generate_fake_name(self) -> str:
        """Generate a fake person name."""
        return fake.name()

    def _generate_fake_address(self, real_value: str) -> str:
        """Generate a fake address preserving structure.

        Parses the original address into components and generates
        fake components that match the structure.
        """
        # Parse components
        components = self._parse_address_components(real_value)

        # Generate fake components
        fake_components = []
        for comp_type, comp_value in components:
            if comp_type == "postal_code":
                fake_components.append(fake.numerify("######"))
            elif comp_type == "city":
                fake_components.append(fake.city())
            elif comp_type == "state":
                # Preserve state from original
                fake_components.append(comp_value)
            elif comp_type == "country":
                # Preserve country from original
                fake_components.append(comp_value)
            elif comp_type == "road":
                fake_components.append(f"{fake.word().title()} Road")
            elif comp_type == "building":
                fake_components.append(
                    f"{fake.word().title()} {fake.random_element(['Tower', 'Building', 'Complex', 'Residency'])}"
                )
            elif comp_type == "house_number":
                fake_components.append(f"Plot No. {fake.numerify('###')}")
            elif comp_type == "village":
                fake_components.append(f"Village {fake.word().title()}")
            elif comp_type == "taluka":
                fake_components.append(f"Taluka {fake.word().title()}")
            else:
                fake_components.append(comp_value)

        return ", ".join(fake_components)

    def _parse_address_components(self, address: str) -> list[tuple[str, str]]:
        """Parse address into typed components."""
        components = []

        # Split by commas
        parts = [p.strip() for p in address.split(",")]

        for part in parts:
            part_lower = part.lower()

            # Postal code
            if re.match(r'(?<!\d)\d{6}(?!\d)', part):
                components.append(("postal_code", part))
            # State
            elif any(state in part_lower for state in [
                "maharashtra", "madhya pradesh", "gujarat", "karnataka",
                "tamil nadu", "uttar pradesh", "haryana", "delhi"
            ]):
                components.append(("state", part))
            # Country
            elif any(country in part_lower for country in [
                "india", "usa", "uk", "united kingdom", "united states"
            ]):
                components.append(("country", part))
            # City
            elif any(city in part_lower for city in [
                "pune", "mumbai", "delhi", "bangalore", "chennai",
                "hyderabad", "kolkata", "ahmednagar", "bhopal"
            ]):
                components.append(("city", part))
            # Road/Street
            elif any(road in part_lower for road in [
                "road", "street", "lane", "marg", "path"
            ]):
                components.append(("road", part))
            # Building/Tower
            elif any(building in part_lower for building in [
                "tower", "building", "complex", "residency", "chambers",
                "apartment", "house", "park", "block", "wing", "floor"
            ]):
                components.append(("building", part))
            # Village
            elif "village" in part_lower:
                components.append(("village", part))
            # Taluka
            elif "taluka" in part_lower:
                components.append(("taluka", part))
            # House/Plot number
            elif re.match(r'^(flat|plot|no|number|unit|s\.?\s*no)', part_lower):
                components.append(("house_number", part))
            # District
            elif "dist" in part_lower or "district" in part_lower:
                components.append(("district", part))
            # Unknown
            else:
                components.append(("unknown", part))

        return components

    def _generate_fake_company(self, real_value: str) -> str:
        """Generate a fake company name preserving legal suffix.

        Detects format from original and preserves:
        - Pvt. Ltd. / Private Limited
        - LLP
        - Bank
        - Trust
        - Limited / Ltd.
        - General company name
        """
        name = fake.company()
        lower = real_value.lower()

        if "llp" in lower:
            return f"{name} LLP"
        elif "pvt. ltd" in lower or "private limited" in lower:
            return f"{name} Pvt. Ltd."
        elif "ltd" in lower or "limited" in lower:
            return f"{name} Ltd."
        elif "bank" in lower:
            return f"{name} Bank"
        elif "trust" in lower:
            return f"{name} Trust"
        elif "foundation" in lower:
            return f"{name} Foundation"
        elif "association" in lower:
            return f"{name} Association"
        elif "society" in lower:
            return f"{name} Society"
        else:
            return name

    def __len__(self) -> int:
        return len(self._registry)

    def __contains__(self, value: str) -> bool:
        return value in self._registry

    def items(self):
        return self._registry.items()
