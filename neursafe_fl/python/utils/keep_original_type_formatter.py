#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-function-docstring, protected-access, invalid-name
"""A formatter that keeps the data type unchanged."""
from string import Formatter


class KeepOriginalTypeFormatter(Formatter):
    """This formatter will keep the original data type during formatting.

    The original formatter will convert all types to str.
    """

    def __init__(self):
        super().__init__()
        self.__field_name = None

    def vformat(self, format_string, args, kwargs):
        value = None
        if self.__is_keep_original_type_needed(format_string):
            value = self.get_field(self.__field_name, args, kwargs)[0]
        else:
            # Equal to: format_string.format_map(kwargs)
            value = super().vformat(format_string, args, kwargs)
        return value

    def __is_keep_original_type_needed(self, format_string):
        return self.__is_replacement_whole(format_string)

    def __is_replacement_whole(self, format_string):
        if format_string == '':
            return False

        sub_formats = self.parse(format_string)

        literal_text, self.__field_name, _, _ = next(sub_formats)
        return not literal_text and not list(sub_formats) \
            and self.__field_name
