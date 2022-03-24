from grabIP import IPadd
key1 = "AIzaSyDHtuC_1DDa3COv-Y_KlIB2wlPFwv0JfPI"


# def IPadd():
# 	from flask import request
# 	try:
# 		local_IP = request.environ['HTTP_X_FORWARDED_FOR']
# 		return local_IP
# 	except:
# 		print("error in IPadd")
# 		# generic IP from internet society of israel in jerusalem
# 		return "74.105.72.198"

def local_time():
	import requests, json, datetime, time
	#grabs your latitude, longitude and Time zone
	IPdata = IPadd()
	loc_request=requests.get('http://ip-api.com/json/' + IPdata)
	type(loc_request)
	loc_request.status_code==requests.codes.ok
	loc_request_json_data = loc_request.text
	Location_info = json.loads(loc_request_json_data)
	longi = str(Location_info['lon'])
	latit = str(Location_info['lat'])
	key1 = "AIzaSyDHtuC_1DDa3COv-Y_KlIB2wlPFwv0JfPI"
	fromepoch = str(int(time.time()))
	loc_request=requests.get("https://maps.googleapis.com/maps/api/timezone/json?location=" + latit + ","+ longi +"&timestamp=" + fromepoch+"&key=" + key1)
	type(loc_request)
	loc_request.status_code==requests.codes.ok
	loc_request_json_data = loc_request.text
	Location_info = json.loads(loc_request_json_data)
	dtos = Location_info['dstOffset']
	raw = Location_info['rawOffset']

	longtime = float(dtos) + float(raw) + float(fromepoch)

	date_time_obj = datetime.datetime.fromtimestamp(longtime)
	return date_time_obj