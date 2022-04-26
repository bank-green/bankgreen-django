from datasource.models.datasource import Datasource, classproperty


class Wikidata(Datasource):
    """ """

    @classproperty
    def tag_prepend_str(cls):
        return cls.__name__.lower() + "_"
