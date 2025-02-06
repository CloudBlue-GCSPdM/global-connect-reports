# -*- coding: utf-8 -*-
#
# Copyright (c) 2021, Carolina Giménez Escalante
# All rights reserved.
#


from cnct import R
from reports.subscriptions_report.utils import convert_to_datetime, get_basic_value, get_value, today_str, \
        get_usage_record_param_value

HEADERS = ['Subscription ID', 'Subscription External ID', 'Status',
           'Item ID', 'Item Name', 'Item MPN', 'Quantity', 'MSRP', 'Cost', 'Price',
           'Product ID', 'Currency', 'Schema', 'Start Date', 'End Date', 'to_exchange_rate_by_config',
           'to_exchange_rate', 'from_exchange_rate_by_config', 'from_exchange_rate', 'entitlement_id',
           'plan_subscription_id', 'invoice_number', 'publisher_name', 'aobo',
           'Exported At']
AZURE_PRODUCT = 'PRD-561-716-033'
AZURE_PARAMS = ["v.to_exchange_rate_by_config", "v.to_exchange_rate", "v.from_exchange_rate_by_config",
                "v.from_exchange_rate", "v.entitlement_id", "v.plan_subscription_id", "v.invoice_number",
                "v.publisher_name", "v.aobo"]


def generate(client, parameters, progress_callback):
    """
    Extracts data from Connect using the ConnectClient instance
    and input parameters provided as arguments, applies
    required transformations (if any) and returns an iterator of rows
    that will be used to fill the Excel file.
    Each element returned by the iterator must be an iterator over
    the columns value.
    :param client: An instance of the CloudBlue Connect
                    client.
    :type client: connect.client.ConnectClient
    :param parameters: Input parameters used to calculate the
                        resulting dataset.
    :type parameters: dict
    :param progress_callback: A function that accepts t
                                argument of type int that must
                                be invoked to notify the progress
                                of the report generation.
    :type progress_callback: func
    """
    records = _get_usage_records(client, parameters)

    progress = 0
    total = records.count()

    if progress == 0:
        yield HEADERS
        progress += 1
        total += 1
        progress_callback(progress, total)

    if total > 0:
        for record in records:
            param1 = '-'
            param2 = '-'
            param3 = '-'
            param4 = '-'
            param5 = '-'
            param6 = '-'
            param7 = '-'
            param8 = '-'
            param9 = '-'
            param10 = '-'
            if get_basic_value(record, 'product_id') == AZURE_PRODUCT:
                parameters_list = record['params']
                param1 = get_usage_record_param_value(parameters_list, AZURE_PARAMS[0])
                param2 = get_usage_record_param_value(parameters_list, AZURE_PARAMS[1])
                param3 = get_usage_record_param_value(parameters_list, AZURE_PARAMS[2])
                param4 = get_usage_record_param_value(parameters_list, AZURE_PARAMS[3])
                param5 = get_usage_record_param_value(parameters_list, AZURE_PARAMS[4])
                param6 = get_usage_record_param_value(parameters_list, AZURE_PARAMS[5])
                param7 = get_usage_record_param_value(parameters_list, AZURE_PARAMS[6])
                param8 = get_usage_record_param_value(parameters_list, AZURE_PARAMS[7])
                param9 = get_usage_record_param_value(parameters_list, AZURE_PARAMS[8])
                param10 = '-'
            msrp = get_basic_value(record, 'amount')
            cost = 0
            price = 0
            if "tier" in record:
                if get_basic_value(record, 'tier') == 0:
                    msrp = get_basic_value(record, 'amount')
                if get_basic_value(record, 'tier') == 1:
                    msrp = 0
                    cost = get_basic_value(record, 'amount')
                if get_basic_value(record, 'tier') == 2:
                    msrp = 0
                    price = get_basic_value(record, 'amount')

            yield (
                get_basic_value(record, 'asset_id'),  # Subscription ID
                get_basic_value(record, 'asset_external_id'),  # Subscription External ID
                get_basic_value(record, 'status'),  # Status
                get_value(record, 'item', 'id'),  # Item ID
                get_value(record, 'item', 'name'),  # Item Name
                get_value(record, 'item', 'mpn'),  # Item MPN
                get_basic_value(record, 'amount'),  # Quantity
                msrp,  # MSRP
                cost,  # Cost
                price,  # Price
                get_basic_value(record, 'product_id'),  # Product ID
                get_value(record, 'usagefile', 'currency'),  # Currency
                get_value(record, 'usagefile', 'schema'),  # Schema
                convert_to_datetime(
                    get_basic_value(record, 'start_date'),   # Start Date
                ),
                convert_to_datetime(
                    get_basic_value(record, 'end_date'),  # End Date
                ),
                param1,
                param2,
                param3,
                param4,
                param5,
                param6,
                param7,
                param8,
                param9,
                param10,
                today_str(),  # Export Date
            )
            progress += 1
            progress_callback(progress, total)


def _get_usage_records(client, parameters):
    query = R()
    query &= R().start_date.ge(parameters['date']['after'])
    query &= R().end_date.le(parameters['date']['before'])

    if parameters.get('product') and parameters['product']['all'] is False:
        query &= R().product_id.oneof(parameters['product']['choices'])

    if parameters.get('ur_status') and parameters['ur_status']['all'] is False:
        query &= R().status.oneof(parameters['ur_status']['choices'])
    else:
        query &= R().status.oneof(['valid', 'approved', 'closed'])

    if parameters.get('mkp') and parameters['mkp']['all'] is False:
        query &= R().marketplace.id.oneof(parameters['mkp']['choices'])

    if parameters.get('hub'):
        query &= R().hub.id.oneof(parameters['hub'].split(sep="|"))

    return client.ns('usage').collection('records').filter(query)
