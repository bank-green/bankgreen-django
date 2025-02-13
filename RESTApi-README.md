# Here are the ways how to call rest api endpoint with curl command


# Fetch all contacts
```
  endpoint : /bank-contacts
  method : GET
  authentication: token required
  response: array of bank contacts in json format
            example : [
                        {
                          "fullname": "test contact one",
                          "email": "test@abcbank.com",
                          "brand_tag": "abc"
                        },
                      ]
```

  curl command : `curl --location 'http://127.0.0.1:8000/api/bank-contacts' --header 'Authorization: YOUR_TOKEN_HERE'`

# Fetch contacts filtered by bank
```
  endpoint : /bank-contacts?bankTag=someBankTagHere
             example : /bank-contacts?bankTag=abc
  method : GET
  authentication: token required
  response: array of bank contacts in json format
            example : [
                        {
                          "fullname": "test contact one",
                          "email": "test@abcbank.com",
                          "brand_tag": "abc"
                        },
                      ]
```

  curl command : `curl --location 'http://127.0.0.1:8000/api/bank-contacts?bankTag=someBankTagHere' --header 'Authorization: Token YOUR_TOKEN_HERE'`

# Create or update a bank by tag
updates the bank at the specified tag.  fields not specified in the body will not be changed.  Creates a new record if the tag does not exist.

```
  endpoint : /bank
  method : PUT
  authentication: token required
  request body: json containing bank details
                example: {
                  "name": "New Bank",
                  "tag": "bank_tag"
                }
  response: json object reflecting the updated bank information
            example: {
              "id": 754,
              "created": "2024-10-11T04:20:01.421975Z",
              "modified": "2024-10-11T04:20:01.421975Z",
              "name": "New Bank",
              "tag": "bank_tag"
              ...
          }
```

  curl command : `curl --location --request PUT 'http://127.0.0.1:8000/api/bank' \ --header 'Authorization: YOUR_TOKEN_HERE' \ --header 'Content-Type: application/json' \ --data '{ "name": "New Bank", "tag": "bank_tag" }'`

# Fetch Commentary `feature_override`
```
  endpoint : /commentaries/[commentary id]/feature_override/
             example : /commentaries/22/feature_override/
  method : GET
  authentication: token required
  successful response returns json of commentary's entire updated feature_override:
            example : {
                        "customers_served": {
                          "corporate": {
                              "additional_details": "some additional details",
                          }
                        }
                      },
  failure response returns json with an "error" key
            example : { "error": "Commentary does not exsist" }
```
  curl command : `curl --location 'http://127.0.0.1:8000/api/commentaries/someId/feature_override' --header 'Authorization: YOUR_TOKEN_HERE'`

# Create or update a Commentary's `feature_override`

```
  endpoint : /commentaries/[commentary id]/feature_override/
             example : /commentaries/22/feature_override/
  method : PUT
  authentication: token required
  request body: json containing valid feature json data
            example: {
                      "policies": {
                        "environmental_policy": {
                            "additional_details": "Comprehensive testing on mocking, mockdiversity, and climate stub.",
                        }
                      }
                    }
  successful response returns json of commentary's entire updated feature_override:
            example: {
                      "policies": {
                        "environmental_policy": {
                            "additional_details": "Comprehensive testing on mocking, mockdiversity, and climate stub.",
                        }
                      },
                    "customers_served": {
                        "corporate": {
                            "additional_details": "some additional details",
                        }
                      },
                    }
  failure response returns json with an "error" key
            example : {
                        "error": ["Additional properties are not allowed ('business_and_corporate' was unexpected)"]
                      }
```
  curl command : `curl --location --request PUT 'http://127.0.0.1:8000/api/commentaries/someId/feature_override' \ --header 'Authorization: YOUR_TOKEN_HERE' \ --header 'Content-Type: application/json' \ --data '{"policies":{"environmental_policy":{"additional_details":"Comprehensive testing on mocking, mockdiversity, and climate stub."}}}'`