This directory stores some random scripts for migrating data to prismic.io.

The migration can be difficult because 

- data is often stored in this sytem in markdown format and converting that to RTF within tabulated data structures is extremely difficult.
- prismic does not offer a write API at a reasonable price.

The best way I've found to do this is to 
1. export django data into tabulated format
2. to copy paste into prismic
3. to query prismic
4. to make sure that the django exported data matches with what's newly in prismic.

Here is a sample graphql query for https://bankgreen.prismic.io/graphql

```
query OurTakeQuery {
  allSfipages(first: 62 , after: "YXJyYXljb25uZWN0aW9uOjk5") {
    totalCount
    pageInfo {
      hasNextPage
      endCursor
    }
    edges {
      node {
        _meta {
          uid
        }
        our_take
      }
    }
  }
}
```