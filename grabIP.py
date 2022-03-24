from flask import request
def IPadd():
  try:
    local_IP = request.headers['HTTP_X_FORWARDED_FOR']
    #local_IP = request.environ['REMOTE_ADDR']
    print(local_IP)
    return local_IP
  except:
    print("error in IPadd")
    return "74.105.72.198"