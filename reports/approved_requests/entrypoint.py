# -*- coding: utf-8 -*-
#
# Copyright (c) 2023, Carolina Giménez Escalante
# All rights reserved.
#

from reports.approved_requests import utils
from reports.approved_requests.api_calls import request_approved_requests

ADOBE_PARAMS = ['adobe_vip_number', 'adobe_order_id', 'transfer_id', 'action_type', 'adobe_user_email',
                'adobe_customer_id',
                'discount_group']
NCE_PARAMS = ['subscription_id', 'csp_order_id', 'nce_migration_id', 'migration_type', 'microsoft_domain',
              'ms_customer_id', 'cart_id']
ADOBE_PRODUCT = 'PRD-463-843-541'


def generate(client, parameters, progress_callback, renderer_type=None, extra_context=None, ):
    requests = request_approved_requests(client, parameters)

    progress = 0

    total = requests.count()
    for request in requests:
        # get subscription parameters values
        parameters_list = request['asset']['params']
        product_id = request['asset']['product']['id']

        param_discount_level = ''
        param_currency = ''

        if product_id == ADOBE_PRODUCT:
            param_subscription_number = utils.get_param_value(parameters_list, 'adobe_vip_number')
            param_order_number = utils.get_param_value(parameters_list, 'adobe_order_id')
            param_transfer_number = utils.get_param_value(parameters_list, 'transfer_id')
            param_action = utils.get_param_value(parameters_list, 'action_type')
            param_user_email = utils.get_param_value(parameters_list, 'adobe_user_email')
            param_cloud_program_id = utils.get_param_value(parameters_list, 'adobe_customer_id')
            param_discount_level = utils.get_discount_level(utils.get_param_value(parameters_list, 'discount_group'))

            # get currency from configuration params
            param_currency = utils.get_param_value(request['asset']['configuration']['params'], 'Adobe_Currency')

        else:
            param_subscription_number = utils.get_param_value(parameters_list, 'subscription_id')
            param_order_number = utils.get_param_value(parameters_list, 'csp_order_id')
            param_transfer_number = utils.get_param_value(parameters_list, 'nce_migration_id')
            param_action = utils.get_param_value(parameters_list, 'migration_type')
            param_user_email = utils.get_param_value(parameters_list, 'microsoft_domain')
            param_cloud_program_id = utils.get_param_value(parameters_list, 'ms_customer_id')

        for item in request['asset']['items']:
            delta_str = _get_delta_str(item)
            if delta_str == '':
                continue

            yield (
                utils.get_basic_value(request, 'id'),  # Request ID
                utils.get_value(request, 'asset', 'id'),  # Connect Subscription ID
                utils.get_value(request, 'asset', 'external_id'),  # End Customer Subscription ID
                param_action,  # Type of Purchase
                param_order_number,  # Adobe Order #
                param_transfer_number,  # Adobe Transfer ID #
                param_subscription_number,  # VIP #
                param_cloud_program_id,  # Adobe Cloud Program ID
                param_discount_level,  # Pricing SKU Level (Volume Discount level)
                utils.get_basic_value(item, 'display_name'),  # Product Description
                utils.get_basic_value(item, 'mpn'),  # Part Number
                utils.get_basic_value(item, 'period'),  # Product Period
                utils.get_basic_value(item, 'quantity'),  # Cumulative Seat
                delta_str,  # Order Delta
                utils.get_value(request['asset']['tiers'], 'tier1', 'id'),  # Reseller ID
                utils.get_value(request['asset']['tiers'], 'tier1', 'external_id'),  # Reseller External ID
                utils.get_value(request['asset']['tiers'], 'tier1', 'name'),  # Reseller Name
                utils.get_value(request['asset']['tiers'], 'customer', 'name'),  # End Customer Name
                utils.get_value(request['asset']['tiers'], 'customer', 'external_id'),  # End Customer External ID
                utils.get_value(request['asset']['connection'], 'provider', 'id'),  # Provider ID
                utils.get_value(request['asset']['connection'], 'provider', 'name'),  # Provider Name
                utils.get_value(request, 'marketplace', 'name'),  # Marketplace
                utils.get_value(request['asset']['connection'], 'hub', 'id'),  # HUB ID
                utils.get_value(request['asset']['connection'], 'hub', 'name'),  # HUB Name
                utils.get_value(request['asset'], 'product', 'id'),  # Product ID
                utils.get_value(request['asset'], 'product', 'name'),  # Product Name
                utils.get_value(request, 'asset', 'status'),  # Subscription Status
                utils.convert_to_datetime(
                    utils.get_basic_value(request, 'effective_date'),  # Effective  Date
                ),
                utils.convert_to_datetime(
                    utils.get_basic_value(request, 'created'),  # Creation  Date
                ),
                utils.get_basic_value(request, 'type'),  # Transaction Type
                param_user_email,  # User Email
                param_currency,  # Currency
                utils.get_basic_value(request['asset']['connection'], 'type'),  # Connection Type,
                utils.today_str(),  # Exported At
            )
        progress += 1
        progress_callback(progress, total)


def _get_delta_str(item):
    if (utils.get_basic_value(item, 'item_type') != 'PPU'
            and (utils.get_basic_value(item, 'quantity') != '0'
                 or utils.get_basic_value(item, 'old_quantity') != '0')):
        delta = 0
        delta_str = '-'
        if len(item['quantity']) > 0 and len(item['old_quantity']) > 0:
            try:
                delta = float(item['quantity']) - float(item['old_quantity'])
            except Exception:
                delta_str = item['quantity'] + ' - ' + item['old_quantity']
        if delta_str == '-' and delta > 0:
            delta_str = "+" + str(delta)
        if delta_str == '-' and delta < 0:
            delta_str = str(delta)
        return delta_str
    return ''
