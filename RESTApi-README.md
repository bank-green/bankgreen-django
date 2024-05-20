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
