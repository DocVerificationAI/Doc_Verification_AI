from modules.verifier import compare_strict_field, verify

def test_date_and_year_comparisons():
    print("--- Testing Date Comparison ---")
    
    # 1. Exact match
    res = compare_strict_field("dob", "15/06/2007", "15/06/2007", 0.95)
    print("Exact date match:", res["status"], "|", res["reason"])
    assert res["status"] == "MATCH"

    # 2. Format normalization match (e.g. 15 June 2007 vs 15/06/2007)
    res = compare_strict_field("dob", "15 June 2007", "15/06/2007", 0.95)
    print("Format normalization match:", res["status"], "|", res["reason"])
    assert res["status"] == "MATCH"

    # 3. Massive year difference (2023 vs 2007, diff = 16) -> MISMATCH
    res = compare_strict_field("dob", "25/6/2023", "15/06/2007", 0.90)
    print("Massive year difference (2023 vs 2007):", res["status"], "|", res["reason"])
    assert res["status"] == "MISMATCH"

    # 4. Massive year difference (2005 vs 2007, diff = 2) -> MISMATCH
    res = compare_strict_field("dob", "15/06/2005", "15/06/2007", 0.90)
    print("Massive year difference (2005 vs 2007):", res["status"], "|", res["reason"])
    assert res["status"] == "MISMATCH"

    # 5. Minor year difference (2006 vs 2007, diff = 1) -> REVIEW
    res = compare_strict_field("dob", "15/06/2006", "15/06/2007", 0.90)
    print("Minor year difference (2006 vs 2007):", res["status"], "|", res["reason"])
    assert res["status"] == "REVIEW"

    # 6. Minor date difference (same year 2007, day/month differs e.g. 25/06/2007 vs 15/06/2007) -> REVIEW
    res = compare_strict_field("dob", "25/06/2007", "15/06/2007", 0.95)
    print("Minor date difference (same year, different day):", res["status"], "|", res["reason"])
    assert res["status"] == "REVIEW"

    print("\n--- Testing Standalone Year Field ---")

    # 7. Exact year match
    res = compare_strict_field("year", "2026", "2026", 0.95)
    print("Exact year match:", res["status"], "|", res["reason"])
    assert res["status"] == "MATCH"

    # 8. Massive year difference (2005 vs 2007, diff = 2) -> MISMATCH
    res = compare_strict_field("year", "2005", "2007", 0.95)
    print("Massive year difference (2005 vs 2007):", res["status"], "|", res["reason"])
    assert res["status"] == "MISMATCH"

    # 9. Massive year difference (2023 vs 2007, diff = 16) -> MISMATCH
    res = compare_strict_field("year", "2023", "2007", 0.95)
    print("Massive year difference (2023 vs 2007):", res["status"], "|", res["reason"])
    assert res["status"] == "MISMATCH"

    # 10. Minor year difference (2006 vs 2007, diff = 1) -> REVIEW
    res = compare_strict_field("year", "2006", "2007", 0.95)
    print("Minor year difference (2006 vs 2007):", res["status"], "|", res["reason"])
    assert res["status"] == "REVIEW"

    print("\n--- Testing Full Verify Function with Marksheet Data ---")
    
    app_data = {
        "name": "Aarav Kumar",
        "dob": "25 /6/2023",
        "roll_number": "1234567",
        "total_marks": "468 / 600",
        "percentage": "78.00"
    }
    extracted_data = {
        "name": "Aarav Kumar",
        "dob": "15/06/2007",
        "roll_number": "1234567",
        "total_marks": "468/600",
        "percentage": "78.00%"
    }
    fields = ["name", "dob", "roll_number", "total_marks", "percentage"]
    
    full_res = verify(app_data, extracted_data, 0.90, fields)
    print("Overall Status:", full_res["status"])
    for f in full_res["fields"]:
        print(f"  {f['field']}: {f['status']} ({f['confidence']}%) - {f['reason']}")
    assert full_res["status"] == "MISMATCH"
    assert any(f["field"] == "dob" and f["status"] == "MISMATCH" for f in full_res["fields"])

    print("\nALL ASSERTIONS PASSED!")

if __name__ == "__main__":
    test_date_and_year_comparisons()
