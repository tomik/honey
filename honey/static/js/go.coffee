
# ==>> CONSTANTS

ALPHABET = ("abcdefghijklmnopqrstuvwxyz").split("");
BOARD_SIZE = 19
FIELD_FIRST = {x: 16, y:16}
FIELD_X_DIFF = 26.1
FIELD_Y_DIFF = 26.1
FIELD_RADIUS = 10

WHITE_STONE_IMG = "/static/img/go_white.png"
BLACK_STONE_IMG = "/static/img/go_black.png"
LAST_WHITE_IMG  = "/static/img/go_last_white.gif"
LAST_BLACK_IMG  = "/static/img/go_last_black.gif"
BOARD_IMG  = "/static/img/go_board.png"

# ==>> BASIC ENUMS

# TODO move this into a common datastructure/utility functions module
# that will be imported before particular games modules 
GameMode = {
  PLAY: "play",
  # A, B, C, ...
  LABEL: "label",
  TRIANGLE: "triangle",
  CIRCLE: "circle",
  SQUARE: "square",
  # can clear the labels, triangle, etc.
  CLEAR: "clear",
}

MarkerType = {
  LABEL: "label",
  TRIANGLE: "triangle",
  CIRCLE: "circle",
  SQUARE: "square",
}

Color = {
  WHITE: "white",
  BLACK: "black"
}

Field = {
  EMPTY: 0,
  WHITE: 1,
  BLACK: 2,
}

MoveType = {
  NORMAL: "normal",
  ROOT: "root",
  RESIGN: "resign"
}

# ==>> DATA STRUCTURES

flipColor = (color) ->
  if color == Color.WHITE then Color.BLACK else Color.WHITE

colorToRaw = (color) ->
  if color == Color.BLACK then "B" else "W"

coordToRaw = (coord) ->
  ALPHABET[coord.x] + ALPHABET[coord.y]

rawToCoord = (raw) ->
  # Parses list of two characters to coords
  [x, y] = [ALPHABET.indexOf(raw[0]), ALPHABET.indexOf(raw[1])]
  if not ~x or not ~y
    throw "invalid coord, raw #{raw}"
  {x: x, y: y}

labelIndexToLetter = (index) ->
  ALPHABET[index % ALPHABET.length].toUpperCase()

labelLetterToIndex = (letter) ->
  ALPHABET.indexOf(letter)

class Move
  constructor: (rawMove=0) ->
    # this is the root
    if not rawMove
      return
    @color = null
    where = null
    if "W" of rawMove
      @color = Color.WHITE
      where = rawMove["W"]
    else if "B" of rawMove
      @color = Color.BLACK
      where = rawMove["B"]
    else
      console.log("Move: no playable move in " + rawMove)
      [@x, @y, @moveType] = [null, null, null]
      return
    if where == "resign"
      @moveType = MoveType.RESIGN
    else if (where.length > 2)
      throw "invalid move definition length #{where}"
    else
      coord = rawToCoord(where)
      [@x, @y, @moveType] = [coord.x, coord.y, MoveType.NORMAL]

  applies: ->
    return @x != null and @y != null and @moveType != null

  toStr: ->
    if @moveType == MoveType.RESIGN
      return "[resign]"
    "[#{@x} #{@y}] #{@color}"

  toRawDict: ->
    d = {}
    if @applies()
      d[colorToRaw(@color)] = coordToRaw({x: @x, y: @y})
    d

# produces position with center of the field (i.e. for empty field)
coordToPosCenter = (coord) ->
  x = FIELD_FIRST.x + coord.x * FIELD_X_DIFF - 1
  y = FIELD_FIRST.y + coord.y * FIELD_Y_DIFF - 1
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
  pos.x -= FIELD_RADIUS / 2 + 3
  pos.y -= FIELD_RADIUS + 2
  pos

# position within FIELD_RADIUS is transformed to coord
# if no coord corresponds to this than null is returned
posToCoord = (pos) ->
  raw_x = (pos.x - FIELD_FIRST.x) / FIELD_X_DIFF
  raw_y = (pos.y - FIELD_FIRST.y) / FIELD_Y_DIFF
  x = Math.round(raw_x)
  y = Math.round(raw_y)
  diff_x = Math.abs(x - raw_x)
  diff_y = Math.abs(y - raw_y)
  if diff_x > FIELD_RADIUS or diff_y > FIELD_RADIUS
    return null
  {x: x, y: y}

# ==>> RULES

class Group
  constructor: (@field, @stones) ->

class BoardDiff
  constructor: (@playedIndex, @captured, @koCapture) ->

# Representation of the go board.  This is very simple without any optimizations.
# Just mapping from coordinates to color occupying the intersection. All the calculations are performed online.
class Board
  constructor: (@size) ->
    # using single dimensional array
    @stones = (Field.EMPTY for i in [0...@size * @size])
    # if ko is captured we remember this(index) to prevent immediate recapturing
    @koCapture = null
    @colorToPlay = Color.BLACK

  toStr: () ->
    res = ""
    for i in [0 .. @size]
      res = res + "#{@stones[i * @size ... (i + 1) * @size]}\n"
    return res

  isValidMove: (move) ->
    [valid, diff] = @playMove(move)
    if valid
      @applyDiff(diff)
    return valid

  applyDiff: (diff) ->
    # remove what was played
    @setField(diff.playedIndex, Field.EMPTY)
    # place what was removed
    for index in diff.captured.stones
      @setField(index, diff.captured.field)
    # restore old koCapture value
    @koCapture = diff.koCapture
    @colorToPlay = flipColor(@colorToPlay)

  playMove: (move) ->
    index = @getIndex(move)
    if not @isEmpty(index)
      return [false, null]
    console.log("index vs. koCapture #{index} #{@koCapture} #{typeof(index)} #{typeof(@koCapture)} #{index == @koCapture}")
    if index == @koCapture
      return [false, null]
    field = if move.color == Color.BLACK then Field.BLACK else Field.WHITE
    @setField(index, field)
    opponentField = if field == Field.BLACK then Field.WHITE else Field.BLACK
    # for the diff
    captured = new Group(opponentField, [])
    playedIndex = index
    diffKoCapture = @koCapture
    # tiny speedup
    hasEmptyNeighbor = false
    for neighbor in @getNeighbors(index)
      console.log("checking neighbor #{neighbor}")
      empty = @isEmpty(neighbor)
      if empty
        hasEmptyNeighbor = true
      else if @getField(neighbor) != field and not @hasLiberty(neighbor)
        captured.stones.push.apply(captured.stones, @captureDragon(neighbor))
        console.log("dragon at #{neighbor} is captured stones #{captured.stones}")
    # check for self suicide
    if not hasEmptyNeighbor and not captured.stones.lenght > 0 and not @hasLiberty(index)
      @setField(index, Field.EMPTY)
      console.log("Board: move #{move.toStr()} is a suicide")
      return [false, null]
    # move is valid - make diff
    if captured.stones.length == 1
      console.log("Board: setting up ko capture at #{captured.stones[0]}")
      @koCapture = captured.stones[0]
    else
      @koCapture = null
    @colorToPlay = flipColor(@colorToPlay)
    return [true, new BoardDiff(playedIndex, captured, diffKoCapture)]

  captureDragon: (startIndex) ->
    startField = @getField(startIndex)
    if startField == Field.EMPTY
      throw "Expected non empty field"
    captured = {}
    toCheck = [startIndex]
    while toCheck.length > 0
      index = toCheck.pop()
      if index of captured
        continue
      field = @getField(index)
      if field != startField
        continue
      for neighborIndex in @getNeighbors(index)
        toCheck.push(neighborIndex)
      captured[index] = true
    # erase from the board
    for index, _ of captured
      @setField(index, Field.EMPTY)
    # TODO better
    return (parseInt(k) for k, _ of captured)

  getIndex: (coord) ->
    return coord.y * @size + coord.x

  getField: (index) ->
    return @stones[index]

  setField: (index, field) ->
    @stones[index] = field

  isEmpty: (index) ->
    return @getField(index) == Field.EMPTY

  getNeighbors: (index) ->
    neighbors = []
    # left
    if index % @size > 0
      neighbors.push(index - 1)
    # up
    if index >= @size
      neighbors.push(index - @size)
    # right
    if index % @size < @size - 1
      neighbors.push(index + 1)
    # down
    if index < @size * (@size - 1)
      neighbors.push(index + @size)
    return neighbors

  # check if the dragon starting at the given index has at least 1 liberty
  hasLiberty: (index) ->
    field = @getField(index)
    visited = {}
    if field == Field.EMPTY
      throw "Expected non empty field"
    toCheck = @getNeighbors(index)
    while toCheck.length > 0
      neighborIndex = toCheck.pop()
      if neighborIndex of visited
        continue
      neighborField = @getField(neighborIndex)
      if neighborField == Field.EMPTY
        return true
      else if neighborField == field
        for neighborNeighborIndex in @getNeighbors(neighborIndex)
          toCheck.push(neighborNeighborIndex)
      visited[neighborIndex] = true
    return false

# Wrapper around the board datastructure fitting into the event system.
class BoardModel
  constructor: () ->
    @board = new Board(19)
    # stack of board diffs
    @diffs = []

  getHandicapStones: (handicap) ->
    if handicap < 2 or handicap > 9
      return []
    if handicap == 5
      return @getHandicapStones(4).concat([[9, 9]])
    if handicap == 7
      return @getHandicapStones(6).concat([[9, 9]])
    # this works for 2, 3, 4, 6, 8, 9
    return [[15, 3], [3, 15], [15, 15], [3, 3],
      [15, 9], [3, 9], [9, 3], [9, 15], [9, 9]][0...handicap]

  onInit: (game) ->
    # handle handicap if any
    if "HA" of game.properties
      handicap = game.properties["HA"]
      if handicap > 0
        for coord in @getHandicapStones(handicap)
          move = new Move()
          [move.x, move.y, move.color, move.moveType] = [coord[0], coord[1], Color.BLACK, MoveType.NORMAL]
          # TODO use placeStone instead
          @board.playMove(move)
        @board.colorToPlay = Color.WHITE

  isValidMove: (move) ->
    return @board.isValidMove(move)

  onPlayMove: (game, node) ->
    [valid, diff] = @board.playMove(node.move)
    if not valid
      throw "BoardModel: Invalid move #{node.move.toStr()}"
    @diffs.push(diff)
    console.log("BoardModel::onPlayMove: \n" + @board.toStr())

  onUnplayMove: (move) ->
    diff = @diffs.pop()
    @board.applyDiff(diff)

# ==>> DISPLAY

# Handles proper board and its elements (stones, triangles, etc.) displaying according to the model.
class BoardView
  constructor: (@model) ->

  onInit: (game) ->
    # html board
    board = $("#board")
    board.append($("<img alt='' style='width:500px;' class='boardimage' galleryimg='no' id='boardimage' src='" + BOARD_IMG + "' border='0'/>"))
    board.css("z-index", "1")
    # drawing canvas
    topCanvas = $("<canvas id='topCanvas'></canvas>")
    $("#boardContainer").append(topCanvas)
    topCanvas.attr("width", "500")
    topCanvas.attr("height", "500")
    topCanvas.css("left", "0px")
    topCanvas.css("top", "0px")
    topCanvas.css("position", "absolute")
    topCanvas.css("z-index", "2")
    @topContext = topCanvas.get(0).getContext("2d")
    @topCanvas = topCanvas.get(0)

  onRedraw: (game) ->
    @redrawBoard(game)

  # places move representing given node on board
  redrawBoard: (game) ->
    @topContext.clearRect(0, 0, @topCanvas.width, @topCanvas.height)
    @redrawStones()
    @redrawBoardMarks(game.currNode)

  # create marks like 1 2 3 directly on board
  putChildMarkOnBoard: (coord, childIndex) ->
    @putMarkerOnBoard(MarkerType.LABEL, coord, {text: childIndex + 1})

  # create marks like A, B, C, ..., triangle, square, circle
  putMarkerOnBoard: (markerType, coord, extra) ->
    pos = coordToPosCenter({x:coord.x, y:coord.y})
    console.log "placing marker at coord #{coord.x} #{coord.y}"
    color = "white"
    # invert the color if there is a white stone
    field = @model.board.getField(@model.board.getIndex(coord))
    if field == Field.WHITE
      color = "black"
    @topContext.strokeStyle = color
    @topContext.fillStyle = color
    @topContext.lineWidth = 2
    radius = FIELD_RADIUS - 1
    if markerType == MarkerType.LABEL
      size = 2.7 * radius
      pos.x -= radius - 3
      pos.y += radius - 3
      @topContext.font = "bold #{size}px monospace"
      @topContext.fillText(extra.text, pos.x, pos.y)
    else if markerType == MarkerType.SQUARE
      radius = radius * 0.9
      @topContext.strokeRect(pos.x - radius, pos.y - radius, radius * 2, radius * 2);
    else if markerType == MarkerType.CIRCLE
      radius = radius * 0.9
      @topContext.beginPath()
      @topContext.arc(pos.x, pos.y, radius, 2 * Math.PI, false);
      @topContext.stroke()
    else if markerType == MarkerType.TRIANGLE
      radius = radius * 0.9
      # correction in the horizontal axis
      x_corr = radius
      # correction in the vertical axis
      y_corr = Math.sqrt(3) * radius / 2
      # TODO equilateral triangle
      @topContext.beginPath()
      @topContext.moveTo(pos.x - x_corr, pos.y + y_corr);
      @topContext.lineTo(pos.x + x_corr, pos.y + y_corr);
      @topContext.lineTo(pos.x, pos.y - x_corr);
      @topContext.lineTo(pos.x - x_corr, pos.y + y_corr);
      @topContext.stroke()
    else
      console.log "cannot draw market type #{markerType}"

  #updates move marks and board marks
  redrawStones: () ->
    # hardcore TODO change
    $(".move").remove()
    for field, i in @model.board.stones
      x = i % @model.board.size
      y = Math.floor(i / @model.board.size)
      coord = {x: x, y: y}
      if field != Field.EMPTY
        pos = coordToPosCenter(coord)
        # draw field
        beginColor =  if field == Field.BLACK then "#4C4646" else "#FFFFFF"
        endColor =  if field == Field.BLACK then "#000000" else "#DDDDDD"
        radius = FIELD_RADIUS + 2
        grd = @topContext.createRadialGradient(pos.x - radius / 2, pos.y - radius / 2, 2, pos.x - radius / 2, pos.y - radius / 2, radius)
        grd.addColorStop(0, beginColor)
        grd.addColorStop(1, endColor)
        @topContext.fillStyle = grd
        @topContext.strokeStyle = "black"
        @topContext.shadowColor = "#000"
        @topContext.shadowBlur = 2
        @topContext.shadowX = 1
        @topContext.shadowY = 1
        @topContext.strokeWidth = 1
        @topContext.beginPath()
        @topContext.arc(pos.x, pos.y, radius, 2 * Math.PI, false);
        @topContext.fill()

  #updates move marks and board marks
  redrawBoardMarks: (placedNode) ->
    # last move mark
    if placedNode.father
      @updateLastMoveMark(placedNode.move.x, placedNode.move.y, placedNode.move.color)
    # TODO limit max number of marks
    if placedNode.children.length > 1
      @putChildMarkOnBoard(child.move, i) for child, i in placedNode.children
    # markers
    for marker, coords of placedNode.markers
      for coord, index in coords
        extra = if marker == MarkerType.LABEL then {text: labelIndexToLetter(index)} else {}
        @putMarkerOnBoard(marker, coord, extra)

  # places mark for last move from the board
  updateLastMoveMark: (x, y, color) ->
    @putMarkerOnBoard(MarkerType.CIRCLE, {x:x, y:y}, {})

  # ==>> CONTROLLER

# Handles user interaction with the board.
class BoardController
  constructor: (@model) ->
    @game = null

  onInit: (game) ->
    @game = game
    board = $("#topCanvas")
    board.click((e) =>
      x = e.pageX - $(e.target).offset().left
      y = e.pageY - $(e.target).offset().top
      coord = posToCoord({x: x, y: y})
      @clickHandler(coord)
      e.preventDefault()
    )

  clickHandler: (coord) ->
    mode = @game.gameMode
    if mode == GameMode.PLAY
      move = new Move()
      [move.x, move.y, move.color, move.moveType] = [coord.x, coord.y, @model.board.colorToPlay, MoveType.NORMAL]
      @game.playMove(move)
    else
      # prevent markers overwriting
      if @game.hasMarker(coord) and mode != GameMode.CLEAR
        return
      if mode == GameMode.TRIANGLE
        @game.placeMarker(coord, MarkerType.TRIANGLE)
      else if mode == GameMode.CIRCLE
        @game.placeMarker(coord, MarkerType.CIRCLE)
      else if mode == GameMode.SQUARE
        @game.placeMarker(coord, MarkerType.SQUARE)
      else if mode == GameMode.LABEL
        @game.placeMarker(coord, MarkerType.LABEL)
      else if mode == GameMode.CLEAR
        @game.clearMarker(coord)
      else
        alert("unknown mode")

# ==>> EXPORT

@BoardView = BoardView
@Move = Move
@BoardController = BoardController
@BoardModel = BoardModel

@GameMode = GameMode
@MarkerType = MarkerType
@coordToRaw = coordToRaw
@rawToCoord = rawToCoord
@labelIndexToLetter = labelIndexToLetter
@labelLetterToIndex = labelLetterToIndex

