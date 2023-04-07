# Here are the ways how to query with graphql

## all brands in a country

**query**

```graphql
query BrandsQuery(
  $country: String
  $recommendedOnly: Boolean
  $rating: [String]
  $first: Int
  $withCommentary: Boolean = false
  $withFeatures: Boolean = false
) {
  brands(
    country: $country
    recommendedOnly: $recommendedOnly
    rating: $rating
    first: $first
    displayOnWebsite: true
  ) {
    edges {
      node {
        name
        tag
        website
        aliases
        commentary @include(if: $withCommentary) {
          rating
          fromTheWebsite
          ourTake
          amountFinancedSince2016
          fossilFreeAlliance
          subtitle
          header
          summary
          details
          fossilFreeAllianceRating
          showOnSustainableBanksPage
        }
        bankFeatures @include(if: $withFeatures) {
          offered
          feature {
            name
          }
          details
        }
        datasources {
          edges {
            node {
              name
              sourceLink
              subclass
            }
          }
        }
      }
    }
  }
}
```

**variables**

```graphql
{
  "country": "IT"
}
```

## individual bank

**query**

```graphql
query BrandByTagQuery($tag: String!) {
  brand(tag: $tag) {
    tag
    name
    website
    commentary {
      rating
      fromTheWebsite
      ourTake
      amountFinancedSince2016
      fossilFreeAlliance
      subtitle
      header
      summary
      details
      fossilFreeAllianceRating
      showOnSustainableBanksPage
    }
    bankFeatures {
      offered
      feature {
        name
      }
      details
    }
    datasources {
      edges {
        node {
          name
          sourceLink
          subclass
        }
      }
    }
  }
}
```

**variables**

```graphql
{
  "tag": "atmos"
}
```

## filter banks by features

**query**

```graphql
query BrandsQuery(
  $country: String
  $first: Int
  $fossilFreeAlliance: Boolean
  $features: [String]
  $regions: [String]
  $subregions: [String]
  $withCommentary: Boolean = false
  $withFeatures: Boolean = false
) {
  brands(
    country: $country
    first: $first
    fossilFreeAlliance: $fossilFreeAlliance
    features: $features
    regions: $regions
    subregions: $subregions
  ) {
    edges {
      node {
        name
        tag
        website
        aliases
        regions {
          id
          name
          slug
        }
        commentary @include(if: $withCommentary) {
          rating
          fromTheWebsite
          ourTake
          amountFinancedSince2016
          fossilFreeAlliance
          subtitle
          header
          summary
          details
          fossilFreeAllianceRating
          showOnSustainableBanksPage
        }
        bankFeatures @include(if: $withFeatures) {
          offered
          feature {
            name
          }
          details
        }
        datasources {
          edges {
            node {
              name
              sourceLink
              subclass
            }
          }
        }
      }
    }
  }
}
```

**variables**

```graphql
{
  "country": "US",
  "fossilFreeAlliance": true,
  "features": [
    "online_only",
    "credit_cards"
  ],
  "first": 300,
  "withCommentary": true,
  "withFeatures": true
}
```
