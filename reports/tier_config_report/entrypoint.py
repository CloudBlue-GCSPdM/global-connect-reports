# -*- coding: utf-8 -*-
#
# Copyright (c) 2021, Carolina Giménez Escalante
# All rights reserved.
#

from cnct import R
from reports.subscriptions_report.utils import get_basic_value
from reports.subscriptions_report.utils import convert_to_datetime, get_value, today_str

HEADERS = ['TC ID', 'Tier External ID', 'Tier ID', 'Tier Name',
           'Product ID', 'Product Name', 'Marketplace ID', 'Marketplace Name',
           'Param1', 'Param 2',
           'Updated At', 'Exported At']


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
    tcs = _get_tcs(client, parameters)

    progress = 0
    total = tcs.count()

    for tc in tcs:

        param1 = ''
        param2 = ''
        # get parameters values
        if 'parameter_id' in parameters and len(str(parameters['parameter_id'])) > 0:
            i = 0
            for param_requested in parameters['parameter_id'].split(sep="|"):
                for param in tc['params']:
                    if param_requested == get_basic_value(param, 'id'):
                        if i == 0:
                            param1 = get_basic_value(param, 'value')
                            HEADERS[8] = get_basic_value(param, 'name')
                        elif i == 1:
                            param2 = get_basic_value(param, 'value')
                            HEADERS[9] = get_basic_value(param, 'name')
                        i = i + 1

        yield (
            get_basic_value(tc, 'id'),
            get_value(tc, 'account', 'external_id'),
            get_value(tc, 'account', 'id'),
            get_value(tc, 'account', 'name'),
            get_value(tc, 'product', 'id'),
            get_value(tc, 'product', 'name'),
            get_value(tc, 'marketplace', 'id'),
            get_value(tc, 'marketplace', 'name'),
            param1,
            param2,
            convert_to_datetime(
                get_value(tc['events'], 'updated', 'at'),
            ),
            today_str(),
            )
        progress += 1
        progress_callback(progress, total)


def _get_tcs(client, parameters):
    tc_status = ['active']

    query = R()
    query &= R().status.oneof(tc_status)

    if parameters.get('connexion_type') and parameters['connexion_type']['all'] is False:
        query &= R().connection.type.oneof(parameters['connexion_type']['choices'])

    if parameters.get('product') and parameters['product']['all'] is False:
        query &= R().product.id.oneof(parameters['product']['choices'])
    if parameters.get('mkp') and parameters['mkp']['all'] is False:
        query &= R().marketplace.id.oneof(parameters['mkp']['choices'])

    return client.ns('tier').collection('configs').filter(query)