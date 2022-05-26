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
        commentary {
          id,
          rating
        }
      }
    }
  }
}
```

## Filter Brand objects by country
```
query {
  brands(countries: "DE") {
    edges {
      node {
        name
        countries {
          name
          code
          alpha3
          numeric
          iocCode
        }
      }
    }
  }
}
```

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
