# Here are the ways how to query with graphql


## Query Brand objects

```
query {
  brands{
    edges {
      node {
        id,
        name,
        tag,
        commentaryBrand {
          id,
          rating
        },
        datasource {
          id,
          name,
          tag
        }
      }
    }
  }
}
```

## Filter Brand objects by country
```
query {
  brands(graphqlCountry_Icontains: "In"){
    edges {
      node {
        id,
        name,
        website,
      }
    }
  }
}
```
*There's a Brand field (graphql_country) to query the database with Graphql. Django-countries doesn't play well with GraphQL.
You can filter ```graphqlCountry_Icontains``` or ```graphqlCountry_Exact```*

## Get one Brand object

```
query {
  brand(id: "id_of_brand"){
    id,
    name,
    tag,
    commentaryBrand {
      id,
      rating
    }
  }
}
```


## Query or Filter Commentary objects

```
query {
  commentaries(rating: "bad"){
    edges {
      node {
        id,
        headline,
        rating,
        brand {
          id,
          name,
          tag
        }
      }
    }
  }
}
```
*delete the attribute if you want all commentaries.*


## Get one Commentary object

```
query {
  commentary(id: "id_of_commentary"){
    id,
    headline,
    rating,
    brand {
      id,
      name,
      tag
    }
  }
}
```
