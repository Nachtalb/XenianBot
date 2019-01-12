class BaseService:
    type = 'base'

    def __init__(self, name: str, url: str, api: str = None, username: str = None, password: str = None):
        self.name = name
        self.url = url.lstrip('/') if url is not None else None
        self.api = api
        self.username = username
        self.password = password

        self.count_qualifiers_as_tag = False
        self.client = None
        self.session = None
        self.tag_limit = None
        self.censored_tags = None

    def init_client(self):
        raise NotImplemented

    def init_session(self):
        raise NotImplemented
