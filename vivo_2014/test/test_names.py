import unittest

from vivo_2014.names import FirstnameLastnameSplitter, LastnameFirstnameSplitter, NameCollection

class NameTest(unittest.TestCase):

    def test_split_firstname_lastname(self):
        expected = ["John", "Snow"]
        result = FirstnameLastnameSplitter().get_name("John Snow").to_list()
        self.assertEquals(result, expected)

    def test_split_firstname_lastname_with_separator(self):
        expected = ["John", "Snow"]
        result = FirstnameLastnameSplitter(",").get_name("John,Snow").to_list()
        self.assertEquals(result, expected)

    def test_split_lastname_firstname(self):
        expected = ["John", "Snow"]
        result = LastnameFirstnameSplitter(",").get_name("Snow, John").to_list()
        self.assertEquals(result, expected)

    def test_split_lastname_firstname_with_too_much_withespace(self):
        expected = ["John", "Snow"]
        result = LastnameFirstnameSplitter(",").get_name("\t Snow,  \t  John ").to_list()
        self.assertEquals(result, expected)

    def test_name_collection(self):
        expected = [["John", "Snow"], ["Samwell", "Tarly"]]
        splitter = LastnameFirstnameSplitter(",")
        collection = NameCollection(splitter)
        result = collection.get_names_list("Snow, John; Tarly, Samwell", ";\s*")
        self.assertEquals(result, expected)

    def test_name_collection_with_separator_duplication(self):
        expected = [["John", "Snow"], ["Samwell", "Tarly"]]
        splitter = LastnameFirstnameSplitter(",")
        collection = NameCollection(splitter)
        result = collection.get_names_list("Snow, John;; Tarly, Samwell", ";\s*")
        self.assertEquals(result, expected)

if __name__ == "__main__": 
    unittest.main()