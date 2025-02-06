# -*- coding: utf-8 -*-
#
# Copyright (c) 2021, Carolina Giménez Escalante
# All rights reserved.
#

from connect.client.rql import R
from reports.subscriptions_report.utils import (get_value, get_basic_value, convert_to_datetime, today_str)

HEADERS = ['Vendor ID', 'Vendor Name', 'Product ID', 'Product Name', 'Product Status', 'Product Version',
           'Category', 'Product Description', 'Supports Suspend and Resume', 'Requires Reseller Authorization',
           'Pay-as-you-go Capability', 'Contract ID', 'Contract Type', 'Contract kind', 'Contract Name',
           'Contract Version', 'Contract Status', 'Marketplace', 'Provider Name', 'Signed Date', 'Item ID',
           'Item Name', 'Item Status', 'Item MPN', 'Item Type', 'Item Period', 'Item Description', 'Exported At']

PRODUCTS = {}

PRODUCT_ITEMS = {}

def generate(client, parameters, progress_callback):
    products = _get_products(client, parameters)
    contracts = _get_contracts(client, parameters)

    progress = 0
    total = products.count() + 1 + contracts.count()

    for product in products:
        vendor_id = get_value(product, 'owner', 'id')
        schema = get_value(product['capabilities'], 'ppu', 'schema')
        ppu = False
        if schema != '-':
            ppu = True

        product = {
            "id": get_basic_value(product, 'id'),
            "vendor_id": get_value(product, 'owner', 'id'),
            "vendor_name": get_value(product, 'owner', 'name'),
            "product_name": get_basic_value(product, 'name'),
            "status": get_basic_value(product, 'status'),
            "version": get_basic_value(product, 'version'),
            "category": get_value(product, 'category', 'name'),
            "description": get_basic_value(product, 'short_description'),
            "suspend_resume": get_value(product, 'configurations', 'suspend_resume_supported'),
            "requires_reseller": get_value(product, 'configurations', 'requires_reseller_information'),
            "ppu": ppu,
        }
        if vendor_id not in PRODUCTS.keys():
            PRODUCTS[vendor_id] = {'products': []}
        PRODUCTS[vendor_id]['products'].append(product)
        items = list(_get_items(client, product['id']))
        PRODUCT_ITEMS[product['id']] = items

    if progress == 0:
        yield HEADERS
        progress += 1
        total += 1
        progress_callback(progress, total)

    for contract in contracts:
        vendor_id = get_value(contract, 'owner', 'id')
        if vendor_id in PRODUCTS.keys():
            products = PRODUCTS[vendor_id]['products']
        else:
            products = []

        for product in products:
            yield from _process_items(contract, product, vendor_id)

        progress += 1
        progress_callback(progress, total)


def _process_items(contract, product, vendor_id):
    items = PRODUCT_ITEMS[product['id']]
    for item in items:
        yield (
            vendor_id,  # Vendor ID
            product['vendor_name'],  # Vendor Name
            product['id'],  # Product ID
            product['product_name'],  # Product Name
            product['status'],  # Product Status
            product['version'],  # Product Version
            product['category'],  # Category
            product['description'],  # Product Description
            product['suspend_resume'],  # Supports Suspend
            product['requires_reseller'],  # Requires Reseller Auth.
            product['ppu'],  # Pay-as-you-go capability.
            get_basic_value(contract, 'id'),  # Contract ID
            get_basic_value(contract, 'type'),  # Contract type
            get_basic_value(contract, 'kind'),  # Contract kind
            get_basic_value(contract, 'name'),  # Contract Name
            get_basic_value(contract, 'version'),  # Contract Version
            get_basic_value(contract, 'status'),  # Contract Status
            get_value(contract, 'marketplace', 'name'),  # Marketplace
            get_value(contract, 'marketplace', 'id'),  # Marketplace ID
            get_value(contract, 'owner', 'name'),  # Provider Name
            convert_to_datetime(
                get_value(contract, 'activation', 'date'),  # Signed  Date
            ),
            get_basic_value(item, 'id'),  # Item ID
            get_basic_value(item, 'name'),  # Item Name
            get_basic_value(item, 'status'),  # Item Status
            get_basic_value(item, 'mpn'),  # Item MPN
            get_basic_value(item, 'type'),  # Item Type
            get_basic_value(item, 'period'),  # Item Period
            get_basic_value(item, 'description'),  # item description
            today_str(),  # Exported At
        )


def _get_products(client, parameters):
    query = R()
    if parameters.get('product') and parameters['product']['all'] is False:
        query &= R().id.oneof(parameters['product']['choices'])
    if parameters.get('product_status') and parameters['product_status']['all'] is False:
        query &= R().status.oneof(parameters['product_status']['choices'])

    return client.products.filter(query).order_by("name")


def _get_contracts(client, parameters):
    query = R()
    query &= R().events.created.at.ge(parameters['date']['after'])
    query &= R().events.created.at.le(parameters['date']['before'])
    status = ['active', 'terminated']
    if parameters.get('status') and parameters['status']['all'] is False:
        query &= R().status.oneof(parameters['status']['choices'])
    else:
        query &= R().status.oneof(status)

    return client.contracts.filter(query)


def _get_items(client, product_id):
    query = R()
    return client.products[product_id].items.filter(query)
