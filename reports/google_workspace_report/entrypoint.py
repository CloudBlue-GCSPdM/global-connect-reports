# -*- coding: utf-8 -*-
#
# Copyright (c) 2023, CloudBlue
# All rights reserved.
#

from connect.client import ClientError, R

from reports.subscriptions_report.utils import (convert_to_datetime, get_value, get_param_value, get_basic_value)

HEADERS = (
    'Subscription ID', 'Subscription External ID', 'Vendor primary key',
    'Subscription Type', 'Google Domain', 'Google Customer ID', 'Item Name', 'Item MPN',
    'Creation date', 'Updated date', 'Status', 'Billing Period',
    'Anniversary Day', 'Anniversary Month', 'Contract ID', 'Contract Name',
    'Customer ID', 'Customer Name', 'Customer External ID',
    'Tier 1 ID', 'Tier 1 Name', 'Tier 1 External ID',
    'Tier 2 ID', 'Tier 2 Name', 'Tier 2 External ID',
    'Provider Account ID', 'Provider Account name',
    'Vendor Account ID', 'Vendor Account Name',
    'Product ID', 'Product Name', 'Hub ID', 'Hub Name',
)

GOOGLE_PRODUCT = ['PRD-550-104-278']


def generate(
        client=None,
        parameters=None,
        progress_callback=None,
        renderer_type=None,
        extra_context_callback=None,
):
    products_primary_keys = {}

    product_params = _get_product_parameters(client)

    subscriptions = _get_subscriptions(client, parameters)
    total = subscriptions.count()
    progress = 0
    if renderer_type == 'csv':
        yield HEADERS
        progress += 1
        total += 1
        progress_callback(progress, total)

    for subscription in subscriptions:
        primary_vendor_key = get_primary_key(
            subscription.get('params', []),
            subscription['product']['id'],
            client,
            products_primary_keys,
        )
        if renderer_type == 'json':
            yield {
                HEADERS[idx].replace(' ', '_').lower(): value
                for idx, value in enumerate(_process_line(subscription, primary_vendor_key, product_params))
            }
        else:
            yield _process_line(subscription, primary_vendor_key, product_params)
        progress += 1
        progress_callback(progress, total)


def _get_subscriptions(client, parameters):
    query = R()
    query &= R().product.id.oneof(GOOGLE_PRODUCT)
    if parameters.get('date') and parameters['date']['after'] != '':
        query &= R().events.created.at.ge(parameters['date']['after'])
        query &= R().events.created.at.le(parameters['date']['before'])
    if parameters.get('mkp') and parameters['mkp']['all'] is False:
        query &= R().marketplace.id.oneof(parameters['mkp']['choices'])
    if parameters.get('connection_type') and parameters['connection_type']['all'] is False:
        query &= R().asset.connection.type.oneof(parameters['connection_type']['choices'])
    if parameters.get('status') and parameters['status']['all'] is False:
        query &= R().status.oneof(parameters['status']['choices'])

    return client.ns('subscriptions').assets.filter(query)


def _get_product_parameters(client):
    product_id = GOOGLE_PRODUCT[0]
    return client.products[product_id].configurations.filter(R()).limit(500)


def calculate_period(delta, uom):
    if delta == 1:
        if uom == 'monthly':
            return 'Monthly'
        return 'Yearly'
    else:
        if uom == 'monthly':
            return f'{int(delta)} Months'
        return f'{int(delta)} Years'


def search_product_primary(parameters):
    for param in parameters:
        if param['constraints'].get('reconciliation'):
            return param['name']


def get_primary_key(parameters, product_id, client, products_primary_keys):
    try:
        if product_id not in products_primary_keys:
            prod_parameters = client.collection(
                'products',
            )[product_id].collection(
                'parameters',
            ).all()
            primary_id = search_product_primary(prod_parameters)
            products_primary_keys[product_id] = primary_id
        for param in parameters:
            if param['id'] == products_primary_keys[product_id]:
                return param['value'] if 'value' in param and len(param['value']) > 0 else '-'
    except ClientError:
        pass
    return '-'


def get_item_data(items):
    if len(items) == 0:
        return '-', '-', '-'
    elif len(items) == 1:
        return items[0]['display_name'], items[0]['mpn'], items[0]['global_id']
    else:
        for item in items:
            if 'GOOGLE_DRIVE_STORAGE' in item.get('mpn'):
                return 'Google Drive Storage', 'GOOGLE_DRIVE_STORAGE', item.get('global_id')

        return items[0]['display_name'], items[0]['mpn'], items[0]['global_id']


def _get_config_item_param(item_id, product_params, param_id):
    for param in product_params:
        if 'parameter' in param and get_value(param, 'parameter', 'id') == param_id:
            if 'item' in param and item_id == get_value(param, 'item', 'id'):
                return get_basic_value(param, 'value')
    return '-'


def _process_line(subscription, primary_vendor_key, product_params):
    params = subscription.get('params', [])
    item_name, item_mpn, item_id = get_item_data(subscription.get('items', []))
    item_sku = _get_config_item_param(item_id, product_params, "sku_id")
    item_product = _get_config_item_param(item_id, product_params, "product_id")

    return (
        subscription.get('id'),
        subscription.get('external_id', '-'),
        primary_vendor_key,
        get_value(subscription, 'connection', 'type'),
        get_param_value(params, 'domain'),
        get_param_value(params, 'customer_id'),
        item_name,
        item_mpn,
        item_sku,
        item_product,
        convert_to_datetime(subscription['events']['created']['at']),
        convert_to_datetime(subscription['events']['updated']['at']),
        subscription.get('status'),
        calculate_period(
            subscription['billing']['period']['delta'],
            subscription['billing']['period']['uom'],
        ) if 'billing' in subscription else '-',
        subscription.get('billing', {}).get('anniversary', {}).get('day', '-'),
        subscription.get('billing', {}).get('anniversary', {}).get('month', '-'),
        subscription['contract']['id'] if 'contract' in subscription else '-',
        subscription['contract']['name'] if 'contract' in subscription else '-',
        get_value(subscription.get('tiers', ''), 'customer', 'id'),
        get_value(subscription.get('tiers', ''), 'customer', 'name'),
        get_value(subscription.get('tiers', ''), 'customer', 'external_id'),
        get_value(subscription.get('tiers', ''), 'tier1', 'id'),
        get_value(subscription.get('tiers', ''), 'tier1', 'name'),
        get_value(subscription.get('tiers', ''), 'tier1', 'external_id'),
        get_value(subscription.get('tiers', ''), 'tier2', 'id'),
        get_value(subscription.get('tiers', ''), 'tier2', 'name'),
        get_value(subscription.get('tiers', ''), 'tier2', 'external_id'),
        get_value(subscription['connection'], 'provider', 'id'),
        get_value(subscription['connection'], 'provider', 'name'),
        get_value(subscription['connection'], 'vendor', 'id'),
        get_value(subscription['connection'], 'vendor', 'name'),
        get_value(subscription, 'product', 'id'),
        get_value(subscription, 'product', 'name'),
        get_value(subscription['connection'], 'hub', 'id'),
        get_value(subscription['connection'], 'hub', 'name'),
    )
