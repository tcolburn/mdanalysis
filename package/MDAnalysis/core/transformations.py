# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8


# Placeholder because transformations moved
# Remove this in version 1.0
import warnings

with warnings.catch_warnings():
    warnings.simplefilter('always', DeprecationWarning)
    warnings.warn(("transformations has moved to MDAnalysis.lib.transformations "
                   "and will be removed from here in release 1.0"),
                  DeprecationWarning)

from ..lib.transformations import *
