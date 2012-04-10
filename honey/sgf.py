"""
Smart Game Format parser.

Parsing is done by calling parseSgf(sgf_string). Resulting object represents a sgf collection.
This object is a list (games) of branches. Each element of the branch is either:
   * a node (dict of properties to values)
   * list of branches representing variants
For navigating and manipulating parsed sgf collection use Cursor.

Example:

parsed == [
    # game 1
    [{"FF": "4", "GM": "0"}, {"W": "aa"}, {"B": "bb"}, [[{"W": "cc"}, {"B": "dd"}], [{"W": "ee"}]]],
    # game 2
    ...
    ]
"""

class LexState:
  COLLECTION = "collection"
  GAME = "game"
  SEQ = "seq"
  NODE = "node"
  PROPERTY = "prop"

class SgfParseError(Exception):
    pass

class CursorError(Exception):
    pass

class Cursor:
    """Abstraction of navigation and manipulation of the parsed sgf game."""
    def __init__(self, nodes):
        self.nodes = nodes
        if not len(nodes):
            raise CursorError("Empty game.")
        # we remember the path with "frames"
        # frame consists of (node, index, parental list)
        self.stack = [(nodes[0], 0, nodes)]

    def get_node(self):
        """Returns current node."""
        node = self.stack[-1][0]
        if type(node) == dict:
            return node
        else:
            raise ValueError("unexpected value")

    def has_variants(self):
        """Check if current node has multiple children (variants)."""
        return bool(self.get_variants())

    def get_variants(self):
        """Get list of variants (list of lists) for given node."""
        node, index, line = self.stack[-1]
        if len(line) <= index + 1:
            return []
        next = line[index + 1]
        if type(next) == list:
            return next
        return []

    def get_variants_num(self):
        """Return the number of variants."""
        if not self.has_variants():
            return 1
        return len(self.get_variants())

    def next(self, variant_index=0):
        """
        Go forward in the game tree.

        @param variant_index index of variant to go to
        @return new current node or None if at the end
        """
        node, index, line = self.stack[-1]
        variants = self.get_variants()
        if variants:
            if variant_index >= len(variants):
                raise CursorError("Invalid variant.")
            assert(len(variants[variant_index]) > 0)
            new_line = variants[variant_index]
            new_index = 0
            new_node = new_line[new_index]
            assert(type(new_node) == dict)
            self.stack.append((new_node, new_index, new_line))
        else:
            if variant_index != 0:
                raise CursorError("No variant.")
            # we are at the end
            if len(line) <= index + 1:
                return None
            # follow the current variant
            self.stack.append((line[index + 1], index + 1, line))
        return self.get_node()

    def get_next(self, variant_index=0):
        """Sneak peek at what the next node is."""
        node = self.next(variant_index)
        if node:
            self.previous()
        return node

    def previous(self):
        """
        Go backward in the game tree.

        @return new current node or None if at the beginning
        """
        if len(self.stack) == 1:
            return None
        self.stack.pop()
        return self.get_node()

    def add_node(self, node):
        """
        Add new child to the current node.
        """
        frame = self.stack[-1]
        curr_node, index, line = frame
        variants = self.get_variants()
        # adding to the end of the variant
        if len(line) == index + 1:
            line.append(node)
        # adding new variant
        elif variants:
            # check that node doesn't exist yet
            for variant in variants:
                if len(variant) and variant[0] == node:
                    raise CursorError("Node already exists.")
            variants.append([node])
        # forking the simple variant
        else:
            if line[index +1] == node:
                raise CursorError("Node already exists.")
            variants = []
            variants.append(line[index + 1:])
            variants.append([node])
            while len(line) > index + 1:
                line.pop()
            line.append(variants)

def nodes_are_same_moves(fst, snd):
    if type(fst) != dict or type(snd) != dict:
        return False
    if fst.get("W", None) != snd.get("W", None) or \
       fst.get("B", None) != snd.get("B", None):
        return False
    return True

def node_to_sgf(node):
    """Returns sgf representation of the node. Properties are sorted alphabetically."""
    properties = ["%s[%s]" % (key, value) for key, value in node.items()]
    return ";" + "".join(sorted(properties))

class SgfHandler:
    """
    Handles events raised during parsing of sgf string.
    On inconsistencies raises SgfParseError.
    After parsing is done final object is retrieved via 'get_result'.
    """
    def __init__(self):
        self.games = []
        self.curr_node = None
        self.branch_stack = []

    def get_result(self):
        if not self.games:
            raise SgfParseError("Empty collection.")
        return self.games

    def on_game_start(self):
        game = []
        self.games.append(game)
        self.branch_stack.append(game)

    def on_game_stop(self):
        if len(self.branch_stack) != 1:
            raise SgfParseError("Invalid end of the game.")
        if not self.curr_node:
            raise SgfParseError("Empty game.")
        self.branch_stack = []
        self.curr_node = None

    def on_node(self):
        branch = self._get_curr_branch()
        self.curr_node = {}
        branch.append(self.curr_node)

    def on_property(self, name, value):
        node = self._get_curr_node()
        if self.curr_node.has_key(name):
            raise SgfParseError("Duplicate property.")
        self.curr_node[name] = value

    def on_branch_start(self):
        branch = self._get_curr_branch()
        # use existing variant
        if type(branch[-1]) == list:
            variants = branch[-1]
        # create new variant
        else:
            variants = []
            branch.append(variants)
        # create new branch
        new_branch = []
        variants.append(new_branch)
        self.branch_stack.append(new_branch)

    def on_branch_stop(self):
        if len(self.branch_stack) <= 1:
            raise SgfParseError("No current branch.")
        self.branch_stack.pop()
        branch = self.branch_stack[-1]
        if len(branch) == 0:
            raise SgfParseError("Empty branch.")
        self.curr_node = branch[-1]

    def _get_curr_branch(self):
        if not self.games:
            raise SgfParseError("No current game.")
        return self.branch_stack[-1]

    def _get_curr_node(self):
        if self.curr_node is None:
            raise SgfParseError("No current node.")
        return self.curr_node

    def __str__(self):
        return "node(%s) branch_stack(%s)" % (self.curr_node, self.branch_stack)

def parseSgf(sgf):
    """ Returns parsed sgf object or throws SgfParseError. """
    handler = SgfHandler()
    _runParser(sgf, handler)
    return handler.get_result()

def _runParser(sgf, handler):
    """ Traverses the sgf string and calls handler on events. """
    state = LexState.COLLECTION
    acc = ""
    depth = 0
    prop_name = None

    for c in sgf:
        #print("state(%s) acc(%s) char(%s)" % (state, acc, c))
        if state == LexState.COLLECTION and c == "(":
            handler.on_game_start()
            state = LexState.SEQ
        elif state == LexState.SEQ and c == ";":
            handler.on_node()
            state = LexState.NODE
        elif state == LexState.NODE and c == ";":
            handler.on_node()
            state = LexState.NODE
        elif state == LexState.NODE and c == "[":
            prop_name = acc
            acc = ""
            state = LexState.PROPERTY
        elif (state == LexState.SEQ or state == LexState.NODE) and c == "(":
            acc = ""
            depth += 1
            state = LexState.SEQ
            handler.on_branch_start()
        elif (state == LexState.NODE or state == LexState.SEQ) and c == ")":
            acc = ""
            if depth == 0:
                handler.on_game_stop()
                state = LexState.COLLECTION
            else:
                handler.on_branch_stop()
                depth -= 1
                state = LexState.SEQ
        elif state == LexState.PROPERTY and c == "]":
            prop_value = acc
            acc = ""
            state = LexState.NODE
            # quick hack to avoid handling properties with multiple values
            if prop_name:
                handler.on_property(prop_name, prop_value)
        elif state == LexState.NODE or state == LexState.PROPERTY:
            acc += c

def makeSgf(coll):
    """Inverse of parseSgf. Takes Sgf collection and produces string with sgf representation."""
    sgf = ""
    for game in coll:
        sgf += _makeSgfFromCursor(Cursor(game))
    return sgf

def _makeSgfFromCursor(cursor):
    begin = cursor.get_node()
    if not begin:
        return ""
    sgf = "("
    finished = False
    while not finished:
        variants_num = cursor.get_variants_num()
        node = cursor.get_node()
        sgf += node_to_sgf(node)
        if variants_num == 1:
            finished = not cursor.next()
        else:
            # recursively solve variants
            for index in xrange(variants_num):
                cursor.next(index)
                sgf += _makeSgfFromCursor(cursor)
                cursor.previous()
            finished = True
    # unroll the cursor
    while cursor.get_node() != begin:
        cursor.previous()
    return sgf + ")"

# tests
import unittest

class TestSgf(unittest.TestCase):
    @staticmethod
    def _trim_sgf_whitespace(sgf_str):
        import re
        return re.sub(r"\s+", "", sgf_str)

    def test_simple(self):
        """ Tests simple sgf parsing with one game in collection, no branches and no errors. """
        sgf = """
        (;FF[4]GM[1]SZ[19];B[aa];W[bb];B[cc])
        """
        coll = parseSgf(sgf)
        self.assertEqual(coll,
            [[{'SZ': '19', 'GM': '1', 'FF': '4'}, {'B': 'aa'}, {'W': 'bb'}, {'B': 'cc'}]])
        self.assertEqual(self._trim_sgf_whitespace(sgf), makeSgf(coll))

    def test_more_games(self):
        """ Tests >1 games in collection are possible. """
        sgf = """
        (;FF[4];B[aa];W[bb];B[cc])
        (;FF[5];W[dd];B[ee];W[ff])
        """
        coll = parseSgf(sgf)
        self.assertEqual(coll,
            [[{'FF': '4'}, {'B': 'aa'}, {'W': 'bb'}, {'B': 'cc'}], [{'FF': '5'}, {'W': 'dd'}, {'B': 'ee'}, {'W': 'ff'}]])
        self.assertEqual(self._trim_sgf_whitespace(sgf), makeSgf(coll))

    def test_no_games(self):
        """ Tests 0 games is invalid. """
        sgf = ""
        try:
            coll = parseSgf(sgf)
        except SgfParseError, e:
            if str(e) == "Empty collection.":
                return
        self.assertFalse(1)

    def test_empty_game(self):
        """ Tests that game without any moves is invalid. """
        sgf = "()"
        try:
            coll = parseSgf(sgf)
        except SgfParseError, e:
            if str(e) == "Empty game.":
                return
        self.assertFalse(1)

    def test_simple_branches(self):
        """ Tests game with one branching node. """
        sgf = """
        (;FF[4]GM[1]SZ[19];B[aa];W[bb](;B[cc];W[dd];B[ee])(;B[hh];W[hg]))
        """
        coll = parseSgf(sgf)
        self.assertEqual(coll,
                [[{'SZ': '19', 'GM': '1', 'FF': '4'}, {'B': 'aa'}, {'W': 'bb'},
                    [[{'B': 'cc'}, {'W': 'dd'}, {'B': 'ee'}], [{'B': 'hh'}, {'W': 'hg'}]]]])
        self.assertEqual(self._trim_sgf_whitespace(sgf), makeSgf(coll))

    def test_multi_branches(self):
        """ Tests having two nodes with variations one of them with three. """
        sgf = """
        (;FF[4]GM[1]SZ[19];B[aa];W[bb](;B[cc];W[dd](;B[ad];W[bd])
        (;B[ee];W[ff]))
        (;B[hh];W[gg])
        (;B[ii];W[jj]))
        """
        coll = parseSgf(sgf)
        self.assertEqual(coll,
            [[{'SZ': '19', 'GM': '1', 'FF': '4'}, {'B': 'aa'},
              {'W': 'bb'},
                  [[{'B': 'cc'}, {'W': 'dd'}, [[{'B': 'ad'}, {'W': 'bd'}], [{'B': 'ee'}, {'W': 'ff'}]]],
                   [{'B': 'hh'}, {'W': 'gg'}],
                   [{'B': 'ii'}, {'W': 'jj'}]],
               ]])
        self.assertEqual(self._trim_sgf_whitespace(sgf), makeSgf(coll))

if __name__ == "__main__":
    unittest.main()

