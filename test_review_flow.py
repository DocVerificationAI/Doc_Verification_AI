from database import save_human_review, load_all_cases

def test_human_review():
    cases = load_all_cases()
    print(f"Loaded {len(cases)} cases from database.")
    
    if cases:
        test_case_id = cases[0]["case_id"]
        print(f"Testing APPROVE on case {test_case_id}")
        save_human_review(test_case_id, "APPROVED", "Automated test approval")
        
        updated_cases = load_all_cases()
        c = next((x for x in updated_cases if x["case_id"] == test_case_id), None)
        assert c is not None
        assert c["status"] == "APPROVED"
        assert c["human_review"]["action"] == "APPROVED"
        print(f"Case {test_case_id} status successfully updated to: {c['status']}")
        
        print(f"Testing REJECT on case {test_case_id}")
        save_human_review(test_case_id, "REJECTED", "Automated test rejection")
        
        updated_cases_2 = load_all_cases()
        c2 = next((x for x in updated_cases_2 if x["case_id"] == test_case_id), None)
        assert c2 is not None
        assert c2["status"] == "REJECTED"
        assert c2["human_review"]["action"] == "REJECTED"
        print(f"Case {test_case_id} status successfully updated to: {c2['status']}")

    print("HUMAN REVIEW TESTS PASSED!")

if __name__ == "__main__":
    test_human_review()
