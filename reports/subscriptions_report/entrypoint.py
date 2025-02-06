# -*- coding: utf-8 -*-
#
# Copyright (c) 2021, Carolina Giménez Escalante
# All rights reserved.
#

from connect.client.rql import R
from .utils import (get_value, get_basic_value, convert_to_datetime, today_str)

HEADERS = ['Subscription ID', 'Subscription External ID',
           'Anniversary Date', 'Term Delta', 'Term Period',
           'Customer ID', 'Customer Name', 'Customer External ID',
           'Param 1', 'Param 2', 'Item Name', 'Item Period', 'Item MPN', 'Item Quantity',
           'Tier 1 ID', 'Tier 1 Name', 'Tier 1 External ID', 'Tier 2 ID',
           'Tier 2 Name', 'Tier 2 External ID', 'Provider  ID', 'Provider Name',
           'Hub ID', 'Hub Name', 'Vendor ID', 'Vendor Name',
           'Marketplace', 'Product ID', 'Product Name', 'Subscription Status',
           'Transaction Date', 'Connection Type', 'Exported At']


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
    subscriptions = _get_subscriptions(client, parameters)

    progress = 0
    total = subscriptions.count() + 1

    for subscription in subscriptions:
        param1 = ''
        param2 = ''

        # get subscription parameters values
        if 'parameter_id' in parameters:
            i = 0
            for param_requested in parameters['parameter_id'].split(sep="|"):
                for param in subscription['params']:
                    if param_requested == get_basic_value(param, 'name'):
                        if i == 0:
                            param1 = get_basic_value(param, 'value')
                            HEADERS[16] = get_basic_value(param, 'name')
                        elif i == 1:
                            param2 = get_basic_value(param, 'value')
                            HEADERS[17] = get_basic_value(param, 'name')
                        i = i + 1

        item_name = ''
        item_period = ''
        item_mpn = ''
        item_quantity = 0
        for item in subscription['items']:
            if item['quantity'] > 0:
                item_name = item['display_name']
                item_period = item['period']
                item_mpn = item['mpn']
                item_quantity = item['quantity']
                continue

        if progress == 0:
            yield HEADERS
            progress += 1
            total += 1
            progress_callback(progress, total)

        yield (
            get_basic_value(subscription, 'id'),  # Subscription ID
            get_basic_value(subscription, 'external_id'),  # Subscription External ID
            # get_value(subscription, 'billing', 'next_date'),  # Anniversary Date
            # get_value(subscription['billing'], 'period', 'delta'),  # Term Delta
            # get_value(subscription['billing'], 'period', 'uom'),  # Term Type
            get_value(subscription['tiers'], 'customer', 'id'),  # Customer ID
            get_value(subscription['tiers'], 'customer', 'name'),  # Customer Name
            get_value(subscription['tiers'], 'customer', 'external_id'),  # Customer External ID
            param1,  # Subscription param 1 value
            param2,  # Subscription param 2 value
            item_name,
            item_period,
            item_mpn,
            item_quantity,
            get_value(subscription['tiers'], 'tier1', 'id'),  # Tier 1 ID
            get_value(subscription['tiers'], 'tier1', 'name'),  # Tier 1 Name
            get_value(subscription['tiers'], 'tier1', 'external_id'),  # Tier 1 External ID
            get_value(subscription['tiers'], 'tier2', 'id'),  # Tier 2 ID
            get_value(subscription['tiers'], 'tier2', 'name'),  # Tier 2 Name
            get_value(subscription['tiers'], 'tier2', 'external_id'),  # Tier 2 External ID
            get_value(subscription['connection'], 'provider', 'id'),  # Provider ID
            get_value(subscription['connection'], 'provider', 'name'),  # Provider Name
            get_value(subscription['connection'], 'hub', 'id'),  # HUB Id
            get_value(subscription['connection'], 'hub', 'name'),  # HUB Name
            get_value(subscription, 'vendor', 'id'),  # Vendor Id
            get_value(subscription, 'vendor', 'name'),  # Vendor Name
            get_value(subscription, 'marketplace', 'name'),  # Marketplace
            get_value(subscription, 'product', 'id'),  # Product ID
            get_value(subscription, 'product', 'name'),  # Product Name
            get_basic_value(subscription, 'status'),  # Subscription Status
            convert_to_datetime(
                get_value(subscription['events'], 'created', 'at'),  # Transaction  Date
            ),
            get_basic_value(subscription['connection'], 'type'),  # Connection Type,
            today_str(),  # Exported At
        )
        progress += 1
        progress_callback(progress, total)


def _get_subscriptions(client, parameters):
    subs_types = ['active', 'suspended', 'terminating', 'terminated', 'draft']

    query = R()
    query &= R().status.oneof(subs_types)
    query &= R().events.created.at.ge(parameters['date']['after'])
    query &= R().events.created.at.le(parameters['date']['before'])

    if parameters.get('connexion_type') and parameters['connexion_type']['all'] is False:
        query &= R().connection.type.oneof(parameters['connexion_type']['choices'])

    if parameters.get('product') and parameters['product']['all'] is False:
        query &= R().product.id.oneof(parameters['product']['choices'])
    if parameters.get('mkp') and parameters['mkp']['all'] is False:
        query &= R().marketplace.id.oneof(parameters['mkp']['choices'])

    # if 'provider_to_exclude' in parameters and len(parameters['provider_to_exclude'].split(sep="|")) > 0:
    #    query &= R().connection.provider.id.out(parameters['provider_to_exclude'].split(sep="|"))

    return client.ns('subscriptions').assets.filter(query)
