# -*- coding: utf-8 -*-
#
# Copyright (c) 2021, Carolina Giménez Escalante
# All rights reserved.
#

from connect.client.rql import R
from reports.subscriptions_report.utils import (get_value, get_basic_value, today_str, convert_to_datetime)

HEADERS = ['Vendor ID', 'Vendor Name', 'Technical Contact', 'Business Contact',
           'Product ID', 'Product Name', 'Product Status', 'Product Version', 'Last Version Date',
           'Category', 'Product Description', 'Supports Suspend and Resume', 'Requires Reseller Authorization',
           'Automated Fulfillment', 'Pay-as-you-go Capability', 'Active Subscriptions', 'Active Synd Subscriptions',
           'Exported At']

PRODUCTS = {}
VENDOR_CONTACTS = {}
VERSIONS = {}


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
            "version": _get_version(get_basic_value(product, 'id'), client)['version'],
            "version_date": _get_version(get_basic_value(product, 'id'), client)['date'],
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

    for vendor in PRODUCTS.keys():
        if vendor not in VENDOR_CONTACTS.keys():
            VENDOR_CONTACTS[vendor] = _get_contacts(vendor, client)

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
                    VENDOR_CONTACTS[vendor_id]["technical"],  # Tech Contact
                    VENDOR_CONTACTS[vendor_id]["business"],  # Business Contact
                    product['id'],  # Product ID
                    product['product_name'],  # Product Name
                    product['status'],  # Product Status
                    product['version'],  # Product Version
                    product['version_date'],  # Last Version Date
                    product['category'],  # Category
                    product['description'],  # Product Description
                    product['suspend_resume'],  # Supports Suspend
                    product['requires_reseller'],  # Requires Reseller Auth.
                    "_get_automated_provisioning(client)",  # Automated Fulfillment
                    product['ppu'],  # Pay-as-you-go capability.
                    _get_active_subscriptions(client, product['id'], False).count(),  # Active Subscriptions
                    _get_active_subscriptions(client, product['id'], True).count(),  # Active Synd Subscriptions
                    today_str(),  # Exported At
                )

        progress += 1
        progress_callback(progress, total)


def _get_version(product_id, client):
    if product_id not in VERSIONS.keys():
        query = R()
        versions = client.products[product_id].versions.filter(query).order_by("created")
        for version in versions:
            if version['latest']:
                v_date = convert_to_datetime(get_value(version['events'],'published', 'at'))
                VERSIONS[product_id] = {'version': version["version"], 'date': v_date}
                return VERSIONS[product_id]
        VERSIONS[product_id] = {'version': '', 'date': '-ccli '}
    return VERSIONS[product_id]


def _get_contacts(vendor_id, client):
    if len(vendor_id) == 0:
        return {"technical": '', "business": ''}

    query = R()
    query &= R().tags.id.oneof(['TG-000'])
    buss_emails = ''
    tech_emails = ''

    query = R()
    query &= R().id.oneof([vendor_id])
    #  business_users = client.account[vendor_id].users.filter(query).order_by("name")
    try:
        for partner in client.partners.filter(query):
            if 'contacts' in partner:
                for contact in partner["contacts"]:
                    for tag in contact["tags"]:
                        if tag['id'] == 'TG-000':
                            buss_emails = buss_emails + contact['email']
                            buss_emails = buss_emails + ', '
                        if tag['id'] == 'TG-001':
                            tech_emails = tech_emails + contact['email']
                            tech_emails = tech_emails + ', '
    except:
        tech_emails = vendor_id
        buss_emails = vendor_id
    #  business_users = client.account[vendor_id].filter(query).order_by("name")

    query = R()
    query &= R().contacts.tags.id.oneof(['TG-001'])
    #  tech_users = client.account[vendor_id].users.filter(query).order_by("name")
    #  tech_users = client.partners[vendor_id].filter(query).order_by("name")

    if len(buss_emails) > 0:
        buss_emails = buss_emails[:len(buss_emails) - 2]
    if len(tech_emails) > 0:
        tech_emails = tech_emails[:len(tech_emails) - 2]

    return {"technical": tech_emails, "business": buss_emails}


def _get_products(client, parameters):
    query = R()
    if parameters.get('product_status') and parameters['product_status']['all'] is False:
        query &= R().status.oneof(parameters['product_status']['choices'])
    if parameters.get('product') and parameters['product']['all'] is False:
        query &= R().id.oneof(parameters['product']['choices'])
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
