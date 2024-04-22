import requests


class ParameterParserException(Exception):
    """Raised when a parameter value cannot be parsed."""

    pass


class TooManyResultsException(Exception):
    """Raised when the query returns too many results."""

    pass


class ProductDownloadException(Exception):
    """Raised when the product cannot be downloaded."""

    pass


class SearchException(Exception):
    """Raised when the search operation cannot be executed.

    Follows the OpenSearch GeoJSON Response Encoding specification:
    https://docs.opengeospatial.org/is/17-047r1/17-047r1.html#39

    :ivar response: error response
    :vartype response: requests.Response
    :ivar body: JSON body of the response
    :vartype body: dict
    :ivar search_exceptions: list of reported search exceptions
    :vartype search_exceptions: list
    """

    def __init__(self, response: requests.Response, *args: object) -> None:
        self.response = response
        messages = []
        try:
            self.body = response.json()
            self.search_exceptions = self.body["exceptions"]

            exception_messages = [
                f"{e['locator']} - {e['exceptionText']}"
                if "locator" in e
                else e["exceptionText"]
                for e in self.search_exceptions
            ]
            messages.extend(exception_messages)
        except ValueError:
            messages.append(response.content)

        super().__init__(*messages, *args)
