# -*- coding: utf-8 -*-
#
# Copyright (c) 2021, Carolina Giménez Escalante
# All rights reserved.
#

from connect.client.rql import R
from reports.subscriptions_report.utils import (get_value, get_basic_value, today_str)

HEADERS = ['Parameter ID', 'Parameter Name', 'Item ID', 'Item Name',
           'Marketplace ID', 'Marketplace Name', 'Value', 'Exported At']


def generate(client=None, parameters=None, progress_callback=None, renderer_type=None, extra_context_callback=None):
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
    params = _get_product_parameters(client, parameters)

    progress = 0
    total = params.count() + 1

    for param in params:

        if progress == 0:
            yield HEADERS
            progress += 1
            total += 1
            progress_callback(progress, total)

        item_id = ''
        item_name = ''
        if 'item' in param:
            item_id = get_value(param, 'item', 'id')
            item_name = get_value(param, 'item', 'name')
        mkp_id = ''
        mkp_name = ''
        if 'marketplace' in param:
            mkp_id = get_value(param, 'marketplace', 'id')
            mkp_name = get_value(param, 'marketplace', 'name')
        value_param = ''
        if 'value' in param:
            value_param = get_basic_value(param, 'value')

        yield (
            get_value(param, 'parameter', 'id'),  # Param ID
            get_value(param, 'parameter', 'title'),  # Param Name
            item_id,  # Item ID
            item_name,  # Item Name
            mkp_id,  # Marketplace ID
            mkp_name,  # Marketplace Name
            value_param,  # Value
            today_str(),  # Exported At
        )

        progress += 1
        progress_callback(progress, total)


def _get_product_parameters(client, parameters):
    query = R()

    product_id = parameters['product']
    if parameters.get('mkp') and parameters['mkp']['all'] is False:
        query &= R().marketplace.id.oneof(parameters['mkp']['choices'])

    return client.products[product_id].configurations.filter(query)
