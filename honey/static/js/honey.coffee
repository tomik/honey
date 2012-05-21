
# ==>> UTILITY FUNCTIONS

# finds element in array satisfying f and returns it
# if not present returns null
findElem = (a, f) ->
  return e for e in a when f(e)
  null

# finds elem in array satisfying f and returns its index
# returns -1 if not present
findElemIndex = (a, f) ->
  return idx for e, idx in a when f(e)
  -1

# checks whether some elem satisfyies f
someElem = (a, f) ->
  return true for e in a when f(e)
  false

coordsEqual = (c1, c2) ->
  return c1.x == c2.x and c1.y == c2.y

randomPos = ->
 Math.floor(Math.random() * (BOARD_SIZE - 1))

isArray = (obj) ->
  return Object.prototype.toString.call(obj) == '[object Array]'

# ==>> BASIC TYPES

class EventDispatcher
  ###
  # This class raises events for the listeners.
  #
  # The events can be following:
  #
  # onInit(game) - raised after the root node (with game information) is loaded
  # onLoad(game) - raised when nodes were loaded but before the initial position is setup
  # onPlayMove(game, node) - raised after current node is updated forward
  # onUnplayMove(game, node) - raised after current node is updated backward
  # onCreateNode(game, node) - raised when new node is created
  #
  # Notes:
  # * Node structure initialization from the input format is done without raising play/unplay events.
  # * New moves (not following existing line of play) must pass model.isValidMove Before onPlayMove is raised
  # * Listener is invoked if it contains a function with the same name as the event (i.e. onLoad)
  ###
  listeners: []

  register: (listener) ->
    @listeners.push(listener)

  dispatch: (name, params...) ->
    for listener in @listeners
      if name of listener
        listener[name](params...)

class Node
  @nextNodeId: 0
  constructor: (@move, @father) ->
    @id = Node.nextNodeId++
    @children = []
    @number = if @father then @father.number + 1 else 0
    # mapping: markerType -> list of coords
    @markers = {}

  @fromMove: (move, father) ->
    new Node(move, father)

  @fromRaw: (raw, father) ->
    move = new Move(raw)
    #if not move.applies()
      #return null
    node = new Node(move, father)
    node.importMarkers(raw)
    node

  getChildIndex: (node) ->
    return i for child, i in @children when child.id == node.id
    -1

  hasBranches: () ->
    return @children.length > 1

  toStr: () ->
    return "{id #{@id} move #{@move.toStr()}}"

  @markerSGFMapping = [
    [MarkerType.TRIANGLE, "TR"],
    [MarkerType.CIRCLE, "CR"],
    [MarkerType.SQUARE, "SQ"],
    [MarkerType.LABEL, "LB"]]

  importMarkers: (rawNode) ->
    # loads the markers from raw definition
    for markerPair in Node.markerSGFMapping
      [marker, sgf] = markerPair
      if not (sgf of rawNode)
        continue
      if not (marker of @markers)
        @markers[marker] = []
      if marker == MarkerType.LABEL
        # temporary list of pairs [index, coord] for board labels (A, B, C)
        # after all the labels are processed they will be ordered based on this
        labels = []
        for rawStr in rawNode[sgf]
          # rawStr format should be xx:Y
          # where xx are coords and Y is a label
          if not rawStr.match(/^[a-z][a-z]:[A-Z]$/)
            console.log("invalid label string format #{rawStr}")
            continue
          coord = rawToCoord(rawStr[0...2])
          index = labelLetterToIndex(rawStr[rawStr.length - 1])
          labels.push([index, coord])
        labels.sort((a, b) -> a[0] - b[0])
        @markers[marker] = (labelPair[1] for labelPair in labels)
      else
        for rawMarker in rawNode[sgf]
          @markers[marker].push(rawToCoord(rawMarker))
    return null

  marker2SGF: (markerType) ->
    # performs mapping from markerType to sgf
    for markerPair in Node.markerSGFMapping
      [marker, sgf] = markerPair
      if markerType == marker
        return sgf
    return null

  export: () ->
    # export node to raw format for update on the server
    d = @move.toRawDict()
    # annotate with markers
    for marker, coords of @markers
      markerSGF = @marker2SGF(marker)
      if markerSGF
        rawCoords = (coordToRaw(coord) for coord in coords)
        if marker == MarkerType.LABEL
          d[markerSGF] = ("#{rawCoord}:#{labelIndexToLetter(index)}" for rawCoord, index in rawCoords)
        else
          d[markerSGF] = rawCoords
    d

# ==>> RAW FORMAT PARSING AND OUTPUTTING

rawParseNodes = (nodes, handler) ->
  for node in nodes
    # variants
    if isArray(node)
      for variant in node
        handler.onBranchStart()
        rawParseNodes(variant, handler)
        handler.onBranchStop()
    else
      handler.onRawNode(node)

rawParse = (nodes, handler, initializer) ->
  if nodes.length <= 0
    return
  gameNode = nodes[0]
  handler.onGameProperty(propName, propValue) for propName, propValue of gameNode
  _game.root = _game.currNode = Node.fromRaw(gameNode, null)
  initializer()
  rawParseNodes(nodes[1...nodes.length], handler)

# parsing object
class RawParseHandler
  constructor: (@game) ->
    # stack of nodes where branching happens
    # used for jumping back once branch is finished
    @junctionStack = []

  onGameProperty: (propName, propValue) ->
    console.log("game property #{propName}=#{propValue}")
    @game.properties[propName] = propValue

  onRawNode: (rawNode) ->
    # create the node for the move
    # we don't question node's validity as the model is not invoked at all
    newNode = Node.fromRaw(rawNode, @game.currNode)
    if newNode
      newNode.father.children.push(newNode)
      @game.currNode = newNode

  onBranchStart: ->
    @junctionStack.push(@game.currNode)

  onBranchStop: ->
    if @junctionStack.length < 1
      throw "parsing error"
    topNode = @junctionStack.pop()
    while @game.currNode != topNode
      @game.currNode = @game.currNode.father

# ==>> Game Logic

class Game
  constructor: () ->
    @currNode = @root = null
    @properties = {}
    @synced = null
    @pastebin = null
    @gameMode = GameMode.PLAY
    @setSynced(true)

  jumpToRoot: () ->
    @currNode = @root

  # shortcut for playing existing nodes
  playNode: (node, redraw) ->
    return @playMove(node.move, redraw)

  # plays a move on the board and updates data structures
  playMove: (move, redraw=true) ->
    # TODO prevent playing resign moves
    #if node.move.moveType == MoveType.RESIGN or not node.father
      #return
    [x, y, color, moveType] = [move.x, move.y, move.color, move.moveType]
    # are we continuing in the existing branch ?
    newNode = findElem @currNode.children, ((e) -> e.move == move)
    if not _boardModel.isValidMove(move)
      console.log("Game: invalid move #{move.toStr()}")
      return false
    # new move
    if not newNode
      newNode = new Node(move, @currNode)
      newNode.father.children.push(newNode)
      _dispatcher.dispatch("onCreateNode", this, newNode)
      @setSynced(false)
    @currNode = newNode
    _dispatcher.dispatch("onPlayMove", this, newNode)
    if redraw
      _dispatcher.dispatch("onRedraw", this)
    return true

  # removes last move from the board
  unplayMove: (redraw=true) ->
    if not @currNode.father
      return
    node = @currNode
    @currNode = @currNode.father
    _dispatcher.dispatch("onUnplayMove", this, node)
    if redraw
      _dispatcher.dispatch("onRedraw", this)

  # Check whether there is a marker for the given marker type.
  # If the markerType is null all markerTypes are checked.
  hasMarker: (coord, markerType=null) ->
    if markerType == null
      for markerType, coords of @currNode.markers
        if someElem coords, ((c) -> coordsEqual(c, coord))
          return true
    else if markerType of @currNode.markers
      return someElem @currNode.markers[markerType], ((c) -> coordsEqual(c, coord))
    return false

  # Places marker of given type (triangle, square, circle, label) on a given coord.
  placeMarker: (coord, markerType) ->
    if @hasMarker(coord, markerType)
      throw "Already has a marker of type #{markerType} on coord #{coord}"
    if not (markerType of @currNode.markers)
      @currNode.markers[markerType] = []
    @currNode.markers[markerType].push(coord)
    @setSynced(false)
    _dispatcher.dispatch("onPlaceMarker", this, @currNode, coord)
    _dispatcher.dispatch("onRedraw", this)

  # Clears the given coord from markers.
  clearMarker: (coord) ->
    if not @hasMarker(coord)
      console.log "No marker on coord #{coord.x} #{coord.y}"
    for markerType, coords of @currNode.markers
      index = findElemIndex coords, ((c)-> coordsEqual(c, coord))
      if ~index
        coords.splice(index, 1)
        break
    @setSynced(false)
    _dispatcher.dispatch("onClearMarker", this, @currNode, coord)
    _dispatcher.dispatch("onRedraw", this)

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
        console.log("Warning: Invalid branch")
        return
      for i in [0...jump]
        node = node.children[branch]
        redraw = true
        @playNode(node, redraw)
        # branch only once
        branch = 0

  # returns a json object representing current node tree
  # this is in the same format as input
  # this can be directly used to replace game.nodes (starting after root)
  exportNodes: (node) ->
    nodes = []
    raw = node.export()
    # push game properties to root
    if not node.father
      for prop, value of @properties when not (prop of raw)
        raw[prop] = value
    nodes.push(raw)
    while true
      if node.children.length > 1
        variants = []
        for child in node.children
          variants.push(@exportNodes(child))
        nodes.push(variants)
        break
      else if node.children.length == 1
        nodes.push(node.children[0].export())
        node = node.children[0]
      else
        break
    return nodes

  # return whether the game is synced to the server data
  isSynced: () ->
    return @synced

  setSynced: (value) ->
    if value != @synced
      @synced = value
      if @synced
        _dispatcher.dispatch("onSynced", this)
      else
        _dispatcher.dispatch("onUnsynced", this)

  # only applicable if not in the root node
  # unplays the current move and cuts the node with whole subtree
  # stores the cut in the pastebin for later pasting
  cut: () ->
    if _game.currNode.father
      previous = _game.currNode
      @pastebin = _game.currNode
      # redraw is done explicitly after the node is removed
      # this is necessary to prevent i.e. child mark placing
      redraw = false
      _game.unplayMove(redraw)
      idx = _game.currNode.children.indexOf(previous)
      _game.currNode.children.splice(idx, 1)
      @setSynced(false)
      _dispatcher.dispatch("onRedraw", this)

  # pastes the content of pastebin after current node
  # creates a variation if necessary
  paste: () ->
    if @pastebin
      _game.currNode.children.push(@pastebin)
      @pastebin.father = _game.currNode
      _dispatcher.dispatch("onRedraw", this)
      @setSynced(false)

  changeMode: () ->
    previous = null
    first = null
    for mode, value of GameMode
      console.log(mode)
      if not first
        first = value
      if previous == @gameMode
        @gameMode = value
        _dispatcher.dispatch("onChangeMode", @gameMode)
        return
      previous = value
    if previous == @gameMode
      @gameMode = first
    _dispatcher.dispatch("onChangeMode", @gameMode)

# ==>> Logging

class Logger
  onInit: (game) ->
    console.log("Logger: received onInit")

  onLoad: (game) ->
    console.log("Logger: received onLoad")

  onCreateNode: (game, node) ->
    console.log("Logger: received onCreateNode node #{node.toStr()}")

  onPlayMove: (game, node) ->
    console.log("Logger: received onPlayMove node #{node.toStr()}")

  onUnplayMove: (game, node) ->
    console.log("Logger: received onUnplayMove node #{node.toStr()}")

  onPlaceMarker: (game, node, coord) ->
    console.log("Logger: received onPlaceMarker node #{node.toStr()} coord #{coord.x} #{coord.y}")

  onClearMarker: (game, node, coord) ->
    console.log("Logger: received onClearMarker node #{node.toStr()} coord #{coord.x} #{coord.y}")

  onRedraw: (game) ->
    console.log("Logger: received onRedraw")

  onChangeMode: (newMode) ->
    console.log("Logger: received onChangeMode newMode #{newMode}")

  onSynced: (game) ->
    console.log("Logger: received onSynced")

  onUnsynced: (game) ->
    console.log("Logger: received onUnsynced")

# ==>> BRIDGE

class Bridge
  # This class handles communication with the UI eventHandler (view).
  constructor: (inputRaw, initPath, eventHandler) ->
    @game = _game
    @inputRaw = inputRaw
    @initPath = initPath
    @eventHandler = eventHandler
    # whether the board key shortcuts apply
    @focus = true
    # TODO this is ugly
    # objects should be registered with _dispatched at one place
    _dispatcher.register(@eventHandler)

  getCurrNodeShortPath: () ->
    # Returns short path to current node in json format as [(branch, node), ...].
    # Example:
    # [(0, 7), (1, 3)] means:
    # Move on 7th node in the main branch, then move to the 3rd node on the first branch
    return @game.getNodeShortPath(@game.currNode)

  getNodes: () ->
    # Returns full node tree without root.
    @game.exportNodes(@game.root)

  syncGame: () ->
    @game.setSynced(true)

  isGameSynced: () ->
    return @game.isSynced()

  setFocus: (value) ->
    @focus = value

  hasFocus: () ->
    @focus

# ==>> GLOBALS

_lastKey = 0
_logger = new Logger()
_dispatcher = new EventDispatcher()
_boardModel = new BoardModel()
_dispatcher.register(_logger)
_dispatcher.register(_boardModel)
_dispatcher.register(new BoardView(_boardModel))
_dispatcher.register(new BoardController(_boardModel))
# global so we can access this from the console
@_game = _game = new Game
# global this is accessed by the template
@Bridge = Bridge

# ==>> DOCUMENT FUNCTIONS

# load position
$ ->
  # onInit is run after the init node is loaded
  initializer = () -> 
    _dispatcher.dispatch("onInit", _game)
  # creates the node structure with moves
  rawParse(_bridge.inputRaw, new RawParseHandler(_game), initializer)
  _game.jumpToRoot()
  _dispatcher.dispatch("onLoad", _game)
  if _bridge.initPath.length > 0
    # follow the init path
    # this is the short path ([[branchId, jump], [branchId, jump], ...])
    _game.followNodeShortPath(_bridge.initPath)
  else
    _dispatcher.dispatch("onRedraw", _game)

# handle keydown including holding the key
$(document).keydown((e) ->
  if not _bridge.hasFocus()
    return
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
  redraw = true
  # move shortcuts 1 - 9
  if key in [49...58]
    variant = key - 49
    if _game.currNode.children.length > variant
      node = _game.currNode.children[variant]
      _game.playNode(node, redraw)
  # left
  else if key == 37
    if _game.currNode.father
      _game.unplayMove(redraw)
      # this event is repeatable
      return true
  # right
  else if key == 39
    if _game.currNode.children.length
      node = _game.currNode.children[0]
      _game.playNode(node, redraw)
      # this event is repeatable
      return true
  # up - go to last junction
  else if key == 38
    if _game.currNode.father
      _game.unplayMove(not redraw)
      while _game.currNode.father and not _game.currNode.hasBranches()
        _game.unplayMove(not redraw)
      _dispatcher.dispatch("onRedraw", _game)
      return true
  # down - go to next junction
  else if key == 40
    if _game.currNode.children.length
      _game.playNode(_game.currNode.children[0], not redraw)
      while _game.currNode.children.length and not _game.currNode.hasBranches()
        if not _game.playNode(_game.currNode.children[0], not redraw)
          break
      _dispatcher.dispatch("onRedraw", _game)
      return true
  # cut current node and its subtree
  else if key == 88
    _game.cut()
  # paste after current node
  else if key == 80
    _game.paste()
  # mode change
  else if key == 77
    _game.changeMode()
  else
    console.log("pressed #{key}")

  _lastKey = key
  # most of the events are not repeatable
  false

