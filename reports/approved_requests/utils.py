import datetime


def get_param_value(params: list, value: str) -> str:
    try:
        if params[0]['id'] == value:
            return params[0]['value']
        if len(params) == 1:
            return '-'
        return get_param_value(list(params[1:]), value)
    except Exception:
        return '-'


def get_basic_value(base, value):
    try:
        if base and value in base:
            return base[value]
        return '-'
    except Exception:
        return '-'


def get_value(base, prop, value):
    if prop in base:
        return get_basic_value(base[prop], value)
    return '-'


def convert_to_datetime(param_value):
    if param_value == "" or param_value == "-" or param_value is None:
        return "-"

    return datetime.datetime.strptime(
        param_value.replace("T", " ").replace("+00:00", ""),
        "%Y-%m-%d %H:%M:%S",
    )


def today() -> datetime:
    return datetime.datetime.today()


def today_str() -> str:
    return datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')


def process_asset_parameters(asset_params: list, asset_parameters: list) -> dict:
    """
    This function takes asset_params and asset_parameters(headers) to reach values in asset_params for
    each key at asset_parameters

    :type asset_params: list
    :type asset_parameters: list
    :param asset_params: requested asset['params'] from connect
    :param asset_parameters: headers with keys to build the dict and reach the values
    :return: dict with values from asset_params and keys from asset_parameters
    """
    params_dict = dict.fromkeys(asset_parameters)
    for param in asset_params:
        param_id = param['id']
        if param_id == 'discount_group':
            discount_group = get_discount_level(param['value'])
            params_dict[param_id] = discount_group
        elif param_id in asset_parameters:
            params_dict[param_id] = param['value']
    return params_dict


def get_discount_level(discount_group: str) -> str:
    """
    Transform the discount_group to a proper level of discount

    :type discount_group: str
    :param discount_group:
    :return: str with level of discount
    """
    if len(discount_group) > 2 and discount_group[2] == 'A':
        discount = 'Level ' + discount_group[1]
    elif len(discount_group) > 2 and discount_group[2] == '0':
        discount = 'TLP Level ' + discount_group[1]
    else:
        discount = 'Empty'
    return discount
