import json
import threading
import time
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
from requests import session, cookies

RECOM_TOP_VIEW = "TOP_VIEWED"
RECOM_MOST_RECENT = "MOST_RECENT"
RECOM_FOR_YOU = "RECOM_FOR_YOU"
RECOM_EXPIRING = "EXPIRING"

class TimVisionSession:
    base_url = 'https://www.timvision.it/AVS'
    deviceType = 'WEB'
    service_name = 'CUBOVISION'
    service_channel = 'CUBOWEB'
    app_version = '10.0.47'
    api_endpoint = session()
    license_endpoint = session()

    def __init__(self):
        self.api_endpoint.headers.update({
            'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:54.0) Gecko/20100101 Firefox/54.0',
            'Accept-Encoding' : 'gzip, deflate',
        })
        self.license_endpoint.headers.update({
            'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:54.0) Gecko/20100101 Firefox/54.0',
            'Accept-Encoding' : 'gzip, deflate',
            'Host' : 'license.timvision.it',
            'Origin' : 'https://www.timvision.it'
        })
        #self.plugin_handle = plugin_handle
        self.setup()

    def setup(self):
        return self.load_app_settings() and self.load_app_version()

    def load_app_version(self):
        r = self.api_endpoint.get("https://www.timvision.it/app_ver.js")
        if r.status_code == 200:
            str1 = r.text
            #str1 = str1.rsplit('{')[1].rsplit('}')[0]
            str1 = str1.rsplit('"')[1].rsplit('"')[0]
            self.app_version = str1
            return True
        return False
    def load_app_settings(self):
        url = 'https://www.timvision.it/TIM/'+self.app_version+'/PROD/IT/'+self.service_channel+'/ITALY/PROPERTIES?deviceType='+self.deviceType+'&serviceName='+self.service_name
        r = self.api_endpoint.get(url)
        if r.status_code == 200:
            data = r.json()
            if data['resultCode'] == 'OK':
                self.license_acquisition_url = data['resultObj']['LICENSEACQUISITIONURL']
                self.user_http_header = data['resultObj']['USER_REQ_HEADER_NAME']
                self.widevine_proxy_url = data['resultObj']['WV_PROXY_URL']
                return True
        return False
    def login(self, username, password):
        data = {
            'username':username,
            'password':password,
            'customData':'{"customData":[{"name":"deviceType","value":'+self.deviceType+'},{"name":"deviceVendor","value":""},{"name":"accountDeviceModel","value":""},{"name":"FirmwareVersion","value":""},{"name":"Loader","value":""},{"name":"ResidentApp","value":""},{"name":"DeviceLanguage","value":"it"},{"name":"NetworkType","value":""},{"name":"DisplayDimension","value":""},{"name":"OSversion","value":"Windows 10"},{"name":"AppVersion","value":""},{"name":"DeviceRooted","value":""},{"name":"NetworkOperatoreName","value":""},{"name":"ServiceOperatorName","value":""},{"name":"Custom1","value":"Firefox"},{"name":"Custom2","value":54},{"name":"Custom3","value":"1920x1080"},{"name":"Custom4","value":"PC"},{"name":"Custom5","value":""},{"name":"Custom6","value":""},{"name":"Custom7","value":""},{"name":"Custom8","value":""},{"name":"Custom9","value":""}]}'
        }
        r = self.api_send_request("Login", method = 'POST', postData=data)
        if r[0]:
            self.api_endpoint.headers.__setitem__(self.user_http_header, r[1]["resultObj"])
            self.sessionLoginHash = r[1]["extObject"]["hash"]
            avs_cookie = self.api_endpoint.cookies.get("avs_cookie")
            self.license_endpoint.headers.__setitem__('AVS_COOKIE',avs_cookie)
            self.stop_check_session = threading.Event()
            check_thread = threading.Thread(target=self.check_session, args=(self.stop_check_session))
            check_thread.start()
            return True
        return False
    def logout(self):
        r = self.api_send_request("Logout")
        if r[0]:
            self.api_endpoint.cookies.clear()
            self.sessionLoginHash = None
            self.api_endpoint.headers.pop(self.user_http_header, None)
            self.stop_check_session.set()
            return True
        return False
    def is_logged(self):
        return self.sessionLoginHash != None
    def api_url(self, action, others = {}):
        query = ""
        if others!=None:
            for key,value in others:
                query += "&"+key+"="+value
        return self.base_url+"/besc?channel="+self.service_channel+"&providerName=TELECOMITALIA&serviceName="+self.service_name+"&action="+action+"&deviceType="+self.deviceType+query
    def api_send_request(self, action, method = 'GET', queryData=None, postData=None):
        r = None
        if method == "POST":
            r = self.api_endpoint.post(self.api_url(action, queryData), data=postData)
        if method == "GET":
            r = self.api_endpoint.get(self.api_url(action, queryData))
        if method == "OPTIONS":
            r = self.api_endpoint.options(self.api_url(action, queryData))
        if r.status_code == 200:
            data = r.json()
            if data["resultCode"] == "OK":
                return [True, data]
        return [False]
    def log_myfile(self, msg):
        f = open("C:\\Users\\pinoe\\Desktop\\timvision.log", "a")
        f.writelines(msg)
        f.close()

    def recommended_video(self, category):
        url = "https://www.timvision.it/TIM/"+self.app_version+"/PROD_WEB/IT/"+self.service_channel+"/ITALY/TRAY/RECOM?deviceType="+self.deviceType+"&serviceName="+self.service_name
        query = {
            "dataSet":"RICH",
            "orderBy":"year",
            "sortOrder":"desc",
            "area":"HOMEPAGE",
            "category":"HomePage",
            "recomType":category,
            "maxResults":"30"
        }
        r = self.api_endpoint.get(url, params = query)
        if r.status_code == 200:
            data = r.json()
            if data["resultCode"] == "OK":
                return data["resultObj"]["containers"]
        return None
    def load_serie_seasons(self, serieId):
        url = "https://www.timvision.it/TIM/"+self.app_version+"/PROD_WEB/IT/"+self.service_channel+"/ITALY/DETAILS?contentId="+str(serieId)+"&type=SERIES&renderEngine=DELTA&deviceType="+self.deviceType+"&serviceName="+self.service_name
        r = self.api_endpoint.get(url)
        if r.status_code == 200:
            data = r.json()[0]
            if data["resultCode"] == "OK":
                return data["resultObj"]["containers"]
        return None
    def load_serie_episodes(self, seasonId):
        url = "https://www.timvision.it/TIM/"+self.app_version+"/PROD_WEB/IT/"+self.service_channel+"/ITALY/DETAILS?renderEngine=DELTA&deviceType="+self.deviceType+"&serviceName="+self.service_name+"&contentId="+seasonId+"&type=SEASON"
        r = self.api_endpoint.get(url)
        if r.status_code == 200:
            data = r.json()[0]
            if data["resultCode"] == "OK":
                containers = data["resultObj"]["containers"]
                for cont in containers:
                    if cont["layout"] == "SEASON":
                        return cont["items"]
        return None
    def check_session(self, stop_event):
        while not stop_event.is_set():
            self.api_send_request("CheckSession")
            stop_event.wait(600)
    def play_video(self, contentId):
        return None
    #TODO : delete this from here
    def play_item (self, manifest, video_id, licenseKey, start_offset=-1, infoLabels={}):
        addon = xbmcaddon.Addon()
        inputstream_addon = self.get_inputstream_addon()
        if inputstream_addon == None:
            #self.show_message("Inputstream addon not found", "Addon error")
            return False

        # track play event
        #self.track_event('playVideo')

        # check esn in settings
        #settings_esn = str(addon.getSetting('esn'))
        #if len(settings_esn) == 0:
        #    addon.setSetting('esn', str(esn))

        # inputstream addon properties
        #msl_service_url = 'http://localhost:' + str(addon.getSetting('msl_service_port'))
        play_item = xbmcgui.ListItem(path=manifest) #manifest = mpd url
        play_item.setContentLookup(False)
        play_item.setMimeType('application/dash+xml')
        play_item.setProperty(inputstream_addon + '.stream_headers', 'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:54.0) Gecko/20100101 Firefox/54.0')        
        play_item.setProperty(inputstream_addon + '.license_type', 'com.widevine.alpha')
        play_item.setProperty(inputstream_addon + '.manifest_type', 'mpd')
        play_item.setProperty(inputstream_addon + '.license_key', licenseKey) #license url
        #play_item.setProperty(inputstream_addon + '.server_certificate', 'Cr0CCAMSEOVEukALwQ8307Y2+LVP+0MYh/HPkwUijgIwggEKAoIBAQDm875btoWUbGqQD8eAGuBlGY+Pxo8YF1LQR+Ex0pDONMet8EHslcZRBKNQ/09RZFTP0vrYimyYiBmk9GG+S0wB3CRITgweNE15cD33MQYyS3zpBd4z+sCJam2+jj1ZA4uijE2dxGC+gRBRnw9WoPyw7D8RuhGSJ95OEtzg3Ho+mEsxuE5xg9LM4+Zuro/9msz2bFgJUjQUVHo5j+k4qLWu4ObugFmc9DLIAohL58UR5k0XnvizulOHbMMxdzna9lwTw/4SALadEV/CZXBmswUtBgATDKNqjXwokohncpdsWSauH6vfS6FXwizQoZJ9TdjSGC60rUB2t+aYDm74cIuxAgMBAAE6EHRlc3QubmV0ZmxpeC5jb20SgAOE0y8yWw2Win6M2/bw7+aqVuQPwzS/YG5ySYvwCGQd0Dltr3hpik98WijUODUr6PxMn1ZYXOLo3eED6xYGM7Riza8XskRdCfF8xjj7L7/THPbixyn4mULsttSmWFhexzXnSeKqQHuoKmerqu0nu39iW3pcxDV/K7E6aaSr5ID0SCi7KRcL9BCUCz1g9c43sNj46BhMCWJSm0mx1XFDcoKZWhpj5FAgU4Q4e6f+S8eX39nf6D6SJRb4ap7Znzn7preIvmS93xWjm75I6UBVQGo6pn4qWNCgLYlGGCQCUm5tg566j+/g5jvYZkTJvbiZFwtjMW5njbSRwB3W4CrKoyxw4qsJNSaZRTKAvSjTKdqVDXV/U5HK7SaBA6iJ981/aforXbd2vZlRXO/2S+Maa2mHULzsD+S5l4/YGpSt7PnkCe25F+nAovtl/ogZgjMeEdFyd/9YMYjOS4krYmwp3yJ7m9ZzYCQ6I8RQN4x/yLlHG5RH/+WNLNUs6JAZ0fFdCmw=')
        play_item.setProperty('inputstreamaddon', inputstream_addon)

        # check if we have a bookmark e.g. start offset position
        if int(start_offset) > 0:
            play_item.setProperty('StartOffset', str(start_offset) + '.0')
        # set infoLabels
        if len(infoLabels) > 0:
            play_item.setInfo('video',  infoLabels)
        #return xbmcplugin.setResolvedUrl(self.plugin_handle, True, listitem=play_item)
    def get_inputstream_addon(self):
        type = 'inputstream.adaptive'
        payload = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'Addons.GetAddonDetails',
            'params': {
                'addonid': type,
                'properties': ['enabled']
            }
        }
        response = xbmc.executeJSONRPC(json.dumps(payload))
        data = json.loads(response)
        if not 'error' in data.keys():
            if data['result']['addon']['enabled']:
                return type
        return None
    def get_certificate_url(self, videoId, cpId):
        #url = "https://license.cubovision.it/WidevineManager/WidevineManager.svc/GetLicense/{ContentIdAVS}/{AssetIdWD}/{CpId}/{Type}/{ClientTime}/{Channel}/{DeviceType}"
        return
