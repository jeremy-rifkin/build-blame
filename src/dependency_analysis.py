import os
import re
import math

from .common import logger

#
# Originally from https://github.com/jeremy-rifkin/cpp-dependency-analyzer
#

Trigraph_translation_table = {
    "=": "#",
    "/": "\\",
    "'": "^",
    "(": "[",
    ")": "]",
    "!": "|",
    "<": "{",
    ">": "}",
    "-": "~"
}
def phase_one(string):
    # trigraphs
    i = 0
    translated_string = ""
    while i < len(string):
        if string[i] == "?" and i < len(string) - 2 and string[i + 1] == "?" and string[i + 2] in Trigraph_translation_table:
            translated_string += Trigraph_translation_table[string[i + 2]]
            i += 3
        else:
            translated_string += string[i]
            i += 1
    return translated_string

def phase_two(string):
    # backslash followed immediately by newline
    i = 0
    translated_string = ""
    # this is a really dirty way of taking care of line number errors for backslash + \n sequences
    line_debt = 0
    while i < len(string):
        if string[i] == "\\" and i < len(string) - 1 and string[i + 1] == "\n":
            i += 2
            line_debt += 1
        elif string[i] == "\n":
            translated_string += "\n" * (1 + line_debt)
            line_debt = 0
            i += 1
        else:
            translated_string += string[i]
            i += 1
    return translated_string

# lexer rules
lexer_rules = [
    ("COMMENT", r"//.*(?=\n|$)"),
    ("MCOMMENT", r"/\*(?:(?!\*/)[\s\S])*\*/"), #r"/\*(?s:.)*\*/"),
    ("RAW_STRING", r"(R\"([^ ()\t\r\v\n]*)\((?P<RAW_STRING_CONTENT>(?:(?!\)\5\").)*)\)\5\")"),
    ("IDENTIFIER", r"[a-zA-Z_$][a-zA-Z0-9_$]*"),
    ("NUMBER", r"[0-9]([eEpP][\-+]?[0-9a-zA-Z.']|[0-9a-zA-Z.'])*"), # basically a ppnumber regex # r"(?:0x|0b)?[0-9a-fA-F]+(?:.[0-9a-fA-F]+)?(?:[eEpP][0-9a-fA-F]+)?(?:u|U|l|L|ul|UL|ll|LL|ull|ULL|f|F)?",
    ("STRING", r"\"(?P<STRING_CONTENT>(?:\\x[0-7]+|\\.|\\0[0-7]{2}|[^\"\\])*)\""),
    ("CHAR", r"'(\\x[0-9a-fA-F]+|\\.|\\0[0-7]{2}|[^\'\\])'"),
    ("PREPROCESSING_DIRECTIVE", r"(?:#|%:)[a-z]+"),
    ("PUNCTUATION", r"[,.<>?/=;:~!#%^&*\-\+|\(\)\{\}\[\]]"),
    ("NEWLINE", r"\n"),
    ("WHITESPACE", r"[ \r\t\f\u200B-\u200D\uFEFF]+") #r"\s+"
]
lexer_ignores = {"COMMENT", "MCOMMENT", "WHITESPACE"}
lexer_regex = ""
class Token:
    def __init__(self, token_type, value, line, pos):
        self.token_type = token_type
        self.value = value
        self.line = line
        self.pos = pos
        # only digraph that needs to be handled
        if token_type == "PREPROCESSING_DIRECTIVE":
            self.value = re.sub(r"^%:", "#", value)
        elif token_type == "NEWLINE":
            self.value = ""
    def __repr__(self):
        if self.value == "":
            return "{} {}".format(self.line, self.token_type)
        else:
            return "{} {} {}".format(self.line, self.token_type, self.value)
def init_lexer():
    global lexer_regex
    if lexer_regex == "":
        for name, pattern in lexer_rules:
            lexer_regex += ("" if lexer_regex == "" else "|") + "(?P<{}>{})".format(name, pattern)
        logger.debug(f"lexer regex: {lexer_regex}")
        lexer_regex = re.compile(lexer_regex)

def phase_three(string):
    # tokenization
    tokens = []
    i = 0
    line = 1
    while True:
        if i >= len(string):
            break
        m = lexer_regex.match(string, i)
        if m:
            groupname = m.lastgroup
            if groupname not in lexer_ignores:
                if groupname == "STRING":
                    tokens.append(Token(groupname, m.group("STRING_CONTENT"), line, i))
                elif groupname == "RAW_STRING":
                    tokens.append(Token(groupname, m.group("RAW_STRING_CONTENT"), line, i))
                else:
                    tokens.append(Token(groupname, m.group(groupname), line, i))
            if groupname == "NEWLINE":
                line += 1
            if groupname == "MCOMMENT":
                line += m.group(groupname).count("\n")
            i = m.end()
        else:
            logger.debug("--------------------------- lexer error ---------------------------")
            logger.debug(string)
            logger.debug(f"index: {i}")
            logger.debug(f"tokens: {tokens}")
            logger.debug(f"line: {line}")
            logger.debug("surrounding code snippet:\n\n{}\n\n".format(string[i-5:i+20]))
            raise Exception("lexer error")
    # TODO ensure there's always a newline token at the end?
    return tokens

def peek_tokens(tokens, seq):
    if len(tokens) < len(seq):
        return False
    for i, token in enumerate(seq):
        if type(seq[i]) is tuple:
            if not (tokens[i].token_type == seq[i][0] and tokens[i].value == seq[i][1]):
                return False
        elif tokens[i].token_type != seq[i]:
            return False
    return True

def expect(tokens, seq, line, after, expected=None):
    good = True
    reason = ""
    if len(tokens) < len(seq):
        good = False
        reason = "EOF"
    else:
        for i, token in enumerate(seq):
            if type(seq[i]) is tuple:
                if not (tokens[i].token_type == seq[i][0] and tokens[i].value == seq[i][1]):
                    good = False
                    reason = "{}".format(tokens[i].token_type)
                    break
            elif tokens[i].token_type != seq[i]:
                good = False
                reason = "{}".format(tokens[i].token_type)
                break
    if not good:
        if expected is not None:
            raise Exception("parse error: expected {} after {} on line {}, found [{}, ...], failed due to {}".format(expected, after, line, tokens[0], reason))
        else:
            raise Exception("parse error: unexpected tokens following {} on line {}, failed due to {}".format(after, line, reason))

def parse_includes(path: str) -> list:
    # get file contents
    with open(path, "r") as f:
        content = f.read()
    # trigraphs
    content = phase_one(content)
    # backslash newline
    content = phase_two(content)
    # tokenize
    tokens = phase_three(content)

    # process the file
    # Preprocessor directives are only valid if they are at the beginning of a line. Code makes
    # sure the next token is always at the start of the line going into each loop iteration.
    includes = [] # files queued up to process so that logic doesn't get put in the middle of the parse logic
    while len(tokens) > 0:
        token = tokens.pop(0)
        if token.token_type == "PREPROCESSING_DIRECTIVE" and token.value == "#include":
            line = token.line
            if len(tokens) == 0:
                raise Exception("parse error: expected token following #include directive, found nothing")
            elif peek_tokens(tokens, ("STRING", )):
                path_token = tokens.pop(0)
                expect(tokens, ("NEWLINE", ), line, "#include declaration")
                tokens.pop(0) # pop eol
                logger.debug("{} #include \"{}\"".format(line, path_token.value))
                #process_queue.append(path_token.value)
                includes.append(path_token.value)
                # self.queue_all(process_queue, os.path.join(os.path.dirname(file_path), path_token.value))
            elif peek_tokens(tokens, (("PUNCTUATION", "<"), )):
                # because tokens can get weird between the angle brackets, the path is extracted from the raw source
                open_bracket = tokens.pop(0)
                i = open_bracket.pos + 1
                while True:
                    if i >= len(content):
                        # error unexpected eof
                        raise Exception("parse error: unexpected end of file in #include directive on line {}.".format(line))
                    if content[i] == ">":
                        # this is our exit condition
                        break
                    elif content[i] == "\n":
                        # unexpected newline
                        # don't know if this is technically allowed or not
                        raise Exception("parse error: unexpected newline in #include directive on line {}.".format(line))
                    i += 1
                # extract path substring
                path = content[open_bracket.pos + 1 : i]
                # consume tokens up to the closing ">"
                while True:
                    if len(tokens) == 0:
                        # shouldn't happen
                        raise Exception("internal parse error: unexpected eof")
                    token = tokens.pop(0)
                    if token.token_type == "PUNCTUATION" and token.value == ">":
                        # exit condition
                        break
                    elif token.token_type == "NEWLINE":
                        # shouldn't happen
                        raise Exception("internal parse error: unexpected newline")
                expect(tokens, ("NEWLINE", ), line, "#include declaration")
                tokens.pop(0) # pop eol
                ## # library includes won't be traversed
                logger.debug("{} #include <{}>".format(line, path))
                includes.append(path)
            elif peek_tokens(tokens, ("IDENTIFIER", )):
                identifier = tokens.pop(0)
                expect(tokens, ("NEWLINE", ), line, "#include declaration")
                logger.debug("Warning: Ignoring #include {}".format(identifier.value))
            else:
                raise Exception("parse error: unexpected token sequence after #include directive on line {}. This may be a valid preprocessing directive and reflect a shortcoming of this parser.".format(line))
        else:
            # need to consume the whole line of tokens
            while token.token_type != "NEWLINE" and len(tokens) > 0:
                token = tokens.pop(0)
    return includes

class DependencyAnalysis:
    def __init__(self, excludes: list, sentinels: list):
        init_lexer()
        self.excludes = excludes
        self.sentinels = sentinels
        self.not_found = set()
        self.visited = set() # set of absolute paths
        # absolute path -> { i: number, dependencies: list[absolute path]}
        self.nodes = {}
        # self.process_file(file_path)

    def resolve_include(self, base: str, file_path: str, search_paths: list):
        # search paths: first search relative, then via the paths
        relative = os.path.join(
            os.path.dirname(base),
            file_path
        )
        if os.path.exists(relative):
            logger.debug(f"        Found: {relative}")
            return os.path.abspath(relative)
        else:
            for search_path in search_paths:
                path = os.path.join(
                    search_path,
                    file_path
                )
                if os.path.exists(path):
                    logger.debug(f"        Found: {path}")
                    return os.path.abspath(path)

    def process_include(self, base: str, file_path: str, search_paths: list):
        resolved = self.resolve_include(base, file_path, search_paths)
        if resolved:
            logger.debug("Recursing into {}".format(file_path))
            self.process_file(resolved, search_paths)
            return resolved
        else:
            self.not_found.add(file_path)
            return None

    def process_file(self, path: str, search_paths: list):
        if path in self.visited:
            return
        for exclude in self.excludes:
            if path.startswith(exclude):
                return
        self.visited.add(path)
        includes = parse_includes(path)
        # print(path)
        logger.debug(f"    Adding includes: {includes}")
        dependencies = set()
        for include in includes:
            resolved = self.process_include(path, include, search_paths)
            if resolved is not None:
                dependencies.add(resolved)
            elif include in self.sentinels:
                if include not in self.nodes:
                    self.nodes[include] = {
                        "i": len(self.nodes),
                        "dependencies": set()
                    }
                dependencies.add(include)

        self.nodes[path] = {
            "i": len(self.nodes),
            "dependencies": dependencies
        }

    def build_matrix(self):
        N = len(self.nodes)
        self.matrix = [[0 for _ in range(N)] for _ in range(N)]
        for key in self.nodes:
            node = self.nodes[key]
            row = node["i"]
            for d in node["dependencies"]:
                if d in self.nodes:
                    self.matrix[row][self.nodes[d]["i"]] = 1
        # deep copy
        self.matrix_closure = [[col for col in row] for row in self.matrix]
        G = self.matrix_closure
        # floyd-warshall
        for k in range(N):
            for i in range(N):
                for j in range(N):
                    G[i][j] = G[i][j] or (G[i][k] and G[k][j])

    def generate_graphviz(self, target_times: dict, include_transitive=False):
        labels = [k for k in self.nodes.keys()]
        greens = [
            "#EAEFE9",
            "#D9E9D5",
            "#BDDDB6",
            "#99CE93",
            "#6EBA70",
            "#3EA258",
            "#218441",
            "#00672A",
            "#00411A",
        ]
        graphviz = ""
        graphviz += "digraph G {\n"
        counts = count_incident_edges(self.matrix_closure, labels, True)
        max_count = max(counts.values())
        max_time = max(target_times.values())
        def get_color(label: str):
            if label in target_times:
                return f"\"{greens[min(int(math.floor((target_times[label] / max_time) * 9)), 8)]}\""
            elif label in counts:
                return min(int(math.floor((counts[label] / max_count) * 9)) + 1, 9)
            else:
                return "white"
        graphviz += "\tsubgraph cluster_{} {{".format("direct") + "\n"
        graphviz += "\t\tnode [colorscheme=reds9] # Apply colorscheme to all nodes\n"
        graphviz += "\t\tlabel=\"{}\";".format("direct dependencies") + "\n"
        for i in range(len(labels)):
            graphviz += "\t\tn{} [label=\"{}\", fillcolor={}, style=\"filled,solid\"];".format(i, os.path.basename(labels[i]), get_color(labels[i])) + "\n"
        graphviz += "\t\t"
        for i, row in enumerate(self.matrix):
            for j, v in enumerate(row):
                if v:
                    graphviz += "n{}->n{};".format(i, j)
        graphviz += "\n"
        graphviz += "\t}\n"

        if include_transitive:
            offset = len(labels)
            graphviz += "\tsubgraph cluster_{} {{".format("indirect") + "\n"
            graphviz += "\t\tnode [colorscheme=reds9] # Apply colorscheme to all nodes" + "\n"
            graphviz += "\t\tlabel=\"{}\";".format("dependency transitive closure") + "\n"
            for i in range(len(labels)):
                graphviz += "\t\tn{} [label=\"{}\", fillcolor={}, style=\"filled,solid\"];".format(i + offset, os.path.basename(labels[i]), get_color(labels[i])) + "\n"
            graphviz += "\t\t"
            for i, row in enumerate(self.matrix_closure):
                for j, v in enumerate(row):
                    if v:
                        graphviz += "n{}->n{}[color={}];".format(i + offset, j + offset, "black" if self.matrix[i][j] else "orange")
            graphviz += "\n"
            graphviz += "\t}\n"

        graphviz += "}\n"

        return graphviz

def count_incident_edges(matrix, labels, tu_only=False):
    counts = {} # label -> count
    for col in range(len(matrix)):
        for row in range(len(matrix)):
            # if the row is not a .c/.cpp file, it's a header so ignore it
            if tu_only and not (labels[row].endswith(".cpp") or labels[row].endswith(".c")):
                continue
            if matrix[row][col]:
                if labels[col] in counts:
                    counts[labels[col]] += 1
                else:
                    counts[labels[col]] = 1
    return counts

def parse_search_paths(command: str) -> list:
    paths = [x.group(1) for x in re.finditer(r"-I([^ ]+)", command)]
    return paths
