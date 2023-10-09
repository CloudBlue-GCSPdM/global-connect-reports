
from connect.client import R
import requests


def request_assets(client, input_data) -> list:
    rql = R().events.created.at.ge(input_data['date']['after'])
    rql &= R().events.created.at.le(input_data['date']['before'])
    rql &= R().product.id.oneof(input_data['product']['choices'])
    if input_data['status'] != "all":
        rql &= R().status.eq(input_data['status'])
    return client('subscriptions').assets.filter(rql).all()


def request_listing(client, marketplace_id, product_id) -> dict:
    rql = R()
    rql &= R().marketplace.id.eq(marketplace_id)
    rql &= R().product.id.eq(product_id)
    rql &= R().status.eq('listed')
    return client.listings.filter(rql).first()


def request_price_list(client, price_list_id) -> dict:
    rql = R()
    rql &= R().pricelist.id.eq(price_list_id)
    rql &= R().status.eq('active')
    return client('pricing').versions.filter(rql).first()


def request_price_list_version_points(client, price_list_version_id) -> list:
    rql = R()
    rql &= R().status.eq('filled')
    return client('pricing').versions[price_list_version_id].points.filter(rql).all()


def request_get(url):
    res = requests.models.Response
    res.status_code = 0
    try:
        res = requests.get(url)
    except requests.exceptions.RequestException as e:
        print(e)
    return res


def request_approved_requests(client, parameters):
    query = R()
    query &= R().status.eq('approved')
    query &= R().created.ge(parameters['date']['after'])
    query &= R().created.le(parameters['date']['before'])

    if parameters.get('connexion_type') and parameters['connexion_type']['all'] is False:
        query &= R().asset.connection.type.oneof(parameters['connexion_type']['choices'])
    if parameters.get('product') and parameters['product']['all'] is False:
        query &= R().asset.product.id.oneof(parameters['product']['choices'])
    if parameters.get('rr_type') and parameters['rr_type']['all'] is False:
        query &= R().type.oneof(parameters['rr_type']['choices'])
    if parameters.get('mkp') and parameters['mkp']['all'] is False:
        query &= R().marketplace.id.oneof(parameters['mkp']['choices'])
    return client.requests.filter(query).order_by("created")


def request_asset(client, asset_id):
    query = R()
    query &= R().id.eq(asset_id)
    return client('subscriptions').assets.filter(query).first()