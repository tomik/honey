
# ==>> UTILITY FUNCTIONS

pathCompare = (a, b) ->
  if a.length != b.length
    return false

  for i in [0...a.length]
    if a[i][0] != b[i][0] or a[i][1] != b[i][1]
      return false
  return true

# finds element in array satisfying f and returns it
# if not present returns null
findElem = (a, f) ->
  return e for e in a when f(e)
  null

randomPos = ->
 Math.floor(Math.random() * (BOARD_SIZE - 1))

# ==>> BASIC TYPES

class EventDispatcher
  listeners: []

  register: (listener) ->
    @listeners.push(listener)

  dispatch: (name, params...) ->
    for listener in @listeners
      if name of listener
        listener[name](params...)

class Node
  @nextNodeId: 0
  constructor: (@move, @father, @committed=false) ->
    @id = Node.nextNodeId++
    @children = []
    @number = if @father then @father.number + 1 else 0

  getChildIndex: (node) ->
    return i for child, i in @children when child.id == node.id
    -1

  hasBranches: () ->
    return @children.length > 1

  toStr: () ->
    return "{id #{@id} move #{@move.toStr()}}"

# ==>> SGF PARSING AND OUTPUTTING

sgfParseNodes = (nodes, handler) ->
  for node in nodes
    move = new Move(node)
    handler.onMove(move)
    if "variants" of node
      for variant in node["variants"]
        handler.onBranchStart()
        sgfParseNodes(variant, handler)
        handler.onBranchStop()

sgfParse = (sgf, handler) ->
  nodes = $.parseJSON(sgf)
  if nodes.length <= 0
    return
  gameNode = nodes[0]
  handler.onGameProperty(propName, propValue) for propName, propValue of gameNode
  sgfParseNodes(nodes[1...nodes.length], handler)

# sgf parsing object
class SgfParseHandler
  constructor: (@game) ->
    # stack of nodes where branching happens
    # used for jumping back once branch is finished
    @junctionStack = []

  onGameProperty: (propName, propValue) ->
    console.log("sgf on game property #{propName}=#{propValue}")
    if propName == "FF" and propValue != "4"
      throw "invalid game type"
    else if propName == "SZ" and propValue != "13"
      throw "invalid board size"
    # player names
    else if propName == "PB"
      @game.properties.red = propValue
    else if propName == "PW"
      @game.properties.blue = propValue
    # other game properties
    else if propName == "SZ"
      @game.properties.size = propValue
    else if propName == "SO"
      @game.properties.source = propValue
    else if propName == "GC"
      @game.properties.gameComment = propValue
    else if propName == "EV"
      @game.properties.hexEvent = propValue

  onMove: (move) ->
    console.log("sgf move #{move.toStr()}")
    @game.playMove(move)

  onBranchStart: ->
    @junctionStack.push(@game.currNode)

  onBranchStop: ->
    if @junctionStack.length < 1
      throw "parsing error"
    topNode = @junctionStack.pop()
    while @game.currNode != topNode
      @game.unplayMove()

# ==>> Game Logic

class Game
  constructor: () ->
    @currNode = @root = new Node(new Move(), null, true)
    @properties = {}

  # shortcut for playing existing nodes
  playNode: (node) ->
    @playMove(node.move, true)

  # plays a move on the board and updates data structures
  playMove: (move, existingMove=false) ->
    [x, y, color, moveType] = [move.x, move.y, move.color, move.moveType]
    # are we continuing in the existing branch ?
    newNode = findElem @currNode.children, ((e) -> e.move == move)
    # new move
    if not newNode
      newNode = new Node(move, @currNode, existingMove)
      newNode.father.children.push(newNode)
      _dispatcher.dispatch("onCreateNode", this, newNode)
    @currNode = newNode
    _dispatcher.dispatch("onPlayMove", this, newNode)

  # removes last move from the board
  unplayMove: () ->
    if not @currNode.father
      return
    node = @currNode
    @currNode = @currNode.father
    _dispatcher.dispatch("onUnPlayMove", this, node)

  # returns a json object representing current node short path
  # short path is in the form [(branch_index, node_index), (branch_index, node_index), ...]
  # short path can be used to locate node in the existing game tree
  # used for displaying and posting comments
  getNodeShortPath: (node) ->
    path = []
    index = 0
    while node.father != null
      if node.father.children.length > 0
        i = node.father.getChildIndex(node)
        # ignore not committed siblings
        # this makes an assumption that all the non-committed changes will be lost (no ajax)
        committed = ((if c.committed then 1 else 0) for c in node.father.children)
        committedSum = committed.reduce (a, b) -> a + b
        i = Math.min i, committedSum
        if i > 0
          path.push([i, index + 1])
          index = -1
      node = node.father
      index += 1
    path.push([0, index])
    return path.reverse()

  # play moves to get to the point described by the short path
  followNodeShortPath: (path) ->
    node = @currNode
    if not node
      throw "current node is invalid"
    for [branch, jump] in path
      if branch >= node.children.length
        throw "Invalid branch"
      for i in [0...jump]
        node = node.children[branch]
        @playNode(node)
        # branch only once
        branch = 0

  # returns a json object representing current node full path
  # full path is a list of nodes from the beginning to the current one
  # full path can be used to insert new variants to the game tree
  getNodeFullPath: (node) ->
    path = []
    while node.father != null
      path.push(node.toSgfDict())
      node = node.father
    return path.reverse()

# ==>> Logging

class Logger
  onInit: (game) ->
    console.log("Init")

  onCreateNode: (game, node) ->
    console.log("Created node #{node.toStr()}")

  onPlayMove: (game, node) ->
    console.log("Playing node #{node.toStr()}")

  onUnPlayMove: (game, node) ->
    console.log("Unplaying node #{node.toStr()}")

# ==>> COMMENTS

class Commenter
  onPlayMove: (game, node) ->
    @updateComments(game)

  onUnPlayMove: (game, node) ->
    @updateComments(game)

  updateComments: (game) ->
    currNode = game.currNode
    path = game.getNodeShortPath(currNode)
    currComments = (comment for comment in _bridge.comments when pathCompare(comment[1], path))
    $("#comments .comment").hide()
    for comment in currComments
      elem = $("#comment_#{comment[0]}")
      elem.show()

# ==>> GLOBALS

_lastKey = 0
# global so we can access this from the console
@_game = _game = new Game
_logger = new Logger()
_dispatcher = new EventDispatcher()
_dispatcher.register(_logger)
_dispatcher.register(new Commenter())
_dispatcher.register(new Display())
_dispatcher.register(new Controller())
_sgfParseHandler = new SgfParseHandler(_game)
_bridge.getCurrNodeShortPath = -> _game.getNodeShortPath(_game.currNode)
_bridge.getCurrNodeFullPath = -> _game.getNodeFullPath(_game.currNode)

# ==>> DOCUMENT FUNCTIONS

# load position
$ ->
  _dispatcher.dispatch("onInit", _game)
  sgfTest = "(;FF[4]EV[hex.mc.2011.feb.1.10]PB[Tiziano]PW[sleepywind]
                SZ[13]GC[game #1301977]SO[http://www.littlegolem.com];
                W[ll];B[swap];W[gg];B[fi];W[ih];B[gd];W[id];B[hj];W[ji])"
  # inputSgf is filled into bridge in the template
  inputSgf = _bridge.inputSgf
  sgfParse(inputSgf or= sgfTest, _sgfParseHandler)
  # jump to the beginning
  while _game.currNode.father
    _game.unplayMove()
  # follow the init path
  # this is the short path ([[branchId, jump], [branchId, jump], ...])
  _game.followNodeShortPath(_bridge.initPath)
  _dispatcher.dispatch("onLoad", _game)

# handle keydown including holding the key
$(document).keydown((e) ->
  if not keydownHandler(e.which)
    return
  # wait for a while before first timer is started
  $(document).oneTime("400ms", "keydown_timer_bootstrap", ->
    $(document).everyTime("100ms", "keydown_timer", ->
      if _lastKey
        keydownHandler(_lastKey)
    , 0)))

# release key timers
$(document).keyup((e) ->
    _lastKey = 0
    $(document).stopTime("keydown_timer")
    $(document).stopTime("keydown_timer_bootstrap"))

# key handling logic
keydownHandler = (key) ->
  # move shortcuts 1 - 9
  if key in [49...58]
    variant = key - 49
    if _game.currNode.children.length > variant
      node = _game.currNode.children[variant]
      _game.playNode(node)
  # left
  else if key == 37
    if _game.currNode.father
      _game.unplayMove()
      # this event is repeatable
      return true
  # right
  else if key == 39
    if _game.currNode.children.length
      node = _game.currNode.children[0]
      _game.playNode(node)
      # this event is repeatable
      return true
  # up - go to last junction
  else if key == 38
    if _game.currNode.father
      _game.unplayMove()
      while _game.currNode.father and not _game.currNode.hasBranches()
        _game.unplayMove()
      return true
  # down - go to next junction
  else if key == 40
    if _game.currNode.children.length
      _game.playNode(_game.currNode.children[0])
      while _game.currNode.children.length and not _game.currNode.hasBranches()
        _game.playNode(_game.currNode.children[0])
      return true
  else
    console.log("pressed #{key}")
  _lastKey = key
  # most of the events are not repeatable
  false

