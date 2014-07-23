# This library tries to implement some intelligent firstname/lastname splitting for some western names.
#
# See http://www.w3.org/International/questions/qa-personal-names to get the whole madness of human 
# name systems and to understand the limited scope of this library!

import re

class Name:
    def __init__(self, firstname, lastname):
        self.firstname = firstname
        self.lastname = lastname

    def to_list(self):
        return [self.firstname, self.lastname]

# Split names based on separator. 
# It's very naive at the moment and does not account for prefixes like "von", "de", etc.
class AbstractSeparatorNameSplitter:
    def __init__(self, separator=" "):
        self.separator = separator

    def split(self, name):
        parts = re.split(self.separator, name)
        return [" ".join(parts[:-1]), parts[-1]]

    def get_name(self, name):
        raise NotImplementedError("AbstractSeparatorNameSplitter is an abstract class!")

    def get_name_list(self, name):
        return self.get_name(name).to_list()


class FirstnameLastnameSplitter(AbstractSeparatorNameSplitter):
    def get_name(self, name):
        first, last = self.split(name)
        return Name(first, last)

class LastnameFirstnameSplitter(AbstractSeparatorNameSplitter):
    def get_name(self, name):
        last, first = self.split(name)
        return Name(first, last)


class NameCollection:
    def __init__(self, splitter):
        self.names = []
        self.splitter = splitter

    def get_names(self, names_string, separator=","):
        return [self.splitter.get_name(name) for name in re.split(separator, names_string)]

    def get_names_list(self, names_string, separator=","):
        return [name.to_list() for name in self.get_names(names_string, separator)]

