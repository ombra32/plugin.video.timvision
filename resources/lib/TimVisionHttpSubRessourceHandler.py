import xbmc

class TimVisionHttpSubRessourceHandler:
    """ Represents the callable internal server routes & translates/executes them to requests for Netflix"""

    def __init__ (self, kodi_helper, timvision_session):
        self.kodi_helper = kodi_helper
        self.timvision_session = timvision_session
        self.prefetch_login()

    def prefetch_login(self):
        credentials = self.kodi_helper.get_credentials()
        user = credentials.get('username')
        passw = credentials.get('password')
        if user!='' and passw!='':
            self.timvision_session.login(user, passw)
    
    def login (self, params):
        email = params.get('username', [''])[0]
        password = params.get('password', [''])[0]
        if email != '' and password != '':
            return self.timvision_session.login(email, password)
        return None

    def recommended_video(self, params):
        pageType = params.get('category',[''])[0]
        return self.timvision_session.recommended_video(pageType)
    
    def load_serie_seasons(self, params):
        serieId = params.get('serieId',[''])[0]
        return self.timvision_session.load_serie_seasons(serieId)

    def load_serie_episodes(self, params):
        seasonId = params.get('seasonId',[''])[0]
        return self.timvision_session.load_serie_episodes(seasonId)
