from json import dump, load


with open("fixtures/initial/initial.json", "r") as file:
    initial = load(file)

# List of models to remove
models_remove_list = [
    "auth.group",
    "auth.permission",
    "auth.user",
    "sessions.session",
    "django_content_type",
]

# Filter out entries with models in the remove list
initial = [x for x in initial if x["model"] not in models_remove_list]

# Save the updated JSON back to the file
with open("fixtures/initial/initial.json", "w") as file:
    dump(initial, file, indent=4)
