
# CONSTANTS
# ====================

BOARD_SIZE = 13
FIELD_FIRST = {x: 52, y:52}
FIELD_X_DIFF = 25
FIELD_Y_DIFF = 21
FIELD_RADIUS = 10

STONE_IMG_RED = "/static/img/red_small.gif"
STONE_IMG_BLUE = "/static/img/blue_small.gif"
LAST_IMG  = "/static/img/last.gif"

# BASIC ENUMS
# ====================

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

# UTILITY FUNCTIONS
# ====================

flipColor = (color) ->
  if color == Color.BLUE then Color.RED else Color.BLUE

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

randomPos = ->
 Math.floor(Math.random() * (BOARD_SIZE - 1))

# GLOBALS
# ====================

# game is a singleton
_gameCreated = false
# monotonic identifier for nodes
_nextNodeId = 0

# BASIC TYPES
# ====================

createDispatcher = ->
  {
    listeners: {}
    register: (name, listener) ->
      if @listeners[name]?
        @listeners[name].push(listener)
      else
        @listeners[name] = [listener]
    dispatch: (name, params...) ->
      if @listeners[name]?
        l(params...) for l in @listeners[name]
  }

createNode = (x, y, color, father, moveType) ->
  {
    x: x
    y: y
    color: color
    father: father
    id: _nextNodeId++
    children: []
    moveType: moveType
    number: if father then father.number + 1 else 0

    getChildIndex: (node) ->
      return i for child, i in @children when child.id == node.id
      -1
    toStr: ->
      "[#{@x} #{@y}] #{@color}"
  }

createGame = () ->
  root = createNode(0, 0, 0, null, MoveType.ROOT)
  {
    root: root
    currNode: root
    nodeMap: {0: root}

    getColorToMove: () ->
      flipColor(@currNode.color)
  }

# global so we can access this from the console
@_game = _game = createGame()

# creates empty field on the board
setupEmptyField = (coord) ->
  pos = coordToPosCenter(coord)
  elem = $("<area id='empty_field_#{coord.x}_#{coord.y}' href='' coords='#{pos.x},#{pos.y},#{FIELD_RADIUS}' shape='circle'/>")
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

# places move representing given node on board
putNodeOnBoard = (node, allow_swap=true) ->
  if (node.moveType == MoveType.RESIGN)
    return
  if (node.moveType == MoveType.SWAP)
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
  putLastMoveMark(node.x, node.y)

# removes move representing given node from board
# handles swap move as well
removeNodeFromBoard = (node) ->
  elem = $("#move_#{node.x}_#{node.y}")
  elem.remove()
  setupEmptyField({x:node.x, y:node.y})
  # with swap add nodes father
  if (node.moveType == MoveType.SWAP)
    putNodeOnBoard(node.father)
  removeLastMoveMark(node.x, node.y)
  putLastMoveMark(node.father.x, node.father.y)

# places mark for last move from the board
putLastMoveMark = (x, y) ->
  # update last mark
  last = $("#last_stone")
  if(!last.length)
    last = $("<img alt='' style='z-index: 1; position: absolute; left: " + x + "px ; top : " + y + "px ;' galleryimg='no' id='last_stone' src='" + LAST_IMG + "'>")
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
  newNode = findElem _game.currNode.children, ((e) -> e.x == x and e.y == y and e.color == color)
  # new move
  if not newNode
    newNode = createNode(x, y, color, _game.currNode, moveType)
    newNode.father.children.push(newNode)
    _dispatcher.dispatch("createNode", newNode)
  # raise event
  _dispatcher.dispatch("playMove", newNode)

# removes last move from the board
unplayMove = () ->
  if (_game.currNode.moveType == MoveType.ROOT)
    return
  _dispatcher.dispatch("unplayMove", _game.currNode)

_dispatcher = createDispatcher()
_dispatcher.register("createNode", (node) -> console.log("Created node #{node.toStr()}"))
_dispatcher.register("playMove", (node) -> console.log("Playing node #{node.toStr()}"))
_dispatcher.register("playMove", (node) -> putNodeOnBoard(node))
_dispatcher.register("playMove", (node) -> _game.currNode = node)
_dispatcher.register("unplayMove", (node) -> console.log("Unplaying node #{node.toStr()}"))
_dispatcher.register("unplayMove", (node) -> removeNodeFromBoard(node))
_dispatcher.register("unplayMove", (node) -> _game.currNode = node.father)

# DOCUMENT FUNCTIONS
# ====================

$ ->
  setupEmptyFields()
  # TOO for debugging
  playMove(randomPos(), randomPos(), _game.getColorToMove(), MoveType.NORMAL) for i in [0...10]

_lastKey = 0

$(document).keydown((e) ->
  keydownHandler(e.which)
  # wait for a while before first timer is started
  $(document).oneTime("400ms", "keydown_timer_bootstrap", ->
    $(document).everyTime("100ms", "keydown_timer", ->
      if (_lastKey)
        keydownHandler(_lastKey)
    , 0)))

$(document).keyup((e) ->
    _lastKey = 0
    $(document).stopTime("keydown_timer")
    $(document).stopTime("keydown_timer_bootstrap"))

keydownHandler = (key) ->
  # left
  if key == 37
    if _game.currNode.father
      unplayMove()
  # right
  else if key == 39
    if _game.currNode.children.length
      node = _game.currNode.children[0]
      playMove(node.x, node.y, node.color, node.moveType)
  # up
  else if key == 38
    cycleBranches(_game.currNode, true)
  # down
  else if key == 40
    cycleBranches(_game.currNode, false)
  # u
  else if key == 88
    removeSubTree(_game.currNode)
  else
    console.log("pressed #{key}")
  _lastKey = key

