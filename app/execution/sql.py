import re

FORBIDDEN=re.compile(r'\b(insert|update|delete|drop|alter|truncate|create|attach|detach|pragma)\b',re.I)

def validate_read_only_sql(sql):
    normalized=sql.strip().rstrip(';')
    if not re.match(r'^(select|with)\b',normalized,re.I):
        return False,'Only SELECT/WITH statements are allowed.'
    if FORBIDDEN.search(normalized): return False,'Mutating SQL keyword detected.'
    return True,'ok'
