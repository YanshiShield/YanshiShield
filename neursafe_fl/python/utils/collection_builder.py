#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-function-docstring, too-few-public-methods
# pylint:disable=invalid-name
"""Collection builder.

   Typical usage example:

   template_collection = {"k1": "{placeholder1}",}
   kwargs = {"placeholder1": "value1"}
   builder = CollectionBuilder(template_collection, kwargs)
   col = builder.format() # {"k1": "value1",}
"""
from string import Formatter

from neursafe_fl.python.utils.keep_original_type_formatter import \
    KeepOriginalTypeFormatter


class CollectionBuilder:
    """Replace all vars in braces with value in the collection.

     Attributes:
         temp_colllection: A collection containing placeholders. For example:
            [{"k1": "{placeholder1}", "k2": "{placeholder2}"}],
            ["{placeholder1}", "{placeholder2}"]

         __kwargs: Replacement values for the placeholders. For example:
            {"placeholder1": "value1"}

         __args: Replacement values for the placeholders(Such as: {1}).
         __keep_original_type_keys: The keys that needs to be replaced
            with the original type of the replacement value.
    """

    def __init__(self, temp_colllection, kwargs, args=(),
                 keep_original_type_keys=None):
        self.__temp_colllection = temp_colllection
        self.__kwargs = kwargs
        self.__args = args
        self.__keep_original_type_keys = keep_original_type_keys

        self.__default_formatter = Formatter()
        self.__keep_type_formatter = KeepOriginalTypeFormatter()

    def format(self):
        return self.__format(self.__temp_colllection, self.__default_formatter)

    def __format(self, template, formatter):
        result = template

        if isinstance(template, str):
            result = formatter.vformat(
                template, self.__args, self.__kwargs)
        elif isinstance(template, list):
            result = [self.__format(
                sub_template, formatter) for sub_template in template]
        elif isinstance(template, dict):
            result = {}
            for k, v in template.items():
                formatter = self.__choose_formatter(k)
                result[k] = self.__format(v, formatter)
        else:
            pass

        return result

    def __choose_formatter(self, key):
        if not self.__keep_original_type_keys:
            formatter = self.__default_formatter
        else:
            if key in self.__keep_original_type_keys:
                formatter = self.__keep_type_formatter
            else:
                formatter = self.__default_formatter
        return formatter
