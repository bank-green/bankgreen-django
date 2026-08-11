import graphene

import brand.schema
import impact.schema


class Query(brand.schema.Query, impact.schema.Query, graphene.ObjectType):
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project
    pass


schema = graphene.Schema(query=Query)
