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
          institutionType {
            name
          }
          institutionCredentials {
            name
          }
          embraceCampaign {
            id
          }
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

## individual bank by tag

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
      topPick
      subtitle
      header
      summary
      details
      fossilFreeAllianceRating
      showOnSustainableBanksPage
      institutionType {
        name
      }
      institutionCredentials {
        name
      }
      embraceCampaign {
        id
      }
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

## individual bank by name

**query**

```graphql
query BrandByNameQuery($name: String!) {
  brandByName(name: $name) {
    tag
    name
    website
    commentary {
      rating
      fromTheWebsite
      ourTake
      amountFinancedSince2016
      fossilFreeAlliance
      topPick
      subtitle
      header
      summary
      details
      fossilFreeAllianceRating
      showOnSustainableBanksPage
      institutionType {
        name
      }
      institutionCredentials {
        name
      }
      embraceCampaign {
        id
      }
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
  "name": "Vanbank"
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
    "checking"
  ],
  "first": 300,
  "withCommentary": true,
  "withFeatures": true
}
```

## all embrace campaigns
```
 query{
  embraceCampaigns{
    id
    name
    description
    configuration
  }
}
```

## Filter brands, website, aliases and countries with embrace campaigns id
```
query{
  brandsFilteredByEmbraceCampaign(id: 1){
    name
    website
    aliases
    tag
    countries 
    {
      name
    }
  }
}
```

## New Endpoint: harvestData

Allows you to fetch and filter harvest data for sustainable banks.

### Query

```graphql
query {
  harvestData(
    tag: String!
    customersServed: String
    depositProducts: String
    financialFeatures: String
    services: String
    institutionalInformation: String
    policies: String
    loanProducts: String
    interestRates: String
  ) {
    customersServed
    depositProducts
    financialFeatures
    services
    institutionalInformation
    policies
    loanProducts
    interestRates
  }
}
```

- *tag* is required and should be the tag of the bank you want to fetch data for.
- All other parameters are optional and can be used for filtering the respective fields.

### Example

```graphql
query {
  harvestData(tag: "atmos", customersServed: "corporate") {
    customersServed
    depositProducts
  }
}
```

This query will return the customersServed and depositProducts data for the bank with the tag "atmos", filtering the customersServed field to only include entries containing the word "corporate".