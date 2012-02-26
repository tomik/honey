"""
Smart Game Format parser.

Parsing is done by calling parseSgf(sgf_string).
Resulting object represents a sgf collection.
This object is a list (games) of lists (nodes) where each node is a dict of properties to values.
Moreover if node has variants (aside from main variant) these are stored
in node under key "variants".
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
    """Abstraction of navigation and manipulation of the sgf parsed game."""
    def __init__(self, nodes):
        self.nodes = nodes
        if not len(nodes):
            raise CursorError("Empty game.")
        # we remember the path with "frames"
        # frame consists of (node, index, parental list)
        self.stack = [(nodes[0], 0, nodes)]

    def get_node(self):
        """Returns current node."""
        return self.stack[-1][0]

    def has_variants(self):
        """Check if current node has multiple children (variants)."""
        return "variants" in self.get_node()

    def get_variants_num(self):
        """Return the number of variants."""
        if not self.has_variants():
            return 1
        return len(self.get_node()["variants"])

    def next(self, variant_index=0):
        """
        Go forward in the game tree.

        @param variant_index index of variant to go to
        @return new current node or None if at the end
        """
        node, index, l = self.stack[-1]
        if "variants" in node:
            variants = node["variants"]
            if variant_index >= len(variants):
                raise CursorError("Invalid variant.")
            assert(len(variants[variant_index]) > 0)
            new_l = variants[variant_index]
            new_index = 0
            new_node = new_l[new_index]
            self.stack.append((new_node, new_index, new_l))
        else:
            if variant_index != 0:
                raise CursorError("No variant.")
            # we are at the end
            if len(l) <= index + 1:
                return None
            self.stack.append((l[index + 1], index + 1, l))
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
        curr_node, index, l = frame
        # adding to the end of the variant
        if len(l) == index + 1:
            # check that node doesn't exist yet
            # TODO be node coordinates aware ?
            if "variants" in curr_node:
                for child in self._get_children(frame):
                    if child == node:
                        raise CursorError("Node already exists.")
                curr_node["variants"].append([node])
            else:
                l.append(node)
        # forking the simple variant
        else:
            if l[index +1] == node:
                raise CursorError("Node already exists.")
            variants = []
            variants.append(l[index + 1:])
            variants.append([node])
            curr_node["variants"] = variants
            while len(l) > index + 1:
                l.pop()

    def _get_children(self, frame):
        node, index, l = frame
        if "variants" not in node:
            if len(l) <= index + 1:
                return
            yield l[index + 1]
            return
        else:
            for variant in node["variants"]:
                if len(variant) > 0:
                    yield variant[0]

class Node(dict):
    """ Representation of a single node in a game.  """
    def __init__(self, *a, **k):
        super(Node, self).__init__(*a, **k)

    def is_same_move(self, other):
        # TODO
        if type(self) != type(other) and type(other) != dict:
            return False
        if self.get("W", None) != other.get("W", None) or \
           self.get("B", None) != other.get("B", None):
            return False
        return True

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
        self.curr_node = Node()
        branch.append(self.curr_node)

    def on_property(self, name, value):
        node = self._get_curr_node()
        if self.curr_node.has_key(name):
            raise SgfParseError("Duplicate property.")
        self.curr_node[name] = value

    def on_branch_start(self):
        node = self._get_curr_node()
        branch = []
        node.setdefault("variants", []).append(branch)
        self.branch_stack.append(branch)

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
            handler.on_property(prop_name, prop_value)
        elif state == LexState.NODE or state == LexState.PROPERTY:
            acc += c
        #print(handler)

# tests
import unittest

class TestSgf(unittest.TestCase):
    def test_simple(self):
        """ Tests simple sgf parsing with one game in collection, no branches and no errors. """
        sgf = """
        (;FF[4]GM[1]SZ[19];B[aa];W[bb];B[cc])
        """
        coll = parseSgf(sgf)
        self.assertEqual(coll,
            [[{'SZ': '19', 'GM': '1', 'FF': '4'}, {'B': 'aa'}, {'W': 'bb'}, {'B': 'cc'}]])

    def test_more_games(self):
        """ Tests >1 games in collection are possible. """
        sgf = """
        (;FF[4];B[aa];W[bb];B[cc])
        (;FF[5];W[dd];B[ee];W[ff])
        """
        coll = parseSgf(sgf)
        self.assertEqual(coll,
            [[{'FF': '4'}, {'B': 'aa'}, {'W': 'bb'}, {'B': 'cc'}], [{'FF': '5'}, {'W': 'dd'}, {'B': 'ee'}, {'W': 'ff'}]])

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
            [[{'SZ': '19', 'GM': '1', 'FF': '4'}, {'B': 'aa'},
            {'variants': [[{'B': 'cc'}, {'W': 'dd'}, {'B': 'ee'}], [{'B': 'hh'}, {'W': 'hg'}]], 'W': 'bb'}]])

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
              {'variants':
                  [[{'B': 'cc'}, {'variants': [[{'B': 'ad'}, {'W': 'bd'}], [{'B': 'ee'}, {'W': 'ff'}]], 'W': 'dd'}],
                   [{'B': 'hh'}, {'W': 'gg'}],
                   [{'B': 'ii'}, {'W': 'jj'}]],
               'W': 'bb'}]])

if __name__ == "__main__":
    unittest.main()

