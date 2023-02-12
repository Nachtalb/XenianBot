from pybooru import Moebooru as PyMoebooru

from xenian.bot.commands.animedatabase_utils.base_service import BaseService


class MoebooruService(BaseService):
    type = "moebooru"

    def __init__(
        self,
        name: str,
        url: str,
        username: str | None = None,
        password: str | None = None,
        hashed_string: str | None = None,
    ) -> None:
        super(MoebooruService, self).__init__(name=name, url=url, username=username, password=password)
        self.tag_limit = 6
        self.hashed_string = hashed_string
        self.count_qualifiers_as_tag = True

        self.init_client()

    def init_client(self):
        if self.username and self.password:
            self.client = PyMoebooru(
                site_name=self.name,
                site_url=self.url,
                hash_string=self.hashed_string,  # type: ignore
                username=self.username,
                password=self.password,
            )
            return

        self.client = PyMoebooru(site_name=self.name, site_url=self.url)
        if not self.url:
            self.url = self.client.site_url.lstrip("/")
