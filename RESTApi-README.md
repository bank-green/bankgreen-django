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
  response: json object reflecting the updated bank information or an error message
            example: {
              "success": true,
              "message": "Bank information updated successfully"
            }
```

  curl command : `curl --location --request PUT 'http://127.0.0.1:8000/api/bank' \ --header 'Authorization: YOUR_TOKEN_HERE' \ --header 'Content-Type: application/json' \ --data '{ "name": "New Bank", "tag": "bank_tag" }'`