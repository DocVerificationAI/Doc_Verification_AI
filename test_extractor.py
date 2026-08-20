from modules.extractor import extract_fields

print("Testing GATE Scorecard extraction...")

test_text = """
GATE 2026 SCORECARD

Name: Anjali Nair
Date of Birth: 15/08/2002
GATE Score: 725
Registration Number: GATE2026AN123
Year: 2026
"""

result = extract_fields(test_text, "GATE Scorecard")

print("\nEXTRACTED DATA:")
print(result)