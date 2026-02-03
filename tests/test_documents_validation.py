from decimal import Decimal

from backend.api.documents_routes import DraftLinePayload, TotalsPayload, _validate_totals


def test_validate_totals_ok():
    lines = [
        DraftLinePayload(
            line_no=1,
            description="Service",
            qty=Decimal("1"),
            unit_price=Decimal("100.00"),
            net=Decimal("100.00"),
            vat=Decimal("20.00"),
            gross=Decimal("120.00"),
            vat_code="VAT20",
            nominal_code="4000",
        )
    ]
    totals = TotalsPayload(net=Decimal("100.00"), vat=Decimal("20.00"), gross=Decimal("120.00"))
    validation = _validate_totals(lines, totals)
    assert validation["status"] == "ok"
    assert validation["issues"] == []


def test_validate_totals_mismatch():
    lines = [
        DraftLinePayload(
            line_no=1,
            description="Service",
            qty=Decimal("1"),
            unit_price=Decimal("100.00"),
            net=Decimal("100.00"),
            vat=Decimal("20.00"),
            gross=Decimal("120.00"),
            vat_code="VAT20",
            nominal_code="4000",
        )
    ]
    totals = TotalsPayload(net=Decimal("90.00"), vat=Decimal("20.00"), gross=Decimal("110.00"))
    validation = _validate_totals(lines, totals)
    assert validation["status"] == "warning"
    assert validation["issues"]
