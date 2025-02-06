# -*- coding: utf-8 -*-
#
# Copyright (c) 2021, Carolina Giménez Escalante
# All rights reserved.
#

from connect.client.rql import R
from reports.subscriptions_report.utils import (get_value, get_basic_value, convert_to_datetime, today_str)

HEADERS = ['Request ID', 'Subscription ID', 'Subscription External ID',
           'Param 1', 'Param 2', 'Item ID', 'Item Name', 'Item Period', 'Item MPN', 'Item Quantity',
           'Provider  ID', 'Provider Name', 'HUB ID', 'HUB Name',
           'Marketplace', 'Product ID', 'Product Name', 'Vendor ID', 'Vendor Name',
           'Subscription Status', 'Assignee', 'Request Status',
           'Effective Date', 'Creation Date', 'Transaction Type', 'Connection Type', 'Exported At']


def generate(client, parameters, progress_callback):
    """
    Extracts data from Connect. Takes all the requests approved between the dates received as parameter.
    Of the Products, marketplaces and environments received.
    Creates a report with one line per subscription and month.

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
    requests = _get_requests(client, parameters)

    progress = 0
    total = requests.count() + 1

    for request in requests:
        param1 = ''
        param2 = ''

        # get subscription parameters values
        if 'parameter_id' in parameters and len(str(parameters['parameter_id'])) > 0:
            i = 0
            for param_requested in parameters['parameter_id'].split(sep="|"):
                for param in request['asset']['params']:
                    if param_requested == get_basic_value(param, 'id'):
                        if i == 0:
                            param1 = get_basic_value(param, 'value')
                            HEADERS[16] = get_basic_value(param, 'name')
                        elif i == 1:
                            param2 = get_basic_value(param, 'value')
                            HEADERS[17] = get_basic_value(param, 'name')
                        i = i + 1

        if progress == 0:
            yield HEADERS
            progress += 1
            total += 1
            progress_callback(progress, total)

        for item in request['asset']['items']:
            item_name = ''
            item_period = ''
            item_mpn = ''
            item_quantity = ''
            item_id = ''
            if item['quantity'] != 'unlimited' and float(item['quantity']) > 0:
                item_name = item['display_name']
                item_period = item['period']
                item_mpn = item['mpn']
                item_quantity = item['quantity']
                item_id = item['id']

            yield (
                    get_basic_value(request, 'id'),  # Request ID
                    get_value(request, 'asset', 'id'),  # Subscription ID
                    get_value(request, 'asset', 'external_id'),  # Subscription External ID
                    param1,  # Subscription param 1 value
                    param2,  # Subscription param 2 value
                    item_name,
                    item_period,
                    item_mpn,
                    item_quantity,
                    item_id,
                    get_value(request['asset']['connection'], 'provider', 'id'),  # Provider ID
                    get_value(request['asset']['connection'], 'provider', 'name'),  # Provider Name
                    get_value(request['asset']['connection'], 'hub', 'id'),  # HUB Id
                    get_value(request['asset']['connection'], 'hub', 'name'),  # HUB Name
                    get_value(request, 'marketplace', 'name'),  # Marketplace
                    get_value(request['asset'], 'product', 'id'),  # Product ID
                    get_value(request['asset'], 'product', 'name'),  # Product Name
                    get_value(request['asset']['connection'], 'vendor', 'id'),  # Vendor Id
                    get_value(request['asset']['connection'], 'vendor', 'name'),  # Vendor Name
                    get_value(request, 'asset', 'status'),  # Subscription Status
                    get_value(request, 'assignee', 'name'),  # Assignee
                    get_basic_value(request, 'status'),  # Request Status
                    convert_to_datetime(
                        get_basic_value(request, 'effective_date'),  # Effective  Date
                    ),
                    convert_to_datetime(
                        get_basic_value(request, 'created'),  # Creation  Date
                    ),
                    get_basic_value(request, 'type'),  # Transaction Type,
                    get_basic_value(request['asset']['connection'], 'type'),  # Connection Type,
                    today_str(),  # Exported At
        )
        if len(request['asset']['items']) == 0:
            yield (
                get_basic_value(request, 'id'),  # Request ID
                get_value(request, 'asset', 'id'),  # Subscription ID
                get_value(request, 'asset', 'external_id'),  # Subscription External ID
                param1,  # Subscription param 1 value
                param2,  # Subscription param 2 value
                'item_name',
                'item_period',
                'item_mpn',
                'item_quantity',
                'item_id',
                get_value(request['asset']['connection'], 'provider', 'id'),  # Provider ID
                get_value(request['asset']['connection'], 'provider', 'name'),  # Provider Name
                get_value(request['asset']['connection'], 'hub', 'id'),  # HUB Id
                get_value(request['asset']['connection'], 'hub', 'name'),  # HUB Name
                get_value(request, 'marketplace', 'name'),  # Marketplace
                get_value(request['asset'], 'product', 'id'),  # Product ID
                get_value(request['asset'], 'product', 'name'),  # Product Name
                get_value(request['asset']['connection'], 'vendor', 'id'),  # Vendor Id
                get_value(request['asset']['connection'], 'vendor', 'name'),  # Vendor Name
                get_value(request, 'asset', 'status'),  # Subscription Status
                get_value(request, 'assignee', 'name'),  # Assignee
                get_basic_value(request, 'status'),  # Request Status
                convert_to_datetime(
                    get_basic_value(request, 'effective_date'),  # Effective  Date
                ),
                convert_to_datetime(
                    get_basic_value(request, 'created'),  # Creation  Date
                ),
                get_basic_value(request, 'type'),  # Transaction Type,
                get_basic_value(request['asset']['connection'], 'type'),  # Connection Type,
                today_str(),  # Exported At
            )
        continue
        progress += 1
        progress_callback(progress, total)


def _get_requests(client, parameters):
    all_status = ['tiers_setup', 'inquiring', 'pending', 'approved', 'failed', 'draft']

    query = R()
    if parameters.get('rr_status') and parameters['rr_status']['all'] is False:
        query &= R().status.oneof(parameters['rr_status']['choices'])
    else:
        query &= R().status.oneof(all_status)

    query &= R().created.ge(parameters['date']['after'])
    query &= R().created.le(parameters['date']['before'])

    if parameters.get('connexion_type') and parameters['connexion_type']['all'] is False:
        query &= R().asset.connection.type.oneof(parameters['connexion_type']['choices'])

    if parameters.get('product') and parameters['product']['all'] is False:
        query &= R().asset.product.id.oneof(parameters['product']['choices'])
    if parameters.get('mkp') and parameters['mkp']['all'] is False:
        query &= R().marketplace.id.oneof(parameters['mkp']['choices'])

    return client.requests.filter(query).order_by("created")
