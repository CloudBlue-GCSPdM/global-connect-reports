# Report Usage Records Report


Subscription Usage Records data per dates, status and Product.
It creates an Excel file (.xlsx) including the following columns (including Azure specific columns):
* Subscription ID
* Subscription External ID
* Status
* Item ID, Item Name, Item MPN
* Quantity, MSRP, Cost, Price
* Product ID
* Currency
* Schema
* Start Date
* End Date
* to_exchange_rate_by_config, to_exchange_rate, from_exchange_rate_by_config, from_exchange_rate
* entitlement_id, plan_subscription_id, 
* invoice_number, publisher_name
* aobo
* Exported At


# Available parameters

The report can be parametrized by:

* Start and End usage record date
* Product
* Status of the Usage record
