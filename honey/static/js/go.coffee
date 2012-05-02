
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
    else if (x = ALPHABET.indexOf(where[0])) == -1 or (y = ALPHABET.indexOf(where[1])) == -1
      throw "invalid move definition #{where}"
    else
      [@x, @y, @moveType] = [x, y, MoveType.NORMAL]

  applies: ->
    return @x != null and @y != null and @moveType != null

  toStr: ->
    if @moveType == MoveType.RESIGN
      return "[resign]"
    "[#{@x} #{@y}] #{@color}"

  toRawDict: ->
    d = {}
    d[colorToRaw(@color)] = coordToRaw({x: @x, y: @y})
    d

# produces position with center of the field (i.e. for empty field)
coordToPosCenter = (coord) ->
  x = FIELD_FIRST.x + coord.x * FIELD_X_DIFF
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

class Model
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
      throw "Model: Invalid move #{node.move.toStr()}"
    @diffs.push(diff)
    console.log("Model::onPlayMove: \n" + @board.toStr())

  onUnplayMove: (move) ->
    diff = @diffs.pop()
    @board.applyDiff(diff)

# ==>> DISPLAY

class Display
  constructor: (@model) ->

  onInit: (game) ->
    # html board
    board = $("#board")
    board.append($("<img alt='' style='width:500px;' class='boardimage' galleryimg='no' id='boardimage' src='" + BOARD_IMG + "' border='0'/>"))

  onRedraw: (game) ->
    @redrawBoard(game)
    Display.updateBoardMarks(game.currNode)

  # places move representing given node on board
  redrawBoard: (game) ->
    # hardcore TODO change
    $(".move").remove()
    for field, i in @model.board.stones
      x = i % @model.board.size
      y = Math.floor(i / @model.board.size)
      coord = {x: x, y: y}
      if field != Field.EMPTY
        # draw field
        src = if field == Field.BLACK then BLACK_STONE_IMG else WHITE_STONE_IMG
        pos = coordToPosTopLeft(coord)
        elem = $("<img alt='' class='move' style='position: absolute; left: #{pos.x}px; top:#{pos.y}px;'
                  galleryimg='no' id='move_#{x}_#{y}' src='#{src}'>")
        elem.appendTo("#board")

  # removes all old marks
  @removeChildMarks: ->
    $(".child_mark").remove()

  # create marks like 1 2 3 directly on board
  @putChildMarkOnBoard: (node, childIndex) ->
    pos = coordToPosForText({x:node.move.x, y:node.move.y})
    elem = $("<div class='child_mark' style='background-color: white; position: absolute; left: #{pos.x}px; top:#{pos.y}px;
              padding-left: 3px; padding-right: 3px; padding-top: 2px; padding-bottom: 2px;'
              id='child_mark_#{node.move.x}_#{node.move.y}'>#{childIndex + 1}</div>")
    elem.appendTo("#board")

  #updates move marks and board marks
  @updateBoardMarks: (placedNode) ->
    if placedNode.father
      Display.updateLastMoveMark(placedNode.move.x, placedNode.move.y, placedNode.move.color)
    else
      Display.removeLastMoveMark()
    Display.removeChildMarks()
    # TODO limit max number of marks
    if placedNode.children.length > 1
      Display.putChildMarkOnBoard(child, i) for child, i in placedNode.children

  # places mark for last move from the board
  @updateLastMoveMark: (x, y, color) ->
    # update last mark
    last = $("#last_stone")
    if(!last.length)
      last = $("<img alt='' style='z-index: 1; position: absolute;
                left: #{x}px ; top : #{y}px ;' galleryimg='no' id='last_stone'>")
      last.appendTo("#board")
    src = if color == Color.BLACK then LAST_BLACK_IMG else LAST_WHITE_IMG
    last.attr("src", src)
    pos = coordToPosTopLeft({x:x, y:y})
    last.css("left", pos.x)
    last.css("top", pos.y)
    last.show()

  # removes mark for last move from the board
  @removeLastMoveMark: ->
    last = $("#last_stone")
    if(last)
      last.hide()

# ==>> CONTROLLER

class Controller
  constructor: (@model) ->
    @game = null

  onInit: (game) ->
    @game = game
    board = $("#board")
    board.click((e) =>
      x = e.pageX - $(e.target).offset().left
      y = e.pageY - $(e.target).offset().top
      coord = posToCoord({x: x, y: y})
      @clickHandler(coord)
      e.preventDefault()
    )

  clickHandler: (coord) ->
    move = new Move()
    [move.x, move.y, move.color, move.moveType] = [coord.x, coord.y, @model.board.colorToPlay, MoveType.NORMAL]
    @game.playMove(move)

# ==>> EXPORT

@Display = Display
@Move = Move
@Controller = Controller
@Model = Model

