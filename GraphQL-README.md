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
          ourTake
          amountFinancedSince2016
          fossilFreeAlliance
          subtitle
          headline
          description1
          description2
          description3
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
      ourTake
      amountFinancedSince2016
      fossilFreeAlliance
      topPick
      subtitle
      headline
      description1
      description2
      description3
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
      ourTake
      amountFinancedSince2016
      fossilFreeAlliance
      topPick
      subtitle
      headline
      description1
      description2
      description3
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
  }
}
```


**variables**

```graphql
{
  "name": "Vancity"
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
  $stateLicensed: String
  $statePhysicalBranch: String
  $withCommentary: Boolean = false
  $withFeatures: Boolean = false
  $harvestData: HarvestDataFilterInput
) {
  brands(
    country: $country
    first: $first
    fossilFreeAlliance: $fossilFreeAlliance
    features: $features
    regions: $regions
    subregions: $subregions
    stateLicensed: $stateLicensed
    statePhysicalBranch: $statePhysicalBranch
    harvestData: $harvestData
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
        stateLicensed {
          tag
        }
        statePhysicalBranch {
          tag
        }
        commentary @include(if: $withCommentary) {
          rating
          ourTake
          amountFinancedSince2016
          fossilFreeAlliance
          subtitle
          headline
          description1
          description2
          description3
          fossilFreeAllianceRating
          showOnSustainableBanksPage
        }
        harvestData {
          customersServed
          depositProducts
          services
          financialFeatures
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
```graphql
query {
  allHarvestData(
    customersServed: String
    depositProducts: String
    financialFeatures: String
    services: String
    institutionalInformation: String
    policies: String
    loanProducts: String
    interestRates: String
  ) {
    tag,
    features{
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
}
```
- *tag* is not required for **allHarvestData** query but required for **harvestData**. In **harvestData** query, you should pass tag of the bank (as param) you want to fetch data for.
- All other parameters are optional and can be used for filtering the respective fields.

### Example

```graphql
query {
  harvestData(tag: "atmos", customersServed: "corporate", financialFeatures: "interest_rates") {
    customersServed
    depositProducts
  }
}
```

```
{
  commentary(id: "Q29tbWVudGFyeTozMzc="){
    harvestData(customersServed: "corporate"){
      customersServed
      depositProducts
    }
  }
}
```

The above two queries will return the customersServed and depositProducts data for the bank with the tag "atmos", filtering the customersServed field to only include entries containing the word "corporate".

```
{
  allHarvestData(depositProducts: "wealth_management"){
    tag
    features{
      depositProducts
    }
  }
}
```
The above query will return the depositProducts data for all banks, filtering the depositProducts field to only include entries containing the word "wealth_management".
