import uuid


# Django Utils

def check_token(tokens):
    uuid_tokens = []
    if not tokens:
        return []
    for token in tokens:
        try:
            uuid_token = uuid.UUID(token)
            uuid_tokens.append(uuid_token)  
        except ValueError:
            continue
        
    return uuid_tokens

# Kendo Utils Integration

def map_kendo_operator_to_django(kendo_operator):
    operator_mapping = {
        'eq': 'exact',
        'neq': 'exclude_exact',
        'isnull': 'isnull',
        'isnotnull': 'exclude_isnull',
        'isempty': 'exact',
        'isnotempty': 'exclude_exact',
        'startswith': 'istartswith',
        'doesnotstartwith': 'exclude_istartswith',
        'contains': 'icontains',
        'doesnotcontain': 'exclude_icontains',
        'endswith': 'iendswith',
        'doesnotendwith': 'exclude_iendswith'
    }
    return operator_mapping.get(kendo_operator)

def get_filters_from_request(request):
    field = request.GET.get('filter[filters][0][field]')
    operator = request.GET.get('filter[filters][0][operator]')
    value = request.GET.get('filter[filters][0][value]')
    operator = map_kendo_operator_to_django(operator)
    
    return {f'{field}__{operator}': value}
        