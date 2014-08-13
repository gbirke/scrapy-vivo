import regex

class PatternNotInDictionaryError(KeyError):
    pass

class PatternCompiler(object):

    def __init__(self, pattern_dict={}):
        self.pattern_dict = pattern_dict

    def compile_pattern(self, pattern, flags=0):
        """
            Code from https://github.com/kaeru-repo/korg/blob/master/korg/pattern.py
        """
        pattern_graph = PatternGraph(self.pattern_dict)
        if pattern_graph.has_cycles():
            raise Exception("Cycle found in pattern dictionary for pattern '%s'" % pattern_graph.cycle_key)
        pattern_re = regex.compile("(?P<substr>%\{(?P<fullname>(?P<patname>\w+)(?::(?P<subname>\w+))?)\})")
        while 1:
            matches = [md.groupdict() for md in pattern_re.finditer(pattern)]
            if len(matches) == 0:
                break
            for md in matches:
                if self.pattern_dict.has_key(md['patname']):
                    if md['subname']:
                        # TODO error if more than one occurance
                        if '(?P<' in self.pattern_dict[md['patname']]:
                            # this is not part of the original logstash implementation
                            # but it might be usefull to be able to replace the
                            # group name used in the pattern
                            repl = regex.sub('\(\?P<(\w+)>', '(?P<%s>' % md['subname'],
                                self.pattern_dict[md['patname']], 1)
                        else:
                            repl = '(?P<%s>%s)' % (md['subname'],
                                self.pattern_dict[md['patname']])
                    else:
                        repl = self.pattern_dict[md['patname']]
                    # print "Replacing %s with %s" %(md['substr'], repl)
                    pattern = pattern.replace(md['substr'],repl)
                else:
                    raise PatternNotInDictionaryError("'%s' not found in pattern dictionary" % md['patname'])
        # print 'pattern: %s' % pattern
        return regex.compile(pattern, flags)

class PatternGraph(object):
    """ Create a graph from a pattern dict to check for cyclic patterns """

    def __init__(self, pattern_dict):
        self.build_nodes(pattern_dict)

    def build_nodes(self, pattern_dict):
        """ Build adjancency map """
        pattern_re = regex.compile("(?P<substr>%\{(?P<fullname>(?P<patname>\w+)(?::(?P<subname>\w+))?)\})")
        self.nodes = {}
        for patname in pattern_dict:
            matches = [md.groupdict() for md in pattern_re.finditer(pattern_dict[patname])]
            if len(matches) == 0:
                continue
            if not self.nodes.has_key(patname):
                    self.nodes[patname] = {"in": [], "out": []}
            for md in matches:
                if not pattern_dict.has_key(md['patname']):
                    continue
                if not self.nodes.has_key(md['patname']):
                    self.nodes[md['patname']] = {"in": [], "out": []}
                self.nodes[patname]["out"].append(md['patname'])
                self.nodes[md['patname']]["in"].append(patname)
        return self.nodes

    def has_cycles(self):
        leaf_nodes = []
        # collect leaf nodes (no incoming edge)
        for n in self.nodes:
            if not len(self.nodes[n]["in"]):
                leaf_nodes.append(n)
        # Remove empty leaf nodes
        while len(leaf_nodes):
            n = leaf_nodes.pop(0)
            for m in self.nodes[n]["out"]:
                self.nodes[m]["in"] = [v for v in self.nodes[m]["in"] if v != n]
                if not len(self.nodes[m]["in"]):
                    leaf_nodes.append(m)
            self.nodes[n]["out"] = []
        # If any node connection is left, we have a circular graph
        for n in self.nodes:
            if len(self.nodes[n]["in"]) or len(self.nodes[n]["out"]):
                self.cycle_key = n
                return True
        return False

class DateMatcher(object):
    patterns = {
        "DAY": "\d{1,2}",
        "MONTH_NUMBER": "\d{1,2}",
        "MONTH_NAMES": "(?:Januar|Februar|M.+rz|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)",
        "VARIABLE_DATE_SEPARATOR":"(?:\.\s*|\s+)",
        "YEAR":  "\d{4}",
        "SEMESTER": "(?:SS\s+%{YEAR}|WS\s+%{YEAR}\s*/\s*%{YEAR:year})",
        "YEARONLY": "%{YEAR:year}",
        "BASIC_NUMERIC": "%{DAY}\.\s*%{MONTH_NUMBER}%{VARIABLE_DATE_SEPARATOR}%{YEAR:year}",
        "BASIC_ALPHANUMERIC": "%{DAY}\.?\s*%{MONTH_NAMES}\s+%{YEAR:year}",
        "PERIOD_DAYS": "%{DAY}\.?\s*-\s*%{DAY}%{VARIABLE_DATE_SEPARATOR}(?:%{MONTH_NAMES}\s+|%{MONTH_NUMBER}%{VARIABLE_DATE_SEPARATOR})%{YEAR:year}",
        "PERIOD_MONTHS": "%{DAY}%{VARIABLE_DATE_SEPARATOR}%{MONTH_NUMBER}%{VARIABLE_DATE_SEPARATOR}-\s*%{DAY}%{VARIABLE_DATE_SEPARATOR}%{MONTH_NUMBER}%{VARIABLE_DATE_SEPARATOR}%{YEAR:year}",

        "DATE": "(:?%{PERIOD_MONTHS}|%{PERIOD_DAYS}|%{BASIC_ALPHANUMERIC}|%{BASIC_NUMERIC}|%{SEMESTER}|%{YEARONLY})"
    }


    def __init__(self, prefix="", suffix="", flags=0, pattern="DATE"):
        to_compile = prefix + DateMatcher.patterns[pattern] + suffix
        self.matcher = PatternCompiler(DateMatcher.patterns).compile_pattern(to_compile, flags)

    def match(self, datestring):
        return self.matcher.search(datestring)