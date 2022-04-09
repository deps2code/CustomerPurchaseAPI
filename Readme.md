Customer Purchase API sample server using aiohttp web framework
==============================

This application is a simple aiohttp web server for customer purchase api

Getting Started
------------
Change the directory to the project directory  

Run the docker compose file and start the server:

`docker-compose up`  

To stop the server:

`docker-compose down` 

To run the tests run:

`pip install -r requirements.txt`
<br /> 

`pytest test.py` 

Project Description
------------

The web server uses sqlite3 as a default database and have the following functionalities:
1) Create a customer using the create customer api
2) Add a new purchase for a customer via add new purchase api
3) List all customer purchases via list customer purchase api
4) Update a customer purchase name and quantity via update customer purchase api
5) Delete all or selected customer purchases via delete customer purchase api

<br />

When the web server starts it checks for a db.sqlite3 database and if not present, it creates a new database and add the following tables:
1) purchases
2) customer

This implementation can be found in the `try_make_db()` in `server.py`

APi Documentation
------------

1) Create Customer API
* POST
* URL: /api/v1/customer
* Request Body:
```json
{
    "name": "John Doe",
    "address": "Amsterdam, NL"
}
```
* Response Body:
```json
{
    "status": "ok",
    "data": {
        "id": 1,
        "name": "John Doe",
        "address": "Amsterdam, NL",
        "created_on": "Apr 09 2022 12:43:17"
    }
}
```
<br />

2) List Customer Purchase API
* GET
* URL: /api/v1/customer
* Response Body:
```json
{
    "status": "ok",
    "data": [
        {
            "purchase_id": 1,
            "purchase_name": "Iphone 10 Pro",
            "quantity": 4,
            "purchased_on": "2022-04-09 12:43:22.237526+00:00",
            "last_updated_on": null
        },
        {
            "purchase_id": 2,
            "purchase_name": "Iphone 12 Pro",
            "quantity": 40,
            "purchased_on": "2022-04-09 12:43:28.321654+00:00",
            "last_updated_on": "2022-04-09 12:43:56.924416+00:00"
        }
    ]
}
```
<br />

3) Add Customer Purchase API
* POST
* URL: /api/v1/purchase/:customer_id
* Request Body:
```json
{
    "purchase_name": "Iphone 12",
    "quantity": 4
}
```
* Response Body:
```json
{
    "status": "ok",
    "data": {
        "id": 2,
        "purchase_name": "Iphone 12",
        "quantity": 4,
        "customer_id": "1",
        "purchased_on": "Apr 09 2022 12:43:28"
    }
}
```
<br />

4) Delete Customer Purchase API
* DELETE
* URL: /api/v1/purchase/:customer_id
* Request Body:
```json
{
    "delete_all": false,
    "purchase_ids": [3,6]
}
```
if `delete_all` is sent as true then it ignores the purchase_ids and delete all purchases for customer
* Response Body:
```json
{
    "status": "ok",
    "deleted_count": 2
}
```
<br />

5) Update Customer Purchase API
* DELETE
* URL: /api/v1/purchase/:purchase_id
* Request Body:
```json
{
    "purchase_name": "Iphone 12 Pro",
    "quantity": 40
}
```
* Response Body:
```json
{
    "status": "ok",
    "data": {
        "id": "2",
        "purchase_name": "Iphone 12 Pro",
        "quantity": 40,
        "purchased_on": "2022-04-09 12:43:28.321654+00:00",
        "last_updated_on": "2022-04-09 12:43:56.924416+00:00"
    }
}
```


