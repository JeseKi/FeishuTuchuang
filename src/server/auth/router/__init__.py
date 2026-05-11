# -*- coding: utf-8 -*-
"""Auth routes package."""

from .base import router
from . import login as _login  # noqa: F401
from . import password_change as _password_change  # noqa: F401
from . import password_reset as _password_reset  # noqa: F401
from . import profile as _profile  # noqa: F401
from . import register as _register  # noqa: F401
from . import two_factor as _two_factor  # noqa: F401

__all__ = ["router"]
