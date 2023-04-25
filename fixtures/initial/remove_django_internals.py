from json import dump, load


with open('fixtures/initial/initial.json', 'r') as file:
    initial = load(file)

models_remove_list = [
    'auth.group', 'auth.permission', 'auth.user', 'sessions.session',
    'django_content_type'
]

initial = [x for x in initial if x['model'] not in models_remove_list]

with open('fixtures/initial/initial.json', 'w') as file:
    dump(initial, file, indent = 4)
