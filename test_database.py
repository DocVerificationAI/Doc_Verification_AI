from database import (
    get_all_cases,
    get_case_field_results
)


cases = get_all_cases()


print("\nALL SAVED CASES:\n")

for case in cases:

    print("=" * 50)

    print(
        "Case ID:",
        case["case_id"]
    )

    print(
        "Document type:",
        case["document_type"]
    )

    print(
        "Status:",
        case["status"]
    )

    print(
        "Overall confidence:",
        case["overall_confidence"]
    )

    print(
        "Created at:",
        case["created_at"]
    )

    print("\nFIELD RESULTS:")

    fields = get_case_field_results(
        case["case_id"]
    )

    for field in fields:

        print(
            field["field_name"],
            "| Application:",
            field["application_value"],
            "| Document:",
            field["document_value"],
            "| Status:",
            field["status"]
        )