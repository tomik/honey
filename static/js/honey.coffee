
# ==>> CONSTANTS

ALPHABET = ("abcdefghijklmnopqrstuvwxyz").split("");
BOARD_SIZE = 13
FIELD_FIRST = {x: 52, y:52}
FIELD_X_DIFF = 25
FIELD_Y_DIFF = 21
FIELD_RADIUS = 10

STONE_IMG_RED = "/static/img/red_small.gif"
STONE_IMG_BLUE = "/static/img/blue_small.gif"
LAST_IMG  = "/static/img/last.gif"

# ==>> BASIC ENUMS

Color = {
  RED: "red",
  BLUE: "blue"
}

MoveType = {
  NORMAL: "normal",
  ROOT: "root",
  SWAP: "swap",
  RESIGN: "resign"
}

# ==>> UTILITY FUNCTIONS

pathCompare = (a, b) ->
  if a.length != b.length
    return false

  for i in [0...a.length]
    if a[i][0] != b[i][0] or a[i][1] != b[i][1]
      return false
  return true

flipColor = (color) ->
  if color == Color.BLUE then Color.RED else Color.BLUE

colorToSgf = (color) ->
  if color == Color.BLUE then "B" else "W"

coordToSgf = (coord) ->
  ALPHABET[coord.x] + ALPHABET[coord.y]  

# finds element in array satisfying f and returns it
# if not present returns null
findElem = (a, f) ->
  return e for e in a when f(e)
  null

# produces position with center of the field (i.e. for empty field)
coordToPosCenter = (coord) ->
  x = FIELD_FIRST.x + coord.x * FIELD_X_DIFF + 0.5 * coord.y * FIELD_X_DIFF
  y = FIELD_FIRST.y + coord.y * FIELD_Y_DIFF
  {x:x, y:y}

# produces position with top left of the field (i.e. for a stone pic)
coordToPosTopLeft = (coord) ->
  pos = coordToPosCenter(coord)
  pos.x -= FIELD_RADIUS + 4
  pos.y -= FIELD_RADIUS + 3
  pos

# produces position for inputting text
coordToPosForText = (coord) ->
  pos = coordToPosCenter(coord)
  pos.x -= FIELD_RADIUS / 2 + 1
  pos.y -= FIELD_RADIUS + 2
  pos

randomPos = ->
 Math.floor(Math.random() * (BOARD_SIZE - 1))

# ==>> BASIC TYPES

class Dispatcher
  listeners: {}

  register: (name, listener) ->
    if @listeners[name]?
      @listeners[name].push(listener)
    else
      @listeners[name] = [listener]

  dispatch: (name, params...) ->
    if @listeners[name]?
      l(params...) for l in @listeners[name]

class Node
  @nextNodeId: 0
  constructor: (@x, @y, @color, @father, @moveType) ->
    @id = Node.nextNodeId++
    @children = []
    @number = if @father then @father.number + 1 else 0

  getChildIndex: (node) ->
    return i for child, i in @children when child.id == node.id
    -1

  hasBranches: () ->
    return @children.length > 1

  toStr: ->
    "[#{@x} #{@y}] #{@color}"
  # static monotonic identifier for nodes

  toSgfDict: ->
    d = {}
    d[colorToSgf(@color)] = coordToSgf({x: @x, y: @y})
    d

class Game
  constructor: () ->
    @currNode = @root = new Node(0, 0, 0, null, MoveType.ROOT)
    @properties = {}

  getColorToMove: () ->
    flipColor(@currNode.color)

# ==>> SGF PARSING AND OUTPUTTING

sgfParseNodes = (nodes, handler) ->
  for node in nodes
    if "W" of node
      handler.onMove("W", node["W"])
    else if "B" of node
      handler.onMove("B", node["B"])
    else
      console.log(node)
      throw "Invalid node"
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
  constructor: () ->
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
      $("#red_player").text(propValue)
      _game.properties.red = propValue
    else if propName == "PW"
      $("#blue_player").text(propValue)
      _game.properties.blue = propValue
    # other game properties
    else if propName == "SZ"
      _game.properties.size = propValue
    else if propName == "SO"
      _game.properties.source = propValue
    else if propName == "GC"
      _game.properties.gameComment = propValue
    else if propName == "EV"
      _game.properties.hexEvent = propValue

  onMove: (who, where) ->
    console.log("sgf move #{who}#{where}")
    color = if who == "W" then Color.RED else Color.BLUE
    if who != "W" and who != "B"
      throw "invalid move color #{who}"
    # resign move is not displayed
    else if where == "resign"
      return
    else if (where == "swap")
      playMove(_game.currNode.y, _game.currNode.x, color, MoveType.SWAP)
    else if (where.length > 2)
      throw "invalid move definition length #{where}"
    else if (x = ALPHABET.indexOf(where[0])) == -1 or (y = ALPHABET.indexOf(where[1])) == -1
      throw "invalid move definition #{where}"
    else
      playMove(x, y, color, MoveType.NORMAL)

  onBranchStart: ->
    @junctionStack.push(_game.currNode)

  onBranchStop: ->
    if @junctionStack.length < 1
      throw "parsing error"
    topNode = @junctionStack.pop()
    while _game.currNode != topNode
      unplayMove()

# ==>> Logic

# creates empty field on the board
setupEmptyField = (coord) ->
  pos = coordToPosCenter(coord)
  elem = $("<area id='empty_field_#{coord.x}_#{coord.y}' href=''
            coords='#{pos.x},#{pos.y},#{FIELD_RADIUS}' shape='circle'/>")
  elem.appendTo("#empty_fields")
  elem.click((e) ->
      e.preventDefault()
      playMove(coord.x, coord.y, _game.getColorToMove(), MoveType.NORMAL))

# setups all empty fields on board
setupEmptyFields = ->
  for i in [0...BOARD_SIZE * BOARD_SIZE]
    coord =
      x: i % BOARD_SIZE
      y: Math.floor(i / BOARD_SIZE)
    setupEmptyField(coord)

# removes all old marks
removeChildMarks = ->
  $(".child_mark").remove()

# create marks like 1 2 3 directly on board
putChildMarkOnBoard = (node, childIndex) ->
  pos = coordToPosForText({x:node.x, y:node.y})
  elem = $("<div class='child_mark' style='position: absolute; left: #{pos.x}px; top:#{pos.y}px;'
            id='child_mark_#{node.x}_#{node.y}'>#{childIndex + 1}</div>")
  elem.appendTo("#board")

# places move representing given node on board
putNodeOnBoard = (node, allowSwap=true) ->
  if (node.moveType == MoveType.SWAP and allowSwap)
    removeNodeFromBoard(node.father)
    return putNodeOnBoard(node, false)
  # remove empty field on that location
  elem = $("#empty_field_#{node.x}_#{node.y}")
  elem.remove()
  # add new empty field
  pos = coordToPosTopLeft({x:node.x, y:node.y})
  imgLocation = if node.color == Color.RED then STONE_IMG_RED else STONE_IMG_BLUE
  elem = $("<img alt='' class='move' style='position: absolute; left: #{pos.x}px; top:#{pos.y}px;'
            galleryimg='no' id='move_#{node.x}_#{node.y}' src='#{imgLocation}'>")
  elem.appendTo("#board")
  updateBoard(node)

#updates move marks and board marks
updateBoard = (placedNode) ->
  if placedNode.father
    updateLastMoveMark(placedNode.x, placedNode.y)
  else
    removeLastMoveMark()
  removeChildMarks()
  if placedNode.children.length > 1
    putChildMarkOnBoard(child, i) for child, i in placedNode.children

# removes move representing given node from board
# handles swap move as well
removeNodeFromBoard = (node) ->
  elem = $("#move_#{node.x}_#{node.y}")
  elem.remove()
  setupEmptyField({x:node.x, y:node.y})
  # with swap add nodes father
  if (node.moveType == MoveType.SWAP)
    putNodeOnBoard(node.father)
  updateBoard(node.father)

# places mark for last move from the board
updateLastMoveMark = (x, y) ->
  # update last mark
  last = $("#last_stone")
  if(!last.length)
    last = $("<img alt='' style='z-index: 1; position: absolute;
              left: ${x}px ; top : #{y}px ;' galleryimg='no' id='last_stone'
              src='#{LAST_IMG}'>")
    last.appendTo("#board")
  pos = coordToPosTopLeft({x:x, y:y})
  last.css("left", pos.x)
  last.css("top", pos.y)
  last.show()

# removes mark for last move from the board
removeLastMoveMark = ->
  last = $("#last_stone")
  if(last)
    last.hide()

# plays a move on the board and updates data structures
playMove = (x, y, color, moveType) ->
  # are we continuing in the existing branch ?
  newNode = findElem _game.currNode.children,
                     ((e) -> e.x == x and e.y == y and e.color == color)
  # new move
  if not newNode
    newNode = new Node(x, y, color, _game.currNode, moveType)
    newNode.father.children.push(newNode)
    _dispatcher.dispatch("createNode", newNode)
  _dispatcher.dispatch("playMove", newNode)

# shortcut for playing existing nodes
playNode = (node) ->
  playMove(node.x, node.y, node.color, node.moveType)

# removes last move from the board
unplayMove = () ->
  if (_game.currNode.moveType == MoveType.ROOT)
    return
  _dispatcher.dispatch("unplayMove", _game.currNode)

# returns a json object representing current node short path
# short path is in the form [(branch_index, node_index), (branch_index, node_index), ...]
# short path can be used to locate node in the existing game tree
# used for displaying and posting comments
getNodeShortPath = (node) ->
  path = []
  index = 0
  while node.father != null
    if node.father.children.length > 0
      i = node.father.getChildIndex(node)
      if i != 0
        path.push([i, index])
        index = -1
    node = node.father
    index += 1
  path.push([0, index])
  return path.reverse()

# returns a json object representing current node full path
# full path is a list of nodes from the beginning to the current one
# full path can be used to insert new variants to the game tree
getNodeFullPath = (node) ->
  path = []
  while node.father != null
    path.push(node.toSgfDict())
    node = node.father
  return path.reverse()

# ==>> GLOBALS

_lastKey = 0
# global so we can access this from the console
@_game = _game = new Game
_dispatcher = new Dispatcher()
_dispatcher.register("createNode", (node) -> console.log("Created node #{node.toStr()}"))
_dispatcher.register("playMove", (node) -> _game.currNode = node)
_dispatcher.register("playMove", (node) -> console.log("Playing node #{node.toStr()}"))
_dispatcher.register("playMove", (node) -> putNodeOnBoard(node))
_dispatcher.register("playMove", (node) -> updateComments(_game.currNode))
_dispatcher.register("unplayMove", (node) -> _game.currNode = node.father)
_dispatcher.register("unplayMove", (node) -> console.log("Unplaying node #{node.toStr()}"))
_dispatcher.register("unplayMove", (node) -> removeNodeFromBoard(node))
_dispatcher.register("unplayMove", (node) -> updateComments(_game.currNode))
_sgfParseHandler = new SgfParseHandler
_bridge.getCurrNodeShortPath = -> getNodeShortPath(_game.currNode)
_bridge.getCurrNodeFullPath = -> getNodeFullPath(_game.currNode)

# ==>> COMMENTS
  
updateComments = (currNode) ->
  path = getNodeShortPath(currNode)
  currComments = (comment for comment in _bridge.comments when pathCompare(comment[1], path))
  $("#comments > .comment").removeClass("selected")
  $("#comments > .comment").hide()
  for comment in currComments
    elem = $("#comment_#{comment[0]}")
    elem.addClass("selected")
    elem.show()

# ==>> DOCUMENT FUNCTIONS

# load position
$ ->
  setupEmptyFields()
  sgfTest = "(;FF[4]EV[hex.mc.2011.feb.1.10]PB[Tiziano]PW[sleepywind]
                SZ[13]GC[game #1301977]SO[http://www.littlegolem.com];
                W[ll];B[swap];W[gg];B[fi];W[ih];B[gd];W[id];B[hj];W[ji])"
  # inputSgf is filled into bridge in the template
  inputSgf = _bridge.inputSgf 
  sgfParse(inputSgf or= sgfTest, _sgfParseHandler)

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
      playNode(node)
  # left
  else if key == 37
    if _game.currNode.father
      unplayMove()
      # this event is repeatable
      return true
  # right
  else if key == 39
    if _game.currNode.children.length
      node = _game.currNode.children[0]
      playNode(node)
      # this event is repeatable
      return true
  # up - go to last junction
  else if key == 38
    if _game.currNode.father
      unplayMove()
      while _game.currNode.father and not _game.currNode.hasBranches()
        unplayMove()
      return true
  # down - go to next junction
  else if key == 40
    if _game.currNode.children.length
      playNode(_game.currNode.children[0])
      while _game.currNode.children.length and not _game.currNode.hasBranches()
        playNode(_game.currNode.children[0])
      return true
  else
    console.log("pressed #{key}")
  _lastKey = key
  # most of the events are not repeatable
  false

