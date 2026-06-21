class ConsentRequiredError(PermissionError):
    pass


class ConsentManager:
    def ensure_confirmed(self, consent_confirmed: bool) -> None:
        if not consent_confirmed:
            raise ConsentRequiredError(
                "Explicit consent is required before analyzing submitted relationship data."
            )

    def privacy_principles(self) -> list[str]:
        return [
            "The user owns submitted text.",
            "No hidden scraping.",
            "No cross-platform ingestion without explicit authorization.",
            "No public scoring.",
            "Records should be deletable and exportable in future storage phases.",
        ]
