
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

# ==>> DATA STRUCTURES

flipColor = (color) ->
  if color == Color.BLUE then Color.RED else Color.BLUE

colorToSgf = (color) ->
  if color == Color.BLUE then "B" else "W"

coordToSgf = (coord) ->
  ALPHABET[coord.x] + ALPHABET[coord.y]

class HexMove
  constructor: (rawMove=0) ->
    if not rawMove
      return
    @color = null
    where = null
    if "W" of rawMove
      @color = Color.RED
      where = rawMove["W"]
    else if "B" of rawMove
      @color = Color.BLUE
      where = rawMove["B"]
    else
      console.log(rawMove)
      throw "Invalid node"
    if where == "resign"
      @moveType = MoveType.RESIGN
    else if (where == "swap")
      @moveType = MoveType.SWAP
    else if (where.length > 2)
      throw "invalid move definition length #{where}"
    else if (x = ALPHABET.indexOf(where[0])) == -1 or (y = ALPHABET.indexOf(where[1])) == -1
      throw "invalid move definition #{where}"
    else
      [@x, @y, @moveType] = [x, y, MoveType.NORMAL]

  toStr: ->
    if @moveType == MoveType.RESIGN
      return "[resign]"
    "[#{@x} #{@y}] #{@color}"

  toSgfDict: ->
    d = {}
    if @moveType == MoveType.SWAP
      d[colorToSgf(@color)] = "swap"
    else
      d[colorToSgf(@color)] = coordToSgf({x: @x, y: @y})
    d

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

# ==>> RULES


# ==>> DISPLAY

# places move representing given node on board
putNodeOnBoard = (node, allowSwap=true) ->
  if not node.father
    return
  if (node.move.moveType == MoveType.SWAP and allowSwap)
    removeNodeFromBoard(node.father)
    return putNodeOnBoard(node, false)
  move = node.move
  # TODO this function should be read only
  if node.move.moveType == MoveType.SWAP
    move.x = node.father.move.y
    move.y = node.father.move.x
    move.color = flipColor(node.father.move.color)
  # remove empty field on that location
  elem = $("#empty_field_#{move.x}_#{move.y}")
  elem.remove()
  # add new empty field
  pos = coordToPosTopLeft({x:move.x, y:move.y})
  imgLocation = if move.color == Color.RED then STONE_IMG_RED else STONE_IMG_BLUE
  elem = $("<img alt='' class='move' style='position: absolute; left: #{pos.x}px; top:#{pos.y}px;'
            galleryimg='no' id='move_#{move.x}_#{move.y}' src='#{imgLocation}'>")
  elem.appendTo("#board")
  updateBoard(node)

# removes all old marks
removeChildMarks = ->
  $(".child_mark").remove()

# create marks like 1 2 3 directly on board
putChildMarkOnBoard = (node, childIndex) ->
  pos = coordToPosForText({x:node.move.x, y:node.move.y})
  elem = $("<div class='child_mark' style='position: absolute; left: #{pos.x}px; top:#{pos.y}px;'
            id='child_mark_#{node.move.x}_#{node.move.y}'>#{childIndex + 1}</div>")
  elem.appendTo("#board")

#updates move marks and board marks
updateBoard = (placedNode) ->
  if placedNode.father
    updateLastMoveMark(placedNode.move.x, placedNode.move.y)
  else
    removeLastMoveMark()
  removeChildMarks()
  # TODO limit max number of marks
  if placedNode.children.length > 1
    putChildMarkOnBoard(child, i) for child, i in placedNode.children

# removes move representing given node from board
# handles swap move as well
removeNodeFromBoard = (node) ->
  elem = $("#move_#{node.move.x}_#{node.move.y}")
  elem.remove()
  # with swap add nodes father
  if (node.move.moveType == MoveType.SWAP)
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

class HexDisplay
  onInit: (game) ->
    # html board
    board = $("#board")
    board.append($("<img alt='' class='boardimage' galleryimg='no' id='boardimage' src='/static/img/board.gif' usemap='#empty_fields' border='0'/>"))

  onPlayMove: (game, node) ->
    if node.move.moveType == MoveType.RESIGN
      return
    putNodeOnBoard(node)

  onUnPlayMove: (game, node) ->
    removeNodeFromBoard(node)

# ==>> CONTROLLER

class HexController
  constructor: () ->
    @game = null

  onInit: (game) ->
    @game = game
    board = $("#board")
    board.append($("<map id='empty_fields' name='empty_fields'>"))
    @setupEmptyFields()

  # creates empty field on the board
  setupEmptyField: (coord) ->
    pos = coordToPosCenter(coord)
    elem = $("<area id='empty_field_#{coord.x}_#{coord.y}' href=''
              coords='#{pos.x},#{pos.y},#{FIELD_RADIUS}' shape='circle'/>")
    elem.appendTo("#empty_fields")
    # cannot use @game directly in the event because of javascript quirkiness in this
    game = @game
    elem.click((e) ->
        e.preventDefault()
        move = new Move()
        # this is pretty much the only place that makes any assumptions about game object
        [move.x, move.y, move.color, move.moveType] = [coord.x, coord.y, flipColor(game.currNode.move.color), MoveType.Normal]
        game.playMove(move))

  # setups all empty fields on board
  setupEmptyFields: () ->
    for i in [0...BOARD_SIZE * BOARD_SIZE]
      coord =
        x: i % BOARD_SIZE
        y: Math.floor(i / BOARD_SIZE)
      @setupEmptyField(coord)

  onUnPlayMove: (game, node) ->
    @setupEmptyField({x:node.move.x, y:node.move.y})

# ==>> EXPORT

@Display = HexDisplay
@Move = HexMove
@Controller = HexController

