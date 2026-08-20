from modules.verifier import verify


application = {

    "name":
        "Ismail Ibrahim Nassar",

    "organization":
        "Kirby",

    "designation":
        "Design Engineer",

    "start_date":
        "01/12/2011",

    "end_date":
        "18/03/2012"
}


extracted = {

    "name":
        "Mr. Ismail Ibrahim Nassar",

    "organization":
        "KIRBY BUILDING SYSTEMS KUWAIT K.S.C.",

    "designation":
        "DESIGN ENGINEER",

    "start_date":
        "01.12.2011",

    "end_date":
        "18.03.2012"
}


fields = [

    "name",
    "organization",
    "designation",
    "start_date",
    "end_date"
]


print(
    "\nTEST STARTED\n"
)


result = verify(

    application,

    extracted,

    0.95,

    fields
)


print(

    "\nFINAL RESULT:\n"
)


print(

    "Status:",

    result["status"]
)


print(

    "Confidence:",

    result["overall_confidence"]
)


print(

    "\nFIELD RESULTS:\n"
)


for field in result["fields"]:

    print(

        field["field"],

        "| Application:",

        field["application"],

        "| Document:",

        field["document"],

        "| Status:",

        field["status"],

        "| Confidence:",

        field["confidence"]
    )

    print(

        "Reason:",

        field["reason"]
    )

    print()