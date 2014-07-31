# This library tries to implement some intelligent firstname/lastname splitting for some western names.
#
# See http://www.w3.org/International/questions/qa-personal-names to get the whole madness of human 
# name systems and to understand the limited scope of this library!

import re

class Name:
    def __init__(self, firstname, lastname):
        self.firstname = firstname
        self.lastname = lastname

    def __eq__(self, other):
        """ Check if two name instances have the same data. If yes, they are considered equal"""
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def to_list(self):
        return [self.firstname, self.lastname]

    def is_equivalent(self, other):
        if self == other:
            return True
        elif self.lastname != other.lastname:
            return False
        else:
            my_firstname = re.sub("\\W", "", self.firstname, flags=re.UNICODE)
            other_firstname = re.sub("\\W", "", other.firstname, flags=re.UNICODE)
            if len(my_firstname) > len(other_firstname):
                return re.match(other_firstname, my_firstname)
            else:
                return re.match(my_firstname, other_firstname)

    @classmethod
    def from_list(cls, name_list):
        return cls(name_list[0], name_list[1])

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

    def strip_whitespace_from_name_parts(self, name_parts):
        return [p.strip() for p in name_parts]


class FirstnameLastnameSplitter(AbstractSeparatorNameSplitter):
    def get_name(self, name):
        name_parts = self.split(name)
        return Name.from_list(self.strip_whitespace_from_name_parts(name_parts))

class LastnameFirstnameSplitter(AbstractSeparatorNameSplitter):
    def get_name(self, name):
        name_parts = self.split(name)
        name_parts.reverse()
        return Name.from_list(self.strip_whitespace_from_name_parts(name_parts))
        


class NameCollection:
    def __init__(self, splitter):
        self.names = []
        self.splitter = splitter

    def get_names(self, names_string, separator=","):
        name_list = []
        for name in re.split(separator, names_string):
            name = name.strip()
            if name:
                name_list.append(self.splitter.get_name(name))
        return name_list

    def get_names_list(self, names_string, separator=","):
        return [name.to_list() for name in self.get_names(names_string, separator)]

    def has_equivalent(self, name):
        for n in self.names:
            if n.is_equivalent(name):
                return True
        return False

