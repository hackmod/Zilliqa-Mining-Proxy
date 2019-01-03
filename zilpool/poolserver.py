# -*- coding: utf-8 -*-
# Zilliqa Mining Pool
# Copyright  @ 2018-2019 Gully Chen
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from json import dumps
from functools import partial
from aiohttp import web
from jsonrpcserver import async_dispatch
from jsonrpcserver.response import ExceptionResponse


# setup logger
FORMAT = "[%(asctime)s %(levelname)-6s %(filename)s:%(lineno)s] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.INFO)


def create_api_handler(config=None):
    compat_dumps = partial(dumps, separators=(",", ":"))

    async def api_handle(request: web.Request) -> web.Response:
        request = await request.text()
        response = await async_dispatch(request,
                                        debug=config.debug,
                                        basic_logging=False,
                                        trim_log_values=True)

        if isinstance(response, ExceptionResponse):
            logging.error("Server Error", exc_info=response.exc)
        if response.wanted:
            return web.json_response(response.deserialized(),
                                     status=response.http_status,
                                     dumps=compat_dumps)
        else:
            return web.Response()
    return api_handle


def start_api_server(conf_file=None, port=None):
    from .common import utils
    from .apis import load_apis
    from .database import init_db

    # merge user's config with default.conf
    config = utils.merge_config(conf_file)

    level = config.get("logging", "info").upper()
    logging.getLogger().setLevel(level=level)

    # init database and apis
    init_db(config)
    load_apis(config)

    # init app
    if port is None:
        port = config.api_server.get("port", "4202")
    api_path = config.api_server.get("path", "/api")
    host = config.api_server.get("host", "0.0.0.0")

    app = web.Application(debug=config.debug)
    app.router.add_post(api_path, create_api_handler(config))

    # start ioloop
    print(f"API endpoint: http://{host}:{port}{api_path}")
    web.run_app(app, host=host, port=port)
