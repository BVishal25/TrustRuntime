RISK_WEIGHTS={'low':1,'medium':3,'high':7,'critical':10}

def score_action(tool_name, arguments):
    text=(tool_name+' '+str(arguments)).lower()
    score=0
    if any(x in text for x in ('delete','drop','truncate')): score+=10
    if any(x in text for x in ('password','secret','credential','token')): score+=8
    if any(x in text for x in ('send','email','upload','post')): score+=5
    if score>=10: return 'critical'
    if score>=7: return 'high'
    if score>=3: return 'medium'
    return 'low'
