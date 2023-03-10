# -*- coding: utf-8 -*-
#
# Copyright (c) 2021, Carolina Giménez Escalante
# All rights reserved.
#

from connect.client.rql import R
from reports.subscriptions_report.utils import (get_value, get_basic_value, today_str)

HEADERS = ['Vendor ID', 'Vendor Name', 'Technical Contact', 'Business Contact',
           'Product ID', 'Product Name', 'Product Status', 'Product Version',
           'Category', 'Product Description', 'Supports Suspend and Resume', 'Requires Reseller Authorization',
           'Automated Fulfillment', 'Pay-as-you-go Capability', 'Active Subscriptions', 'Active Synd Subscriptions', 'Exported At']

PRODUCTS = {}


def generate(client, parameters, progress_callback):
    products = _get_products(client, parameters)
    listings = _get_listings(client, parameters)

    progress = 0
    total = products.count() + 1 + listings.count()

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

    if progress == 0:
        yield HEADERS
        progress += 1
        total += 1
        progress_callback(progress, total)

    processed = []
    for listing in listings:
        vendor_id = get_value(listing, 'vendor', 'id')
        if vendor_id in PRODUCTS.keys():
            products = PRODUCTS[vendor_id]['products']
        else:
            products = []

        for product in products:
            if get_value(listing, 'product', 'id') == product['id'] and product['id'] not in processed:
                processed.append(product['id'])
                yield (
                    vendor_id,  # Vendor ID
                    product['vendor_name'],  # Vendor Name
                    "-",  # Tech Contact
                    "-",  # Business Contact
                    product['id'],  # Product ID
                    product['product_name'],  # Product Name
                    product['status'],  # Product Status
                    product['version'],  # Product Version
                    '',  # Last Version Date
                    product['category'],  # Category
                    product['description'],  # Product Description
                    product['suspend_resume'],  # Supports Suspend
                    product['requires_reseller'],  # Requires Reseller Auth.
                    _get_automated_provisioning(client),  # Automated Fulfillment
                    product['ppu'],  # Pay-as-you-go capability.
                    _get_active_subscriptions(client, product['id'], False).count(),  # Active Subscriptions
                    _get_active_subscriptions(client, product['id'], True).count(),  # Active Synd Subscriptions
                    today_str(),  # Exported At
                )

        progress += 1
        progress_callback(progress, total)


def _get_products(client, parameters):
    query = R()
    if parameters.get('product_status') and parameters['product_status']['all'] is False:
        query &= R().status.oneof(parameters['product_status']['choices'])
    return client.products.filter(query).order_by("name")


def _get_listings(client, parameters):
    query = R()
    query &= R().status.oneof(['listed'])
    if parameters.get('mkp') and parameters['mkp']['all'] is False:
        query &= R().marketplace.id.oneof(parameters['mkp']['choices'])
    if parameters.get('product') and parameters['product']['all'] is False:
        query &= R().product.id.oneof(parameters['product']['choices'])

    return client.listings.filter(query)


def _get_active_subscriptions(client, product, syndc):
    query = R()
    query &= R().status.oneof(['active'])
    query &= R().connection.type.oneof(['production'])
    query &= R().product.id.oneof([product])
    if syndc:
        query &= R().connection.provider.id.out(['PA-239-689'])

    return client.assets.filter(query)


def _get_automated_provisioning(client):
    query = R()
    query &= R().status.oneof(['active'])
    query &= R().extension.name.oneof(['custom', 'eaas'])
    tokens_list = client('auth').tokens.filter(query)
    token_ids = []
    for token in tokens_list:
        token_ids.append(token['id'])

    query = R()
    query &= R().events.updated.by.id.oneof(token_ids)

    return client.conversations.filter(query).count() > 0
