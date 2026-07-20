from language import RobotLanguage

lang = RobotLanguage()

print(lang.name)

print(lang.version)

for category, func in lang.all_functions():

    print(category, func["name"])