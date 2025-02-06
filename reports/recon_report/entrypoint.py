# -*- coding: utf-8 -*-
#
# Copyright (c) 2023, Carolina Gimenez Escalante
# All rights reserved.

from datetime import datetime
from connect.client.rql import R
from .utils import get_first_day_month, get_last_day_month
from .utils import (get_value, get_basic_value, convert_to_datetime, today_str,
                    get_next_month_anniversary, get_next_year_anniversary, MonthlyBillingItem)

HEADERS = ['Month Year', 'Subscription ID', 'Subscription External ID',
           'Subscription External UUID', 'Vendor Subscription Id',
           'Item Name', 'Item MPN', 'Item Period', 'Quantity', 'Consumption',
           'Customer Name', 'Customer External ID', 'Customer Email',
           'Tier 1 Name', 'Tier 1 External ID',
           'Marketplace', 'Hub Name', 'Product Name', 'Subscription Status',
           'Date', 'Subscription Start Date', 'Subscription End Date', 'Exported At']


def generate(
        client=None,
        input_data=None,
        progress_callback=None,
        renderer_type='xlsx',
        extra_context_callback=None,
):
    subscriptions = _get_subscriptions(client, input_data)

    progress = 0
    total = subscriptions.count() + 1

    for subscription in subscriptions:
        subscription_active_periods = {}
        requests = _get_approved_requests(client, get_basic_value(subscription, 'id'))
        # consumption = _get_consumption(client, get_basic_value(subscription, 'id'))
        item_per_date_list = {}

        product_name = get_value(subscription, 'product', 'name')
        vendor_sub_id = ''

        for param in subscription['params']:
            if get_basic_value(param, 'name') == 'KasperskySubscriptionId':
                vendor_sub_id = get_basic_value(param, 'value')
            if get_basic_value(param, 'name') == 'team_name':
                vendor_sub_id = get_basic_value(param, 'value')
            if get_basic_value(param, 'name') == 'entitlement_id':
                vendor_sub_id = get_basic_value(param, 'value')
            if get_basic_value(param, 'name') == 'subscription_id':
                vendor_sub_id = get_basic_value(param, 'value')
            if get_basic_value(param, 'name') == 'CorporateEmailAddress':
                vendor_sub_id = get_basic_value(param, 'value')

        # get subscription active periods
        period_number = 1
        start = ''
        subs_start_date = ''
        subs_end_date = ''
        periods: list = []
        items = {}
        end = None
        for request in requests:
            if request['type'] == 'purchase':
                start = convert_to_datetime(get_basic_value(request, 'effective_date'))
                subs_start_date = start
                items = request["asset"]["items"]

            if request['type'] == 'cancel' or request['type'] == 'suspend' or request['type'] == 'change':
                end = convert_to_datetime(get_basic_value(request, 'effective_date'))
                subscription_active_periods[period_number] = {"start": start,
                                                              "end": end,
                                                              "items": items}
                if request['type'] == 'cancel':
                    subs_end_date = end
                period_number = period_number + 1

            if request['type'] == 'change' or request['type'] == 'resume':
                start = convert_to_datetime(get_basic_value(request, 'effective_date'))
                end = None
                items = request["asset"]["items"]

        if end is None:
            subscription_active_periods[period_number] = {"start": start,
                                                          "end": end,
                                                          "items": items}

        if len(subscription_active_periods) == 0:
            # Subscription without approved requests.
            continue

        if progress == 0 and renderer_type != 'xlsx':
            yield HEADERS
            progress += 1
            total += 1
            progress_callback(progress, total)

        for active_period in subscription_active_periods.keys():
            start = subscription_active_periods[active_period]["start"]
            end = subscription_active_periods[active_period]["end"]

            for item in subscription_active_periods[active_period]['items']:
                if item['quantity'].isdigit() and int(item['quantity']) > 0:
                    period = get_basic_value(item, 'period')

                    if period == 'OneTime':
                        billing_item = MonthlyBillingItem(
                            item_mpn=get_basic_value(item, 'mpn'),
                            item_period=period,
                            item_display_name=get_basic_value(item, 'display_name'),
                            quantity=get_basic_value(item, 'quantity'),
                            old_quantity=get_basic_value(item, 'old_quantity')
                        )
                        item_per_date_list = {get_first_day_month(start): billing_item}

                    else:
                        # Solo las anuales para reporte Dell
                        # if period.lower().__contains__('month'):
                        #    continue

                        date_period: datetime = start
                        last_date = end
                        if last_date is None:
                            last_date = get_first_day_month(datetime.today())

                        while date_period <= last_date:
                            billing_item = MonthlyBillingItem(
                                item_mpn=get_basic_value(item, 'mpn'),
                                item_period=period,
                                item_display_name=get_basic_value(item, 'display_name'),
                                quantity=get_basic_value(item, 'quantity'),
                                old_quantity=get_basic_value(item, 'old_quantity')
                            )
                            item_per_date_list[get_first_day_month(date_period)] = billing_item

                            if period.lower().__contains__('year'):
                                date_period = get_next_year_anniversary(date_period, 1)
                                if period.lower().__contains__('2'):
                                    date_period = get_next_year_anniversary(date_period, 1)
                                if period.lower().__contains__('3'):
                                    date_period = get_next_year_anniversary(date_period, 2)
                            if period.lower().__contains__('month'):
                                date_period = get_next_month_anniversary(date_period)

            for date in item_per_date_list.keys():
                subscription_period: MonthlyBillingItem = item_per_date_list[date]

               # if date < convert_to_datetime(input_data['date_end']):
               #     continue

                billing_date = get_last_day_month(date) # ultimo dia del mes del term de la sub.

                if billing_date.month == start.month and billing_date.year == start.year: # si es el primer term
                    billing_date = start # se pone ese dia, no el último del mes, esto lo quería Kaspersky

                if billing_date >= get_first_day_month(start) and (end is None or end >= billing_date):
                    # se incluye si el mes del term es anterior al ultimo term
                    qty = subscription_period.Quantity
                    if date in periods:
                        qty = subscription_period.Delta
                    if subscription_period.Period.lower().__contains__('year'):
                        if (subs_start_date.month != date.month and
                                date != get_next_year_anniversary(subs_start_date, 1)):
                            qty = subscription_period.Delta

                    periods.append(datetime(date.year, date.month, 1, 0, 0, 0))
                    yield (
                        date,
                        get_basic_value(subscription, 'id'),  # Subscription ID
                        get_basic_value(subscription, 'external_id'),  # Subscription External ID
                        get_basic_value(subscription, 'external_uid'),  # Subscription External UUID
                        vendor_sub_id,  # Kaspersky Subscription Id
                        subscription_period.Item_name,  # Item Name
                        subscription_period.Item_mpn,  # Item MPN
                        subscription_period.Period,  # Item Period
                        int(qty),  # Quantity
                        0,
                        get_value(subscription['tiers'], 'customer', 'name'),  # Customer Name
                        get_value(subscription['tiers'], 'customer', 'external_id'),  # Customer External ID
                        get_value(subscription['tiers']['customer']['contact_info'], 'contact', 'email'),
                        # Customer email
                        get_value(subscription['tiers'], 'tier1', 'name'),  # Tier 1 Name
                        get_value(subscription['tiers'], 'tier1', 'external_id'),  # Tier 1 External ID
                        get_value(subscription, 'marketplace', 'name'),  # Marketplace
                        get_value(subscription['connection'], 'hub', 'name'),  # Hub Name
                        product_name,  # Product Name
                        get_basic_value(subscription, 'status'),  # Subscription Status
                        billing_date,  # Date billing_date
                        subs_start_date,  # Subscription Start Date subs_start_date
                        subs_end_date,  # Subscription end Date
                        today_str(),  # Exported At
                    )
            progress += 1
            progress_callback(progress, total)


def _get_subscriptions(client, parameters):
    # All the subscriptions created during the report period.
    subs_types = ['active', 'suspended', 'terminating', 'terminated']

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
    if parameters.get('hub'):
        query &= R().connection.hub.id.oneof(parameters['hub'].split(sep="|"))

    return client.ns('subscriptions').assets.filter(query)


def _get_items(client, subscription_id):
    return client.assets[subscription_id].get()['items']


def _get_approved_requests(client, asset_id):
    # All the subscription requests approved sorted by creation date
    query = R()
    query &= R().status.oneof(['approved'])
    query &= R().asset.id.oneof([str(asset_id)])

    return client.requests.filter(query).order_by("created")

def _get_consumption(client, asset_id):
    # Consumed
    query = R()
    query &= R().asset.id.oneof([str(asset_id)])

    return client.usage.aggregates.filter(query)

