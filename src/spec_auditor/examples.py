from .models import AuditReport, DefectType, Evidence, Finding, Severity


def build_example_report() -> AuditReport:
    return AuditReport(
        reviewed_files=["accounts.md", "checkout.md", "pricing.md"],
        findings=[
            Finding(
                evidence=[
                    Evidence(
                        file="pricing.md",
                        quote="Promotional discounts stack with tier discounts.",
                    ),
                    Evidence(
                        file="pricing.md",
                        quote="Promotional discounts do not stack with tier discounts.",
                    ),
                ],
                section="3. Promotional Codes",
                issue="The same section both permits and prohibits discount stacking.",
                defect_type=DefectType.INCONSISTENCY,
                severity=Severity.HIGH,
                suggested_fix="Confirm the intended policy and remove the conflicting statement.",
            ),
            Finding(
                evidence=[
                    Evidence(
                        file="checkout.md",
                        quote="Orders over RM100 qualify for free shipping.",
                    ),
                    Evidence(
                        file="pricing.md",
                        quote="Orders of RM150 or more qualify for free shipping.",
                    ),
                ],
                section="4. Payment",
                issue="The documents specify different free-shipping thresholds.",
                defect_type=DefectType.INCONSISTENCY,
                severity=Severity.HIGH,
                suggested_fix=(
                    "Confirm the threshold and whether it is inclusive, "
                    "then align both documents."
                ),
            ),
            Finding(
                evidence=[
                    Evidence(
                        file="checkout.md",
                        quote=(
                            "Postcode is validated against the carrier service "
                            "described in section 4.2."
                        ),
                    )
                ],
                section="3. Delivery Details",
                issue="The referenced section 4.2 does not exist in the supplied documents.",
                defect_type=DefectType.BROKEN_REFERENCE,
                severity=Severity.MEDIUM,
                suggested_fix="Add the referenced section or correct the section reference.",
            ),
            Finding(
                evidence=[
                    Evidence(
                        file="checkout.md",
                        quote=(
                            "The system must respond quickly when validating the postcode."
                        ),
                    )
                ],
                section="3. Delivery Details",
                issue="“Quickly” does not define a testable response-time requirement.",
                defect_type=DefectType.AMBIGUITY,
                severity=Severity.MEDIUM,
                suggested_fix=(
                    "Ask the requirement owner to define a measurable response-time target."
                ),
            ),
        ],
    )


