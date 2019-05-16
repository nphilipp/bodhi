# Copyright © 2019 Red Hat, Inc. and others.
#
# This file is part of Bodhi.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""Asynchronous tasks for Bodhi."""

import logging
import sys

import celery

from bodhi.server import bugs, buildsys, initialize_db
from bodhi.server.config import config
from bodhi.server.util import pyfile_to_module


# Workaround https://github.com/celery/celery/issues/5416
if celery.version_info < (4, 3) and sys.version_info >= (3, 7):
    from re import Pattern
    from celery.app.routes import re as routes_re
    routes_re._pattern_type = Pattern


log = logging.getLogger('bodhi')

# The Celery app object.
app = celery.Celery()
app.config_from_object(pyfile_to_module(config["celery_config"], "celeryconfig"))


def _do_init():
    config.load_config()
    initialize_db(config)
    buildsys.setup_buildsystem(config)
    bugs.set_bugtracker()
