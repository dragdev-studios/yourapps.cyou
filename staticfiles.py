# This exists purely for fine-grained control over cache.

from starlette.staticfiles import StaticFiles as _SF, NotModifiedResponse

import os
import typing

from starlette.responses import (
    FileResponse,
)
from starlette.datastructures import Headers

PathLike = typing.Union[str, "os.PathLike[str]"]


class StaticFiles(_SF):
    def file_response(
        self,
        full_path: PathLike,
        stat_result: os.stat_result,
        scope,
        status_code: int = 200,
    ):
        method = scope["method"]
        heads = {"cache-control": "max-age=31536000"}
        request_headers = Headers(heads)
        # print("Serving file", full_path)

        response = FileResponse(full_path, status_code=status_code, stat_result=stat_result, method=method)
        response.headers["cache-control"] = "max-age=31536000"
        if self.is_not_modified(response.headers, request_headers):
            return NotModifiedResponse(response.headers)
        return response
