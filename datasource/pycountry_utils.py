import pycountry

pycountries = {x.name.lower(): x.alpha_2 for x in pycountry.countries}
# Taiwan is sometimes referred to as a republic of china
pycountries["taiwan, republic of china"] = "TW"
pycountries["taiwan"] = "TW"
pycountries["united states of america"] = "US"
pycountries["south korea"] = "KR"
pycountries["netherlands the"] = "NL"
